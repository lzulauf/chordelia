"""Tests for centralized global scale context helpers."""

from fractions import Fraction

import pytest

from chordelia.scale_context import (
    get_chordelia_context,
    get_default_note_duration_context,
    reset_chordelia_context,
    coerce_scale_context_value,
    coerce_default_note_duration_value,
    get_global_scale_context,
    reset_global_scale_context,
    set_chordelia_context,
    set_global_scale_context,
    with_chordelia_context,
    with_global_scale_context,
)
from chordelia.rhythm import Duration
from chordelia.scales import Scale


@pytest.fixture(autouse=True)
def _clear_global_scale_context():
    reset_chordelia_context()
    yield
    reset_chordelia_context()


class TestScaleContextCoercion:
    """Scale-context value coercion behavior."""

    def test_coerce_scale_instance_returns_same_value(self):
        scale = Scale("C", "major")

        assert coerce_scale_context_value(scale) is scale

    def test_coerce_scale_string_parses_supported_forms(self):
        major = coerce_scale_context_value("D")
        minor = coerce_scale_context_value("Am")

        assert str(major.root) == "D"
        assert str(minor.root) == "A"
        assert minor.scale_type.value == "natural_minor"

    def test_coerce_invalid_type_raises(self):
        with pytest.raises(TypeError):
            coerce_scale_context_value(object())


class TestDefaultDurationContextCoercion:
    """Default-duration coercion behavior."""

    def test_coerce_note_fraction_duration_to_beats(self):
        duration = coerce_default_note_duration_value(Duration("eighth"))

        assert duration.mode == "beats"
        assert duration.as_beats() == Fraction(1, 2)

    def test_coerce_numeric_value_to_beats_duration(self):
        duration = coerce_default_note_duration_value(Fraction(3, 4))

        assert duration.mode == "beats"
        assert duration.as_beats() == Fraction(3, 4)

    def test_coerce_invalid_type_raises(self):
        with pytest.raises(TypeError):
            coerce_default_note_duration_value(object())


class TestChordeliaContext:
    """Unified runtime context getter/setter and nested sparse override behavior."""

    def test_set_chordelia_context_sparse_updates(self):
        set_chordelia_context(scale="C", default_note_duration=1)

        updated = set_chordelia_context(scale="F")

        assert str(updated.scale.root) == "F"
        assert updated.default_note_duration.as_beats() == 1

    def test_with_chordelia_context_nested_sparse_overrides(self):
        with with_chordelia_context(scale="C", default_note_duration=1):
            outer = get_chordelia_context()
            assert str(outer.scale.root) == "C"
            assert outer.default_note_duration.as_beats() == 1

            with with_chordelia_context(scale="F"):
                inner_scale = get_chordelia_context()
                assert str(inner_scale.scale.root) == "F"
                assert inner_scale.default_note_duration.as_beats() == 1

            restored = get_chordelia_context()
            assert str(restored.scale.root) == "C"
            assert restored.default_note_duration.as_beats() == 1

    def test_with_chordelia_context_can_clear_one_field(self):
        with with_chordelia_context(scale="C", default_note_duration=1):
            with with_chordelia_context(scale=None):
                active = get_chordelia_context()
                assert active.scale is None
                assert active.default_note_duration.as_beats() == 1


class TestGlobalScaleContext:
    """Global scale context getter/setter and scoped override behavior."""

    def test_set_and_get_global_scale_context(self):
        applied = set_global_scale_context("Bb")

        assert str(applied.root) == "Bb"
        assert str(get_global_scale_context().root) == "Bb"

    def test_with_global_scale_context_restores_previous_state(self):
        set_global_scale_context("C")

        with with_global_scale_context("F") as scoped:
            assert str(scoped.root) == "F"
            assert str(get_global_scale_context().root) == "F"

        assert str(get_global_scale_context().root) == "C"

    def test_reset_global_scale_context_clears_state(self):
        set_global_scale_context("E")

        reset_global_scale_context()

        assert get_global_scale_context() is None

    def test_reset_global_scale_context_preserves_default_duration(self):
        set_chordelia_context(scale="E", default_note_duration=Fraction(1, 2))

        reset_global_scale_context()

        assert get_global_scale_context() is None
        assert get_default_note_duration_context().as_beats() == Fraction(1, 2)

    def test_default_note_duration_getter_returns_context_value(self):
        set_chordelia_context(default_note_duration=Fraction(1, 2))

        active_duration = get_default_note_duration_context()

        assert active_duration.mode == "beats"
        assert active_duration.as_beats() == Fraction(1, 2)
