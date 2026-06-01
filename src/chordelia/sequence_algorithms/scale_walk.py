"""Scale-walk sequence generation algorithm."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, ClassVar, TYPE_CHECKING

from chordelia.chords import Chord
from chordelia.randomization import (
    SequenceRandomizationAlgorithm,
    _choose_duration_for_remaining,
    _choose_scale_walk_start_pitch_class,
    _chord_with_octave_for_sequence,
    _coerce_duration_weight_map,
    _coerce_probability,
    _fallback_anchor_chord,
    _generate_scale_walk_pitch_classes,
    _infer_scale_walk_direction,
    _repair_scale_walk_pitch_classes,
    _resolve_optional_chord,
    _resolve_optional_scale,
    _scale_walk_note_from_pitch_class,
    _scale_with_octave_for_sequence,
)
from chordelia.scales import Scale, ScaleType
from chordelia.sequences import Sequence

if TYPE_CHECKING:
    from chordelia.randomization import Random


class ScaleWalkSequenceAlgorithm(SequenceRandomizationAlgorithm):
    """Directional scale walk with stateful direction/index carry-forward.

    Accepted generate kwargs:
    - duration_weights: WeightInput[TimelineLike]
      Relative duration weights for each emitted note event.
    - direction_change_probability: float in [0, 1]
      Probability to flip movement direction after each emitted event.
      Default is 0.2.
    - run_step_probability: float in [0, 1]
      Probability to advance by 2 scale steps instead of 1.
      Default is 0.2.

    Notes:
    - When chord context is provided, generated walks begin and end on chord
      tones.
    - Out-of-scale notes (when present) move chromatically one semitone per
      step.
    - Direction changes are only allowed on steps that originate from
      in-scale notes.
    - If no scale is provided, this algorithm defaults to C major.
    """

    name: ClassVar[str] = "scale_walk"
    default_selection_weight: ClassVar[float] = 30.0

    def __init__(self) -> None:
        self._last_pitch_class: int | None = None
        self._last_direction: int | None = None

    def generate(
        self,
        *,
        rng: "Random",
        beat_length: Fraction,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **params: Any,
    ) -> Sequence:
        """Generate a scale-constrained walk sequence."""
        scale_obj = _resolve_optional_scale(scale) or Scale("C", ScaleType.MAJOR)
        normalized_scale = _scale_with_octave_for_sequence(scale_obj)
        chord_obj = _resolve_optional_chord(chord)
        if chord_obj is None:
            chord_obj = _fallback_anchor_chord(rng, normalized_scale)

        normalized_chord = _chord_with_octave_for_sequence(
            chord_obj,
            fallback_octave=normalized_scale.root.octave or 4,
        )

        duration_weights = _coerce_duration_weight_map(params.get("duration_weights"))
        direction_change_probability = _coerce_probability(
            params.get("direction_change_probability", 0.2),
            label="direction_change_probability",
        )
        run_step_probability = _coerce_probability(
            params.get("run_step_probability", 0.2),
            label="run_step_probability",
        )

        scale_notes = tuple(normalized_scale.notes)
        scale_pitch_classes = tuple(note.pitch_class for note in scale_notes)
        chord_notes = tuple(normalized_chord.notes)
        chord_pitch_classes = tuple(
            dict.fromkeys(note.pitch_class for note in chord_notes)
        )

        if not chord_pitch_classes:
            chord_pitch_classes = (scale_pitch_classes[0],)

        start_pitch_class = _choose_scale_walk_start_pitch_class(
            rng,
            chord_pitch_classes=chord_pitch_classes,
            last_pitch_class=self._last_pitch_class,
        )
        initial_direction = (
            self._last_direction
            if self._last_direction in {-1, 1}
            else rng.engine.choice((-1, 1))
        )

        durations: list[Fraction] = []
        remaining = beat_length
        while remaining > 0:
            duration = _choose_duration_for_remaining(rng, remaining, duration_weights)
            durations.append(duration)
            remaining -= duration

        walk_pitch_classes, _ = _generate_scale_walk_pitch_classes(
            rng,
            length=len(durations),
            start_pitch_class=start_pitch_class,
            initial_direction=initial_direction,
            scale_pitch_classes=scale_pitch_classes,
            direction_change_probability=direction_change_probability,
            run_step_probability=run_step_probability,
        )
        repaired_pitch_classes = _repair_scale_walk_pitch_classes(
            walk_pitch_classes,
            initial_direction=initial_direction,
            scale_pitch_classes=scale_pitch_classes,
            chord_pitch_classes=chord_pitch_classes,
        )

        scale_note_by_pitch_class = {
            note.pitch_class: note for note in scale_notes
        }
        chord_note_by_pitch_class = {
            note.pitch_class: note for note in chord_notes
        }
        fallback_octave = normalized_scale.root.octave or 4

        entries = [
            (
                _scale_walk_note_from_pitch_class(
                    pitch_class,
                    scale_note_by_pitch_class=scale_note_by_pitch_class,
                    chord_note_by_pitch_class=chord_note_by_pitch_class,
                    fallback_octave=fallback_octave,
                ),
                duration,
            )
            for pitch_class, duration in zip(repaired_pitch_classes, durations, strict=False)
        ]

        self._last_pitch_class = repaired_pitch_classes[-1]
        if len(repaired_pitch_classes) > 1:
            self._last_direction = _infer_scale_walk_direction(
                previous_pitch_class=repaired_pitch_classes[-2],
                current_pitch_class=repaired_pitch_classes[-1],
                scale_pitch_classes=scale_pitch_classes,
            )
        else:
            self._last_direction = initial_direction

        return Sequence(entries)
