"""LilyPond backend adapter for SheetMusic SVG rendering."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from chordelia.sheet_music import SheetMusic

_SPELLING_PATTERN = re.compile(r"^\s*([A-Ga-g])([#b]{0,2})?(-?\d+)?\s*$")

_DURATION_TO_LILYPOND = {
    Fraction(4, 1): "1",
    Fraction(3, 1): "2.",
    Fraction(2, 1): "2",
    Fraction(3, 2): "4.",
    Fraction(1, 1): "4",
    Fraction(3, 4): "8.",
    Fraction(1, 2): "8",
    Fraction(3, 8): "16.",
    Fraction(1, 4): "16",
    Fraction(3, 16): "32.",
    Fraction(1, 8): "32",
    Fraction(3, 32): "64.",
    Fraction(1, 16): "64",
}

_DURATION_VALUES_DESC = sorted(_DURATION_TO_LILYPOND, reverse=True)

_MIDI_PC_TO_LILYPOND = (
    "c",
    "cis",
    "d",
    "dis",
    "e",
    "f",
    "fis",
    "g",
    "gis",
    "a",
    "ais",
    "b",
)

_SUPPORTED_BACKGROUNDS = {"white", "transparent"}


def make_lilypond_svg_renderer(
    lilypond_executable: str | Path,
    *,
    crop: bool = True,
    background: str = "white",
) -> Callable[[SheetMusic], str]:
    """Create a SheetMusic renderer callable backed by LilyPond."""

    executable = _resolve_lilypond_executable(lilypond_executable)
    normalized_background = _normalize_background(background)

    def _renderer(sheet: SheetMusic) -> str:
        return render_sheet_music_via_lilypond(
            sheet,
            lilypond_executable=executable,
            crop=crop,
            background=normalized_background,
        )

    return _renderer


def configure_sheet_music_lilypond_backend(
    lilypond_executable: str | Path,
    *,
    format_name: str = "svg",
    crop: bool = True,
    background: str = "white",
) -> None:
    """Configure SheetMusic format output to use the LilyPond SVG backend."""

    from chordelia.sheet_music import SheetMusic

    normalized_format = SheetMusic._normalize_format(format_name)
    SheetMusic._RENDER_BACKEND_ADAPTERS[normalized_format] = make_lilypond_svg_renderer(
        lilypond_executable,
        crop=crop,
        background=background,
    )


def render_sheet_music_via_lilypond(
    sheet: SheetMusic,
    *,
    lilypond_executable: str | Path,
    crop: bool = True,
    background: str = "white",
) -> str:
    """Render one SheetMusic instance to SVG through LilyPond."""

    executable = _resolve_lilypond_executable(lilypond_executable)
    normalized_background = _normalize_background(background)
    lilypond_source = _sheet_to_lilypond_source(sheet)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ly_path = tmp_path / "sheet.ly"
        output_prefix = tmp_path / "sheet"
        ly_path.write_text(lilypond_source, encoding="utf-8")

        command = [
            executable,
            "--svg",
            "-dno-point-and-click",
            "-o",
            str(output_prefix),
            str(ly_path),
        ]
        if crop:
            command.insert(2, "-dcrop")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"LilyPond executable not found: {executable!r}"
            ) from exc

        if result.returncode != 0:
            raise RuntimeError(
                "LilyPond rendering failed.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        if crop:
            svg_candidates = sorted(tmp_path.glob("sheet*.cropped.svg"))
            if not svg_candidates:
                svg_candidates = sorted(tmp_path.glob("sheet*.svg"))
        else:
            svg_candidates = sorted(tmp_path.glob("sheet*.svg"))

        if not svg_candidates:
            raise RuntimeError("LilyPond did not produce an SVG output file.")

        rendered_svg = svg_candidates[0].read_text(encoding="utf-8")
        if normalized_background == "transparent":
            return rendered_svg
        return _with_white_svg_background(rendered_svg)


def _normalize_background(background: str) -> str:
    """Validate and normalize supported background modes."""
    normalized = background.strip().lower()
    if normalized not in _SUPPORTED_BACKGROUNDS:
        supported = ", ".join(sorted(_SUPPORTED_BACKGROUNDS))
        raise ValueError(
            f"Unsupported background {background!r}. Supported values: {supported}"
        )
    return normalized


def _with_white_svg_background(svg_text: str) -> str:
    """Ensure rendered SVG has a white background rect under the score."""
    if 'class="chordelia-lilypond-bg"' in svg_text:
        return svg_text

    match = re.search(r"<svg\b[^>]*>", svg_text)
    if match is None:
        return svg_text

    rect = (
        '<rect class="chordelia-lilypond-bg" x="0" y="0" '
        'width="100%" height="100%" fill="#ffffff"/>'
    )
    return f"{svg_text[:match.end()]}{rect}{svg_text[match.end():]}"


def _resolve_lilypond_executable(lilypond_executable: str | Path) -> str:
    """Resolve a LilyPond executable command or path."""

    candidate = str(lilypond_executable).strip()
    if not candidate:
        raise ValueError("lilypond_executable must be a non-empty path or command")

    if Path(candidate).name == candidate:
        resolved = shutil.which(candidate)
        if resolved is not None:
            return resolved

    return candidate


def _sheet_to_lilypond_source(sheet: SheetMusic) -> str:
    """Serialize SheetMusic score data into a minimal LilyPond source."""

    numerator, denominator = sheet.score.metadata.time_signature
    tempo = sheet.score.metadata.tempo
    clef = getattr(sheet, "clef", None)
    clef_value = getattr(clef, "value", "treble")
    tempo_line = f"    \\tempo 4 = {tempo}\\n" if getattr(sheet, "_render_tempo_metadata", False) else ""
    scale_directives = _iterable_scale_directives(sheet)
    key_line = "" if scale_directives else _key_signature_line(sheet)
    tokens = " ".join(_score_tokens(sheet, directives=scale_directives))

    key_section = ""
    if key_line:
        key_section = f"    {key_line}\n"

    return (
        '\\version "2.24.4"\n'
        "\\paper { indent = 0\\mm line-width = 180\\mm }\n"
        "\\layout { ragged-right = ##t }\n"
        "\\score {\n"
        "  \\new Staff {\n"
        f"    \\clef {clef_value}\n"
        "    \\set Staff.printKeyCancellation = ##f\n"
        "    \\omit Staff.KeyCancellation\n"
        f"    \\time {numerator}/{denominator}\n"
        f"{tempo_line}"
        f"{key_section}"
        f"    {tokens}\n"
        "  }\n"
        "}\n"
    )


def _key_signature_line(sheet: SheetMusic) -> str:
    """Build a LilyPond key directive for supported scale contexts."""

    scale = getattr(sheet, "_staff_scale", None)
    if scale is None:
        return ""

    return _key_signature_line_for_scale(scale)


def _key_signature_line_for_scale(scale) -> str:
    """Build a LilyPond key directive for one scale from explicit accidental notes."""

    key_signature_notes = getattr(scale, "key_signature_notes", None)
    if callable(key_signature_notes):
        notes = key_signature_notes()
    else:
        notes = ()

    alterations = _lily_key_alterations_from_notes(notes)
    return f"\\set Staff.keyAlterations = #`({alterations})"


def _iterable_scale_directives(sheet: SheetMusic) -> dict[Fraction, list[str]]:
    """Return beat-indexed LilyPond directives for iterable scale annotations."""

    annotations = getattr(sheet, "_measure_scale_annotations", ())
    if not annotations:
        return {}

    directives: dict[Fraction, list[str]] = {}
    for beat, scale, label in annotations:
        marker_directives: list[str] = []

        key_line = _key_signature_line_for_scale(scale)
        if key_line:
            marker_directives.append(key_line)

        safe_label = str(label).replace('"', "'")
        marker_directives.append(f'\\mark \\markup {{ "{safe_label}" }}')

        if marker_directives:
            directives[beat] = marker_directives

    return directives


def _lily_key_alterations_from_notes(notes) -> str:
    """Convert accidental notes into a LilyPond keyAlterations list body."""

    if not notes:
        return ""

    step_map = {
        "C": 0,
        "D": 1,
        "E": 2,
        "F": 3,
        "G": 4,
        "A": 5,
        "B": 6,
    }
    accidental_map = {
        -2: "DOUBLE-FLAT",
        -1: "FLAT",
        1: "SHARP",
        2: "DOUBLE-SHARP",
    }

    tokens: list[str] = []
    for note in notes:
        step_name = note.name.name
        if step_name not in step_map:
            continue

        accidental_value = int(note.accidental.value)
        accidental_name = accidental_map.get(accidental_value)
        if accidental_name is None:
            continue

        tokens.append(f"({step_map[step_name]} . ,{accidental_name})")

    return " ".join(tokens)


def _score_tokens(
    sheet: SheetMusic,
    *,
    directives: dict[Fraction, list[str]] | None = None,
) -> list[str]:
    """Convert score events to a monophonic/chord LilyPond token stream."""

    events = list(sheet.score.events)
    mode = events[0].beat.mode if events else "beats"

    directive_points = sorted((directives or {}).items(), key=lambda item: item[0])
    directive_index = 0

    if not events:
        tokens: list[str] = []
        if mode == "beats":
            while directive_index < len(directive_points) and directive_points[directive_index][0] == 0:
                tokens.extend(directive_points[directive_index][1])
                directive_index += 1
        if not tokens:
            tokens.append("r1")
        return tokens

    cursor = Fraction(0, 1)
    tokens: list[str] = []

    def emit_directives_through(target: Fraction) -> None:
        nonlocal cursor, directive_index
        while directive_index < len(directive_points):
            marker, marker_directives = directive_points[directive_index]
            if marker > target:
                break

            if marker > cursor:
                gap_before_marker = marker - cursor
                for part in _split_duration(gap_before_marker):
                    tokens.append(f"r{_DURATION_TO_LILYPOND[part]}")
                cursor = marker

            tokens.extend(marker_directives)
            directive_index += 1

    if mode == "beats":
        emit_directives_through(Fraction(0, 1))

    for event in events:
        beat = event.beat.as_beats()
        duration = event.duration.as_beats()

        if mode == "beats":
            emit_directives_through(beat)

        if beat > cursor:
            gap = beat - cursor
            for part in _split_duration(gap):
                tokens.append(f"r{_DURATION_TO_LILYPOND[part]}")

        tokens.append(_event_token(event))
        cursor = max(cursor, beat + duration)

    if mode == "beats":
        emit_directives_through(cursor)

    return tokens


def _event_token(event) -> str:
    """Convert one score event to a LilyPond note/chord token."""

    pitches = _event_pitches(event)
    base = pitches[0] if len(pitches) == 1 else f"<{' '.join(pitches)}>"

    parts = _split_duration(event.duration.as_beats())
    if len(parts) == 1:
        return f"{base}{_DURATION_TO_LILYPOND[parts[0]]}"

    tied_tokens = [f"{base}{_DURATION_TO_LILYPOND[part]}" for part in parts]
    return " ~ ".join(tied_tokens)


def _event_pitches(event) -> list[str]:
    """Build LilyPond pitch tokens for one event."""

    if event.spelling is not None and len(event.spelling) == len(event.pitches):
        return [
            _lily_pitch_from_spelling(spelling, fallback_midi=pitch)
            for spelling, pitch in zip(event.spelling, event.pitches, strict=False)
        ]
    return [_lily_pitch_from_midi(pitch) for pitch in event.pitches]


def _lily_pitch_from_spelling(spelling: str, *, fallback_midi: int) -> str:
    """Convert note spelling text to a LilyPond pitch token."""

    match = _SPELLING_PATTERN.match(spelling)
    if match is None:
        return _lily_pitch_from_midi(fallback_midi)

    letter = match.group(1).lower()
    accidental_text = match.group(2) or ""
    octave_text = match.group(3)

    accidental_suffix = {
        "": "",
        "#": "is",
        "##": "isis",
        "b": "es",
        "bb": "eses",
    }.get(accidental_text)
    if accidental_suffix is None:
        return _lily_pitch_from_midi(fallback_midi)

    if octave_text is None:
        octave = (fallback_midi // 12) - 1
    else:
        octave = int(octave_text)

    return f"{letter}{accidental_suffix}{_lily_octave_marks(octave)}"


def _lily_pitch_from_midi(pitch: int) -> str:
    """Convert MIDI pitch numbers to LilyPond pitch tokens."""

    pitch_class = pitch % 12
    octave = (pitch // 12) - 1
    return f"{_MIDI_PC_TO_LILYPOND[pitch_class]}{_lily_octave_marks(octave)}"


def _lily_octave_marks(octave: int) -> str:
    """Return LilyPond octave markers where c' corresponds to C4."""

    delta = octave - 3
    if delta > 0:
        return "'" * delta
    if delta < 0:
        return "," * (-delta)
    return ""


def _split_duration(duration: Fraction) -> list[Fraction]:
    """Split beat durations into representable LilyPond duration components."""

    if duration <= 0:
        raise ValueError(f"duration must be positive, got {duration}")

    remaining = duration
    parts: list[Fraction] = []
    while remaining > 0:
        candidate = next((value for value in _DURATION_VALUES_DESC if value <= remaining), None)
        if candidate is None:
            raise ValueError(f"Unsupported duration for LilyPond conversion: {duration}")
        parts.append(candidate)
        remaining -= candidate
    return parts
