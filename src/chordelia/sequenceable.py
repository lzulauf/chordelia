"""Canonical Sequenceable protocol and conversion boundary helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable, TypeAlias

from chordelia.score import ScoreEvent, ScoreEventContext
from chordelia.rhythm import Duration, TimelineLike, coerce_timeline_duration

if TYPE_CHECKING:
    from chordelia.intervals import IntervalLike
    from chordelia.notes import Note
    from chordelia.scales import Scale


DurationLike: TypeAlias = TimelineLike


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


@runtime_checkable
class Sequenceable(Protocol):
    """Protocol for values that can render and transpose in sequence workflows."""

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        """Emit normalized score events and consumed span for the provided context."""

    def transpose(self, interval: 'IntervalLike | int') -> 'Sequenceable':
        """Return a transposed value that preserves sequenceable behavior."""


@runtime_checkable
class PlayableSource(Protocol):
    """Protocol for values that can be normalized into timed score events."""

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        """Emit normalized score events and consumed span for playback/export."""


@runtime_checkable
class VisualRenderableSource(Protocol):
    """Protocol for values that can be rendered in visual score workflows."""

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        """Emit normalized score events and consumed span for notation rendering."""


@runtime_checkable
class SheetMusicScaleResolver(Protocol):
    """Optional sheet-music capability for supplying an explicit staff scale."""

    def sheet_music_global_scale(self) -> 'Scale | str | None':
        """Return preferred global scale context for sheet rendering."""


@runtime_checkable
class TempoMetadataSource(Protocol):
    """Optional capability for indicating tempo metadata rendering intent."""

    def sheet_music_should_render_tempo_metadata(self) -> bool:
        """Return whether tempo metadata should be emitted in sheet rendering."""


@runtime_checkable
class NotesLike(Protocol):
    """Protocol for values that can represent zero or more notes."""

    def to_notes(self) -> tuple[Note, ...]:
        """Return the note collection represented by this value."""


def _coerce_consumed_duration(value: DurationLike) -> Duration:
    """Coerce consumed span values into beat/time Duration values."""
    duration = coerce_timeline_duration(value, field_name="consumed_duration")

    if duration.mode == "seconds":
        non_positive = duration.as_seconds() <= 0
    else:
        non_positive = duration.as_beats() <= 0
    if non_positive:
        raise ValueError(f"consumed_duration must be > 0, got {duration}")

    return duration


def _sequence_render_for(value: Any, context: ScoreEventContext) -> SequenceRender:
    """Convert any supported value into a unified sequence render output."""
    if not isinstance(value, Sequenceable):
        raise TypeError(
            f"{type(value).__name__} is not Sequenceable. "
            "Use Score or a Sequenceable source (for example Note, Chord, Sequence, or Rest)."
        )

    result = value.render_for_context(context)

    if not isinstance(result, SequenceRender):
        raise TypeError(
            "Sequenceable conversion must return SequenceRender values, "
            f"got {type(result).__name__}."
        )

    return result
