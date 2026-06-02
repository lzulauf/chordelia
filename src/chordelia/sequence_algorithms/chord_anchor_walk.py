"""Chord-anchor walk sequence generation algorithm."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, ClassVar, TYPE_CHECKING

from chordelia.chords import Chord
from chordelia.randomization import (
    SequenceRandomizationAlgorithm,
    _choose_duration_for_remaining,
    _chord_with_octave_for_sequence,
    _closest_scale_note_index,
    _coerce_duration_weight_map,
    _coerce_probability,
    _fallback_anchor_chord,
    _resolve_optional_chord,
    _resolve_optional_scale,
    _scale_with_octave_for_sequence,
)
from chordelia.scales import Scale, ScaleType
from chordelia.sequences import Sequence

if TYPE_CHECKING:
    from chordelia.randomization import Random


class ChordAnchorWalkSequenceAlgorithm(SequenceRandomizationAlgorithm):
    """Scale walk constrained to chord-tone starts/ends.

    Accepted generate kwargs:
    - duration_weights: WeightInput[TimelineLike]
      Relative duration weights for each emitted event.
    - jump_probability: float in [0, 1]
            Probability for interior events to jump directly to a chord tone instead
            of moving one scale step.
            Jumps are only considered when the current note is already a chord tone,
            so jump transitions are always chord-tone to chord-tone.
      Default is 0.35.

    Notes:
    - If scale is omitted, this algorithm defaults to C major.
    - If chord is omitted, a fallback chord is sampled/derived from the scale.
    """

    name: ClassVar[str] = "chord_anchor_walk"
    default_selection_weight: ClassVar[float] = 20.0

    def generate(
        self,
        *,
        rng: "Random",
        beat_length: Fraction,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **params: Any,
    ) -> Sequence:
        """Generate a chord-anchored walk sequence."""
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
        jump_probability = _coerce_probability(
            params.get("jump_probability", 0.35),
            label="jump_probability",
        )

        chord_tones = tuple(normalized_chord.notes)
        chord_pitch_classes = {note.pitch_class for note in chord_tones}
        scale_notes = tuple(normalized_scale.notes)

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
                current_pitch_class = scale_notes[previous_index].pitch_class
                can_jump = current_pitch_class in chord_pitch_classes
                if can_jump and rng.engine.random() < jump_probability:
                    payload = rng.engine.choice(chord_tones)
                    previous_index = _closest_scale_note_index(scale_notes, payload)
                else:
                    previous_index = (previous_index + rng.engine.choice((-1, 1))) % len(scale_notes)
                    payload = scale_notes[previous_index]

            entries.append((payload, duration))

        return Sequence(entries)
