"""First-class sequence composition models built on the Sequenceable boundary."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable, TypeAlias

from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.rhythm import Duration
from chordelia.score import ScoreEvent, ScoreEventContext
from chordelia.sequenceable import NotesLike, Sequenceable, _score_events_for


DurationLike = Duration | int | float


def _coerce_duration(value: DurationLike, *, field_name: str) -> Duration:
    """Coerce values into beat/time Duration values for deterministic scheduling."""
    if isinstance(value, Duration):
        duration = value
    else:
        duration = Duration.from_beats(value, None)

    if duration.mode == "note_fraction":
        raise ValueError(
            f"{field_name} must be beat-based or time-based Duration. "
            "Use Duration.from_beats(...) or Duration.from_seconds(...)."
        )

    return duration


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

    def score_events_for_context(self, context: ScoreEventContext) -> tuple[ScoreEvent, ...]:
        events: list[ScoreEvent] = []
        for layer in self.layers:
            events.extend(_score_events_for(layer, context))
        return tuple(events)


@dataclass(frozen=True, slots=True)
class Rest:
    """Explicit silent payload marker for sequence timelines."""

    def to_notes(self) -> tuple[Note, ...]:
        """Represent this rest as an empty note collection."""
        return ()

    def score_events_for_context(self, _context: ScoreEventContext) -> tuple[ScoreEvent, ...]:
        """Rests are sequenceable and emit no score events."""
        return ()


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
            if isinstance(entry_value, Sequence):
                normalized_entries.extend(entry_value.entries)
                continue
            if isinstance(entry_value, Sequenceable):
                normalized_entries.append(SequenceEntry(payload=entry_value))
                continue
            normalized_entries.append(SequenceEntry.coerce(entry_value))
        object.__setattr__(self, "entries", tuple(normalized_entries))

    def appended(self, *entries: 'SequenceInputLike') -> "Sequence":
        """Return a new sequence with entries appended in order."""
        return Sequence((*self.entries, *entries))

    def score_events_for_context(self, context: ScoreEventContext) -> tuple[ScoreEvent, ...]:
        """Flatten sequence entries into score events using deterministic scheduling."""
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
            events.extend(_score_events_for(entry.payload, child_context))

            end = start + entry.duration
            if entry.offset is None:
                cursor = end
            elif end > cursor:
                cursor = end

        return tuple(events)

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)


SequenceEntryLike: TypeAlias = (
    SequenceEntry
    | tuple[Any, DurationLike]
    | tuple[Any, DurationLike, DurationLike | None]
)

SequenceInputLike: TypeAlias = SequenceEntryLike | Sequenceable
