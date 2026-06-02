"""Canonical Sequenceable protocol and adapter registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

from chordelia.score import ScoreEvent, ScoreEventContext
from chordelia.rhythm import Duration

if TYPE_CHECKING:
    from chordelia.intervals import IntervalLike
    from chordelia.notes import Note


DurationLike = Duration | int | float


@dataclass(frozen=True, slots=True)
class SequenceRender:
    """Unified sequenceable render output: emitted events plus consumed span."""

    events: tuple[ScoreEvent, ...]
    consumed_duration: DurationLike

    def __post_init__(self) -> None:
        consumed_duration = _coerce_consumed_duration(self.consumed_duration)
        events = tuple(self.events)
        for event in events:
            if not isinstance(event, ScoreEvent):
                raise TypeError(
                    "SequenceRender events must contain ScoreEvent values, "
                    f"got {type(event).__name__}."
                )
            if event.beat.mode != consumed_duration.mode or event.duration.mode != consumed_duration.mode:
                raise ValueError(
                    "SequenceRender events and consumed_duration must use the same timing mode "
                    f"(got event mode {event.beat.mode!r} and consumed mode {consumed_duration.mode!r})."
                )

        object.__setattr__(self, "events", events)
        object.__setattr__(self, "consumed_duration", consumed_duration)


SequenceableAdapter = Callable[[Any, ScoreEventContext], SequenceRender]

_ADAPTER_REGISTRY: dict[type[Any], SequenceableAdapter] = {}


@runtime_checkable
class Sequenceable(Protocol):
    """Protocol for values that can render and transpose in sequence workflows."""

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        """Emit normalized score events and consumed span for the provided context."""

    def transpose(self, interval: 'IntervalLike') -> 'Sequenceable':
        """Return a transposed value that preserves sequenceable behavior."""


@runtime_checkable
class NotesLike(Protocol):
    """Protocol for values that can represent zero or more notes."""

    def to_notes(self) -> tuple[Note, ...]:
        """Return the note collection represented by this value."""


def _register_sequenceable_adapter(type_: type[Any], adapter: SequenceableAdapter) -> None:
    """Register an adapter for values that do not implement Sequenceable directly."""
    if not isinstance(type_, type):
        raise TypeError(f"type_ must be a type, got {type_!r}")
    if not callable(adapter):
        raise TypeError("adapter must be callable")
    _ADAPTER_REGISTRY[type_] = adapter


def _unregister_sequenceable_adapter(type_: type[Any]) -> None:
    """Remove a previously registered adapter when present."""
    _ADAPTER_REGISTRY.pop(type_, None)


def _clear_sequenceable_adapters() -> None:
    """Clear all registered adapters, useful in tests."""
    _ADAPTER_REGISTRY.clear()


def _coerce_consumed_duration(value: DurationLike) -> Duration:
    """Coerce consumed span values into beat/time Duration values."""
    if isinstance(value, Duration):
        duration = value
    else:
        duration = Duration.from_beats(value, None)

    if duration.mode == "note_fraction":
        raise ValueError(
            "consumed_duration must be beat-based or time-based Duration. "
            "Use Duration.from_beats(...) or Duration.from_seconds(...)."
        )

    if duration.mode == "seconds":
        non_positive = duration.as_seconds() <= 0
    else:
        non_positive = duration.as_beats() <= 0
    if non_positive:
        raise ValueError(f"consumed_duration must be > 0, got {duration}")

    return duration


def _sequence_render_for(value: Any, context: ScoreEventContext) -> SequenceRender:
    """Convert any supported value into a unified sequence render output."""
    if isinstance(value, Sequenceable):
        result = value.render_for_context(context)
    else:
        adapter = _find_adapter(value)
        if adapter is None:
            raise TypeError(
                f"{type(value).__name__} is not Sequenceable and has no registered adapter. "
                "Register one with _register_sequenceable_adapter(...)."
            )
        result = adapter(value, context)

    if not isinstance(result, SequenceRender):
        raise TypeError(
            "Sequenceable conversion must return SequenceRender values, "
            f"got {type(result).__name__}."
        )

    return result


def _find_adapter(value: Any) -> SequenceableAdapter | None:
    """Resolve adapter by scanning MRO for exact and base-type registrations."""
    for type_ in type(value).__mro__:
        adapter = _ADAPTER_REGISTRY.get(type_)
        if adapter is not None:
            return adapter
    return None
