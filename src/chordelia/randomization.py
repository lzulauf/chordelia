"""Seeded musical randomization helpers.

This module provides a domain-focused Random wrapper around ``random.Random``
for deterministic musical object generation.
"""

from __future__ import annotations

import math
import random as std_random
from collections.abc import Mapping, Sequence as SequenceABC
from fractions import Fraction
from functools import wraps
from typing import Any, Callable, ClassVar, Protocol, TypeAlias, TypeVar, runtime_checkable

from chordelia.chords import Chord, ChordQuality
from chordelia.degrees import Degree, DegreeLike
from chordelia.intervals import Interval, IntervalLike
from chordelia.notes import Note
from chordelia.rhythm import TimelineLike, coerce_timeline_duration
from chordelia.scale_context import coerce_scale_context_value, get_global_scale_context
from chordelia.scales import Scale, ScaleType
from chordelia.sequences import Rest, Sequence

T = TypeVar("T")
WeightNumber: TypeAlias = int | float
WeightInput: TypeAlias = Mapping[T, WeightNumber] | SequenceABC[tuple[T, WeightNumber]]

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

_DEFAULT_SEQUENCE_DURATION_WEIGHTS: dict[Fraction, WeightNumber] = {
    Fraction(1, 4): 20,
    Fraction(1, 2): 30,
    Fraction(1, 1): 30,
    Fraction(2, 1): 15,
    Fraction(4, 1): 5,
}

_DEFAULT_SEQUENCE_ALGORITHM_WEIGHTS: dict[str, WeightNumber] = {
    "motif_variation": 40,
    "scale_walk": 30,
    "chord_anchor_walk": 20,
    "pure_random": 10,
}


@runtime_checkable
class SequenceRandomizationAlgorithm(Protocol):
    """Object-based contract for sequence randomization algorithms."""

    name: ClassVar[str]
    default_selection_weight: ClassVar[float]

    def generate(
        self,
        *,
        rng: "Random",
        beat_length: Fraction,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **params: Any,
    ) -> Sequence: ...


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
    def choice(self_or_cls: "Random | type[Random]", values: SequenceABC[T]) -> T:
        """Select one item uniformly from a non-empty sequence."""
        rng = _resolve_random_receiver(self_or_cls)
        candidates = tuple(values)
        if not candidates:
            raise ValueError("values cannot be empty")
        return rng._engine.choice(candidates)

    @dualmethod
    def weighted_choice(
        self_or_cls: "Random | type[Random]",
        values: SequenceABC[T],
        weights: SequenceABC[WeightNumber],
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

    @dualmethod
    def sequence(
        self_or_cls: "Random | type[Random]",
        beat_length: TimelineLike,
        *,
        algorithm: SequenceRandomizationAlgorithm | str | None = None,
        algorithm_weights: WeightInput[str] | None = None,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **algorithm_params: Any,
    ) -> Sequence:
        """Generate a randomized Sequence with exact consumed beat length."""
        rng = _resolve_random_receiver(self_or_cls)
        total_beats = _coerce_positive_beat_length(
            beat_length,
            field_name="beat_length",
        )

        algorithm_instance = _resolve_algorithm_instance(
            rng=rng,
            algorithm=algorithm,
            algorithm_weights=algorithm_weights,
        )

        generated = algorithm_instance.generate(
            rng=rng,
            beat_length=total_beats,
            scale=scale,
            chord=chord,
            **algorithm_params,
        )

        _validate_sequence_consumes_exact_beats(generated, total_beats)
        return generated


class PureRandomSequenceAlgorithm:
    """Random selector over notes, rests, chords, and continuation actions."""

    name: ClassVar[str] = "pure_random"
    default_selection_weight: ClassVar[float] = 10.0

    def generate(
        self,
        *,
        rng: Random,
        beat_length: Fraction,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **params: Any,
    ) -> Sequence:
        scale_obj = _resolve_optional_scale(scale)
        chord_obj = _resolve_optional_chord(chord)

        duration_weights = _coerce_duration_weight_map(params.get("duration_weights"))
        event_type_weights = _coerce_event_type_weights(params.get("event_type_weights"))
        pitch_change_probability = _coerce_probability(
            params.get("pitch_change_probability", 0.65),
            label="pitch_change_probability",
        )

        entries: list[list[Any]] = []
        last_pitched_index: int | None = None
        last_note: Note | None = None

        remaining = beat_length
        while remaining > 0:
            duration = _choose_duration_for_remaining(
                rng,
                remaining,
                duration_weights,
            )

            selection_weights = dict(event_type_weights)
            if last_pitched_index is None:
                selection_weights["continue"] = 0.0

            action = rng.weighted_choice_map(selection_weights)
            if action == "continue" and last_pitched_index is not None:
                entries[last_pitched_index][1] += duration
                remaining -= duration
                continue

            if action == "rest":
                payload: Any = Rest()
            elif action == "chord":
                payload = _sample_chord_for_context(
                    rng,
                    scale=scale_obj,
                    chord=chord_obj,
                )
            else:
                if last_note is not None and rng.engine.random() > pitch_change_probability:
                    payload = last_note
                else:
                    payload = _sample_note_for_context(
                        rng,
                        scale=scale_obj,
                        chord=chord_obj,
                    )

            entries.append([payload, duration])
            if not isinstance(payload, Rest):
                last_pitched_index = len(entries) - 1
                if isinstance(payload, Note):
                    last_note = payload

            remaining -= duration

        return Sequence((payload, duration) for payload, duration in entries)


class MotifVariationSequenceAlgorithm:
    """Motif-first generator that reuses motif state across calls."""

    name: ClassVar[str] = "motif_variation"
    default_selection_weight: ClassVar[float] = 40.0

    def __init__(self, *, motif_beats: TimelineLike | None = None) -> None:
        self._motif_beats = motif_beats
        self._motif_template: tuple[tuple[Any, Fraction], ...] | None = None

    def generate(
        self,
        *,
        rng: Random,
        beat_length: Fraction,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **params: Any,
    ) -> Sequence:
        scale_obj = _resolve_optional_scale(scale)
        chord_obj = _resolve_optional_chord(chord)

        motif_span = self._resolve_motif_span(
            beat_length,
            params.get("motif_beats"),
        )
        if params.get("reset_motif", False) or self._motif_template is None:
            self._motif_template = self._build_motif(
                rng,
                motif_span,
                scale=scale_obj,
                chord=chord_obj,
                params=params,
            )

        mutation_probability = _coerce_probability(
            params.get("mutation_probability", 0.25),
            label="mutation_probability",
        )

        entries: list[tuple[Any, Fraction]] = []
        remaining = beat_length
        motif = self._motif_template
        assert motif is not None

        while remaining > 0:
            for payload, duration in motif:
                if remaining <= 0:
                    break

                clipped_duration = min(duration, remaining)
                mutated_payload = self._mutate_payload(
                    payload,
                    rng=rng,
                    scale=scale_obj,
                    probability=mutation_probability,
                )
                entries.append((mutated_payload, clipped_duration))
                remaining -= clipped_duration

        return Sequence(entries)

    def _resolve_motif_span(
        self,
        beat_length: Fraction,
        motif_override: TimelineLike | None,
    ) -> Fraction:
        if motif_override is not None:
            span = _coerce_positive_beat_length(
                motif_override,
                field_name="motif_beats",
            )
            return min(span, beat_length)

        if self._motif_beats is not None:
            span = _coerce_positive_beat_length(
                self._motif_beats,
                field_name="motif_beats",
            )
            return min(span, beat_length)

        return min(Fraction(4, 1), beat_length)

    def _build_motif(
        self,
        rng: Random,
        motif_span: Fraction,
        *,
        scale: Scale | None,
        chord: Chord | None,
        params: dict[str, Any],
    ) -> tuple[tuple[Any, Fraction], ...]:
        motif_source = PureRandomSequenceAlgorithm().generate(
            rng=rng,
            beat_length=motif_span,
            scale=scale,
            chord=chord,
            event_type_weights=params.get(
                "motif_event_type_weights",
                {
                    "note": 7,
                    "rest": 1,
                    "chord": 2,
                    "continue": 1,
                },
            ),
            duration_weights=params.get("duration_weights"),
            pitch_change_probability=params.get("pitch_change_probability", 0.7),
        )
        return tuple(
            (entry.payload, entry.duration.as_beats())
            for entry in motif_source.entries
        )

    def _mutate_payload(
        self,
        payload: Any,
        *,
        rng: Random,
        scale: Scale | None,
        probability: float,
    ) -> Any:
        if isinstance(payload, Rest):
            return payload
        if rng.engine.random() > probability:
            return payload

        if isinstance(payload, Note):
            if scale is not None:
                direction = rng.engine.choice((-1, 1))
                return payload.shift(direction, scale=scale)
            return payload.transpose(rng.engine.choice((-1, 1)))

        return payload


class ScaleWalkSequenceAlgorithm:
    """Directional scale walk with stateful direction/index carry-forward."""

    name: ClassVar[str] = "scale_walk"
    default_selection_weight: ClassVar[float] = 30.0

    def __init__(self) -> None:
        self._last_index: int | None = None
        self._last_direction: int | None = None

    def generate(
        self,
        *,
        rng: Random,
        beat_length: Fraction,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **params: Any,
    ) -> Sequence:
        del chord

        scale_obj = _resolve_optional_scale(scale) or Scale("C", ScaleType.MAJOR)
        duration_weights = _coerce_duration_weight_map(params.get("duration_weights"))
        direction_change_probability = _coerce_probability(
            params.get("direction_change_probability", 0.2),
            label="direction_change_probability",
        )
        run_step_probability = _coerce_probability(
            params.get("run_step_probability", 0.2),
            label="run_step_probability",
        )

        scale_notes = tuple(note.with_octave(None) for note in scale_obj.notes)
        index = (
            self._last_index
            if self._last_index is not None
            else rng.engine.randrange(len(scale_notes))
        )
        direction = (
            self._last_direction
            if self._last_direction in {-1, 1}
            else rng.engine.choice((-1, 1))
        )

        entries: list[tuple[Any, Fraction]] = []
        remaining = beat_length
        while remaining > 0:
            duration = _choose_duration_for_remaining(rng, remaining, duration_weights)
            entries.append((scale_notes[index], duration))

            if rng.engine.random() < direction_change_probability:
                direction *= -1

            step = 2 if rng.engine.random() < run_step_probability else 1
            index = (index + (direction * step)) % len(scale_notes)
            remaining -= duration

        self._last_index = index
        self._last_direction = direction
        return Sequence(entries)


class ChordAnchorWalkSequenceAlgorithm:
    """Scale walk constrained to chord-tone starts/ends."""

    name: ClassVar[str] = "chord_anchor_walk"
    default_selection_weight: ClassVar[float] = 20.0

    def generate(
        self,
        *,
        rng: Random,
        beat_length: Fraction,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **params: Any,
    ) -> Sequence:
        scale_obj = _resolve_optional_scale(scale) or Scale("C", ScaleType.MAJOR)
        chord_obj = _resolve_optional_chord(chord)

        if chord_obj is None:
            chord_obj = _fallback_anchor_chord(rng, scale_obj)

        duration_weights = _coerce_duration_weight_map(params.get("duration_weights"))
        jump_probability = _coerce_probability(
            params.get("jump_probability", 0.35),
            label="jump_probability",
        )

        chord_tones = tuple(note.with_octave(None) for note in chord_obj.notes)
        scale_notes = tuple(note.with_octave(None) for note in scale_obj.notes)

        durations: list[Fraction] = []
        remaining = beat_length
        while remaining > 0:
            duration = _choose_duration_for_remaining(rng, remaining, duration_weights)
            durations.append(duration)
            remaining -= duration

        if not durations:
            return Sequence(())

        entries: list[tuple[Any, Fraction]] = []
        previous_index = 0
        for i, duration in enumerate(durations):
            if i == 0 or i == len(durations) - 1:
                payload = rng.engine.choice(chord_tones)
                previous_index = _closest_scale_note_index(scale_notes, payload)
            else:
                if rng.engine.random() < jump_probability:
                    payload = rng.engine.choice(chord_tones)
                    previous_index = _closest_scale_note_index(scale_notes, payload)
                else:
                    previous_index = (previous_index + rng.engine.choice((-1, 1))) % len(scale_notes)
                    payload = scale_notes[previous_index]

            entries.append((payload, duration))

        return Sequence(entries)


def _resolve_algorithm_instance(
    *,
    rng: Random,
    algorithm: SequenceRandomizationAlgorithm | str | None,
    algorithm_weights: WeightInput[str] | None,
) -> SequenceRandomizationAlgorithm:
    if algorithm is not None and algorithm_weights is not None:
        raise ValueError("algorithm_weights cannot be used with an explicit algorithm")

    if algorithm is None:
        weighted_names = _resolve_algorithm_weight_map(algorithm_weights)
        selected_name = rng.weighted_choice_map(weighted_names)
        return _instantiate_registered_algorithm(selected_name)

    if isinstance(algorithm, str):
        return _instantiate_registered_algorithm(algorithm)

    if _is_sequence_algorithm_instance(algorithm):
        return algorithm

    raise TypeError(
        "algorithm must be a SequenceRandomizationAlgorithm instance, algorithm name, or None"
    )


def _resolve_algorithm_weight_map(
    algorithm_weights: WeightInput[str] | None,
) -> dict[str, float]:
    if algorithm_weights is None:
        return {
            _coerce_registered_algorithm_name(name): _coerce_weight_number(weight, label="algorithm_weights")
            for name, weight in _DEFAULT_SEQUENCE_ALGORITHM_WEIGHTS.items()
        }

    candidates, weights = _coerce_weight_input(
        algorithm_weights,
        coerce_value=_coerce_registered_algorithm_name,
        label="algorithm_weights",
    )
    return {name: weight for name, weight in zip(candidates, weights, strict=False)}


def _instantiate_registered_algorithm(name: str) -> SequenceRandomizationAlgorithm:
    normalized_name = _coerce_registered_algorithm_name(name)
    return _SEQUENCE_ALGORITHM_REGISTRY[normalized_name]()


def _coerce_registered_algorithm_name(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"algorithm names must be str, got {type(value).__name__}"
        )

    normalized_name = value.strip().lower().replace("-", "_")
    if normalized_name not in _SEQUENCE_ALGORITHM_REGISTRY:
        known = ", ".join(sorted(_SEQUENCE_ALGORITHM_REGISTRY))
        raise ValueError(
            f"Unknown sequence algorithm {value!r}. Valid options: {known}."
        )
    return normalized_name


def _is_sequence_algorithm_instance(value: Any) -> bool:
    return callable(getattr(value, "generate", None))


def _coerce_positive_beat_length(value: TimelineLike, *, field_name: str) -> Fraction:
    duration = coerce_timeline_duration(value, field_name=field_name)
    if duration.mode != "beats":
        raise ValueError(f"{field_name} must use beat-mode timing")

    beats = duration.as_beats()
    if beats <= 0:
        raise ValueError(f"{field_name} must be > 0 beats")
    return beats


def _coerce_duration_weight_map(
    duration_weights: WeightInput[TimelineLike] | None,
) -> tuple[tuple[Fraction, ...], tuple[float, ...]]:
    if duration_weights is None:
        return (
            tuple(_DEFAULT_SEQUENCE_DURATION_WEIGHTS.keys()),
            tuple(float(weight) for weight in _DEFAULT_SEQUENCE_DURATION_WEIGHTS.values()),
        )

    return _coerce_weight_input(
        duration_weights,
        coerce_value=lambda value: _coerce_positive_beat_length(
            value,
            field_name="duration_weights",
        ),
        label="duration_weights",
    )


def _coerce_event_type_weights(
    event_type_weights: WeightInput[str] | None,
) -> dict[str, float]:
    default = {
        "note": 6.0,
        "rest": 1.0,
        "chord": 2.0,
        "continue": 1.0,
    }
    if event_type_weights is None:
        return default

    candidates, weights = _coerce_weight_input(
        event_type_weights,
        coerce_value=lambda value: _coerce_event_type_name(value),
        label="event_type_weights",
    )
    resolved = {name: weight for name, weight in zip(candidates, weights, strict=False)}
    for key in ("note", "rest", "chord", "continue"):
        resolved.setdefault(key, 0.0)
    return resolved


def _coerce_event_type_name(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"event_type_weights keys must be str, got {type(value).__name__}"
        )

    normalized = value.strip().lower()
    if normalized not in {"note", "rest", "chord", "continue"}:
        raise ValueError(
            "event_type_weights keys must be one of: note, rest, chord, continue"
        )
    return normalized


def _choose_duration_for_remaining(
    rng: Random,
    remaining: Fraction,
    duration_weight_map: tuple[tuple[Fraction, ...], tuple[float, ...]],
) -> Fraction:
    durations, weights = duration_weight_map
    valid: list[Fraction] = []
    valid_weights: list[float] = []

    for duration, weight in zip(durations, weights, strict=False):
        if duration <= remaining:
            valid.append(duration)
            valid_weights.append(weight)

    if not valid:
        return remaining

    if sum(valid_weights) == 0:
        return min(valid)

    return rng.engine.choices(valid, weights=valid_weights, k=1)[0]


def _sample_note_for_context(
    rng: Random,
    *,
    scale: Scale | None,
    chord: Chord | None,
) -> Note:
    if scale is not None:
        return rng.note(scale=scale).with_octave(None)
    if chord is not None:
        return rng.engine.choice(tuple(note.with_octave(None) for note in chord.notes))
    return rng.chromatic_note().with_octave(None)


def _sample_chord_for_context(
    rng: Random,
    *,
    scale: Scale | None,
    chord: Chord | None,
) -> Chord:
    if chord is not None:
        return chord

    if scale is not None:
        try:
            return rng.chord(scale=scale)
        except ValueError:
            pass

    return rng.chromatic_chord()


def _resolve_optional_scale(scale: Scale | str | None) -> Scale | None:
    if scale is None:
        return None
    return coerce_scale_context_value(scale)


def _resolve_optional_chord(chord: Chord | str | None) -> Chord | None:
    if chord is None:
        return None
    if isinstance(chord, Chord):
        return chord
    if isinstance(chord, str):
        return Chord.from_string(chord)
    raise TypeError(f"chord must be Chord, str, or None; got {type(chord).__name__}")


def _fallback_anchor_chord(rng: Random, scale: Scale) -> Chord:
    try:
        return rng.chord(scale=scale)
    except ValueError:
        scale_notes = scale.notes
        if len(scale_notes) >= 3:
            return Chord.from_notes((scale_notes[0], scale_notes[2], scale_notes[-1]))
        return Chord.from_notes((scale_notes[0], scale_notes[0], scale_notes[0]))


def _closest_scale_note_index(scale_notes: tuple[Note, ...], target: Note) -> int:
    for index, note in enumerate(scale_notes):
        if note.pitch_class == target.pitch_class:
            return index
    return 0


def _coerce_probability(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a numeric probability")

    probability = float(value)
    if probability < 0.0 or probability > 1.0:
        raise ValueError(f"{label} must be in range [0, 1]")
    return probability


def _validate_sequence_consumes_exact_beats(sequence: Sequence, expected_beats: Fraction) -> None:
    cursor = Fraction(0, 1)
    for entry in sequence.entries:
        if entry.duration.mode != "beats":
            raise ValueError("Generated sequence must use beat-mode timing")

        duration = entry.duration.as_beats()
        if entry.offset is None:
            start = cursor
        else:
            if entry.offset.mode != "beats":
                raise ValueError("Generated sequence offsets must use beat-mode timing")
            start = entry.offset.as_beats()

        end = start + duration
        if entry.offset is None:
            cursor = end
        elif end > cursor:
            cursor = end

    consumed = cursor
    if consumed != expected_beats:
        raise ValueError(
            f"Generated sequence consumed {consumed} beats; expected {expected_beats}."
        )


_SEQUENCE_ALGORITHM_REGISTRY: dict[str, Callable[[], SequenceRandomizationAlgorithm]] = {
    PureRandomSequenceAlgorithm.name: PureRandomSequenceAlgorithm,
    MotifVariationSequenceAlgorithm.name: MotifVariationSequenceAlgorithm,
    ScaleWalkSequenceAlgorithm.name: ScaleWalkSequenceAlgorithm,
    ChordAnchorWalkSequenceAlgorithm.name: ChordAnchorWalkSequenceAlgorithm,
}


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
    weights: SequenceABC[WeightNumber],
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
    elif isinstance(weighted_values, SequenceABC) and not isinstance(
        weighted_values,
        (str, bytes, bytearray),
    ):
        for pair in weighted_values:
            if (
                not isinstance(pair, SequenceABC)
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
    "SequenceRandomizationAlgorithm",
    "PureRandomSequenceAlgorithm",
    "MotifVariationSequenceAlgorithm",
    "ScaleWalkSequenceAlgorithm",
    "ChordAnchorWalkSequenceAlgorithm",
    "WeightInput",
    "dualmethod",
    "get_global_random",
    "configure_global_random",
    "reset_global_random",
]
