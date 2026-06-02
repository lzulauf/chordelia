"""Tests for sequence-level randomization APIs and built-in algorithms."""

from __future__ import annotations

import pytest

from chordelia import (
    ChordAnchorWalkSequenceAlgorithm,
    MotifVariationSequenceAlgorithm,
    PureRandomSequenceAlgorithm,
    Random,
    ScaleWalkSequenceAlgorithm,
    SequenceRandomizationAlgorithm,
)
from chordelia.rhythm import Duration
from chordelia.sequences import Sequence


pytestmark = pytest.mark.usefixtures(
    "reset_global_scale_context_state",
    "reset_global_random_state",
)


class TestRandomSequenceValidation:
    """Validation behavior for Random.sequence dispatch."""

    @pytest.mark.parametrize("beat_length", [0, -1, -0.5])
    def test_sequence_rejects_non_positive_beat_length(self, beat_length):
        with pytest.raises(ValueError, match="beat_length must be > 0"):
            Random(seed=1).sequence(beat_length)

    def test_sequence_rejects_seconds_mode_length(self):
        with pytest.raises(ValueError, match="beat-mode"):
            Random(seed=1).sequence(Duration.from_seconds(1))

    def test_sequence_rejects_unknown_algorithm_name(self):
        with pytest.raises(ValueError, match="Unknown sequence algorithm"):
            Random(seed=1).sequence(4, algorithm="missing")

    def test_sequence_rejects_unknown_algorithm_weight_keys(self):
        with pytest.raises(ValueError, match="Unknown sequence algorithm"):
            Random(seed=1).sequence(4, algorithm_weights={"missing": 1.0})

    def test_sequence_rejects_weights_with_explicit_algorithm(self):
        with pytest.raises(ValueError, match="cannot be used with an explicit algorithm"):
            Random(seed=1).sequence(
                4,
                algorithm=PureRandomSequenceAlgorithm(),
                algorithm_weights={"pure_random": 1.0},
            )

    def test_sequence_rejects_algorithm_params_wrapper_keyword(self):
        with pytest.raises(TypeError, match="algorithm_params wrapper is not supported"):
            Random(seed=1).sequence(
                4,
                algorithm="pure_random",
                scale="C major",
                algorithm_params={"mutation_probability": 0},
            )

    def test_sequence_rejects_duck_typed_non_subclass_algorithm_instance(self):
        class DuckAlgorithm:
            name = "duck"
            default_selection_weight = 1.0

            def generate(self, **kwargs):
                return Sequence(())

        with pytest.raises(TypeError, match="SequenceRandomizationAlgorithm instance"):
            Random(seed=1).sequence(4, algorithm=DuckAlgorithm())


class TestSequenceAlgorithmDiscovery:
    """Runtime discovery behavior for sequence algorithm subclasses."""

    def test_builtin_algorithms_are_direct_subclasses(self):
        direct = sorted(
            SequenceRandomizationAlgorithm.__subclasses__(),
            key=lambda subclass: subclass.__name__,
        )
        assert PureRandomSequenceAlgorithm in direct
        assert MotifVariationSequenceAlgorithm in direct
        assert ScaleWalkSequenceAlgorithm in direct
        assert ChordAnchorWalkSequenceAlgorithm in direct


class TestRandomSequenceDispatchAndDeterminism:
    """Dispatch paths and deterministic behavior checks."""

    def test_weighted_algorithm_selection_is_deterministic(self):
        rng_a = Random(seed=202606)
        rng_b = Random(seed=202606)
        weights = {
            "motif_variation": 40,
            "scale_walk": 30,
            "chord_anchor_walk": 20,
            "pure_random": 10,
        }

        seq_a = rng_a.sequence(8, algorithm_weights=weights, scale="A natural_minor")
        seq_b = rng_b.sequence(8, algorithm_weights=weights, scale="A natural_minor")

        assert seq_a == seq_b
