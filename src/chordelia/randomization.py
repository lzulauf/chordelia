"""Seeded musical randomization helpers.

This module provides a domain-focused Random wrapper around ``random.Random``
for deterministic musical object generation.
"""

from __future__ import annotations

import math
import random as std_random
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import Any, Callable, TypeAlias, TypeVar

from chordelia.chords import Chord, ChordQuality
from chordelia.degrees import Degree, DegreeLike
from chordelia.intervals import Interval, IntervalLike
from chordelia.notes import Note
from chordelia.scale_context import coerce_scale_context_value, get_global_scale_context
from chordelia.scales import Scale, ScaleType

T = TypeVar("T")
WeightNumber: TypeAlias = int | float
WeightInput: TypeAlias = Mapping[T, WeightNumber] | Sequence[tuple[T, WeightNumber]]

_CHROMATIC_ROOT_CANDIDATES: tuple[str, ...] = (
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
)

_DEFAULT_SCALE_TYPE_WEIGHTS: dict[ScaleType, WeightNumber] = {
    ScaleType.MAJOR: 80,
    ScaleType.NATURAL_MINOR: 60,
    ScaleType.HARMONIC_MINOR: 8,
    ScaleType.MELODIC_MINOR: 6,
    ScaleType.DORIAN: 8,
    ScaleType.PHRYGIAN: 3,
    ScaleType.LYDIAN: 5,
    ScaleType.MIXOLYDIAN: 7,
    ScaleType.AEOLIAN: 3,
    ScaleType.LOCRIAN: 1,
    ScaleType.IONIAN: 2,
    ScaleType.PENTATONIC_MAJOR: 4,
    ScaleType.PENTATONIC_MINOR: 4,
    ScaleType.BLUES: 2,
    ScaleType.WHOLE_TONE: 1,
    ScaleType.DIMINISHED: 1,
    ScaleType.CHROMATIC: 0,
}

_DEFAULT_CHORD_QUALITY_WEIGHTS: dict[ChordQuality, WeightNumber] = {
    ChordQuality.MAJOR: 38,
    ChordQuality.MINOR: 34,
    ChordQuality.DIMINISHED: 8,
    ChordQuality.AUGMENTED: 6,
    ChordQuality.SUSPENDED_2: 6,
    ChordQuality.SUSPENDED_4: 6,
    ChordQuality.POWER: 2,
}

_DEFAULT_INTERVAL_WEIGHTS: dict[str, WeightNumber] = {
    "P1": 3,
    "m2": 5,
    "M2": 14,
    "m3": 11,
    "M3": 14,
    "P4": 9,
    "#4": 4,
    "P5": 14,
    "m6": 7,
    "M6": 8,
    "m7": 5,
    "M7": 3,
    "P8": 3,
}


class dualmethod:
    """Descriptor that supports instance and class-style invocation."""

    def __init__(self, func: Callable[..., Any]):
        self._func = func
        wraps(func)(self)

    def __get__(self, instance: Any, owner: type | None = None) -> Callable[..., Any]:
        receiver = instance if instance is not None else owner

        @wraps(self._func)
        def _bound(*args: Any, **kwargs: Any) -> Any:
            return self._func(receiver, *args, **kwargs)

        return _bound


class Random:
    """Deterministic random musical selector wrapper."""

    def __init__(
        self,
        seed: int | float | str | bytes | bytearray | None = None,
        *,
        engine: std_random.Random | None = None,
    ) -> None:
        if seed is not None and engine is not None:
            raise ValueError("Random accepts either seed or engine, but not both")

        if engine is not None and not isinstance(engine, std_random.Random):
            raise TypeError(
                "engine must be an instance of random.Random; "
                f"got {type(engine).__name__}"
            )

        self._engine = engine if engine is not None else std_random.Random(seed)

    @property
    def engine(self) -> std_random.Random:
        """Return the wrapped stdlib random engine used by selectors."""
        return self._engine

    @dualmethod
    def choice(self_or_cls: "Random | type[Random]", values: Sequence[T]) -> T:
        """Select one item uniformly from a non-empty sequence."""
        rng = _resolve_random_receiver(self_or_cls)
        candidates = tuple(values)
        if not candidates:
            raise ValueError("values cannot be empty")
        return rng._engine.choice(candidates)

    @dualmethod
    def weighted_choice(
        self_or_cls: "Random | type[Random]",
        values: Sequence[T],
        weights: Sequence[WeightNumber],
    ) -> T:
        """Select one item from values using relative numeric weights."""
        rng = _resolve_random_receiver(self_or_cls)
        candidates = tuple(values)
        if not candidates:
            raise ValueError("values cannot be empty")

        relative_weights = _coerce_relative_weights(weights, length=len(candidates))
        return rng._engine.choices(candidates, weights=relative_weights, k=1)[0]

    @dualmethod
    def weighted_choice_map(
        self_or_cls: "Random | type[Random]",
        weighted_values: WeightInput[T],
    ) -> T:
        """Select one item from relative-weight mapping or pair sequence."""
        rng = _resolve_random_receiver(self_or_cls)
        candidates, weights = _coerce_weight_input(
            weighted_values,
            coerce_value=lambda value: value,
            label="weighted_values",
        )
        return rng._engine.choices(candidates, weights=weights, k=1)[0]

    @dualmethod
    def scale(
        self_or_cls: "Random | type[Random]",
        *,
        root_weights: WeightInput[Note | str] | None = None,
        scale_type_weights: WeightInput[ScaleType | str] | None = None,
    ) -> Scale:
        """Select a scale using weighted root/type choices."""
        rng = _resolve_random_receiver(self_or_cls)

        if root_weights is None:
            root_candidates = tuple(Note(value) for value in _CHROMATIC_ROOT_CANDIDATES)
            root = rng._engine.choice(root_candidates)
        else:
            root_candidates, root_weight_values = _coerce_weight_input(
                root_weights,
                coerce_value=_coerce_note_value,
                label="root_weights",
            )
            root = rng._engine.choices(root_candidates, weights=root_weight_values, k=1)[0]

        if scale_type_weights is None:
            type_candidates = tuple(_DEFAULT_SCALE_TYPE_WEIGHTS.keys())
            type_weights = tuple(_DEFAULT_SCALE_TYPE_WEIGHTS.values())
            scale_type = rng._engine.choices(type_candidates, weights=type_weights, k=1)[0]
        else:
            type_candidates, type_weights = _coerce_weight_input(
                scale_type_weights,
                coerce_value=_coerce_scale_type,
                label="scale_type_weights",
            )
            scale_type = rng._engine.choices(type_candidates, weights=type_weights, k=1)[0]

        return Scale(root, scale_type)

    @dualmethod
    def degree(
        self_or_cls: "Random | type[Random]",
        scale: Scale | str | None = None,
        *,
        degree_weights: WeightInput[DegreeLike] | None = None,
    ) -> Degree:
        """Select a valid scale degree using explicit or global scale context."""
        rng = _resolve_random_receiver(self_or_cls)
        active_scale = _resolve_scale(scale)
        span = len(active_scale.notes)

        if degree_weights is None:
            return Degree(rng._engine.choice(tuple(range(1, span + 1))))

        degree_candidates, weights = _coerce_weight_input(
            degree_weights,
            coerce_value=lambda value: _coerce_degree_for_span(value, span),
            label="degree_weights",
        )
        return rng._engine.choices(degree_candidates, weights=weights, k=1)[0]

    @dualmethod
    def note(
        self_or_cls: "Random | type[Random]",
        scale: Scale | str | None = None,
        *,
        degree_weights: WeightInput[DegreeLike] | None = None,
    ) -> Note:
        """Select a note from a resolved scale via degree sampling."""
        rng = _resolve_random_receiver(self_or_cls)
        active_scale = _resolve_scale(scale)
        sampled_degree = rng.degree(scale=active_scale, degree_weights=degree_weights)
        return active_scale.degree(sampled_degree)

    @dualmethod
    def chord(
        self_or_cls: "Random | type[Random]",
        scale: Scale | str | None = None,
        *,
        degree_weights: WeightInput[DegreeLike] | None = None,
    ) -> Chord:
        """Select a diatonic triad from a resolved scale via degree sampling."""
        rng = _resolve_random_receiver(self_or_cls)
        active_scale = _resolve_scale(scale)
        sampled_degree = rng.degree(scale=active_scale, degree_weights=degree_weights)
        return active_scale.chord_for_degree(sampled_degree)

    @dualmethod
    def chromatic_note(
        self_or_cls: "Random | type[Random]",
        *,
        note_weights: WeightInput[Note | str] | None = None,
    ) -> Note:
        """Select a chromatic note independent of any scale context."""
        rng = _resolve_random_receiver(self_or_cls)

        if note_weights is None:
            return Note(rng._engine.choice(_CHROMATIC_ROOT_CANDIDATES))

        note_candidates, note_weight_values = _coerce_weight_input(
            note_weights,
            coerce_value=_coerce_note_value,
            label="note_weights",
        )
        return rng._engine.choices(note_candidates, weights=note_weight_values, k=1)[0]

    @dualmethod
    def chromatic_chord(
        self_or_cls: "Random | type[Random]",
        *,
        root_weights: WeightInput[Note | str] | None = None,
        quality_weights: WeightInput[ChordQuality | str] | None = None,
    ) -> Chord:
        """Select a chromatic chord independent of any scale context."""
        rng = _resolve_random_receiver(self_or_cls)

        root = rng.chromatic_note(note_weights=root_weights)

        if quality_weights is None:
            quality_candidates = tuple(_DEFAULT_CHORD_QUALITY_WEIGHTS.keys())
            quality_weight_values = tuple(_DEFAULT_CHORD_QUALITY_WEIGHTS.values())
            quality = rng._engine.choices(
                quality_candidates,
                weights=quality_weight_values,
                k=1,
            )[0]
        else:
            quality_candidates, quality_weight_values = _coerce_weight_input(
                quality_weights,
                coerce_value=_coerce_chord_quality,
                label="quality_weights",
            )
            quality = rng._engine.choices(
                quality_candidates,
                weights=quality_weight_values,
                k=1,
            )[0]

        return Chord(root, quality)

    @dualmethod
    def interval(
        self_or_cls: "Random | type[Random]",
        *,
        interval_weights: WeightInput[IntervalLike] | None = None,
    ) -> Interval:
        """Select an interval independent of any scale context."""
        rng = _resolve_random_receiver(self_or_cls)

        if interval_weights is None:
            interval_candidates, interval_weight_values = _coerce_weight_input(
                _DEFAULT_INTERVAL_WEIGHTS,
                coerce_value=Interval.coerce,
                label="interval_weights",
            )
        else:
            interval_candidates, interval_weight_values = _coerce_weight_input(
                interval_weights,
                coerce_value=Interval.coerce,
                label="interval_weights",
            )

        return rng._engine.choices(
            interval_candidates,
            weights=interval_weight_values,
            k=1,
        )[0]


_GLOBAL_RANDOM: Random | None = None


def get_global_random() -> Random:
    """Return the global Random singleton, constructing it lazily."""
    global _GLOBAL_RANDOM
    if _GLOBAL_RANDOM is None:
        _GLOBAL_RANDOM = Random()
    return _GLOBAL_RANDOM


def configure_global_random(
    *,
    seed: int | float | str | bytes | bytearray | None = None,
    engine: std_random.Random | None = None,
) -> Random:
    """Replace and return the global Random singleton configuration."""
    global _GLOBAL_RANDOM
    _GLOBAL_RANDOM = Random(seed=seed, engine=engine)
    return _GLOBAL_RANDOM


def reset_global_random() -> None:
    """Clear the global Random singleton."""
    global _GLOBAL_RANDOM
    _GLOBAL_RANDOM = None


def _resolve_random_receiver(receiver: Any) -> Random:
    if isinstance(receiver, Random):
        return receiver

    if isinstance(receiver, type) and issubclass(receiver, Random):
        return get_global_random()

    raise TypeError("Random selector called with an invalid receiver")


def _coerce_relative_weights(
    weights: Sequence[WeightNumber],
    *,
    length: int,
) -> tuple[float, ...]:
    if len(weights) != length:
        raise ValueError("weights length must match values length")

    relative: list[float] = []
    for weight in weights:
        relative.append(_coerce_weight_number(weight, label="weights"))

    if not relative:
        raise ValueError("weights cannot be empty")

    if sum(relative) == 0:
        raise ValueError("at least one weight must be positive")

    return tuple(relative)


def _coerce_weight_input(
    weighted_values: WeightInput[T],
    *,
    coerce_value: Callable[[Any], T],
    label: str,
) -> tuple[tuple[T, ...], tuple[float, ...]]:
    pairs: list[tuple[Any, Any]] = []

    if isinstance(weighted_values, Mapping):
        pairs = list(weighted_values.items())
    elif isinstance(weighted_values, Sequence) and not isinstance(
        weighted_values,
        (str, bytes, bytearray),
    ):
        for pair in weighted_values:
            if (
                not isinstance(pair, Sequence)
                or isinstance(pair, (str, bytes, bytearray))
                or len(pair) != 2
            ):
                raise TypeError(
                    f"{label} sequence entries must be 2-item (value, weight) pairs"
                )
            pairs.append((pair[0], pair[1]))
    else:
        raise TypeError(
            f"{label} must be a mapping or sequence of (value, weight) pairs"
        )

    if not pairs:
        raise ValueError(f"{label} cannot be empty")

    candidates: list[T] = []
    weights: list[float] = []

    for value, weight in pairs:
        candidates.append(coerce_value(value))
        weights.append(_coerce_weight_number(weight, label=label))

    if sum(weights) == 0:
        raise ValueError(f"{label} must include at least one positive weight")

    return tuple(candidates), tuple(weights)


def _coerce_weight_number(weight: Any, *, label: str) -> float:
    if isinstance(weight, bool) or not isinstance(weight, (int, float)):
        raise TypeError(f"{label} weights must be finite numeric values")

    value = float(weight)
    if not math.isfinite(value):
        raise TypeError(f"{label} weights must be finite numeric values")

    if value < 0:
        raise ValueError(f"{label} weights cannot be negative")

    return value


def _resolve_scale(scale: Scale | str | None) -> Scale:
    if scale is not None:
        resolved = coerce_scale_context_value(scale)
    else:
        resolved = get_global_scale_context()

    if resolved is None:
        raise ValueError(
            "Random selector requires a scale context. "
            "Provide scale=... or set_global_scale_context(...)."
        )

    return resolved


def _coerce_degree_for_span(value: DegreeLike, span: int) -> Degree:
    degree = Degree.coerce(value)
    if degree.has_alteration:
        raise ValueError(
            "degree weights must use unaltered scale degrees in the resolved span"
        )

    number = degree.to_int()
    if number < 1 or number > span:
        raise ValueError(
            f"degree weights must be within resolved scale span 1..{span}; got {number}"
        )

    return Degree(number)


def _coerce_note_value(value: Note | str) -> Note:
    if isinstance(value, Note):
        return value
    if isinstance(value, str):
        return Note(value)
    raise TypeError(f"note values must be Note or str, got {type(value).__name__}")


def _coerce_scale_type(value: ScaleType | str) -> ScaleType:
    if isinstance(value, ScaleType):
        return value
    if isinstance(value, str):
        return ScaleType(value.strip().lower())
    raise TypeError(
        f"scale type values must be ScaleType or str, got {type(value).__name__}"
    )


def _coerce_chord_quality(value: ChordQuality | str) -> ChordQuality:
    if isinstance(value, ChordQuality):
        return value
    if isinstance(value, str):
        return ChordQuality.from_string(value.strip())
    raise TypeError(
        f"quality values must be ChordQuality or str, got {type(value).__name__}"
    )


__all__ = [
    "Random",
    "WeightInput",
    "dualmethod",
    "get_global_random",
    "configure_global_random",
    "reset_global_random",
]
