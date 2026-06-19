"""Built-in SVG backend for SheetMusic rendering."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any

from chordelia.rhythm import Duration

if TYPE_CHECKING:
    from chordelia.sheet_music import SheetMusic


def render_sheet_music_svg(sheet: "SheetMusic") -> str:
    """Render a deterministic SVG representation of one SheetMusic score."""
    score = sheet.score
    width = sheet._svg_width()
    height = 220
    left_margin = 68.0
    right_margin = 30.0
    top_margin = 24.0
    staff_top = 80.0
    staff_spacing = 12.0
    staff_bottom = staff_top + (4 * staff_spacing)
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
            end_time = sheet._duration_value(end_duration)
            if end_time <= 0:
                end_time = 1.0
    else:
        end_time = 1.0

    default_key_sig_accidentals = sheet._key_signature_accidentals_for_render()
    scale_annotation_entries = sheet._scale_measure_annotations_for_render()

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
            return content_start_x + (sheet._duration_value(beat) * pixels_per_unit)

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
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fffdf8"/>',
        f'<text x="{left_margin:.2f}" y="{top_margin:.2f}" font-family="Georgia, serif" font-size="14" fill="#1a1a1a">CHORDELIA SHEET</text>',
        sheet._render_clef_symbol(
            left_margin=left_margin,
            staff_top=staff_top,
            staff_bottom=staff_bottom,
        ),
    ]

    if sheet._render_tempo_metadata:
        lines.insert(
            4,
            (
                f'<text x="{left_margin:.2f}" y="{top_margin + 18:.2f}" '
                'font-family="Georgia, serif" font-size="12" fill="#444">'
                f'tempo {score.metadata.tempo} | meter {score.metadata.time_signature[0]}/{score.metadata.time_signature[1]}'
                "</text>"
            ),
        )

    for line_index in range(5):
        y = staff_top + (line_index * staff_spacing)
        lines.append(
            f'<line class="staff-line" x1="{left_margin:.2f}" y1="{y:.2f}" x2="{width - right_margin:.2f}" y2="{y:.2f}" stroke="#222" stroke-width="1"/>'
        )

    lines.append(
        f'<line class="staff-barline" x1="{content_start_x:.2f}" y1="{staff_top:.2f}" x2="{content_start_x:.2f}" y2="{staff_bottom:.2f}" stroke="#222" stroke-width="1.2"/>'
    )
    lines.append(
        f'<line class="staff-barline" x1="{width - right_margin:.2f}" y1="{staff_top:.2f}" x2="{width - right_margin:.2f}" y2="{staff_bottom:.2f}" stroke="#222" stroke-width="1.2"/>'
    )

    if timing_mode == "beats":
        for marker, accidentals in sorted(measure_key_signatures.items(), key=lambda item: item[0]):
            if marker < 0 or marker >= end_beats:
                continue

            key_start_x = _x_for_measure_start(marker) + 6.0
            lines.extend(
                sheet._render_key_signature(
                    accidentals,
                    x_start=key_start_x,
                    staff_bottom=staff_bottom,
                    staff_spacing=staff_spacing,
                )
            )

            scale_label = measure_labels.get(marker)
            if scale_label is not None:
                lines.append(
                    f'<text class="scale-label" x="{key_start_x:.2f}" y="{top_margin + 34:.2f}" font-family="Georgia, serif" font-size="11" fill="#444">{scale_label}</text>'
                )

        numerator, _denominator = score.metadata.time_signature
        if numerator > 0:
            marker = Fraction(numerator, 1)
            while marker < end_beats:
                x = _x_for_measure_start(marker)
                if x >= (width - right_margin):
                    break
                lines.append(
                    f'<line class="measure-barline" x1="{x:.2f}" y1="{staff_top:.2f}" x2="{x:.2f}" y2="{staff_bottom:.2f}" stroke="#444" stroke-width="1"/>'
                )
                marker += Fraction(numerator, 1)
    else:
        lines.extend(
            sheet._render_key_signature(
                default_key_sig_accidentals,
                x_start=left_margin + 6.0,
                staff_bottom=staff_bottom,
                staff_spacing=staff_spacing,
            )
        )

        lines.extend(
            sheet._render_measure_barlines(
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
        event_key_accidental_map = sheet._key_accidental_map_for_beat(event.beat)
        note_render_data = sheet._event_note_render_data(
            event,
            staff_bottom=staff_bottom,
            staff_spacing=staff_spacing,
            key_accidental_map=event_key_accidental_map,
        )
        steps = tuple(int(item["step"]) for item in note_render_data)
        duration_beats = sheet._duration_beats(event.duration)
        stem_up = sheet._stem_up_for_steps(steps)
        positioned_notes = sheet._position_noteheads(
            note_render_data,
            base_x=x,
            stem_up=stem_up,
        )
        duration_beats_value = duration_beats
        beat_beats = event.beat.as_beats() if event.beat.mode == "beats" else None

        notehead_open, has_stem = sheet._notehead_style(duration_beats)
        notehead_class = "notehead-open" if notehead_open else "notehead-filled"
        if notehead_open:
            notehead_style = 'fill="#fffdf8" stroke="#111" stroke-width="1.1"'
        else:
            notehead_style = 'fill="#111"'

        stem_line = ""
        stem_geometry = None
        if has_stem:
            stem_line, stem_geometry = sheet._render_stem(
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
                "flag_count": sheet._flag_count(duration_beats_value),
                "has_stem": has_stem,
            }
        )

    beam_lines, beamed_levels = sheet._render_beams(
        rendered_events,
        measure_beats=score.metadata.time_signature[0],
    )

    for index, layout in enumerate(rendered_events):
        positioned_notes = layout["positioned_notes"]
        duration_beats = layout["duration_beats"]

        lines.extend(
            sheet._render_ledger_lines(
                positioned_notes=positioned_notes,
                staff_bottom=staff_bottom,
                staff_spacing=staff_spacing,
            )
        )

        lines.extend(sheet._render_note_accidentals(note_render_data=positioned_notes))

        for note in sorted(positioned_notes, key=lambda item: (float(item["y"]), float(item["x"]))):
            lines.append(
                (
                    f'<ellipse class="notehead {layout["notehead_class"]}" '
                    f'cx="{float(note["x"]):.2f}" cy="{float(note["y"]):.2f}" '
                    f'rx="5" ry="3.6" {layout["notehead_style"]}/>'
                )
            )

        if sheet._is_dotted_duration(duration_beats):
            lines.extend(sheet._render_dots(positioned_notes=positioned_notes))

        if layout["has_stem"]:
            lines.append(layout["stem_line"])

            flag_count = int(layout["flag_count"])
            beamed_level_count = beamed_levels.get(index, 0)
            remaining_flags = max(0, flag_count - beamed_level_count)
            stem_geometry = layout["stem_geometry"]
            if remaining_flags > 0 and stem_geometry is not None:
                lines.extend(sheet._render_flags(stem_geometry, count=remaining_flags))

    lines.extend(beam_lines)

    lines.append("</svg>")
    return "\n".join(lines)
