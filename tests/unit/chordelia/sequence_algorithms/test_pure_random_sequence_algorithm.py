"""Behavior tests for PureRandomSequenceAlgorithm."""

from __future__ import annotations

from fractions import Fraction

import pytest

from chordelia import PureRandomSequenceAlgorithm, Random
from chordelia.notes import Note
from chordelia.scales import Scale, ScaleType
from chordelia.sequences import Sequence


pytestmark = pytest.mark.usefixtures(
    "reset_global_scale_context_state",
    "reset_global_random_state",
)


def _consumed_beats(sequence: Sequence) -> Fraction:
    return sum((entry.duration.as_beats() for entry in sequence.entries), Fraction(0, 1))


class TestPureRandomSequenceAlgorithm:
    """Behavior checks for pure random sequence generation."""

    def test_generate_fills_exact_requested_beat_span(self):
        sequence = Random(seed=5).sequence(
            Fraction(15, 2),
            algorithm=PureRandomSequenceAlgorithm(),
            scale="C major",
        )

        assert _consumed_beats(sequence) == Fraction(15, 2)

    def test_generate_can_extend_prior_pitched_entry_via_tie(self):
        sequence = Random(seed=1).sequence(
            4,
            algorithm=PureRandomSequenceAlgorithm(),
            scale="C major",
            event_type_weights={"note": 1.0, "tie": 100.0, "rest": 0.0, "chord": 0.0},
            duration_weights={1: 1.0},
        )

        # At least one tie should collapse events into fewer entries than durations.
        assert len(sequence.entries) < 4
        assert _consumed_beats(sequence) == Fraction(4, 1)

    def test_generate_note_events_include_octave_for_octaveless_scale(self):
        sequence = Random(seed=17).sequence(
            4,
            algorithm="pure_random",
            scale=Scale("C", ScaleType.MAJOR),
            event_type_weights={"note": 1.0, "tie": 0.0, "rest": 0.0, "chord": 0.0},
            duration_weights={1: 1.0},
        )

        for entry in sequence.entries:
            assert isinstance(entry.payload, Note)
            assert entry.payload.octave == 4
