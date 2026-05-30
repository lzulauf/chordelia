"""Tests for centralized global scale context helpers."""

import pytest

from chordelia.scale_context import (
    coerce_scale_context_value,
    get_global_scale_context,
    reset_global_scale_context,
    set_global_scale_context,
    with_global_scale_context,
)
from chordelia.scales import Scale


@pytest.fixture(autouse=True)
def _clear_global_scale_context():
    reset_global_scale_context()
    yield
    reset_global_scale_context()


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
