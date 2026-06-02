"""Tests for the randomization module."""

from __future__ import annotations

import random as std_random
from unittest.mock import patch

import pytest

from chordelia import Random, configure_global_random, get_global_random, reset_global_random
from chordelia.chords import ChordQuality
from chordelia.degrees import Degree
from chordelia.intervals import Interval
from chordelia.randomization import dualmethod
from chordelia.scale_context import with_global_scale_context
from chordelia.scales import Scale, ScaleType


pytestmark = pytest.mark.usefixtures(
    "reset_global_scale_context_state",
    "reset_global_random_state",
)


class TestRandomConstruction:
    """Construction, engine wrapping, and invariant checks."""

    def test_seed_and_engine_are_mutually_exclusive(self):
        with pytest.raises(ValueError, match="either seed or engine"):
            Random(seed=10, engine=std_random.Random(10))

    def test_engine_type_is_validated(self):
        with pytest.raises(TypeError, match="engine must be an instance"):
            Random(engine=object())

    def test_engine_property_returns_wrapped_engine(self):
        engine = std_random.Random(42)

        rng = Random(engine=engine)

        assert rng.engine is engine


class TestWeightedSelectionValidation:
    """Validation behavior for generic weighted helpers."""

    def test_choice_requires_non_empty_candidates(self):
        with pytest.raises(ValueError, match="values cannot be empty"):
            Random(seed=1).choice(())

    def test_weighted_choice_requires_matching_lengths(self):
        with pytest.raises(ValueError, match="weights length must match"):
            Random(seed=1).weighted_choice(("a", "b"), (1.0,))

    @pytest.mark.parametrize(
        "weights, expected_error",
        [
            pytest.param((1.0, -1.0), ValueError, id="negative"),
            pytest.param((1.0, float("inf")), TypeError, id="infinite"),
            pytest.param((1.0, float("nan")), TypeError, id="nan"),
            pytest.param((1.0, True), TypeError, id="bool"),
            pytest.param((0.0, 0.0), ValueError, id="all-zero"),
        ],
    )
    def test_weighted_choice_validates_weight_values(self, weights, expected_error):
        with pytest.raises(expected_error):
            Random(seed=1).weighted_choice(("a", "b"), weights)

    def test_weighted_choice_map_accepts_mapping(self):
        rng = Random(seed=1)

        selected = rng.weighted_choice_map({"x": 0.0, "y": 1.0})

        assert selected == "y"

    def test_weighted_choice_map_accepts_pair_sequence(self):
        rng = Random(seed=1)

        selected = rng.weighted_choice_map((("x", 0.0), ("y", 1.0)))

        assert selected == "y"

    def test_weighted_choice_accepts_integer_relative_weights(self):
        rng = Random(seed=1)

        selected = rng.weighted_choice(("x", "y"), (0, 5))

        assert selected == "y"

    def test_weighted_choice_uses_relative_ratio_not_absolute_total(self):
        rng_a = Random(seed=123)
        rng_b = Random(seed=123)

        selected_a = rng_a.weighted_choice(("x", "y", "z"), (1, 3, 6))
        selected_b = rng_b.weighted_choice(("x", "y", "z"), (10, 30, 60))

        assert selected_a == selected_b

    def test_weighted_choice_map_validates_container_shape(self):
        rng = Random(seed=1)

        with pytest.raises(TypeError, match="mapping or sequence"):
            rng.weighted_choice_map(123)

        with pytest.raises(TypeError, match="2-item"):
            rng.weighted_choice_map(("bad", "shape"))


class TestDeterminism:
    """Seeded behavior is deterministic and reproducible."""

    def test_same_seed_same_sequence(self):
        rng1 = Random(seed=202606)
        rng2 = Random(seed=202606)
        c_major = Scale("C", ScaleType.MAJOR)

        seq1 = (
            str(rng1.scale()),
            str(rng1.degree(scale=c_major)),
            str(rng1.note(scale=c_major)),
            str(rng1.chord(scale=c_major)),
            str(rng1.chromatic_note()),
            str(rng1.chromatic_chord()),
            str(rng1.interval()),
        )
        seq2 = (
            str(rng2.scale()),
            str(rng2.degree(scale=c_major)),
            str(rng2.note(scale=c_major)),
            str(rng2.chord(scale=c_major)),
            str(rng2.chromatic_note()),
            str(rng2.chromatic_chord()),
            str(rng2.interval()),
        )

        assert seq1 == seq2

    def test_different_seeds_produce_different_observed_sequence(self):
        rng1 = Random(seed=10)
        rng2 = Random(seed=11)

        seq1 = [str(rng1.chromatic_note()) for _ in range(12)]
        seq2 = [str(rng2.chromatic_note()) for _ in range(12)]

        assert seq1 != seq2


class TestScaleAwareSelectors:
    """Scale-aware behavior for degree/note/chord selectors."""

    def test_degree_uses_global_scale_context_when_scale_not_provided(self):
        rng = Random(seed=1)

        with with_global_scale_context("C"):
            degree = rng.degree()

        assert isinstance(degree, Degree)
        assert 1 <= degree.to_int() <= 7

    def test_scale_aware_selectors_raise_without_any_scale_context(self):
        rng = Random(seed=1)

        with pytest.raises(ValueError, match="requires a scale context"):
            rng.degree()

        with pytest.raises(ValueError, match="requires a scale context"):
            rng.note()

        with pytest.raises(ValueError, match="requires a scale context"):
            rng.chord()

    def test_note_is_in_resolved_scale(self):
        rng = Random(seed=1)
        scale = Scale("C", ScaleType.MAJOR)

        note = rng.note(scale=scale)

        assert scale.contains_note(note)

    def test_chord_uses_sampled_degree_and_scale_harmony(self):
        rng = Random(seed=1)
        scale = Scale("C", ScaleType.MAJOR)

        chord = rng.chord(scale=scale, degree_weights={5: 1.0})

        assert chord == scale.chord_for_degree(5)

    def test_chord_propagates_heptatonic_guard(self):
        rng = Random(seed=1)
        blues = Scale("C", ScaleType.BLUES)

        with pytest.raises(ValueError, match="heptatonic"):
            rng.chord(scale=blues)

    def test_degree_weights_validate_degree_span_and_alteration(self):
        rng = Random(seed=1)
        c_major = Scale("C", ScaleType.MAJOR)

        with pytest.raises(ValueError, match="resolved scale span"):
            rng.degree(scale=c_major, degree_weights={8: 1.0})

        with pytest.raises(ValueError, match="unaltered scale degrees"):
            rng.degree(scale=c_major, degree_weights={"b2": 1.0})

    def test_scale_supports_weighted_root_and_scale_type_with_zero_exclusion(self):
        rng = Random(seed=99)

        selected = rng.scale(
            root_weights={"C": 0.0, "D": 1.0},
            scale_type_weights={ScaleType.MAJOR: 1.0, ScaleType.NATURAL_MINOR: 0.0},
        )

        assert str(selected.root) == "D"
        assert selected.scale_type == ScaleType.MAJOR

    def test_scale_can_select_modal_scale_type_directly(self):
        rng = Random(seed=1)

        selected = rng.scale(
            root_weights={"C": 1.0},
            scale_type_weights={ScaleType.DORIAN: 1.0},
        )

        assert str(selected.root) == "C"
        assert selected.pattern == (0, 2, 3, 5, 7, 9, 10)


class TestChromaticSelectors:
    """Chromatic selectors explicitly ignore scale context."""

    def test_chromatic_note_honors_weights(self):
        rng = Random(seed=1)

        selected = rng.chromatic_note(note_weights={"F#": 1.0, "C": 0.0})

        assert str(selected) == "F#"

    def test_chromatic_chord_honors_root_and_quality_weights(self):
        rng = Random(seed=1)

        selected = rng.chromatic_chord(
            root_weights={"A": 1.0},
            quality_weights={ChordQuality.MINOR: 1.0},
        )

        assert str(selected.root) == "A"
        assert selected.quality is ChordQuality.MINOR

    def test_interval_honors_weighted_input(self):
        rng = Random(seed=1)

        selected = rng.interval(interval_weights={"P5": 1.0, "m2": 0.0})

        assert isinstance(selected, Interval)
        assert selected.number == 5
        assert selected.semitones == 7

    def test_chromatic_selectors_do_not_consult_global_scale_context(self):
        rng = Random(seed=1)

        with patch(
            "chordelia.randomization.get_global_scale_context",
            side_effect=AssertionError("should not be called"),
        ):
            rng.chromatic_note()
            rng.chromatic_chord()
            rng.interval()


class TestGlobalSingletonAndDualInvocation:
    """Global singleton lifecycle and dual invocation semantics."""

    def test_get_global_random_is_lazy_and_idempotent(self):
        first = get_global_random()
        second = get_global_random()

        assert isinstance(first, Random)
        assert first is second

    def test_configure_global_random_replaces_singleton(self):
        original = get_global_random()

        replaced = configure_global_random(seed=123)

        assert replaced is get_global_random()
        assert replaced is not original

    def test_reset_global_random_recreates_singleton_on_next_get(self):
        first = configure_global_random(seed=1)

        reset_global_random()
        second = get_global_random()

        assert second is not first

    def test_class_calls_use_persistent_singleton_state(self):
        configure_global_random(seed=999)

        first = Random.chromatic_note()
        second = Random.chromatic_note()

        reset_global_random()
        configure_global_random(seed=999)

        replay_first = Random.chromatic_note()
        replay_second = Random.chromatic_note()

        assert str(first) == str(replay_first)
        assert str(second) == str(replay_second)

    def test_instance_and_class_calls_have_parity_for_equivalent_state(self):
        instance_rng = Random(seed=777)
        configure_global_random(seed=777)
        c_major = Scale("C", ScaleType.MAJOR)

        instance_outputs = (
            str(instance_rng.scale()),
            str(instance_rng.degree(scale=c_major)),
            str(instance_rng.note(scale=c_major)),
            str(instance_rng.chromatic_note()),
            str(instance_rng.interval()),
        )
        class_outputs = (
            str(Random.scale()),
            str(Random.degree(scale=c_major)),
            str(Random.note(scale=c_major)),
            str(Random.chromatic_note()),
            str(Random.interval()),
        )

        assert instance_outputs == class_outputs

    def test_dualmethod_rejects_invalid_receiver_context(self):
        descriptor = Random.__dict__["degree"]

        with pytest.raises(TypeError):
            descriptor._func(object(), scale=Scale("C", ScaleType.MAJOR))
