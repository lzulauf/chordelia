"""Behavior tests for ChordAnchorWalkSequenceAlgorithm."""

from __future__ import annotations

from fractions import Fraction

import pytest

from chordelia import ChordAnchorWalkSequenceAlgorithm, Random
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


class TestChordAnchorWalkSequenceAlgorithm:
    """Behavior checks for chord anchor walk sequence generation."""

    def test_generate_fills_exact_requested_beat_span(self):
        sequence = Random(seed=5).sequence(
            Fraction(15, 2),
            algorithm=ChordAnchorWalkSequenceAlgorithm(),
            scale="C major",
            chord="Am",
        )

        assert _consumed_beats(sequence) == Fraction(15, 2)

    def test_generate_starts_and_ends_on_chord_tones(self):
        sequence = Random(seed=13).sequence(
            8,
            algorithm="chord_anchor_walk",
            scale="C major",
            chord="Am",
        )

        chord_tones = {note.pitch_class for note in Chord.from_string("Am").notes}
        first = sequence.entries[0].payload
        last = sequence.entries[-1].payload
        assert isinstance(first, Note)
        assert isinstance(last, Note)
        assert first.pitch_class in chord_tones
        assert last.pitch_class in chord_tones

    def test_generate_assigns_octave_when_scale_context_has_none(self):
        sequence = Random(seed=13).sequence(
            8,
            algorithm="chord_anchor_walk",
            scale=Scale("C", ScaleType.MAJOR),
            chord="Am",
        )

        for entry in sequence.entries:
            assert isinstance(entry.payload, Note)
            assert entry.payload.octave is not None

    def test_generate_allows_jumps_only_between_chord_tones(self):
        sequence = Random(seed=21).sequence(
            24,
            algorithm="chord_anchor_walk",
            scale="C major",
            chord="Am",
            duration_weights={1: 1.0},
            jump_probability=1.0,
        )

        scale_pitch_classes = tuple(
            note.pitch_class for note in Scale("C", ScaleType.MAJOR).notes
        )
        scale_index_by_pitch_class = {
            pitch_class: index
            for index, pitch_class in enumerate(scale_pitch_classes)
        }
        chord_pitch_classes = {
            note.pitch_class for note in Chord.from_string("Am").notes
        }

        pitch_classes = [entry.payload.pitch_class for entry in sequence.entries]
        for index in range(len(pitch_classes) - 1):
            current_pitch_class = pitch_classes[index]
            next_pitch_class = pitch_classes[index + 1]
            current_index = scale_index_by_pitch_class[current_pitch_class]
            next_index = scale_index_by_pitch_class[next_pitch_class]

            forward = (next_index - current_index) % len(scale_pitch_classes)
            backward = (current_index - next_index) % len(scale_pitch_classes)
            is_adjacent_step = forward == 1 or backward == 1

            # Non-chord notes must continue by scale-step movement only.
            if current_pitch_class not in chord_pitch_classes:
                assert is_adjacent_step

            # Non-adjacent moves represent jump transitions and must be chord-to-chord.
            if not is_adjacent_step:
                assert current_pitch_class in chord_pitch_classes
                assert next_pitch_class in chord_pitch_classes
