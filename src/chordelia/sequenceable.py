"""Canonical Sequenceable protocol and adapter registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

from chordelia.score import ScoreEvent, ScoreEventContext

if TYPE_CHECKING:
    from chordelia.notes import Note


SequenceableAdapter = Callable[[Any, ScoreEventContext], tuple[ScoreEvent, ...]]

_ADAPTER_REGISTRY: dict[type[Any], SequenceableAdapter] = {}


@runtime_checkable
class Sequenceable(Protocol):
    """Protocol for values that can emit score events under a context."""

    def score_events_for_context(self, context: ScoreEventContext) -> tuple[ScoreEvent, ...]:
        """Emit normalized score events for the provided context."""


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


def _score_events_for(value: Any, context: ScoreEventContext) -> tuple[ScoreEvent, ...]:
    """Convert any supported value into a tuple of score events."""
    if isinstance(value, Sequenceable):
        raw_events = value.score_events_for_context(context)
    else:
        adapter = _find_adapter(value)
        if adapter is None:
            raise TypeError(
                f"{type(value).__name__} is not Sequenceable and has no registered adapter. "
                "Register one with _register_sequenceable_adapter(...)."
            )
        raw_events = adapter(value, context)

    events = tuple(raw_events)
    for event in events:
        if not isinstance(event, ScoreEvent):
            raise TypeError(
                "Sequenceable conversion must return ScoreEvent values, "
                f"got {type(event).__name__}."
            )
    return events


def _find_adapter(value: Any) -> SequenceableAdapter | None:
    """Resolve adapter by scanning MRO for exact and base-type registrations."""
    for type_ in type(value).__mro__:
        adapter = _ADAPTER_REGISTRY.get(type_)
        if adapter is not None:
            return adapter
    return None
