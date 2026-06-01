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
