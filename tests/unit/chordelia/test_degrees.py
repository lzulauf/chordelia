"""Test suite for first-class Degree support."""

import pytest

from chordelia.degrees import Degree
from chordelia.accidentals import Accidental


class TestDegreeCreation:
    """Test Degree construction and coercion boundaries."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            pytest.param(1, Degree(1), id="int"),
            pytest.param("ii", Degree(2), id="roman-lower"),
            pytest.param("V", Degree(5), id="roman-upper"),
            pytest.param("bIII", Degree(3, accidental=-1), id="flat-roman"),
            pytest.param("#4", Degree(4, accidental=1), id="sharp-numeric"),
        ],
    )
    def test_coerce(self, value, expected):
        assert Degree.coerce(value) == expected

    def test_coerce_existing_degree_returns_same_instance(self):
        degree = Degree(6)
        assert Degree.coerce(degree) is degree

    @pytest.mark.parametrize("value", [0, -1])
    def test_invalid_numeric_degree(self, value):
        with pytest.raises(ValueError):
            Degree(value)

    @pytest.mark.parametrize("value", [None, 1.5, object()])
    def test_invalid_coerce_type(self, value):
        with pytest.raises(ValueError):
            Degree.coerce(value)


class TestDegreeStringParsing:
    """Test Degree string grammar and Roman semantics."""

    @pytest.mark.parametrize(
        "text, number, accidental_offset, roman_case, is_roman, diminished",
        [
            pytest.param("1", 1, 0, "none", False, False, id="numeric"),
            pytest.param("bb7", 7, -2, "none", False, False, id="numeric-double-flat"),
            pytest.param("I", 1, 0, "upper", True, False, id="roman-upper"),
            pytest.param("iv", 4, 0, "lower", True, False, id="roman-lower"),
            pytest.param("bIII", 3, -1, "upper", True, False, id="roman-accidental"),
            pytest.param("#iv", 4, 1, "lower", True, False, id="roman-sharp"),
            pytest.param("vii°", 7, 0, "lower", True, True, id="roman-diminished-symbol"),
            pytest.param("V7", 5, 0, "upper", True, False, id="roman-with-suffix"),
        ],
    )
    def test_from_string_fields(
        self,
        text,
        number,
        accidental_offset,
        roman_case,
        is_roman,
        diminished,
    ):
        degree = Degree.from_string(text)

        assert degree.number == number
        assert degree.accidental == Accidental.from_offset(accidental_offset)
        assert degree.accidental_offset == accidental_offset
        assert degree.roman_case == roman_case
        assert degree.is_roman is is_roman
        assert degree.had_diminished_symbol is diminished

    @pytest.mark.parametrize("text", ["", " ", "H", "I#", "b#3", "-3"])
    def test_from_string_invalid(self, text):
        with pytest.raises(ValueError):
            Degree.from_string(text)


class TestDegreeConversion:
    """Test int and Roman conversion helpers."""

    def test_int_conversion(self):
        degree = Degree.from_string("bIII")
        assert degree.to_int() == 3
        assert int(degree) == 3

    def test_to_roman_case_modes(self):
        degree = Degree.from_string("ii")

        assert degree.to_roman("upper") == "II"
        assert degree.to_roman("lower") == "ii"
        assert degree.to_roman("preserve") == "ii"
        assert degree.to_roman("auto") == "II"

    def test_to_roman_preserve_uses_input_case_when_available(self):
        degree = Degree.from_string("bIII")
        assert degree.to_roman("preserve") == "bIII"

    def test_to_roman_preserve_defaults_to_upper_without_source_case(self):
        degree = Degree(6)
        assert degree.to_roman("preserve") == "VI"

    def test_to_roman_preserves_diminished_symbol(self):
        degree = Degree.from_string("vii°")
        assert degree.to_roman("preserve") == "vii°"
        assert degree.to_roman("upper") == "VII°"


class TestDegreeFunctionalHints:
    """Test Roman-case functional hint metadata."""

    def test_uppercase_major_hint(self):
        assert Degree.from_string("IV").functional_hint == "major"

    def test_lowercase_minor_hint(self):
        assert Degree.from_string("ii").functional_hint == "minor_or_diminished"

    def test_diminished_hint(self):
        assert Degree.from_string("vii°").functional_hint == "diminished"

    def test_numeric_has_no_functional_hint(self):
        assert Degree(4).functional_hint is None


class TestDegreeShift:
    """Test diatonic shift behavior on Degree values."""

    def test_shift_wraps_with_default_span(self):
        assert Degree(1).shift(1) == Degree(2)
        assert Degree(7).shift(1) == Degree(1)
        assert Degree(1).shift(-1) == Degree(7)

    def test_shift_supports_compound_steps(self):
        assert Degree(1).shift(8) == Degree(2)
        assert Degree(3).shift(15) == Degree(4)

    def test_shift_without_wrap_returns_absolute_ordinal(self):
        shifted = Degree.from_string("bIII").shift(2, wrap=False)

        assert shifted.number == 5
        assert shifted.accidental_offset == -1

    def test_shift_without_wrap_rejects_non_positive_result(self):
        with pytest.raises(ValueError, match="resulting ordinal >= 1"):
            Degree(1).shift(-1, wrap=False)

    def test_shift_preserves_roman_metadata(self):
        shifted = Degree.from_string("ii").shift(2)

        assert shifted.is_roman is True
        assert shifted.roman_case == "lower"
        assert str(shifted) == "iv"

    @pytest.mark.parametrize("span", [0, -1])
    def test_shift_validates_span_range(self, span):
        with pytest.raises(ValueError, match="span must be >= 1"):
            Degree(1).shift(1, span=span)

    @pytest.mark.parametrize(
        "kwargs",
        [
            pytest.param({"steps": 1.5}, id="non-int-steps"),
            pytest.param({"steps": 1, "span": 7.5}, id="non-int-span"),
            pytest.param({"steps": 1, "wrap": "yes"}, id="non-bool-wrap"),
        ],
    )
    def test_shift_validates_types(self, kwargs):
        with pytest.raises(TypeError):
            Degree(1).shift(**kwargs)
