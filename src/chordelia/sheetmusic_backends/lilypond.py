"""LilyPond backend adapter for SheetMusic SVG rendering."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import TYPE_CHECKING, Callable

from chordelia.scales import ScaleType

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


def make_lilypond_svg_renderer(
    lilypond_executable: str | Path,
    *,
    crop: bool = True,
) -> Callable[[SheetMusic], str]:
    """Create a SheetMusic renderer callable backed by LilyPond."""

    executable = _resolve_lilypond_executable(lilypond_executable)

    def _renderer(sheet: SheetMusic) -> str:
        return render_sheet_music_via_lilypond(
            sheet,
            lilypond_executable=executable,
            crop=crop,
        )

    return _renderer


def configure_sheet_music_lilypond_backend(
    lilypond_executable: str | Path,
    *,
    format_name: str = "svg",
    crop: bool = True,
) -> None:
    """Configure SheetMusic format output to use the LilyPond SVG backend."""

    from chordelia.sheet_music import SheetMusic

    normalized_format = SheetMusic._normalize_format(format_name)
    SheetMusic._RENDER_BACKEND_ADAPTERS[normalized_format] = make_lilypond_svg_renderer(
        lilypond_executable,
        crop=crop,
    )


def render_sheet_music_via_lilypond(
    sheet: SheetMusic,
    *,
    lilypond_executable: str | Path,
    crop: bool = True,
) -> str:
    """Render one SheetMusic instance to SVG through LilyPond."""

    executable = _resolve_lilypond_executable(lilypond_executable)
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

        return svg_candidates[0].read_text(encoding="utf-8")


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
    key_line = _key_signature_line(sheet)
    tokens = " ".join(_score_tokens(sheet))

    key_section = ""
    if key_line:
        key_section = f"    {key_line}\n"

    return (
        '\\version "2.24.4"\n'
        "\\paper { indent = 0\\mm line-width = 180\\mm }\n"
        "\\layout { ragged-right = ##t }\n"
        "\\score {\n"
        "  \\new Staff {\n"
        "    \\clef treble\n"
        f"    \\time {numerator}/{denominator}\n"
        f"    \\tempo 4 = {tempo}\n"
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

    if scale.scale_type in {ScaleType.MAJOR, ScaleType.IONIAN}:
        mode = "major"
    elif scale.scale_type in {ScaleType.NATURAL_MINOR, ScaleType.AEOLIAN}:
        mode = "minor"
    else:
        return ""

    key_root = _lily_key_pitch_from_note(scale.root)
    return f"\\key {key_root} \\{mode}"


def _lily_key_pitch_from_note(note) -> str:
    """Convert a root note to a LilyPond key pitch (no octave marks)."""

    letter = note.name.name.lower()
    accidental = int(note.accidental.value)
    accidental_suffix = {
        -2: "eses",
        -1: "es",
        0: "",
        1: "is",
        2: "isis",
    }.get(accidental)
    if accidental_suffix is None:
        raise ValueError(f"Unsupported accidental for LilyPond key: {note}")
    return f"{letter}{accidental_suffix}"


def _score_tokens(sheet: SheetMusic) -> list[str]:
    """Convert score events to a monophonic/chord LilyPond token stream."""

    events = list(sheet.score.events)
    if not events:
        return ["r1"]

    cursor = Fraction(0, 1)
    tokens: list[str] = []

    for event in events:
        beat = event.beat.as_beats()
        duration = event.duration.as_beats()

        if beat > cursor:
            gap = beat - cursor
            for part in _split_duration(gap):
                tokens.append(f"r{_DURATION_TO_LILYPOND[part]}")

        tokens.append(_event_token(event))
        cursor = max(cursor, beat + duration)

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
