"""Built-in SVG backend for SheetMusic rendering."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any

from chordelia.rhythm import Duration
from chordelia.sheet_music import SheetClef
from chordelia.sheetmusic_backends.helpers import (
    key_accidental_map_for_beat,
    measure_scale_annotations_for_render,
    ordered_key_signature_accidentals,
    parse_spelling,
)

if TYPE_CHECKING:
    from chordelia.sheet_music import SheetMusic


SVG_LEFT_MARGIN = 52.55
SVG_RIGHT_MARGIN = 25.37
SVG_TOP_MARGIN = 17.11
SVG_BOTTOM_MARGIN = 17.9
SVG_STAFF_SPACING = 10.16
SVG_STAFF_LINE_WIDTH = 0.92
SVG_MEASURE_BARLINE_WIDTH = 0.88
SVG_TRAILING_BARLINE_WIDTH = 1.23
SVG_NOTEHEAD_RX = 5.32
SVG_NOTEHEAD_RY = 3.56
SVG_NOTEHEAD_ROTATION_DEGREES = -21.25
SVG_MIN_WIDTH = 522
SVG_WIDTH_BASE = 215.39
SVG_WIDTH_PER_UNIT = 45.17
SVG_STEM_LENGTH = 27.99
SVG_CHORD_COLLISION_SHIFT = 4.41

_LETTER_INDEX = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}
_MIDI_TO_LETTER_INDEX = {
    0: 0,
    1: 0,
    2: 1,
    3: 1,
    4: 2,
    5: 3,
    6: 3,
    7: 4,
    8: 4,
    9: 5,
    10: 5,
    11: 6,
}
_CLEF_BOTTOM_LINE_INDEX = {
    SheetClef.TREBLE.value: (4 * 7) + _LETTER_INDEX["E"],
    SheetClef.BASS.value: (2 * 7) + _LETTER_INDEX["G"],
}
_KEY_SHARP_STEPS_BY_CLEF = {
    SheetClef.TREBLE.value: {
        "F": 8,
        "C": 5,
        "G": 9,
        "D": 6,
        "A": 3,
        "E": 7,
        "B": 4,
    },
    SheetClef.BASS.value: {
        "F": 6,
        "C": 3,
        "G": 7,
        "D": 4,
        "A": 1,
        "E": 5,
        "B": 2,
    },
}
_KEY_FLAT_STEPS_BY_CLEF = {
    SheetClef.TREBLE.value: {
        "B": 4,
        "E": 7,
        "A": 3,
        "D": 6,
        "G": 2,
        "C": 5,
        "F": 1,
    },
    SheetClef.BASS.value: {
        "B": 2,
        "E": 5,
        "A": 1,
        "D": 4,
        "G": 0,
        "C": 3,
        "F": -1,
    },
}


def _duration_value(duration: Duration) -> float:
    if duration.mode == "seconds":
        return float(duration.as_seconds())
    return float(duration.as_beats())


def _duration_beats(duration: Duration) -> Fraction | None:
    if duration.mode != "beats":
        return None
    return duration.as_beats()


def _svg_width(score) -> int:
    if not score.events:
        return int(SVG_MIN_WIDTH)
    end_time = max(_duration_value(event.beat + event.duration) for event in score.events)
    return max(int(SVG_MIN_WIDTH), int(SVG_WIDTH_BASE + (end_time * SVG_WIDTH_PER_UNIT)))


def _notehead_style(duration_beats: Fraction | None) -> tuple[bool, bool]:
    if duration_beats is None:
        return False, True
    if duration_beats >= Fraction(4, 1):
        return True, False
    if duration_beats >= Fraction(2, 1):
        return True, True
    return False, True


def _is_dotted_duration(duration_beats: Fraction | None) -> bool:
    if duration_beats is None:
        return False
    return duration_beats in {
        Fraction(3, 1),
        Fraction(3, 2),
        Fraction(3, 4),
        Fraction(3, 8),
        Fraction(3, 16),
        Fraction(3, 32),
    }


def _flag_count(duration_beats: Fraction | None) -> int:
    if duration_beats is None or duration_beats >= Fraction(1, 1):
        return 0
    if duration_beats >= Fraction(1, 2):
        return 1
    if duration_beats >= Fraction(1, 4):
        return 2
    if duration_beats >= Fraction(1, 8):
        return 3
    return 4


def _stem_up_for_steps(steps: tuple[int, ...]) -> bool:
    if not steps:
        return True
    return (sum(steps) / len(steps)) < 4.0


class _SvgLayout:
    def __init__(self, sheet: "SheetMusic"):
        self.sheet = sheet

    def _bottom_line_index_for_clef(self, clef: SheetClef) -> int:
        return _CLEF_BOTTOM_LINE_INDEX[clef.value]

    def _parse_spelling_with_accidental(self, spelling: str) -> tuple[int, int, int] | None:
        parsed = parse_spelling(spelling)
        if parsed is None:
            return None

        letter, accidental_offset, octave = parsed
        if octave is None:
            return None

        return _LETTER_INDEX[letter], accidental_offset, octave

    def _staff_step_for_pitch(self, pitch: int, spelling: str | None) -> int:
        if spelling is not None:
            parsed = self._parse_spelling_with_accidental(spelling)
            if parsed is not None:
                letter_index, _accidental_offset, octave = parsed
                return (octave * 7 + letter_index) - self._bottom_line_index_for_clef(self.sheet.clef)

        pitch_class = pitch % 12
        letter_index = _MIDI_TO_LETTER_INDEX[pitch_class]
        octave = (pitch // 12) - 1
        return (octave * 7 + letter_index) - self._bottom_line_index_for_clef(self.sheet.clef)

    def render_key_signature(
        self,
        accidentals: list[tuple[str, int]],
        *,
        x_start: float,
        staff_bottom: float,
        staff_spacing: float,
    ) -> list[str]:
        sharp_steps = _KEY_SHARP_STEPS_BY_CLEF[self.sheet.clef.value]
        flat_steps = _KEY_FLAT_STEPS_BY_CLEF[self.sheet.clef.value]
        lines: list[str] = []
        for index, (letter, accidental_value) in enumerate(accidentals):
            x = x_start + (index * 10.0)
            if accidental_value == 1:
                step = sharp_steps[letter]
                symbol = "&#9839;"
            else:
                step = flat_steps[letter]
                symbol = "&#9837;"
            y = staff_bottom - (step * (staff_spacing / 2.0)) + 4.0
            lines.append(
                f'<text class="key-accidental" x="{x:.2f}" y="{y:.2f}" font-family="Bravura, Noto Music, serif" font-size="18" fill="#111">{symbol}</text>'
            )
        return lines

    def render_clef_symbol(
        self,
        *,
        left_margin: float,
        staff_top: float,
        staff_bottom: float,
    ) -> str:
        staff_spacing = (staff_bottom - staff_top) / 4.0
        half_staff_spacing = staff_spacing / 2.0
        if self.sheet.clef is SheetClef.BASS:
            f_line_y = staff_bottom - (6.0 * half_staff_spacing)
            return (
                f'<text x="{left_margin - 27:.2f}" y="{f_line_y:.2f}" '
                'font-family="Bravura, Noto Music, serif" '
                'font-size="38" fill="#111" dominant-baseline="middle">&#119074;</text>'
            )
        g_line_y = staff_bottom - (2.0 * half_staff_spacing)
        return (
            f'<text x="{left_margin - 30:.2f}" y="{g_line_y:.2f}" '
            'font-family="Bravura, Noto Music, serif" '
            'font-size="46" fill="#111" dominant-baseline="middle">&#119070;</text>'
        )

    def render_measure_barlines(
        self,
        x_start: float,
        x_end: float,
        y_top: float,
        y_bottom: float,
        pixels_per_unit: float,
    ) -> list[str]:
        score = self.sheet.score
        if not score.events:
            return []
        timing_mode = score.events[0].beat.mode
        if timing_mode != "beats":
            return []
        numerator, _denominator = score.metadata.time_signature
        if numerator <= 0:
            return []
        end_time = max(_duration_value(event.beat + event.duration) for event in score.events)
        if end_time <= 0:
            return []
        lines: list[str] = []
        measure = float(numerator)
        marker = measure
        while marker < end_time:
            x = x_start + (marker * pixels_per_unit)
            if x >= x_end:
                break
            lines.append(
                f'<line class="measure-barline" x1="{x:.2f}" y1="{y_top:.2f}" x2="{x:.2f}" y2="{y_bottom:.2f}" stroke="#444" stroke-width="1"/>'
            )
            marker += measure
        return lines

    def position_noteheads(
        self,
        note_render_data: list[dict[str, float | int | str | None]],
        *,
        base_x: float,
        stem_up: bool,
    ) -> list[dict[str, float | int | str | None]]:
        if len(note_render_data) <= 1:
            single = [dict(item) for item in note_render_data]
            for item in single:
                item["x"] = base_x
            return single
        indexed = list(enumerate(note_render_data))
        indexed.sort(key=lambda pair: (int(pair[1]["step"]), float(pair[1]["y"])))
        collision_shift = -SVG_CHORD_COLLISION_SHIFT if stem_up else SVG_CHORD_COLLISION_SHIFT
        offsets: dict[int, float] = {index: 0.0 for index, _item in indexed}
        for i in range(1, len(indexed)):
            current_index, current = indexed[i]
            previous_index, previous = indexed[i - 1]
            if int(current["step"]) - int(previous["step"]) == 1:
                offsets[current_index] = collision_shift if offsets[previous_index] == 0.0 else 0.0
        positioned: list[dict[str, float | int | str | None]] = []
        for index, item in enumerate(note_render_data):
            entry = dict(item)
            entry["x"] = base_x + offsets.get(index, 0.0)
            positioned.append(entry)
        return positioned

    def event_note_render_data(
        self,
        event,
        *,
        staff_bottom: float,
        staff_spacing: float,
        key_accidental_map: dict[str, int],
    ) -> list[dict[str, float | int | str | None]]:
        data: list[dict[str, float | int | str | None]] = []
        spellings = event.spelling if event.spelling is not None else ()
        for index, pitch in enumerate(event.pitches):
            spelling = spellings[index] if index < len(spellings) else None
            parsed = self._parse_spelling_with_accidental(spelling) if spelling is not None else None
            if parsed is not None:
                letter_index, accidental_offset, octave = parsed
                step = (octave * 7 + letter_index) - self._bottom_line_index_for_clef(self.sheet.clef)
                letter_name = "CDEFGAB"[letter_index]
                note_accidental = accidental_offset
            else:
                step = self._staff_step_for_pitch(pitch, None)
                pitch_class = pitch % 12
                letter_index = _MIDI_TO_LETTER_INDEX[pitch_class]
                letter_name = "CDEFGAB"[letter_index]
                natural_pc = _LETTER_INDEX[letter_name]
                offset = pitch_class - natural_pc
                if offset > 6:
                    offset -= 12
                elif offset < -6:
                    offset += 12
                note_accidental = offset
            y = staff_bottom - (step * (staff_spacing / 2.0))
            data.append(
                {
                    "step": step,
                    "y": y,
                    "letter": letter_name,
                    "accidental": note_accidental,
                    "key_accidental_expected": key_accidental_map.get(letter_name, 0),
                }
            )
        return data

    @staticmethod
    def _accidental_symbol(offset: int) -> str | None:
        if offset == 0:
            return "&#9838;"
        if offset == 1:
            return "&#9839;"
        if offset == -1:
            return "&#9837;"
        if offset == 2:
            return "&#9839;&#9839;"
        if offset == -2:
            return "&#9837;&#9837;"
        return None

    def render_note_accidentals(
        self,
        *,
        note_render_data: list[dict[str, float | int | str | None]],
    ) -> list[str]:
        lines: list[str] = []
        for data in note_render_data:
            letter = data["letter"]
            accidental = data["accidental"]
            y = float(data["y"])
            x = float(data["x"])
            if not isinstance(letter, str) or not isinstance(accidental, int):
                continue
            expected = data.get("key_accidental_expected")
            if not isinstance(expected, int):
                expected = self.sheet._staff_key_accidental_map.get(letter, 0)
            if accidental == expected:
                continue
            symbol = self._accidental_symbol(accidental)
            if symbol is None:
                continue
            lines.append(
                f'<text class="note-accidental" x="{x - 13.0:.2f}" y="{y + 4.0:.2f}" font-family="Bravura, Noto Music, serif" font-size="16" fill="#111">{symbol}</text>'
            )
        return lines

    @staticmethod
    def render_ledger_lines(
        *,
        positioned_notes: list[dict[str, float | int | str | None]],
        staff_bottom: float,
        staff_spacing: float,
    ) -> list[str]:
        lines: list[str] = []
        for note in positioned_notes:
            step = int(note["step"])
            x = float(note["x"])
            ledger_steps: set[int] = set()
            if step < 0:
                ledger_steps.update(range(-2, step - 1, -2))
            elif step > 8:
                ledger_steps.update(range(10, step + 1, 2))
            for ledger_step in sorted(ledger_steps):
                y = staff_bottom - (ledger_step * (staff_spacing / 2.0))
                lines.append(
                    f'<line class="ledger-line" x1="{x - 8:.2f}" y1="{y:.2f}" x2="{x + 8:.2f}" y2="{y:.2f}" stroke="#111" stroke-width="1"/>'
                )
        return lines

    @staticmethod
    def render_stem(
        *,
        positioned_notes: list[dict[str, float | int | str | None]],
        stem_up: bool,
    ) -> tuple[str, dict[str, float | bool] | None]:
        if not positioned_notes:
            return "", None
        if stem_up:
            anchor_y = min(float(note["y"]) for note in positioned_notes)
            anchor_x = max(float(note["x"]) for note in positioned_notes if float(note["y"]) == anchor_y)
            end_y = anchor_y - SVG_STEM_LENGTH
            stem_x = anchor_x + 4.8
        else:
            anchor_y = max(float(note["y"]) for note in positioned_notes)
            anchor_x = min(float(note["x"]) for note in positioned_notes if float(note["y"]) == anchor_y)
            end_y = anchor_y + SVG_STEM_LENGTH
            stem_x = anchor_x - 4.8
        stem_line = (
            f'<line class="note-stem" x1="{stem_x:.2f}" y1="{anchor_y:.2f}" '
            f'x2="{stem_x:.2f}" y2="{end_y:.2f}" stroke="#111" stroke-width="1"/>'
        )
        return stem_line, {
            "x": stem_x,
            "anchor_y": anchor_y,
            "end_y": end_y,
            "stem_up": stem_up,
        }

    @staticmethod
    def render_flags(stem_geometry: dict[str, float | bool], *, count: int) -> list[str]:
        x = float(stem_geometry["x"])
        end_y = float(stem_geometry["end_y"])
        stem_up = bool(stem_geometry["stem_up"])
        lines: list[str] = []
        for index in range(count):
            offset = index * 5.0
            if stem_up:
                y1 = end_y + offset
                x2 = x + 8.0
                y2 = y1 + 3.8
            else:
                y1 = end_y - offset
                x2 = x - 8.0
                y2 = y1 - 3.8
            lines.append(
                f'<line class="note-flag" x1="{x:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#111" stroke-width="1"/>'
            )
        return lines

    def render_beams(
        self,
        rendered_events: list[dict[str, Any]],
        *,
        measure_beats: int,
    ) -> tuple[list[str], dict[int, int]]:
        if measure_beats <= 0:
            return [], {}
        beam_lines: list[str] = []
        beamed_levels: dict[int, int] = {}
        run_start: int | None = None
        for index, layout in enumerate(rendered_events):
            is_candidate = (
                layout["has_stem"]
                and layout["stem_geometry"] is not None
                and layout["duration_beats"] is not None
                and layout["flag_count"] > 0
                and layout["beat_beats"] is not None
            )
            if not is_candidate:
                if run_start is not None:
                    lines, levels = self._render_beam_run(rendered_events, run_start, index - 1, measure_beats=measure_beats)
                    beam_lines.extend(lines)
                    for event_index, level in levels.items():
                        beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), level)
                    run_start = None
                continue
            if run_start is None:
                run_start = index
                continue
            if self._can_continue_beam_run(previous=rendered_events[index - 1], current=layout, measure_beats=measure_beats):
                continue
            lines, levels = self._render_beam_run(rendered_events, run_start, index - 1, measure_beats=measure_beats)
            beam_lines.extend(lines)
            for event_index, level in levels.items():
                beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), level)
            run_start = index
        if run_start is not None:
            lines, levels = self._render_beam_run(rendered_events, run_start, len(rendered_events) - 1, measure_beats=measure_beats)
            beam_lines.extend(lines)
            for event_index, level in levels.items():
                beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), level)
        return beam_lines, beamed_levels

    @staticmethod
    def _can_continue_beam_run(*, previous: dict[str, Any], current: dict[str, Any], measure_beats: int) -> bool:
        previous_beat = previous["beat_beats"]
        previous_duration = previous["duration_beats"]
        current_beat = current["beat_beats"]
        if previous_beat is None or previous_duration is None or current_beat is None:
            return False
        if previous["stem_up"] != current["stem_up"]:
            return False
        if (current_beat // measure_beats) != (previous_beat // measure_beats):
            return False
        return current_beat == (previous_beat + previous_duration)

    def _render_beam_run(
        self,
        rendered_events: list[dict[str, Any]],
        start_index: int,
        end_index: int,
        *,
        measure_beats: int,
    ) -> tuple[list[str], dict[int, int]]:
        del measure_beats
        if end_index - start_index < 1:
            return [], {}
        run_indices = list(range(start_index, end_index + 1))
        max_level = max(int(rendered_events[index]["flag_count"]) for index in run_indices)
        if max_level <= 0:
            return [], {}
        lines: list[str] = []
        beamed_levels: dict[int, int] = {}
        for level in range(1, max_level + 1):
            level_run: list[int] = []
            for index in run_indices:
                if int(rendered_events[index]["flag_count"]) >= level:
                    level_run.append(index)
                    continue
                if len(level_run) >= 2:
                    segment_lines, segment_levels = self._render_beam_segment(rendered_events, level_run, level=level)
                    lines.extend(segment_lines)
                    for event_index, event_level in segment_levels.items():
                        beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), event_level)
                elif len(level_run) == 1 and level >= 2:
                    hook_lines, hook_levels = self._render_beam_hook(rendered_events, run_indices, note_index=level_run[0], level=level)
                    lines.extend(hook_lines)
                    for event_index, event_level in hook_levels.items():
                        beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), event_level)
                level_run = []
            if len(level_run) >= 2:
                segment_lines, segment_levels = self._render_beam_segment(rendered_events, level_run, level=level)
                lines.extend(segment_lines)
                for event_index, event_level in segment_levels.items():
                    beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), event_level)
            elif len(level_run) == 1 and level >= 2:
                hook_lines, hook_levels = self._render_beam_hook(rendered_events, run_indices, note_index=level_run[0], level=level)
                lines.extend(hook_lines)
                for event_index, event_level in hook_levels.items():
                    beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), event_level)
        return lines, beamed_levels

    @staticmethod
    def _render_beam_segment(
        rendered_events: list[dict[str, Any]],
        run_indices: list[int],
        *,
        level: int,
    ) -> tuple[list[str], dict[int, int]]:
        first = rendered_events[run_indices[0]]
        last = rendered_events[run_indices[-1]]
        first_stem = first["stem_geometry"]
        last_stem = last["stem_geometry"]
        if first_stem is None or last_stem is None:
            return [], {}
        x1 = float(first_stem["x"])
        x2 = float(last_stem["x"])
        y1_base = float(first_stem["end_y"])
        y2_base = float(last_stem["end_y"])
        stem_up = bool(first_stem["stem_up"])
        level_offset = (-(level - 1) * 5.0) if stem_up else ((level - 1) * 5.0)
        y1 = y1_base + level_offset
        y2 = y2_base + level_offset
        thickness = 2.8 if stem_up else -2.8
        polygon = (
            f'<polygon class="note-beam" points="{x1:.2f},{y1:.2f} {x2:.2f},{y2:.2f} '
            f'{x2:.2f},{y2 + thickness:.2f} {x1:.2f},{y1 + thickness:.2f}" fill="#111"/>'
        )
        return [polygon], {index: level for index in run_indices}

    @staticmethod
    def _render_beam_hook(
        rendered_events: list[dict[str, Any]],
        run_indices: list[int],
        *,
        note_index: int,
        level: int,
    ) -> tuple[list[str], dict[int, int]]:
        layout = rendered_events[note_index]
        stem = layout["stem_geometry"]
        if stem is None:
            return [], {}
        try:
            position = run_indices.index(note_index)
        except ValueError:
            return [], {}
        x = float(stem["x"])
        y_base = float(stem["end_y"])
        stem_up = bool(stem["stem_up"])
        level_offset = (-(level - 1) * 5.0) if stem_up else ((level - 1) * 5.0)
        y = y_base + level_offset
        level_indices = [index for index in run_indices if int(rendered_events[index]["flag_count"]) >= level]
        previous_level_index = None
        next_level_index = None
        for candidate in reversed(level_indices):
            if candidate < note_index:
                previous_level_index = candidate
                break
        for candidate in level_indices:
            if candidate > note_index:
                next_level_index = candidate
                break
        if previous_level_index is None and next_level_index is not None:
            hook_right = True
        elif next_level_index is None and previous_level_index is not None:
            hook_right = False
        elif previous_level_index is not None and next_level_index is not None:
            current_beat = layout["beat_beats"]
            previous_beat = rendered_events[previous_level_index]["beat_beats"]
            next_beat = rendered_events[next_level_index]["beat_beats"]
            if current_beat is None or previous_beat is None or next_beat is None:
                hook_right = (next_level_index - note_index) <= (note_index - previous_level_index)
            else:
                previous_gap = current_beat - previous_beat
                next_gap = next_beat - current_beat
                if next_gap < previous_gap:
                    hook_right = True
                elif previous_gap < next_gap:
                    hook_right = False
                else:
                    hook_right = (next_level_index - note_index) <= (note_index - previous_level_index)
        elif position == len(run_indices) - 1:
            hook_right = False
        elif position == 0:
            hook_right = True
        else:
            prev_index = run_indices[position - 1]
            next_index = run_indices[position + 1]
            prev_stem = rendered_events[prev_index]["stem_geometry"]
            next_stem = rendered_events[next_index]["stem_geometry"]
            if prev_stem is None or next_stem is None:
                hook_right = True
            else:
                prev_gap = abs(x - float(prev_stem["x"]))
                next_gap = abs(float(next_stem["x"]) - x)
                hook_right = next_gap <= prev_gap
        hook_length = 9.0
        x2 = x + hook_length if hook_right else x - hook_length
        y2 = y
        thickness = 2.8 if stem_up else -2.8
        polygon = (
            f'<polygon class="note-beam note-beam-hook" points="{x:.2f},{y:.2f} {x2:.2f},{y2:.2f} '
            f'{x2:.2f},{y2 + thickness:.2f} {x:.2f},{y + thickness:.2f}" fill="#111"/>'
        )
        return [polygon], {note_index: level}

    @staticmethod
    def render_dots(*, positioned_notes: list[dict[str, float | int | str | None]]) -> list[str]:
        return [
            (
                f'<circle class="note-dot" '
                f'cx="{float(note["x"]) + 10.0:.2f}" '
                f'cy="{float(note["y"]):.2f}" r="1.4" fill="#111"/>'
            )
            for note in sorted(positioned_notes, key=lambda item: (float(item["y"]), float(item["x"])))
        ]


def render_sheet_music_svg(sheet: "SheetMusic") -> str:
    """Render a deterministic SVG representation of one SheetMusic score."""
    layout = _SvgLayout(sheet)
    score = sheet.score
    width = _svg_width(score)
    left_margin = SVG_LEFT_MARGIN
    right_margin = SVG_RIGHT_MARGIN
    top_margin = SVG_TOP_MARGIN
    bottom_margin = SVG_BOTTOM_MARGIN
    staff_spacing = SVG_STAFF_SPACING
    half_staff_spacing = staff_spacing / 2.0

    # Expand vertical bounds to include ledger-heavy passages instead of clipping.
    min_step = 0
    max_step = 8
    if score.events:
        rendered_steps: list[int] = []
        for event in score.events:
            spellings = event.spelling if event.spelling is not None else ()
            for note_index, pitch in enumerate(event.pitches):
                spelling = spellings[note_index] if note_index < len(spellings) else None
                rendered_steps.append(layout._staff_step_for_pitch(pitch, spelling))
        if rendered_steps:
            min_step = min(rendered_steps)
            max_step = max(rendered_steps)

    render_min_step = min(-2, min_step - 2)
    render_max_step = max(10, max_step + 2)
    staff_bottom = top_margin + (render_max_step * half_staff_spacing)
    staff_top = staff_bottom - (4 * staff_spacing)
    height = int(
        top_margin + ((render_max_step - render_min_step) * half_staff_spacing) + bottom_margin + 0.999
    )
    timing_mode = score.events[0].beat.mode if score.events else "beats"

    end_beats = Fraction(1, 1)
    if score.events:
        end_duration = max(event.beat + event.duration for event in score.events)
        if timing_mode == "beats":
            end_beats = end_duration.as_beats()
            if end_beats <= 0:
                end_beats = Fraction(1, 1)
            end_time = float(end_beats)
        else:
            end_time = _duration_value(end_duration)
            if end_time <= 0:
                end_time = 1.0
    else:
        end_time = 1.0

    default_key_sig_accidentals = ordered_key_signature_accidentals(sheet._staff_key_accidental_map)
    scale_annotation_entries = measure_scale_annotations_for_render(sheet._measure_scale_annotations)

    measure_key_signatures: dict[Fraction, list[tuple[str, int]]] = {}
    measure_labels: dict[Fraction, str] = {}
    if timing_mode == "beats":
        for beat, accidentals, label in scale_annotation_entries:
            measure_key_signatures[beat] = accidentals
            measure_labels[beat] = label

        if Fraction(0, 1) not in measure_key_signatures and default_key_sig_accidentals:
            measure_key_signatures[Fraction(0, 1)] = default_key_sig_accidentals

    key_width_by_measure: dict[Fraction, float] = {}
    if timing_mode == "beats":
        for beat, accidentals in measure_key_signatures.items():
            width_value = (len(accidentals) * 10.0) + (8.0 if accidentals else 0.0)
            if width_value > 0:
                key_width_by_measure[beat] = width_value
        sorted_key_markers = tuple(sorted(key_width_by_measure))
        total_key_width = sum(
            key_width_by_measure[marker]
            for marker in sorted_key_markers
            if marker < end_beats
        )
        content_start_x = left_margin
        timeline_width = max(1.0, width - left_margin - right_margin - total_key_width)
    else:
        key_sig_width = (len(default_key_sig_accidentals) * 10.0) + (
            8.0 if default_key_sig_accidentals else 0.0
        )
        content_start_x = left_margin + key_sig_width
        sorted_key_markers = ()
        timeline_width = max(1.0, width - left_margin - right_margin)

    pixels_per_unit = timeline_width / end_time

    def _cumulative_key_width(beat: Fraction, *, include_current: bool) -> float:
        if not sorted_key_markers:
            return 0.0

        total = 0.0
        for marker in sorted_key_markers:
            if include_current:
                if marker <= beat:
                    total += key_width_by_measure[marker]
            else:
                if marker < beat:
                    total += key_width_by_measure[marker]
        return total

    def _x_for_beat(beat: Duration) -> float:
        if beat.mode != "beats":
            return content_start_x + (_duration_value(beat) * pixels_per_unit)

        beat_value = beat.as_beats()
        return (
            content_start_x
            + (float(beat_value) * pixels_per_unit)
            + _cumulative_key_width(beat_value, include_current=True)
        )

    def _x_for_measure_start(beat: Fraction) -> float:
        return (
            content_start_x
            + (float(beat) * pixels_per_unit)
            + _cumulative_key_width(beat, include_current=False)
        )

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        layout.render_clef_symbol(
            left_margin=left_margin,
            staff_top=staff_top,
            staff_bottom=staff_bottom,
        ),
    ]

    if sheet._render_tempo_metadata:
        lines.append(
            (
                f'<text x="{left_margin:.2f}" y="{max(12.0, staff_top - 10.0):.2f}" '
                'font-family="Times New Roman, serif" font-size="11" fill="#222">'
                f'q = {score.metadata.tempo}'
                "</text>"
            )
        )

    for line_index in range(5):
        y = staff_top + (line_index * staff_spacing)
        lines.append(
            f'<line class="staff-line" x1="{left_margin:.2f}" y1="{y:.2f}" x2="{width - right_margin:.2f}" y2="{y:.2f}" stroke="#111" stroke-width="{SVG_STAFF_LINE_WIDTH:.2f}"/>'
        )

    lines.append(
        f'<line class="staff-barline" x1="{content_start_x:.2f}" y1="{staff_top:.2f}" x2="{content_start_x:.2f}" y2="{staff_bottom:.2f}" stroke="#111" stroke-width="{SVG_MEASURE_BARLINE_WIDTH:.2f}"/>'
    )
    lines.append(
        f'<line class="staff-barline" x1="{width - right_margin:.2f}" y1="{staff_top:.2f}" x2="{width - right_margin:.2f}" y2="{staff_bottom:.2f}" stroke="#111" stroke-width="{SVG_TRAILING_BARLINE_WIDTH:.2f}"/>'
    )

    if timing_mode == "beats":
        for marker, accidentals in sorted(measure_key_signatures.items(), key=lambda item: item[0]):
            if marker < 0 or marker >= end_beats:
                continue

            key_start_x = _x_for_measure_start(marker) + 6.0
            lines.extend(
                layout.render_key_signature(
                    accidentals,
                    x_start=key_start_x,
                    staff_bottom=staff_bottom,
                    staff_spacing=staff_spacing,
                )
            )

            scale_label = measure_labels.get(marker)
            if scale_label is not None:
                lines.append(
                    f'<text class="scale-label" x="{key_start_x:.2f}" y="{max(12.0, staff_top - 20.0):.2f}" font-family="Times New Roman, serif" font-size="10" fill="#333">{scale_label}</text>'
                )

        numerator, _denominator = score.metadata.time_signature
        if numerator > 0:
            marker = Fraction(numerator, 1)
            while marker < end_beats:
                x = _x_for_measure_start(marker)
                if x >= (width - right_margin):
                    break
                lines.append(
                    f'<line class="measure-barline" x1="{x:.2f}" y1="{staff_top:.2f}" x2="{x:.2f}" y2="{staff_bottom:.2f}" stroke="#222" stroke-width="{SVG_MEASURE_BARLINE_WIDTH:.2f}"/>'
                )
                marker += Fraction(numerator, 1)
    else:
        lines.extend(
            layout.render_key_signature(
                default_key_sig_accidentals,
                x_start=left_margin + 6.0,
                staff_bottom=staff_bottom,
                staff_spacing=staff_spacing,
            )
        )

        lines.extend(
            layout.render_measure_barlines(
                content_start_x,
                width - right_margin,
                staff_top,
                staff_bottom,
                pixels_per_unit,
            )
        )

    rendered_events: list[dict[str, Any]] = []
    for event in score.events:
        x = _x_for_beat(event.beat)
        event_key_accidental_map = key_accidental_map_for_beat(
            event.beat,
            sheet._staff_key_accidental_map,
            sheet._measure_scale_annotations,
        )
        note_render_data = layout.event_note_render_data(
            event,
            staff_bottom=staff_bottom,
            staff_spacing=staff_spacing,
            key_accidental_map=event_key_accidental_map,
        )
        steps = tuple(int(item["step"]) for item in note_render_data)
        duration_beats = _duration_beats(event.duration)
        stem_up = _stem_up_for_steps(steps)
        positioned_notes = layout.position_noteheads(
            note_render_data,
            base_x=x,
            stem_up=stem_up,
        )
        duration_beats_value = duration_beats
        beat_beats = event.beat.as_beats() if event.beat.mode == "beats" else None

        notehead_open, has_stem = _notehead_style(duration_beats)
        notehead_class = "notehead-open" if notehead_open else "notehead-filled"
        if notehead_open:
            notehead_style = 'fill="#ffffff" stroke="#111" stroke-width="1.0"'
        else:
            notehead_style = 'fill="#111"'

        stem_line = ""
        stem_geometry = None
        if has_stem:
            stem_line, stem_geometry = layout.render_stem(
                positioned_notes=positioned_notes,
                stem_up=stem_up,
            )

        rendered_events.append(
            {
                "event": event,
                "positioned_notes": positioned_notes,
                "steps": steps,
                "duration_beats": duration_beats_value,
                "beat_beats": beat_beats,
                "stem_up": stem_up,
                "notehead_class": notehead_class,
                "notehead_style": notehead_style,
                "stem_line": stem_line,
                "stem_geometry": stem_geometry,
                "flag_count": _flag_count(duration_beats_value),
                "has_stem": has_stem,
            }
        )

    beam_lines, beamed_levels = layout.render_beams(
        rendered_events,
        measure_beats=score.metadata.time_signature[0],
    )

    for index, event_layout in enumerate(rendered_events):
        positioned_notes = event_layout["positioned_notes"]
        duration_beats = event_layout["duration_beats"]

        lines.extend(
            layout.render_ledger_lines(
                positioned_notes=positioned_notes,
                staff_bottom=staff_bottom,
                staff_spacing=staff_spacing,
            )
        )

        lines.extend(layout.render_note_accidentals(note_render_data=positioned_notes))

        for note in sorted(positioned_notes, key=lambda item: (float(item["y"]), float(item["x"]))):
            note_x = float(note["x"])
            note_y = float(note["y"])
            lines.append(
                (
                    f'<ellipse class="notehead {event_layout["notehead_class"]}" '
                    f'cx="{note_x:.2f}" cy="{note_y:.2f}" '
                    f'rx="{SVG_NOTEHEAD_RX:.2f}" ry="{SVG_NOTEHEAD_RY:.2f}" '
                    f'transform="rotate({SVG_NOTEHEAD_ROTATION_DEGREES:.2f} {note_x:.2f} {note_y:.2f})" {event_layout["notehead_style"]}/>'
                )
            )

        if _is_dotted_duration(duration_beats):
            lines.extend(layout.render_dots(positioned_notes=positioned_notes))

        if event_layout["has_stem"]:
            lines.append(event_layout["stem_line"])

            flag_count = int(event_layout["flag_count"])
            beamed_level_count = beamed_levels.get(index, 0)
            remaining_flags = max(0, flag_count - beamed_level_count)
            stem_geometry = event_layout["stem_geometry"]
            if remaining_flags > 0 and stem_geometry is not None:
                lines.extend(layout.render_flags(stem_geometry, count=remaining_flags))

    lines.extend(beam_lines)

    lines.append("</svg>")
    return "\n".join(lines)
