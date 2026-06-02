"""Behavior tests for MotifVariationSequenceAlgorithm."""

from __future__ import annotations

from fractions import Fraction

import pytest

from chordelia import MotifVariationSequenceAlgorithm, Random
from chordelia.notes import Note
from chordelia.sequences import Sequence


pytestmark = pytest.mark.usefixtures(
    "reset_global_scale_context_state",
    "reset_global_random_state",
)


def _consumed_beats(sequence: Sequence) -> Fraction:
    return sum((entry.duration.as_beats() for entry in sequence.entries), Fraction(0, 1))


class TestMotifVariationSequenceAlgorithm:
    """Behavior checks for motif variation sequence generation."""

    def test_generate_fills_exact_requested_beat_span(self):
        sequence = Random(seed=5).sequence(
            Fraction(15, 2),
            algorithm=MotifVariationSequenceAlgorithm(),
            scale="C major",
        )

        assert _consumed_beats(sequence) == Fraction(15, 2)

    def test_algorithm_instance_reuse_preserves_stateful_continuity(self):
        rng = Random(seed=77)
        motif = MotifVariationSequenceAlgorithm(motif_beats=2)

        seq_a = rng.sequence(
            8,
            algorithm=motif,
            scale="D minor",
            mutation_probability=0,
        )
        seq_b = rng.sequence(
            8,
            algorithm=motif,
            scale="D minor",
            mutation_probability=0,
        )

        assert motif._motif_template is not None
        assert seq_a == seq_b

    def test_algorithm_accepts_explicit_motif_sequence_constructor_arg(self):
        rng = Random(seed=77)
        motif_sequence = Sequence(
            (
                (Note("C4"), 1),
                (Note("D4"), 1),
            )
        )
        motif = MotifVariationSequenceAlgorithm(
            motif_beats=2,
            motif_sequence=motif_sequence,
        )

        sequence = rng.sequence(
            4,
            algorithm=motif,
            mutation_probability=0,
        )

        expected = Sequence(
            (
                (Note("C4"), 1),
                (Note("D4"), 1),
                (Note("C4"), 1),
                (Note("D4"), 1),
            )
        )
        assert sequence == expected

    def test_constructor_rejects_non_sequence_motif_sequence(self):
        with pytest.raises(TypeError, match="motif_sequence must be a chordelia.sequences.Sequence"):
            MotifVariationSequenceAlgorithm(
                motif_sequence=[(Note("C4"), 1)],
            )

    def test_constructor_rejects_empty_motif_sequence(self):
        with pytest.raises(ValueError, match="motif_sequence must contain at least one entry"):
            MotifVariationSequenceAlgorithm(
                motif_sequence=Sequence(()),
            )

    def test_generate_rejects_call_time_motif_sequence_arg(self):
        rng = Random(seed=77)
        motif = MotifVariationSequenceAlgorithm(motif_beats=2)

        with pytest.raises(TypeError, match="motif_sequence must be provided to"):
            rng.sequence(
                4,
                algorithm=motif,
                motif_sequence=Sequence(((Note("C4"), 1),)),
            )

    def test_generate_mutation_handles_out_of_scale_motif_note(self):
        rng = Random(seed=77)
        motif = MotifVariationSequenceAlgorithm(
            motif_sequence=Sequence(((Note("C#4"), 1),))
        )

        sequence = rng.sequence(
            4,
            algorithm=motif,
            scale="C major",
            mutation_probability=1.0,
        )

        assert _consumed_beats(sequence) == Fraction(4, 1)
        assert len(sequence.entries) == 4
        assert all(isinstance(entry.payload, Note) for entry in sequence.entries)
