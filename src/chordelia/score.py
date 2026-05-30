"""Canonical score models and conversion boundary for sequenceable inputs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal

from chordelia.rhythm import Duration
from chordelia.scale_context import get_default_note_duration_context


DurationLike = Duration | int | float
_UNCHANGED = object()
RetriggerPolicy = Literal["delta", "retrigger_all"]


def _validate_normalized_fraction(value: float, *, field_name: str) -> None:
    """Validate normalized articulation values constrained to [0.0, 1.0]."""
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")


def _validate_retrigger_policy(value: str) -> None:
    """Validate supported playback retrigger policies."""
    if value not in {"delta", "retrigger_all"}:
        raise ValueError(
            "retrigger_policy must be 'delta' or 'retrigger_all', "
            f"got {value!r}"
        )


def _coerce_duration(value: DurationLike, *, field_name: str) -> Duration:
    """Coerce values into beat/time Duration for deterministic event timing."""
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


def _duration_sort_value(value: Duration):
    """Return comparable timeline values by mode for deterministic sorting."""
    if value.mode == "seconds":
        return value.as_seconds()
    try:
        return value.as_beats()
    except ValueError:
        return value.fraction


@dataclass(frozen=True, slots=True)
class ScoreEvent:
    """A single timed event in a normalized score timeline."""

    beat: DurationLike
    duration: DurationLike
    pitches: tuple[int, ...]
    velocity: int = 64
    channel: int = 0
    voice: int = 0
    spelling: tuple[str, ...] | None = None
    gate_width: float | None = None
    gate_offset: float | None = None

    def __post_init__(self) -> None:
        beat = _coerce_duration(self.beat, field_name="beat")
        duration = _coerce_duration(self.duration, field_name="duration")

        if beat.mode != duration.mode:
            raise ValueError(
                "beat and duration must use the same timing mode "
                f"(got {beat.mode!r} and {duration.mode!r})"
            )

        if _is_negative(beat):
            raise ValueError(f"beat must be >= 0, got {beat}")
        if _is_non_positive(duration):
            raise ValueError(f"duration must be > 0, got {duration}")
        if not self.pitches:
            raise ValueError("pitches must be non-empty")

        for pitch in self.pitches:
            if not isinstance(pitch, int):
                raise ValueError(f"pitch values must be integers, got {pitch!r}")
            if not 0 <= pitch <= 127:
                raise ValueError(f"pitch values must be 0-127, got {pitch}")

        if not 0 <= self.velocity <= 127:
            raise ValueError(f"velocity must be 0-127, got {self.velocity}")
        if self.channel < 0:
            raise ValueError(f"channel must be >= 0, got {self.channel}")
        if self.voice < 0:
            raise ValueError(f"voice must be >= 0, got {self.voice}")
        if self.gate_width is not None:
            _validate_normalized_fraction(self.gate_width, field_name="gate_width")
        if self.gate_offset is not None:
            _validate_normalized_fraction(self.gate_offset, field_name="gate_offset")

        object.__setattr__(self, "beat", beat)
        object.__setattr__(self, "duration", duration)
        object.__setattr__(self, "pitches", tuple(self.pitches))
        if self.spelling is not None:
            object.__setattr__(self, "spelling", tuple(self.spelling))


@dataclass(frozen=True, slots=True)
class ScoreEventContext:
    """Context values used when converting sequenceable objects to score events."""

    tempo: int = 120
    time_signature: tuple[int, int] = (4, 4)
    start_offset: DurationLike = Duration.from_beats(0, None)
    default_duration: DurationLike = Duration.from_beats(1, None)
    velocity: int = 64
    channel: int = 0
    voice: int = 0
    key_signature: str | None = None

    def __post_init__(self) -> None:
        start_offset = _coerce_duration(self.start_offset, field_name="start_offset")
        default_duration = _coerce_duration(self.default_duration, field_name="default_duration")

        if start_offset.mode != default_duration.mode:
            raise ValueError(
                "start_offset and default_duration must use the same timing mode "
                f"(got {start_offset.mode!r} and {default_duration.mode!r})"
            )

        if _is_negative(start_offset):
            raise ValueError(f"start_offset must be >= 0, got {start_offset}")
        if _is_non_positive(default_duration):
            raise ValueError(f"default_duration must be > 0, got {default_duration}")
        if self.tempo <= 0:
            raise ValueError(f"tempo must be > 0, got {self.tempo}")
        if len(self.time_signature) != 2:
            raise ValueError("time_signature must be (numerator, denominator)")

        numerator, denominator = self.time_signature
        if numerator <= 0:
            raise ValueError(f"time signature numerator must be > 0, got {numerator}")
        if denominator <= 0:
            raise ValueError(f"time signature denominator must be > 0, got {denominator}")
        if not 0 <= self.velocity <= 127:
            raise ValueError(f"velocity must be 0-127, got {self.velocity}")
        if self.channel < 0:
            raise ValueError(f"channel must be >= 0, got {self.channel}")
        if self.voice < 0:
            raise ValueError(f"voice must be >= 0, got {self.voice}")

        object.__setattr__(self, "start_offset", start_offset)
        object.__setattr__(self, "default_duration", default_duration)

    def with_start_offset(self, start_offset: DurationLike) -> "ScoreEventContext":
        """Return a copy with a new start offset."""
        return replace(self, start_offset=start_offset)


@dataclass(frozen=True, slots=True)
class ScoreMetadata:
    """Score-level metadata used by wrappers and renderers."""

    tempo: int = 120
    time_signature: tuple[int, int] = (4, 4)
    key_signature: str | None = None
    ppq: int = 480
    gate_width: float = 0.9
    gate_offset: float = 0.0
    retrigger_policy: RetriggerPolicy = "retrigger_all"

    def __post_init__(self) -> None:
        if self.tempo <= 0:
            raise ValueError(f"tempo must be > 0, got {self.tempo}")
        if len(self.time_signature) != 2:
            raise ValueError("time_signature must be (numerator, denominator)")
        numerator, denominator = self.time_signature
        if numerator <= 0:
            raise ValueError(f"time signature numerator must be > 0, got {numerator}")
        if denominator <= 0:
            raise ValueError(f"time signature denominator must be > 0, got {denominator}")
        if self.ppq <= 0:
            raise ValueError(f"ppq must be > 0, got {self.ppq}")
        _validate_normalized_fraction(self.gate_width, field_name="gate_width")
        _validate_normalized_fraction(self.gate_offset, field_name="gate_offset")
        _validate_retrigger_policy(self.retrigger_policy)

    def with_tempo(self, tempo: int) -> "ScoreMetadata":
        """Return a copy with updated tempo."""
        return replace(self, tempo=tempo)

    def with_(
        self,
        *,
        tempo: int | object = _UNCHANGED,
        time_signature: tuple[int, int] | object = _UNCHANGED,
        key_signature: str | None | object = _UNCHANGED,
        ppq: int | object = _UNCHANGED,
        gate_width: float | object = _UNCHANGED,
        gate_offset: float | object = _UNCHANGED,
        retrigger_policy: RetriggerPolicy | object = _UNCHANGED,
    ) -> "ScoreMetadata":
        """Return a copy with any combination of metadata field updates."""
        changes: dict[str, Any] = {}
        if tempo is not _UNCHANGED:
            changes["tempo"] = tempo
        if time_signature is not _UNCHANGED:
            changes["time_signature"] = time_signature
        if key_signature is not _UNCHANGED:
            changes["key_signature"] = key_signature
        if ppq is not _UNCHANGED:
            changes["ppq"] = ppq
        if gate_width is not _UNCHANGED:
            changes["gate_width"] = gate_width
        if gate_offset is not _UNCHANGED:
            changes["gate_offset"] = gate_offset
        if retrigger_policy is not _UNCHANGED:
            changes["retrigger_policy"] = retrigger_policy

        if not changes:
            return self
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class Score:
    """Canonical score wrapper around a sequenceable source and normalized events."""

    source: Any
    metadata: ScoreMetadata
    events: tuple[ScoreEvent, ...]

    def __post_init__(self) -> None:
        events = tuple(self.events)
        if events:
            first_mode = events[0].beat.mode
            for event in events:
                if event.beat.mode != first_mode or event.duration.mode != first_mode:
                    raise ValueError("All score events must share the same timing mode")

        ordered_events = tuple(sorted(events, key=_score_event_sort_key))
        object.__setattr__(self, "events", ordered_events)

    @classmethod
    def from_sequenceable(
        cls,
        source: Any,
        *,
        tempo: int = 120,
        time_signature: tuple[int, int] = (4, 4),
        key_signature: str | None = None,
        default_duration: DurationLike | None = None,
        ppq: int = 480,
        gate_width: float = 0.9,
        gate_offset: float = 0.0,
        retrigger_policy: RetriggerPolicy = "retrigger_all",
    ) -> "Score":
        """Create a score by normalizing any sequenceable (or adapted) value."""
        from chordelia.sequenceable import _sequence_render_for

        resolved_default_duration = (
            default_duration
            if default_duration is not None
            else get_default_note_duration_context()
        )

        context = ScoreEventContext(
            tempo=tempo,
            time_signature=time_signature,
            key_signature=key_signature,
            default_duration=(
                resolved_default_duration
                if resolved_default_duration is not None
                else Duration.from_beats(1, None)
            ),
        )
        render = _sequence_render_for(source, context)
        events = render.events
        metadata = ScoreMetadata(
            tempo=tempo,
            time_signature=time_signature,
            key_signature=key_signature,
            ppq=ppq,
            gate_width=gate_width,
            gate_offset=gate_offset,
            retrigger_policy=retrigger_policy,
        )
        return cls(source=source, metadata=metadata, events=events)

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self):
        return iter(self.events)

    @property
    def duration(self) -> Duration:
        """Return the normalized score span from beat/second zero to timeline end."""
        if not self.events:
            return Duration.from_beats(0, None)
        return max(event.beat + event.duration for event in self.events)

    def with_tempo(self, tempo: int) -> "Score":
        """Return a copy with updated metadata tempo."""
        return self.with_(tempo=tempo)

    def with_(
        self,
        *,
        source: Any = _UNCHANGED,
        metadata: ScoreMetadata | object = _UNCHANGED,
        events: tuple[ScoreEvent, ...] | list[ScoreEvent] | object = _UNCHANGED,
        tempo: int | object = _UNCHANGED,
        time_signature: tuple[int, int] | object = _UNCHANGED,
        key_signature: str | None | object = _UNCHANGED,
        ppq: int | object = _UNCHANGED,
        gate_width: float | object = _UNCHANGED,
        gate_offset: float | object = _UNCHANGED,
        retrigger_policy: RetriggerPolicy | object = _UNCHANGED,
    ) -> "Score":
        """Return a copy with source/events and/or metadata fields updated."""
        next_source = self.source if source is _UNCHANGED else source
        next_events = self.events if events is _UNCHANGED else events

        base_metadata = self.metadata if metadata is _UNCHANGED else metadata
        if not isinstance(base_metadata, ScoreMetadata):
            raise TypeError(
                f"metadata must be ScoreMetadata, got {type(base_metadata).__name__}"
            )

        next_metadata = base_metadata.with_(
            tempo=tempo,
            time_signature=time_signature,
            key_signature=key_signature,
            ppq=ppq,
            gate_width=gate_width,
            gate_offset=gate_offset,
            retrigger_policy=retrigger_policy,
        )

        return Score(source=next_source, metadata=next_metadata, events=next_events)


def _score_event_sort_key(event: ScoreEvent):
    """Deterministic ordering key for normalized score events."""
    return (
        _duration_sort_value(event.beat),
        event.channel,
        event.voice,
        event.pitches,
        _duration_sort_value(event.duration),
    )


def score_from_sequenceable(
    source: Any,
    *,
    tempo: int = 120,
    time_signature: tuple[int, int] = (4, 4),
    key_signature: str | None = None,
    default_duration: DurationLike | None = None,
    gate_width: float = 0.9,
    gate_offset: float = 0.0,
    retrigger_policy: RetriggerPolicy = "retrigger_all",
) -> Score:
    """Compatibility helper that delegates to Score.from_sequenceable."""
    return Score.from_sequenceable(
        source,
        tempo=tempo,
        time_signature=time_signature,
        key_signature=key_signature,
        default_duration=default_duration,
        gate_width=gate_width,
        gate_offset=gate_offset,
        retrigger_policy=retrigger_policy,
    )
