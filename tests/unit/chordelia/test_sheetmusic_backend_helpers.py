"""Tests for shared semantic helpers used by sheet-music backends."""

from fractions import Fraction

import pytest

from chordelia.rhythm import Duration
from chordelia.scales import Scale
from chordelia.sheetmusic_backends.helpers import (
    key_accidental_map_for_beat,
    key_accidental_map_from_scale,
    measure_scale_annotations_for_render,
    ordered_key_signature_accidentals,
    parse_spelling,
)


class TestParseSpelling:
    """Spelling parser contracts shared across rendering backends."""

    @pytest.mark.parametrize(
        ("spelling", "expected"),
        (
            ("C#4", ("C", 1, 4)),
            ("Bb3", ("B", -1, 3)),
            ("F", ("F", 0, None)),
            ("G##5", ("G", 2, 5)),
            ("Db", ("D", -1, None)),
        ),
    )
    def test_parse_spelling_parses_supported_forms(self, spelling: str, expected):
        assert parse_spelling(spelling) == expected

    @pytest.mark.parametrize("spelling", ("H4", "C#b4", "C###4", ""))
    def test_parse_spelling_returns_none_for_invalid_values(self, spelling: str):
        assert parse_spelling(spelling) is None


class TestKeyAccidentalHelpers:
    """Scale and key-signature helper behavior for shared semantic IR."""

    def test_key_accidental_map_from_scale_handles_none(self):
        assert key_accidental_map_from_scale(None) == {}

    def test_key_accidental_map_from_scale_for_d_major(self):
        accidental_map = key_accidental_map_from_scale(Scale("D", "major"))

        assert accidental_map == {"F": 1, "C": 1}

    def test_ordered_key_signature_accidentals_for_sharp_key(self):
        accidentals = ordered_key_signature_accidentals({"F": 1, "C": 1})

        assert accidentals == [("F", 1), ("C", 1)]

    def test_ordered_key_signature_accidentals_for_flat_key(self):
        accidentals = ordered_key_signature_accidentals({"B": -1, "E": -1})

        assert accidentals == [("B", -1), ("E", -1)]

    def test_ordered_key_signature_accidentals_returns_empty_for_mixed_map(self):
        accidentals = ordered_key_signature_accidentals({"F": 1, "B": -1})

        assert accidentals == []


class TestMeasureScaleAnnotationHelpers:
    """Measure annotation helpers should provide stable sorted render projections."""

    def test_measure_scale_annotations_for_render_sorts_and_projects(self):
        annotations = (
            (Fraction(4, 1), Scale("Bb", "major"), "Bb Major"),
            (Fraction(0, 1), Scale("D", "major"), "D Major"),
        )

        projected = measure_scale_annotations_for_render(annotations)

        assert projected == (
            (Fraction(0, 1), [("F", 1), ("C", 1)], "D Major"),
            (Fraction(4, 1), [("B", -1), ("E", -1)], "Bb Major"),
        )

    def test_measure_scale_annotations_for_render_last_marker_wins(self):
        annotations = (
            (Fraction(0, 1), Scale("C", "major"), "C Major"),
            (Fraction(0, 1), Scale("D", "major"), "D Major"),
        )

        projected = measure_scale_annotations_for_render(annotations)

        assert projected == ((Fraction(0, 1), [("F", 1), ("C", 1)], "D Major"),)


class TestActiveKeyAccidentalMap:
    """Beat-scoped key accidental resolution used by event rendering backends."""

    def test_key_accidental_map_for_beat_resolves_active_annotation(self):
        base_map = key_accidental_map_from_scale(Scale("D", "major"))
        annotations = (
            (Fraction(4, 1), Scale("Bb", "major"), "Bb Major"),
        )

        before_change = key_accidental_map_for_beat(
            Duration.from_beats(3, None),
            base_map,
            annotations,
        )
        at_change = key_accidental_map_for_beat(
            Duration.from_beats(4, None),
            base_map,
            annotations,
        )
        after_change = key_accidental_map_for_beat(
            Duration.from_beats(6, None),
            base_map,
            annotations,
        )

        assert before_change == {"F": 1, "C": 1}
        assert at_change == {"B": -1, "E": -1}
        assert after_change == {"B": -1, "E": -1}

    def test_key_accidental_map_for_beat_keeps_base_map_for_seconds_mode(self):
        base_map = key_accidental_map_from_scale(Scale("D", "major"))
        annotations = (
            (Fraction(0, 1), Scale("Bb", "major"), "Bb Major"),
        )

        resolved = key_accidental_map_for_beat(
            Duration.from_seconds(1),
            base_map,
            annotations,
        )

        assert resolved == {"F": 1, "C": 1}
