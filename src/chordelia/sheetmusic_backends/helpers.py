"""Shared semantic helpers for sheet-music backends."""

from __future__ import annotations

from fractions import Fraction
import re

from chordelia.rhythm import Duration
from chordelia.scales import Scale


AccidentalMap = dict[str, int]
OrderedKeySignature = list[tuple[str, int]]
MeasureScaleAnnotation = tuple[Fraction, Scale, str]
RenderedScaleAnnotation = tuple[Fraction, OrderedKeySignature, str]
ParsedSpelling = tuple[str, int, int | None]


_SPELLING_PATTERN = re.compile(r"^\s*([A-Ga-g])([#b]{0,2})?(-?\d+)?\s*$")
_LETTER_ORDER = ("C", "D", "E", "F", "G", "A", "B")
_KEY_SHARP_ORDER = ("F", "C", "G", "D", "A", "E", "B")
_KEY_FLAT_ORDER = ("B", "E", "A", "D", "G", "C", "F")


def parse_spelling(spelling: str) -> ParsedSpelling | None:
    """Parse a note spelling into (letter, accidental offset, optional octave)."""
    match = _SPELLING_PATTERN.match(spelling)
    if match is None:
        return None

    letter = match.group(1).upper()
    accidental_text = match.group(2) or ""
    octave_text = match.group(3)

    if accidental_text == "":
        accidental_offset = 0
    elif set(accidental_text) == {"#"}:
        accidental_offset = len(accidental_text)
    elif set(accidental_text) == {"b"}:
        accidental_offset = -len(accidental_text)
    else:
        return None

    octave = int(octave_text) if octave_text is not None else None
    return (letter, accidental_offset, octave)


def key_accidental_map_from_scale(scale: Scale | None) -> AccidentalMap:
    """Build expected letter accidental map from one scale key signature."""
    if scale is None:
        return {}

    accidental_map: AccidentalMap = {}
    for note in scale.key_signature_notes():
        letter = note.name.name
        accidental = int(note.accidental.value)
        existing = accidental_map.get(letter)
        if existing is not None and existing != accidental:
            return {}
        accidental_map[letter] = accidental

    return accidental_map


def ordered_key_signature_accidentals(accidental_map: AccidentalMap) -> OrderedKeySignature:
    """Return accidental glyph order for conventional sharp/flat key signatures."""
    if not accidental_map:
        return []

    values = {accidental_map.get(letter, 0) for letter in _LETTER_ORDER}
    if values.issubset({0, 1}):
        ordered = _KEY_SHARP_ORDER
        expected_value = 1
    elif values.issubset({0, -1}):
        ordered = _KEY_FLAT_ORDER
        expected_value = -1
    else:
        return []

    return [
        (letter, expected_value)
        for letter in ordered
        if accidental_map.get(letter, 0) == expected_value
    ]


def measure_scale_annotations_for_render(
    annotations: tuple[MeasureScaleAnnotation, ...],
) -> tuple[RenderedScaleAnnotation, ...]:
    """Project measure annotations into sorted key-signature glyph annotations."""
    if not annotations:
        return ()

    by_measure: dict[Fraction, tuple[OrderedKeySignature, str]] = {}
    for beat, scale, label in annotations:
        by_measure[beat] = (
            ordered_key_signature_accidentals(key_accidental_map_from_scale(scale)),
            label,
        )

    return tuple(
        (beat, values[0], values[1])
        for beat, values in sorted(by_measure.items(), key=lambda item: item[0])
    )


def key_accidental_map_for_beat(
    beat: Duration,
    base_accidental_map: AccidentalMap,
    annotations: tuple[MeasureScaleAnnotation, ...],
) -> AccidentalMap:
    """Resolve active key accidental map for one event beat position."""
    if beat.mode != "beats" or not annotations:
        return base_accidental_map

    beat_value = beat.as_beats()
    active_map = base_accidental_map
    for marker, scale, _label in annotations:
        if marker > beat_value:
            break
        active_map = key_accidental_map_from_scale(scale)

    return active_map
