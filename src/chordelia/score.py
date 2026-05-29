"""Canonical score models and conversion boundary for sequenceable inputs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any


FractionLike = Fraction | int | float


def _coerce_fraction(value: FractionLike, *, field_name: str) -> Fraction:
    """Coerce numeric values into Fraction for deterministic timing."""
    try:
        return Fraction(value).limit_denominator()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric, got {value!r}") from exc


@dataclass(frozen=True, slots=True)
class ScoreEvent:
    """A single timed event in a normalized score timeline."""

    beat: FractionLike
    duration: FractionLike
    pitches: tuple[int, ...]
    velocity: int = 64
    channel: int = 0
    voice: int = 0
    spelling: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        beat = _coerce_fraction(self.beat, field_name="beat")
        duration = _coerce_fraction(self.duration, field_name="duration")

        if beat < 0:
            raise ValueError(f"beat must be >= 0, got {beat}")
        if duration <= 0:
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
    start_offset: FractionLike = Fraction(0, 1)
    default_duration: FractionLike = Fraction(1, 1)
    velocity: int = 64
    channel: int = 0
    voice: int = 0
    key_signature: str | None = None

    def __post_init__(self) -> None:
        start_offset = _coerce_fraction(self.start_offset, field_name="start_offset")
        default_duration = _coerce_fraction(self.default_duration, field_name="default_duration")

        if start_offset < 0:
            raise ValueError(f"start_offset must be >= 0, got {start_offset}")
        if default_duration <= 0:
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

    def with_start_offset(self, start_offset: FractionLike) -> "ScoreEventContext":
        """Return a copy with a new start offset."""
        return replace(self, start_offset=start_offset)


@dataclass(frozen=True, slots=True)
class ScoreMetadata:
    """Score-level metadata used by wrappers and renderers."""

    tempo: int = 120
    time_signature: tuple[int, int] = (4, 4)
    key_signature: str | None = None
    ppq: int = 480

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


@dataclass(frozen=True, slots=True)
class Score:
    """Canonical score wrapper around a sequenceable source and normalized events."""

    source: Any
    metadata: ScoreMetadata
    events: tuple[ScoreEvent, ...]

    def __post_init__(self) -> None:
        ordered_events = tuple(sorted(self.events, key=_score_event_sort_key))
        object.__setattr__(self, "events", ordered_events)

    @classmethod
    def from_sequenceable(
        cls,
        source: Any,
        *,
        tempo: int = 120,
        time_signature: tuple[int, int] = (4, 4),
        key_signature: str | None = None,
        ppq: int = 480,
    ) -> "Score":
        """Create a score by normalizing any sequenceable (or adapted) value."""
        from chordelia.sequenceable import _score_events_for

        context = ScoreEventContext(
            tempo=tempo,
            time_signature=time_signature,
            key_signature=key_signature,
        )
        events = _score_events_for(source, context)
        metadata = ScoreMetadata(
            tempo=tempo,
            time_signature=time_signature,
            key_signature=key_signature,
            ppq=ppq,
        )
        return cls(source=source, metadata=metadata, events=events)

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self):
        return iter(self.events)


def _score_event_sort_key(event: ScoreEvent) -> tuple[Fraction, int, int, tuple[int, ...], Fraction]:
    """Deterministic ordering key for normalized score events."""
    return (event.beat, event.channel, event.voice, event.pitches, event.duration)


def score_from_sequenceable(
    source: Any,
    *,
    tempo: int = 120,
    time_signature: tuple[int, int] = (4, 4),
    key_signature: str | None = None,
) -> Score:
    """Compatibility helper that delegates to Score.from_sequenceable."""
    return Score.from_sequenceable(
        source,
        tempo=tempo,
        time_signature=time_signature,
        key_signature=key_signature,
    )
