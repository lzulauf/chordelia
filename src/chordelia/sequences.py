"""First-class sequence composition models built on the Sequenceable boundary."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Iterable, TypeAlias

from chordelia.chords import Chord
from chordelia.intervals import IntervalLike, coerce_chromatic_semitones
from chordelia.notes import Note
from chordelia.rhythm import Duration, TimelineLike, coerce_timeline_duration
from chordelia.scale_context import coerce_scale_context_value
from chordelia.score import ScoreEvent, ScoreEventContext
from chordelia.sequenceable import NotesLike, SequenceRender, Sequenceable, _sequence_render_for

if TYPE_CHECKING:
    from chordelia.scales import Scale


DurationLike: TypeAlias = TimelineLike


def _coerce_duration(value: DurationLike, *, field_name: str) -> Duration:
    """Coerce values into beat/time Duration values for deterministic scheduling."""
    return coerce_timeline_duration(value, field_name=field_name)


def _is_negative(value: Duration) -> bool:
    """Check whether a duration value is negative in its own mode."""
    if value.mode == "seconds":
        return value.as_seconds() < 0
    return value.as_beats() < 0


def _is_non_positive(value: Duration) -> bool:
    """Check whether a duration value is <= 0 in its own mode."""
    if value.mode == "seconds":
        return value.as_seconds() <= 0
    return value.as_beats() <= 0


def _coerce_payload(value: Any) -> Any:
    """Normalize ergonomic payload forms into canonical sequenceable payloads."""
    if isinstance(value, Sequenceable):
        return value
    if isinstance(value, (str, bytes)):
        return value
    if isinstance(value, Iterable):
        layers: list[Sequenceable] = []
        for item in value:
            layer = _coerce_layer(item)
            if layer is None:
                return value
            layers.append(layer)

        if not layers:
            return Rest()
        # Keep ergonomic note-list support as one chord payload.
        if all(isinstance(layer, Note) for layer in layers):
            return Chord.from_notes(tuple(layers))
        if len(layers) == 1:
            return layers[0]
        return _SimultaneousPayload(tuple(layers))
    return value


def _coerce_layer(value: Any) -> Sequenceable | None:
    """Coerce a simultaneous-layer item while preserving object boundaries."""
    if isinstance(value, Sequenceable):
        return value
    if isinstance(value, str):
        return Note.from_string(value)
    if isinstance(value, NotesLike):
        notes = value.to_notes()
        if not notes:
            return Rest()
        if len(notes) == 1:
            return notes[0]
        return Chord.from_notes(notes)
    return None


@dataclass(frozen=True, slots=True)
class _SimultaneousPayload:
    """Private sequenceable wrapper for simultaneous layer emission."""

    layers: tuple[Sequenceable, ...]

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        events: list[ScoreEvent] = []
        for layer in self.layers:
            events.extend(_sequence_render_for(layer, context).events)
        return SequenceRender(events=tuple(events), consumed_duration=context.default_duration)

    def transpose(self, interval: IntervalLike | int) -> "_SimultaneousPayload":
        """Return a transposed copy while preserving simultaneous boundaries."""
        return _SimultaneousPayload(
            tuple(_transpose_payload(layer, interval) for layer in self.layers)
        )

    def shift(self, steps: int, *, scale: 'Scale | str | None' = None) -> "_SimultaneousPayload":
        """Return a diatonically shifted copy while preserving simultaneous boundaries."""
        return _SimultaneousPayload(
            tuple(_shift_payload(layer, steps, scale=scale) for layer in self.layers)
        )


@dataclass(frozen=True, slots=True)
class Rest:
    """Explicit silent payload marker for sequence timelines."""

    def to_notes(self) -> tuple[Note, ...]:
        """Represent this rest as an empty note collection."""
        return ()

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        """Rests are sequenceable and emit no score events while consuming span."""
        return SequenceRender(events=(), consumed_duration=context.default_duration)

    def transpose(self, interval: IntervalLike | int) -> "Rest":
        """Transpose is a no-op for rests but accepted for recursive sequence transforms."""
        coerce_chromatic_semitones(interval)
        return self

    def shift(self, steps: int, *, scale: 'Scale | str | None' = None) -> "Rest":
        """Shift is a no-op for rests but accepted for recursive sequence transforms."""
        if not isinstance(steps, int) or isinstance(steps, bool):
            raise TypeError(f"steps must be an int, got {type(steps).__name__}")
        if scale is not None:
            coerce_scale_context_value(scale)
        return self


@dataclass(frozen=True, slots=True)
class SequenceEntry:
    """One scheduled payload plus timing metadata inside a Sequence."""

    payload: Any
    duration: DurationLike = Duration.from_beats(1, None)
    offset: DurationLike | None = None

    @classmethod
    def coerce(cls, value: 'SequenceEntryLike') -> 'SequenceEntry':
        """Coerce tuple and model forms into SequenceEntry."""
        if isinstance(value, cls):
            return value
        if isinstance(value, tuple):
            if len(value) == 2:
                payload, duration = value
                return cls(payload=payload, duration=duration)
            if len(value) == 3:
                payload, duration, offset = value
                return cls(payload=payload, duration=duration, offset=offset)
            raise ValueError(
                "SequenceEntry tuple form must be (payload, duration) "
                "or (payload, duration, offset)."
            )
        raise ValueError(
            "Sequence entry must be SequenceEntry or tuple form "
            "(payload, duration[, offset])."
        )

    def __post_init__(self) -> None:
        payload = _coerce_payload(self.payload)
        duration = _coerce_duration(self.duration, field_name="duration")
        offset = (
            _coerce_duration(self.offset, field_name="offset")
            if self.offset is not None
            else None
        )

        if _is_non_positive(duration):
            raise ValueError(f"duration must be > 0, got {duration}")
        if offset is not None and _is_negative(offset):
            raise ValueError(f"offset must be >= 0, got {offset}")
        if offset is not None and offset.mode != duration.mode:
            raise ValueError(
                "offset and duration must use the same timing mode "
                f"(got {offset.mode!r} and {duration.mode!r})"
            )

        object.__setattr__(self, "payload", payload)
        object.__setattr__(self, "duration", duration)
        object.__setattr__(self, "offset", offset)


@dataclass(frozen=True, slots=True)
class Sequence:
    """Immutable ordered collection of sequence entries."""

    entries: tuple[SequenceEntry, ...]

    def __init__(self, entries: Iterable['SequenceInputLike'] = ()):
        normalized_entries: list[SequenceEntry] = []
        for entry_value in entries:
            if isinstance(entry_value, Sequenceable):
                normalized_entries.append(SequenceEntry(payload=entry_value))
                continue
            normalized_entries.append(SequenceEntry.coerce(entry_value))
        object.__setattr__(self, "entries", tuple(normalized_entries))

    def appended(self, *entries: 'SequenceInputLike') -> "Sequence":
        """Return a new sequence with entries appended in order."""
        return Sequence((*self.entries, *entries))

    def transpose(self, interval: IntervalLike | int) -> "Sequence":
        """Return a recursively transposed sequence with unchanged timing metadata."""
        semitone_steps = coerce_chromatic_semitones(interval)
        transposed_entries = tuple(
            SequenceEntry(
                payload=_transpose_payload(entry.payload, semitone_steps),
                duration=entry.duration,
                offset=entry.offset,
            )
            for entry in self.entries
        )
        return Sequence(transposed_entries)

    def shift(self, steps: int, *, scale: 'Scale | str | None' = None) -> "Sequence":
        """Return a recursively shifted sequence with unchanged timing metadata."""
        if not isinstance(steps, int) or isinstance(steps, bool):
            raise TypeError(f"steps must be an int, got {type(steps).__name__}")

        scale_obj = coerce_scale_context_value(scale) if scale is not None else None
        shifted_entries = tuple(
            SequenceEntry(
                payload=_shift_payload(entry.payload, steps, scale=scale_obj),
                duration=entry.duration,
                offset=entry.offset,
            )
            for entry in self.entries
        )
        return Sequence(shifted_entries)

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        """Render sequence entries into score events using deterministic span scheduling."""
        events: list[ScoreEvent] = []
        cursor = context.start_offset

        for entry in self.entries:
            if entry.duration.mode != cursor.mode:
                raise ValueError(
                    "SequenceEntry duration mode must match context timing mode "
                    f"(got {entry.duration.mode!r} and {cursor.mode!r})"
                )

            if entry.offset is None:
                start = cursor
            else:
                if entry.offset.mode != cursor.mode:
                    raise ValueError(
                        "SequenceEntry offset mode must match context timing mode "
                        f"(got {entry.offset.mode!r} and {cursor.mode!r})"
                    )
                start = context.start_offset + entry.offset

            child_context = replace(
                context,
                start_offset=start,
                default_duration=entry.duration,
            )
            child_render = _sequence_render_for(entry.payload, child_context)
            if child_render.consumed_duration.mode != cursor.mode:
                raise ValueError(
                    "Rendered child consumed_duration mode must match context timing mode "
                    f"(got {child_render.consumed_duration.mode!r} and {cursor.mode!r})"
                )
            events.extend(child_render.events)

            end = start + child_render.consumed_duration
            if entry.offset is None:
                cursor = end
            elif end > cursor:
                cursor = end

        return SequenceRender(
            events=tuple(events),
            consumed_duration=cursor - context.start_offset,
        )

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def sheet_music_should_render_tempo_metadata(self) -> bool:
        """Signal SheetMusic to render tempo metadata for sequence-backed sources."""
        return True


SequenceEntryLike: TypeAlias = (
    SequenceEntry
    | tuple[Any, DurationLike]
    | tuple[Any, DurationLike, DurationLike | None]
)

SequenceInputLike: TypeAlias = SequenceEntryLike | Sequenceable


def _transpose_payload(payload: Any, interval: IntervalLike | int) -> Any:
    """Transpose one payload value or raise an actionable capability error."""
    if isinstance(payload, Sequenceable):
        return payload.transpose(interval)

    raise ValueError(
        "Sequence.transpose requires Sequenceable payloads that implement transpose(interval). "
        f"Unsupported payload type: {type(payload).__name__}."
    )


def _shift_payload(payload: Any, steps: int, *, scale: 'Scale | str | None' = None) -> Any:
    """Diatonically shift one payload value or raise an actionable capability error."""
    if isinstance(payload, Sequenceable):
        shift_method = getattr(payload, "shift", None)
        if shift_method is None:
            raise ValueError(
                "Sequence.shift requires Sequenceable payloads that implement shift(steps). "
                f"Unsupported payload type: {type(payload).__name__}."
            )
        if scale is None:
            return shift_method(steps)
        return shift_method(steps, scale=scale)

    raise ValueError(
        "Sequence.shift requires Sequenceable payloads that implement shift(steps). "
        f"Unsupported payload type: {type(payload).__name__}."
    )
