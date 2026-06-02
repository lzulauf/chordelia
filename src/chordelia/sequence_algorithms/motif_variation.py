"""Motif-variation sequence generation algorithm."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, ClassVar, TYPE_CHECKING

from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.randomization import (
    SequenceRandomizationAlgorithm,
    _coerce_positive_beat_length,
    _coerce_probability,
    _ensure_note_has_octave,
    _resolve_optional_chord,
    _resolve_optional_scale,
    _scale_with_octave_for_sequence,
)
from chordelia.rhythm import TimelineLike
from chordelia.scales import Scale
from chordelia.sequences import Rest, Sequence
from chordelia.sequence_algorithms.pure_random import PureRandomSequenceAlgorithm

if TYPE_CHECKING:
    from chordelia.randomization import Random


class MotifVariationSequenceAlgorithm(SequenceRandomizationAlgorithm):
    """Motif-first generator that reuses motif state across calls.

    Constructor args:
    - motif_beats: TimelineLike | None
      Optional default motif span used when generate(..., motif_beats=...) is
      not provided. If omitted entirely, motif span defaults to 4 beats or
      beat_length, whichever is smaller.
    - motif_sequence: Sequence | None
      Optional initial motif template. When provided, this sequence becomes
      the active motif template used until reset or rebuilt.

    Accepted generate kwargs:
    - motif_beats: TimelineLike
      Per-call motif span override.
    - reset_motif: bool
      If true, rebuild motif template before generation.
      Default is false.
    - mutation_probability: float in [0, 1]
      Probability that each repeated motif payload mutates.
      Default is 0.25.
      Notes outside the active scale mutate chromatically by one semitone
      to preserve directional motion without requiring diatonic membership.
    - motif_event_type_weights: WeightInput[str]
      Relative action weights used only when initially building the motif via
      PureRandomSequenceAlgorithm.
      Defaults to {"note": 7, "rest": 1, "chord": 2, "tie": 1}.
    - duration_weights: WeightInput[TimelineLike]
      Duration weights used during initial motif creation.
    - pitch_change_probability: float in [0, 1]
      Passed to PureRandomSequenceAlgorithm for motif construction.
      Default is 0.7 during motif creation.
    """

    name: ClassVar[str] = "motif_variation"
    default_selection_weight: ClassVar[float] = 40.0

    def __init__(
        self,
        *,
        motif_beats: TimelineLike | None = None,
        motif_sequence: Sequence | None = None,
    ) -> None:
        self._motif_beats = motif_beats
        self._motif_template = (
            self._template_from_motif_sequence(motif_sequence)
            if motif_sequence is not None
            else None
        )

    def generate(
        self,
        *,
        rng: "Random",
        beat_length: Fraction,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **params: Any,
    ) -> Sequence:
        """Generate a sequence by repeating and mutating a cached motif template."""
        scale_obj = _resolve_optional_scale(scale)
        chord_obj = _resolve_optional_chord(chord)

        if "motif_sequence" in params:
            raise TypeError(
                "motif_sequence must be provided to "
                "MotifVariationSequenceAlgorithm(...) constructor"
            )

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
        rng: "Random",
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
                    "tie": 1,
                },
            ),
            duration_weights=params.get("duration_weights"),
            pitch_change_probability=params.get("pitch_change_probability", 0.7),
        )
        return tuple(
            (entry.payload, entry.duration.as_beats())
            for entry in motif_source.entries
        )

    def _template_from_motif_sequence(
        self,
        motif_sequence: Sequence,
    ) -> tuple[tuple[Any, Fraction], ...]:
        if not isinstance(motif_sequence, Sequence):
            raise TypeError(
                "motif_sequence must be a chordelia.sequences.Sequence instance"
            )

        template = tuple(
            (entry.payload, entry.duration.as_beats())
            for entry in motif_sequence.entries
        )
        if not template:
            raise ValueError("motif_sequence must contain at least one entry")

        if any(duration <= 0 for _, duration in template):
            raise ValueError("motif_sequence entries must have positive durations")

        return template

    def _mutate_payload(
        self,
        payload: Any,
        *,
        rng: "Random",
        scale: Scale | None,
        probability: float,
    ) -> Any:
        if isinstance(payload, Rest):
            return payload
        if rng.engine.random() > probability:
            return payload

        if isinstance(payload, Note):
            direction = rng.engine.choice((-1, 1))
            payload_note = _ensure_note_has_octave(payload, fallback_octave=4)

            if scale is not None:
                normalized_scale = _scale_with_octave_for_sequence(
                    scale,
                    fallback_octave=payload_note.octave or 4,
                )
                if normalized_scale.degree_for_chord_root(payload_note) is not None:
                    return payload_note.shift(direction, scale=normalized_scale)
                return payload_note.transpose(direction)

            return payload_note.transpose(direction)

        return payload
