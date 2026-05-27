"""Unit tests for the canonical accidental enum."""

import pytest

from chordelia.accidentals import Accidental


class TestAccidentalConstruction:
    """Test accidental construction and canonical identity."""

    @pytest.mark.parametrize(
        "offset, expected",
        [
            pytest.param(-2, Accidental.DOUBLE_FLAT, id="double-flat"),
            pytest.param(-1, Accidental.FLAT, id="flat"),
            pytest.param(0, Accidental.NATURAL, id="natural"),
            pytest.param(1, Accidental.SHARP, id="sharp"),
            pytest.param(2, Accidental.DOUBLE_SHARP, id="double-sharp"),
        ],
    )
    def test_from_offset_returns_canonical_singleton(self, offset, expected):
        accidental = Accidental.from_offset(offset)
        assert accidental is expected

    @pytest.mark.parametrize("offset", [-3, 3])
    def test_from_offset_rejects_out_of_range(self, offset):
        with pytest.raises(ValueError):
            Accidental.from_offset(offset)


class TestAccidentalCoercion:
    """Test coercion from supported accidental representations."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            pytest.param(Accidental.SHARP, Accidental.SHARP, id="existing-instance"),
            pytest.param(-1, Accidental.FLAT, id="int-flat"),
            pytest.param(0, Accidental.NATURAL, id="int-natural"),
            pytest.param(2, Accidental.DOUBLE_SHARP, id="int-double-sharp"),
            pytest.param("b", Accidental.FLAT, id="string-flat"),
            pytest.param("##", Accidental.DOUBLE_SHARP, id="string-double-sharp"),
            pytest.param("", Accidental.NATURAL, id="string-empty-natural"),
            pytest.param("n", Accidental.NATURAL, id="string-n-natural"),
            pytest.param("natural", Accidental.NATURAL, id="string-natural-word"),
        ],
    )
    def test_coerce_supported_values(self, value, expected):
        assert Accidental.coerce(value) is expected

    @pytest.mark.parametrize("value", [None, 1.5, object(), "x", "#b", "bbb", "###"])
    def test_coerce_rejects_invalid_values(self, value):
        with pytest.raises(ValueError):
            Accidental.coerce(value)


class TestAccidentalConversions:
    """Test conversions between accidental representations."""

    @pytest.mark.parametrize(
        "accidental, expected_symbol, expected_offset, expected_name",
        [
            pytest.param(Accidental.DOUBLE_FLAT, "bb", -2, "DOUBLE_FLAT", id="double-flat"),
            pytest.param(Accidental.FLAT, "b", -1, "FLAT", id="flat"),
            pytest.param(Accidental.NATURAL, "", 0, "NATURAL", id="natural"),
            pytest.param(Accidental.SHARP, "#", 1, "SHARP", id="sharp"),
            pytest.param(Accidental.DOUBLE_SHARP, "##", 2, "DOUBLE_SHARP", id="double-sharp"),
        ],
    )
    def test_symbol_offset_and_name(self, accidental, expected_symbol, expected_offset, expected_name):
        assert accidental.to_symbol() == expected_symbol
        assert str(accidental) == expected_symbol
        assert accidental.to_offset() == expected_offset
        assert accidental.value == expected_offset
        assert int(accidental) == expected_offset
        assert accidental.name == expected_name

    def test_enum_iteration_returns_ordered_canonical_values(self):
        assert tuple(Accidental) == (
            Accidental.DOUBLE_FLAT,
            Accidental.FLAT,
            Accidental.NATURAL,
            Accidental.SHARP,
            Accidental.DOUBLE_SHARP,
        )


class TestAccidentalEqualityAndHashing:
    """Test equality and hash semantics for accidental enum members."""

    def test_equality_is_offset_based(self):
        assert Accidental.from_offset(1) == Accidental.SHARP
        assert Accidental.from_offset(-1) != Accidental.SHARP

    def test_hashing_supports_set_and_dict_usage(self):
        accidental_set = {Accidental.SHARP, Accidental.from_offset(1), Accidental.FLAT}
        assert len(accidental_set) == 2

        accidental_map = {Accidental.SHARP: "sharp"}
        assert accidental_map[Accidental.from_string("#")] == "sharp"
