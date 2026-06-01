"""Behavior tests for ScaleWalkSequenceAlgorithm."""

from __future__ import annotations

from fractions import Fraction

import pytest

from chordelia import Random, ScaleWalkSequenceAlgorithm
from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.scales import Scale, ScaleType
from chordelia.sequences import Sequence


pytestmark = pytest.mark.usefixtures(
    "reset_global_scale_context_state",
    "reset_global_random_state",
)


def _consumed_beats(sequence: Sequence) -> Fraction:
    return sum((entry.duration.as_beats() for entry in sequence.entries), Fraction(0, 1))


class TestScaleWalkSequenceAlgorithm:
    """Behavior checks for scale walk sequence generation."""

    def test_generate_fills_exact_requested_beat_span(self):
        sequence = Random(seed=5).sequence(
            Fraction(15, 2),
            algorithm=ScaleWalkSequenceAlgorithm(),
            scale="C major",
        )

        assert _consumed_beats(sequence) == Fraction(15, 2)

    def test_generate_notes_stay_in_scale(self):
        scale = Scale("E", ScaleType.NATURAL_MINOR)
        sequence = Random(seed=9).sequence(8, algorithm="scale_walk", scale=scale)

        allowed = {note.pitch_class for note in scale.notes}
        for entry in sequence.entries:
            assert isinstance(entry.payload, Note)
            assert entry.payload.pitch_class in allowed

    def test_generate_starts_and_ends_on_chord_tones_when_chord_provided(self):
        sequence = Random(seed=9).sequence(
            8,
            algorithm="scale_walk",
            scale="C major",
            chord="G",
        )

        chord_tones = {note.pitch_class for note in Chord.from_string("G").notes}
        first_note = sequence.entries[0].payload
        final_note = sequence.entries[-1].payload
        assert isinstance(first_note, Note)
        assert isinstance(final_note, Note)
        assert first_note.pitch_class in chord_tones
        assert final_note.pitch_class in chord_tones

    def test_generate_out_of_scale_steps_are_chromatic_and_direction_changes_only_in_scale(self):
        sequence = Random(seed=12).sequence(
            16,
            algorithm="scale_walk",
            scale="C major",
            chord="F#",
            duration_weights={1: 1.0},
            direction_change_probability=1.0,
            run_step_probability=0.0,
        )

        scale_pitch_classes = tuple(note.pitch_class for note in Scale("C", ScaleType.MAJOR).notes)
        scale_set = set(scale_pitch_classes)
        scale_index_by_pitch_class = {
            pitch_class: index for index, pitch_class in enumerate(scale_pitch_classes)
        }
        chord_tones = {note.pitch_class for note in Chord.from_string("F#").notes}

        pitch_classes = [entry.payload.pitch_class for entry in sequence.entries]
        assert pitch_classes[0] in chord_tones
        assert pitch_classes[-1] in chord_tones

        directions: list[int] = []
        for index in range(len(pitch_classes) - 1):
            current_pitch_class = pitch_classes[index]
            next_pitch_class = pitch_classes[index + 1]

            if current_pitch_class in scale_set:
                scale_index = scale_index_by_pitch_class[current_pitch_class]
                upward = {
                    scale_pitch_classes[(scale_index + 1) % len(scale_pitch_classes)],
                    scale_pitch_classes[(scale_index + 2) % len(scale_pitch_classes)],
                }
                downward = {
                    scale_pitch_classes[(scale_index - 1) % len(scale_pitch_classes)],
                    scale_pitch_classes[(scale_index - 2) % len(scale_pitch_classes)],
                }
                delta = (next_pitch_class - current_pitch_class) % 12
                assert next_pitch_class in upward | downward or delta in {1, 11}
                if next_pitch_class in upward or delta == 1:
                    step_direction = 1
                else:
                    step_direction = -1
            else:
                delta = (next_pitch_class - current_pitch_class) % 12
                assert delta in {1, 11}
                step_direction = 1 if delta == 1 else -1

            directions.append(step_direction)

        for index in range(1, len(directions)):
            if directions[index] != directions[index - 1]:
                # Direction flips are only allowed when the move originated in-scale.
                assert pitch_classes[index] in scale_set

    def test_generate_assigns_octave_when_scale_context_has_none(self):
        sequence = Random(seed=9).sequence(
            8,
            algorithm="scale_walk",
            scale=Scale("E", ScaleType.NATURAL_MINOR),
        )

        for entry in sequence.entries:
            assert isinstance(entry.payload, Note)
            assert entry.payload.octave is not None
