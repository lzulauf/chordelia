"""Sheet music rendering wrapper built on canonical Score normalization."""

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from enum import Enum
from fractions import Fraction
from pathlib import Path
import re
from typing import Any, Callable, Iterable, TypeAlias, Union

from chordelia.rhythm import Duration
from chordelia.score import Score, ScoreEvent, ScoreMetadata
from chordelia.scales import Scale
from chordelia.sequenceable import (
    Sequenceable,
    SheetMusicScaleResolver,
    TempoMetadataSource,
    VisualRenderableSource,
)


SheetMusicAtomSource: TypeAlias = Score | VisualRenderableSource
SheetMusicGalleryItem: TypeAlias = Union[SheetMusicAtomSource, "SheetMusic"]
SheetMusicSource: TypeAlias = Union[SheetMusicAtomSource, Iterable[SheetMusicGalleryItem]]


def _render_sheet_music_svg_backend(sheet: "SheetMusic") -> str:
    """Load and dispatch to the dedicated built-in SVG backend renderer."""
    from chordelia.sheetmusic_backends.svg import render_sheet_music_svg

    return render_sheet_music_svg(sheet)


class SheetClef(str, Enum):
    """Supported clefs for sheet rendering."""

    TREBLE = "treble"
    BASS = "bass"


class SheetMusic:
    """Canonical sheet-rendering wrapper around a normalized Score."""

    _RENDER_BACKEND_ADAPTERS: dict[str, str | Callable[["SheetMusic"], str]] = {
        "svg": _render_sheet_music_svg_backend,
    }

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
    _SPELLING_PATTERN = re.compile(r"^\s*([A-Ga-g])([#b]{0,2})?(-?\d+)?\s*$")
    _KEY_SHARP_ORDER = ("F", "C", "G", "D", "A", "E", "B")
    _KEY_FLAT_ORDER = ("B", "E", "A", "D", "G", "C", "F")
    _KEY_SHARP_STEPS_BY_CLEF = {
        SheetClef.TREBLE: {
            "F": 8,
            "C": 5,
            "G": 9,
            "D": 6,
            "A": 3,
            "E": 7,
            "B": 4,
        },
        SheetClef.BASS: {
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
        SheetClef.TREBLE: {
            "B": 4,
            "E": 7,
            "A": 3,
            "D": 6,
            "G": 2,
            "C": 5,
            "F": 1,
        },
        SheetClef.BASS: {
            "B": 2,
            "E": 5,
            "A": 1,
            "D": 4,
            "G": 0,
            "C": 3,
            "F": -1,
        },
    }
    _CLEF_BOTTOM_LINE_INDEX = {
        SheetClef.TREBLE: (4 * 7) + _LETTER_INDEX["E"],
        SheetClef.BASS: (2 * 7) + _LETTER_INDEX["G"],
    }

    def __init__(
        self,
        source: SheetMusicSource,
        *,
        clef: str | SheetClef = "auto",
        tempo: int = 120,
        time_signature: tuple[int, int] = (4, 4),
        key_signature: str | None = None,
        ppq: int = 480,
        scale: Scale | str | None = None,
    ):
        self._measure_scale_annotations: tuple[tuple[Fraction, Scale, str], ...] = ()
        self._render_tempo_metadata = self._is_song_or_score_source(source)

        if isinstance(source, Score):
            self.score = source
        elif self._is_renderable_iterable_source(source):
            self.score, self._measure_scale_annotations = self._score_from_renderable_iterable(
                source,
                tempo=tempo,
                time_signature=time_signature,
                key_signature=key_signature,
                ppq=ppq,
            )
        else:
            self.score = Score.from_sequenceable(
                source,
                tempo=tempo,
                time_signature=time_signature,
                key_signature=key_signature,
                ppq=ppq,
            )

        self.clef = self._resolve_clef(clef)

        self._staff_scale = self._resolve_staff_scale(
            source=source,
            scale=scale,
            metadata_key=self.score.metadata.key_signature,
        )
        self._staff_key_accidental_map = self._key_accidental_map_from_scale(self._staff_scale)

    @staticmethod
    def _is_song_or_score_source(source: SheetMusicSource) -> bool:
        """Return True when source opts in to tempo metadata rendering."""
        if isinstance(source, TempoMetadataSource):
            return bool(source.sheet_music_should_render_tempo_metadata())

        render_tempo = getattr(source, "sheet_music_should_render_tempo_metadata", None)
        if callable(render_tempo):
            return bool(render_tempo())
        return False

    @staticmethod
    def _is_renderable_iterable_source(source: SheetMusicSource) -> bool:
        """Return True when source should be treated as a gallery-style iterable."""
        if isinstance(source, (str, bytes, bytearray)):
            return False
        if isinstance(source, VisualRenderableSource):
            return False
        return isinstance(source, IterableABC)

    @classmethod
    def _score_from_renderable_iterable(
        cls,
        source: Iterable[SheetMusicGalleryItem],
        *,
        tempo: int,
        time_signature: tuple[int, int],
        key_signature: str | None,
        ppq: int,
    ) -> tuple[Score, tuple[tuple[Fraction, Scale, str], ...]]:
        """Normalize iterable renderables into one combined score timeline."""
        values = tuple(source)
        combined_events: list[ScoreEvent] = []
        scale_annotations: list[tuple[Fraction, Scale, str]] = []
        cursor: Duration | None = None
        measure_duration = Duration.from_beats(time_signature[0], None)

        for value in values:
            item_score = cls._coerce_gallery_value_to_score(
                value,
                tempo=tempo,
                time_signature=time_signature,
                key_signature=key_signature,
                ppq=ppq,
            )
            item_mode = cls._score_timing_mode(item_score)

            if cursor is None:
                cursor = (
                    Duration.from_seconds(0)
                    if item_mode == "seconds"
                    else Duration.from_beats(0, None)
                )
            elif cursor.mode != item_mode:
                raise ValueError(
                    "All renderable values in a SheetMusic iterable must share the same timing mode"
                )

            item_start = cursor
            scale_annotation = cls._coerce_scale_annotation(value)
            if item_start.mode == "beats" and scale_annotation is not None:
                scale_annotations.append(
                    (item_start.as_beats(), scale_annotation, scale_annotation.name)
                )

            for event in item_score.events:
                combined_events.append(
                    ScoreEvent(
                        beat=event.beat + cursor,
                        duration=event.duration,
                        pitches=event.pitches,
                        velocity=event.velocity,
                        channel=event.channel,
                        voice=event.voice,
                        spelling=event.spelling,
                        gate_width=event.gate_width,
                        gate_offset=event.gate_offset,
                    )
                )

            cursor = cls._next_gallery_cursor(
                cursor,
                consumed=item_score.duration,
                measure_duration=measure_duration,
            )

        metadata = ScoreMetadata(
            tempo=tempo,
            time_signature=time_signature,
            key_signature=key_signature,
            ppq=ppq,
        )
        return (
            Score(source=values, metadata=metadata, events=tuple(combined_events)),
            tuple(scale_annotations),
        )

    @staticmethod
    def _coerce_scale_annotation(value: Any) -> Scale | None:
        """Extract a concrete Scale when one value semantically represents a scale."""
        if isinstance(value, Scale):
            return value

        if isinstance(value, SheetMusic) and isinstance(value.score.source, Scale):
            return value.score.source

        return None

    @staticmethod
    def _coerce_gallery_value_to_score(
        value: SheetMusicGalleryItem,
        *,
        tempo: int,
        time_signature: tuple[int, int],
        key_signature: str | None,
        ppq: int,
    ) -> Score:
        """Coerce one gallery value into a Score instance."""
        if isinstance(value, SheetMusic):
            return value.score
        if isinstance(value, Score):
            return value

        return Score.from_sequenceable(
            value,
            tempo=tempo,
            time_signature=time_signature,
            key_signature=key_signature,
            ppq=ppq,
        )

    @staticmethod
    def _score_timing_mode(score: Score) -> str:
        """Return timing mode for a score, defaulting empty scores to beat mode."""
        if not score.events:
            return "beats"
        return score.events[0].beat.mode

    @classmethod
    def _next_gallery_cursor(
        cls,
        cursor: Duration,
        *,
        consumed: Duration,
        measure_duration: Duration,
    ) -> Duration:
        """Advance to the next item start, aligning beat-mode timelines to measures."""
        if consumed.mode != cursor.mode:
            raise ValueError(
                "All renderable values in a SheetMusic iterable must share the same timing mode"
            )

        next_cursor = cursor + consumed
        if next_cursor.mode != "beats":
            return next_cursor

        return cls._align_to_measure_boundary(next_cursor, measure_duration)

    @staticmethod
    def _align_to_measure_boundary(position: Duration, measure_duration: Duration) -> Duration:
        """Round beat-mode positions up to the next measure boundary."""
        if position.mode != "beats" or measure_duration.mode != "beats":
            return position

        measure_beats = measure_duration.as_beats()
        if measure_beats <= 0:
            return position

        beats = position.as_beats()
        if beats <= 0:
            return position

        measure_index = beats / measure_beats
        whole_measures = (
            measure_index.numerator + measure_index.denominator - 1
        ) // measure_index.denominator
        return Duration.from_beats(whole_measures * measure_beats, None)

    @classmethod
    def _coerce_requested_clef(cls, value: str | SheetClef) -> str:
        """Normalize user clef input to treble/bass/auto tokens."""
        if isinstance(value, SheetClef):
            return value.value

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"treble", "bass", "auto"}:
                return normalized

        raise ValueError(
            f"Invalid clef {value!r}. Expected one of: 'treble', 'bass', or 'auto'."
        )

    def _resolve_clef(self, requested_clef: str | SheetClef) -> SheetClef:
        """Resolve a concrete clef for rendering, including auto mode."""
        normalized = self._coerce_requested_clef(requested_clef)
        if normalized == "treble":
            return SheetClef.TREBLE
        if normalized == "bass":
            return SheetClef.BASS

        unique_pitches = sorted({pitch for event in self.score.events for pitch in event.pitches})
        if not unique_pitches:
            return SheetClef.TREBLE

        midpoint = len(unique_pitches) // 2
        if len(unique_pitches) % 2 == 1:
            median_pitch = float(unique_pitches[midpoint])
        else:
            median_pitch = (unique_pitches[midpoint - 1] + unique_pitches[midpoint]) / 2.0

        if median_pitch < 60.0:
            return SheetClef.BASS
        return SheetClef.TREBLE

    @classmethod
    def score_to_file(
        cls,
        score: Score,
        file_path: str | Path,
        *,
        clef: str | SheetClef = "auto",
        format: str = "svg",
    ) -> Path:
        """Write a score to a sheet-music output file and return the resulting path."""
        if not isinstance(score, Score):
            raise TypeError(f"score must be a Score instance, got {type(score).__name__}")

        sheet = cls(score, clef=clef)
        return sheet.to_file(file_path, format=format)

    def to_file(self, file_path: str | Path, *, format: str = "svg") -> Path:
        """Render sheet output to disk and return the resulting path."""
        normalized_format = self._normalize_format(format)
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rendered_output = self._render_with_backend(
            normalized_format,
            original_format=format,
        )
        output_path.write_text(rendered_output, encoding="utf-8")
        return output_path

    def _render_with_backend(self, normalized_format: str, *, original_format: str) -> str:
        """Dispatch rendering through the configured backend adapter map."""
        renderer_entry = self._RENDER_BACKEND_ADAPTERS.get(normalized_format)
        if renderer_entry is None:
            supported_formats = ", ".join(sorted(self._RENDER_BACKEND_ADAPTERS))
            raise ValueError(
                f"Unsupported sheet output format {original_format!r}. Supported formats: {supported_formats}"
            )

        if isinstance(renderer_entry, str):
            renderer = getattr(self, renderer_entry, None)
            if not callable(renderer):
                raise RuntimeError(
                    f"Configured sheet renderer {renderer_entry!r} for format {normalized_format!r} is not callable"
                )
            return renderer()

        if not callable(renderer_entry):
            raise RuntimeError(
                f"Configured sheet renderer {renderer_entry!r} for format {normalized_format!r} is not callable"
            )
        return renderer_entry(self)

    def _repr_mimebundle_(self, include=None, exclude=None):
        """Return a notebook-friendly mime bundle with SVG and plain-text fallback."""
        del include, exclude
        summary = (
            "SheetMusic(" 
            f"events={len(self.score.events)}, "
            f"tempo={self.score.metadata.tempo}, "
            f"time_signature={self.score.metadata.time_signature}"
            ")"
        )
        return {
            "image/svg+xml": self._render_with_backend(
                "svg",
                original_format="image/svg+xml",
            ),
            "text/plain": summary,
        }

    def _render_svg(self) -> str:
        """Compatibility wrapper that delegates to the built-in SVG backend module."""
        return _render_sheet_music_svg_backend(self)

    def _resolve_staff_scale(
        self,
        *,
        source: SheetMusicSource,
        scale: Scale | str | None,
        metadata_key: str | None,
    ) -> Scale | None:
        """Resolve optional rendering scale input to a Scale instance."""
        source_scale = self._scale_from_wrapped_source(source)
        if source_scale is not None:
            return source_scale
        if scale is not None:
            return self._coerce_scale_value(scale)
        if metadata_key is not None:
            return self._coerce_scale_value(metadata_key)
        return None

    @staticmethod
    def _scale_from_wrapped_source(source: SheetMusicSource) -> Scale | None:
        """Ask wrapped source types for their preferred staff scale when available."""
        if isinstance(source, SheetMusicScaleResolver):
            resolved = source.sheet_music_global_scale()
            if resolved is None:
                return None
            if isinstance(resolved, (Scale, str)):
                return SheetMusic._coerce_scale_value_static(resolved)
            raise TypeError(
                "sheet_music_global_scale() must return Scale, str, or None; "
                f"got {type(resolved).__name__}."
            )

        resolve_scale = getattr(source, "sheet_music_global_scale", None)
        if callable(resolve_scale):
            resolved = resolve_scale()
            if resolved is None:
                return None
            if isinstance(resolved, (Scale, str)):
                return SheetMusic._coerce_scale_value_static(resolved)
            raise TypeError(
                "sheet_music_global_scale() must return Scale, str, or None; "
                f"got {type(resolved).__name__}."
            )

        return None

    @staticmethod
    def _coerce_scale_value_static(value: Scale | str) -> Scale:
        """Static helper for coercing scale values outside instance context."""
        if isinstance(value, Scale):
            return value
        if isinstance(value, str):
            raw = value.strip()
            compact = raw.replace(" ", "")

            minor_suffix = compact.endswith("m") and len(compact) >= 2
            if minor_suffix:
                root_text = compact[:-1]
                scale_type = "natural_minor"
            else:
                match = re.match(
                    r"^([A-Ga-g](?:#|b)?)(?:\s*(major|minor|natural_minor|harmonic_minor|melodic_minor))?$",
                    raw,
                    re.IGNORECASE,
                )
                if match is None:
                    raise ValueError(
                        f"Could not parse scale string {value!r}. Expected forms like 'D', 'Bb', 'Am', or 'E minor'."
                    )
                root_text = match.group(1)
                mode_text = match.group(2)
                if mode_text is None:
                    scale_type = "major"
                else:
                    normalized_mode = mode_text.lower()
                    scale_type = "natural_minor" if normalized_mode == "minor" else normalized_mode

            return Scale(root_text, scale_type)
        raise TypeError(
            f"scale must be Scale or str, got {type(value).__name__}"
        )

    def _coerce_scale_value(self, value: Scale | str) -> Scale:
        """Coerce user scale values into a concrete Scale."""
        if isinstance(value, str):
            return self._scale_from_string(value)
        return self._coerce_scale_value_static(value)

    def _scale_from_string(self, text: str) -> Scale:
        """Parse compact scale strings like 'D', 'Bb', 'Am', or 'E minor'."""
        raw = text.strip()
        compact = raw.replace(" ", "")

        minor_suffix = compact.endswith("m") and len(compact) >= 2
        if minor_suffix:
            root_text = compact[:-1]
            scale_type = "natural_minor"
        else:
            match = re.match(
                r"^([A-Ga-g](?:#|b)?)(?:\s*(major|minor|natural_minor|harmonic_minor|melodic_minor))?$",
                raw,
                re.IGNORECASE,
            )
            if match is None:
                raise ValueError(
                    f"Could not parse scale string {text!r}. Expected forms like 'D', 'Bb', 'Am', or 'E minor'."
                )
            root_text = match.group(1)
            mode_text = match.group(2)
            if mode_text is None:
                scale_type = "major"
            else:
                normalized_mode = mode_text.lower()
                scale_type = "natural_minor" if normalized_mode == "minor" else normalized_mode

        return Scale(root_text, scale_type)

    def _key_accidental_map_from_scale(self, scale: Scale | None) -> dict[str, int]:
        """Build expected letter-accidental map from a diatonic scale when possible."""
        if scale is None:
            return {}

        accidental_map: dict[str, int] = {}
        for note in scale.key_signature_notes():
            letter = note.name.name
            accidental = int(note.accidental.value)
            existing = accidental_map.get(letter)
            if existing is not None and existing != accidental:
                return {}
            accidental_map[letter] = accidental

        return accidental_map

    def _key_signature_accidentals_for_render(self) -> list[tuple[str, int]]:
        """Return ordered key-signature accidental glyphs from the active scale map."""
        return self._key_signature_accidentals_for_map(self._staff_key_accidental_map)

    def _key_signature_accidentals_for_scale(self, scale: Scale) -> list[tuple[str, int]]:
        """Return ordered key-signature accidentals for one concrete scale."""
        return self._key_signature_accidentals_for_map(
            self._key_accidental_map_from_scale(scale)
        )

    def _key_signature_accidentals_for_map(
        self,
        accidental_map: dict[str, int],
    ) -> list[tuple[str, int]]:
        """Return ordered key-signature accidental glyphs for one accidental map."""
        if not accidental_map:
            return []

        values = {accidental_map.get(letter, 0) for letter in self._LETTER_INDEX}
        if values.issubset({0, 1}):
            ordered = self._KEY_SHARP_ORDER
            expected_value = 1
        elif values.issubset({0, -1}):
            ordered = self._KEY_FLAT_ORDER
            expected_value = -1
        else:
            return []

        return [
            (letter, expected_value)
            for letter in ordered
            if accidental_map.get(letter, 0) == expected_value
        ]

    def _scale_measure_annotations_for_render(
        self,
    ) -> tuple[tuple[Fraction, list[tuple[str, int]], str], ...]:
        """Return ordered measure-start key signatures and labels for iterable scales."""
        if not self._measure_scale_annotations:
            return ()

        by_measure: dict[Fraction, tuple[list[tuple[str, int]], str]] = {}
        for beat, scale, label in self._measure_scale_annotations:
            by_measure[beat] = (self._key_signature_accidentals_for_scale(scale), label)

        return tuple(
            (beat, values[0], values[1])
            for beat, values in sorted(by_measure.items(), key=lambda item: item[0])
        )

    def _key_accidental_map_for_beat(self, beat: Duration) -> dict[str, int]:
        """Resolve active key accidental expectations for one event beat position."""
        if beat.mode != "beats" or not self._measure_scale_annotations:
            return self._staff_key_accidental_map

        beat_value = beat.as_beats()
        active_map = self._staff_key_accidental_map
        for marker, scale, _label in self._measure_scale_annotations:
            if marker > beat_value:
                break
            active_map = self._key_accidental_map_from_scale(scale)

        return active_map

    def _render_key_signature(
        self,
        accidentals: list[tuple[str, int]],
        *,
        x_start: float,
        staff_bottom: float,
        staff_spacing: float,
    ) -> list[str]:
        """Render key signature accidental symbols in the active clef."""
        sharp_steps = self._KEY_SHARP_STEPS_BY_CLEF[self.clef]
        flat_steps = self._KEY_FLAT_STEPS_BY_CLEF[self.clef]
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

    def _render_clef_symbol(
        self,
        *,
        left_margin: float,
        staff_top: float,
        staff_bottom: float,
    ) -> str:
        """Render the leading clef glyph for the active clef."""
        if self.clef is SheetClef.BASS:
            return (
                f'<text x="{left_margin - 28:.2f}" y="{staff_top + 38:.2f}" '
                'font-family="Bravura, Noto Music, serif" font-size="40" fill="#111">&#119074;</text>'
            )
        return (
            f'<text x="{left_margin - 30:.2f}" y="{staff_bottom + 4:.2f}" '
            'font-family="Bravura, Noto Music, serif" font-size="44" fill="#111">&#119070;</text>'
        )

    def _render_measure_barlines(
        self,
        x_start: float,
        x_end: float,
        y_top: float,
        y_bottom: float,
        pixels_per_unit: float,
    ) -> list[str]:
        """Render internal measure barlines when score timing is beat-based."""
        if not self.score.events:
            return []

        timing_mode = self.score.events[0].beat.mode
        if timing_mode != "beats":
            return []

        numerator, _denominator = self.score.metadata.time_signature
        if numerator <= 0:
            return []

        end_time = max(self._duration_value(event.beat + event.duration) for event in self.score.events)
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

    @staticmethod
    def _stem_up_for_steps(steps: tuple[int, ...]) -> bool:
        """Decide stem direction with a simple average-step heuristic."""
        if not steps:
            return True
        return (sum(steps) / len(steps)) < 4.0

    def _position_noteheads(
        self,
        note_render_data: list[dict[str, float | int | str | None]],
        *,
        base_x: float,
        stem_up: bool,
    ) -> list[dict[str, float | int | str | None]]:
        """Apply horizontal displacement for adjacent-step chord notehead collisions."""
        if len(note_render_data) <= 1:
            single = [dict(item) for item in note_render_data]
            for item in single:
                item["x"] = base_x
            return single

        indexed = list(enumerate(note_render_data))
        indexed.sort(key=lambda pair: (int(pair[1]["step"]), float(pair[1]["y"])))

        collision_shift = -5.0 if stem_up else 5.0
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

    def _event_note_render_data(
        self,
        event,
        *,
        staff_bottom: float,
        staff_spacing: float,
        key_accidental_map: dict[str, int],
    ) -> list[dict[str, float | int | str | None]]:
        """Collect render metadata per event note (step/y/letter/accidental)."""
        data: list[dict[str, float | int | str | None]] = []
        spellings = event.spelling if event.spelling is not None else ()
        for index, pitch in enumerate(event.pitches):
            spelling = spellings[index] if index < len(spellings) else None
            parsed = self._parse_spelling_with_accidental(spelling) if spelling is not None else None

            if parsed is not None:
                letter_index, accidental_offset, octave = parsed
                step = (octave * 7 + letter_index) - self._bottom_line_index_for_clef(self.clef)
                letter_name = "CDEFGAB"[letter_index]
                note_accidental = accidental_offset
            else:
                step = self._staff_step_for_pitch(pitch, None, clef=self.clef)
                pitch_class = pitch % 12
                letter_index = self._MIDI_TO_LETTER_INDEX[pitch_class]
                letter_name = "CDEFGAB"[letter_index]
                natural_pc = self._LETTER_INDEX[letter_name]
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

    def _render_note_accidentals(
        self,
        *,
        note_render_data: list[dict[str, float | int | str | None]],
    ) -> list[str]:
        """Render explicit note accidentals against active key signature context."""
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
                expected = self._staff_key_accidental_map.get(letter, 0)
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
    def _accidental_symbol(offset: int) -> str | None:
        """Map accidental semitone offsets to renderable glyph entities."""
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

    def _svg_width(self) -> int:
        """Scale output width by score duration to keep spacing readable."""
        if not self.score.events:
            return 640
        end_time = max(self._duration_value(event.beat + event.duration) for event in self.score.events)
        return max(640, int(180 + (end_time * 140)))

    @staticmethod
    def _duration_value(duration) -> float:
        """Convert Duration values to a float timeline coordinate."""
        if duration.mode == "seconds":
            return float(duration.as_seconds())
        return float(duration.as_beats())

    @staticmethod
    def _duration_beats(duration) -> Fraction | None:
        """Return beat-based duration where available, else None."""
        if duration.mode != "beats":
            return None
        return duration.as_beats()

    @staticmethod
    def _notehead_style(duration_beats: Fraction | None) -> tuple[bool, bool]:
        """Return (is_open_notehead, has_stem) for a duration value."""
        if duration_beats is None:
            return False, True
        if duration_beats >= Fraction(4, 1):
            return True, False
        if duration_beats >= Fraction(2, 1):
            return True, True
        return False, True

    @staticmethod
    def _is_dotted_duration(duration_beats: Fraction | None) -> bool:
        """Detect common dotted durations in beat space."""
        if duration_beats is None:
            return False
        dotted_values = {
            Fraction(3, 1),
            Fraction(3, 2),
            Fraction(3, 4),
            Fraction(3, 8),
            Fraction(3, 16),
            Fraction(3, 32),
        }
        return duration_beats in dotted_values

    @staticmethod
    def _flag_count(duration_beats: Fraction | None) -> int:
        """Return how many stem flags to render for short durations."""
        if duration_beats is None or duration_beats >= Fraction(1, 1):
            return 0
        if duration_beats >= Fraction(1, 2):
            return 1
        if duration_beats >= Fraction(1, 4):
            return 2
        if duration_beats >= Fraction(1, 8):
            return 3
        return 4

    @classmethod
    def _bottom_line_index_for_clef(cls, clef: SheetClef) -> int:
        """Return the absolute diatonic index for the active clef bottom line."""
        return cls._CLEF_BOTTOM_LINE_INDEX[clef]

    @classmethod
    def _staff_step_for_pitch(
        cls,
        pitch: int,
        spelling: str | None,
        *,
        clef: SheetClef,
    ) -> int:
        """Map a pitch to a diatonic staff step relative to the active clef."""
        if spelling is not None:
            parsed = cls._parse_spelling(spelling)
            if parsed is not None:
                letter_index, octave = parsed
                return (octave * 7 + letter_index) - cls._bottom_line_index_for_clef(clef)

        pitch_class = pitch % 12
        letter_index = cls._MIDI_TO_LETTER_INDEX[pitch_class]
        octave = (pitch // 12) - 1
        return (octave * 7 + letter_index) - cls._bottom_line_index_for_clef(clef)

    @classmethod
    def _parse_spelling(cls, spelling: str) -> tuple[int, int] | None:
        """Parse note spelling text into (letter_index, octave)."""
        parsed = cls._parse_spelling_with_accidental(spelling)
        if parsed is None:
            return None
        letter_index, _accidental_offset, octave = parsed
        return letter_index, octave

    @classmethod
    def _parse_spelling_with_accidental(
        cls,
        spelling: str,
    ) -> tuple[int, int, int] | None:
        """Parse note spelling text into (letter_index, accidental_offset, octave)."""
        match = cls._SPELLING_PATTERN.match(spelling)
        if match is None:
            return None
        letter = match.group(1).upper()
        accidental_text = match.group(2) or ""
        octave_text = match.group(3)
        if octave_text is None:
            return None
        if set(accidental_text) == {"#"}:
            accidental_offset = len(accidental_text)
        elif set(accidental_text) == {"b"}:
            accidental_offset = -len(accidental_text)
        elif accidental_text == "":
            accidental_offset = 0
        else:
            return None
        return cls._LETTER_INDEX[letter], accidental_offset, int(octave_text)

    def _event_staff_positions(self, event, *, staff_bottom: float, staff_spacing: float) -> list[tuple[int, float]]:
        """Return per-note staff step and y coordinate pairs for an event."""
        positions: list[tuple[int, float]] = []
        spellings = event.spelling if event.spelling is not None else ()
        for index, pitch in enumerate(event.pitches):
            spelling = spellings[index] if index < len(spellings) else None
            step = self._staff_step_for_pitch(pitch, spelling, clef=self.clef)
            y = staff_bottom - (step * (staff_spacing / 2.0))
            positions.append((step, y))
        return positions

    def _render_ledger_lines(
        self,
        *,
        positioned_notes: list[dict[str, float | int | str | None]],
        staff_bottom: float,
        staff_spacing: float,
    ) -> list[str]:
        """Render ledger lines for notes that sit outside the five-line staff."""
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
    def _render_stem(
        *,
        positioned_notes: list[dict[str, float | int | str | None]],
        stem_up: bool,
    ) -> tuple[str, dict[str, float | bool] | None]:
        """Render one stem per chord event using a simple direction heuristic."""
        if not positioned_notes:
            return "", None

        if stem_up:
            anchor_y = min(float(note["y"]) for note in positioned_notes)
            anchor_x = max(
                float(note["x"])
                for note in positioned_notes
                if float(note["y"]) == anchor_y
            )
            end_y = anchor_y - 28.0
            stem_x = anchor_x + 4.8
        else:
            anchor_y = max(float(note["y"]) for note in positioned_notes)
            anchor_x = min(
                float(note["x"])
                for note in positioned_notes
                if float(note["y"]) == anchor_y
            )
            end_y = anchor_y + 28.0
            stem_x = anchor_x - 4.8

        stem_line = (
            f'<line class="note-stem" x1="{stem_x:.2f}" y1="{anchor_y:.2f}" '
            f'x2="{stem_x:.2f}" y2="{end_y:.2f}" stroke="#111" stroke-width="1"/>'
        )
        stem_geometry = {
            "x": stem_x,
            "anchor_y": anchor_y,
            "end_y": end_y,
            "stem_up": stem_up,
        }
        return stem_line, stem_geometry

    @staticmethod
    def _render_flags(stem_geometry: dict[str, float | bool], *, count: int) -> list[str]:
        """Render simple stem flags for short durations."""
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

    def _render_beams(
        self,
        rendered_events: list[dict[str, Any]],
        *,
        measure_beats: int,
    ) -> tuple[list[str], dict[int, int]]:
        """Render beam segments for contiguous runs of short beat-based notes."""
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
                    lines, levels = self._render_beam_run(
                        rendered_events,
                        run_start,
                        index - 1,
                        measure_beats=measure_beats,
                    )
                    beam_lines.extend(lines)
                    for event_index, level in levels.items():
                        beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), level)
                    run_start = None
                continue

            if run_start is None:
                run_start = index
                continue

            if self._can_continue_beam_run(
                previous=rendered_events[index - 1],
                current=layout,
                measure_beats=measure_beats,
            ):
                continue

            lines, levels = self._render_beam_run(
                rendered_events,
                run_start,
                index - 1,
                measure_beats=measure_beats,
            )
            beam_lines.extend(lines)
            for event_index, level in levels.items():
                beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), level)
            run_start = index

        if run_start is not None:
            lines, levels = self._render_beam_run(
                rendered_events,
                run_start,
                len(rendered_events) - 1,
                measure_beats=measure_beats,
            )
            beam_lines.extend(lines)
            for event_index, level in levels.items():
                beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), level)

        return beam_lines, beamed_levels

    @staticmethod
    def _can_continue_beam_run(
        *,
        previous: dict[str, Any],
        current: dict[str, Any],
        measure_beats: int,
    ) -> bool:
        """Return True when two short notes belong to the same beam run."""
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
        """Render beams for one contiguous run, including multi-beam levels."""
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
                    segment_lines, segment_levels = self._render_beam_segment(
                        rendered_events,
                        level_run,
                        level=level,
                    )
                    lines.extend(segment_lines)
                    for event_index, event_level in segment_levels.items():
                        beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), event_level)
                elif len(level_run) == 1 and level >= 2:
                    hook_lines, hook_levels = self._render_beam_hook(
                        rendered_events,
                        run_indices,
                        note_index=level_run[0],
                        level=level,
                    )
                    lines.extend(hook_lines)
                    for event_index, event_level in hook_levels.items():
                        beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), event_level)
                level_run = []

            if len(level_run) >= 2:
                segment_lines, segment_levels = self._render_beam_segment(
                    rendered_events,
                    level_run,
                    level=level,
                )
                lines.extend(segment_lines)
                for event_index, event_level in segment_levels.items():
                    beamed_levels[event_index] = max(beamed_levels.get(event_index, 0), event_level)
            elif len(level_run) == 1 and level >= 2:
                hook_lines, hook_levels = self._render_beam_hook(
                    rendered_events,
                    run_indices,
                    note_index=level_run[0],
                    level=level,
                )
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
        """Render one beam segment over a run at a specific flag level."""
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

        beamed_levels = {index: level for index in run_indices}
        return [polygon], beamed_levels

    @staticmethod
    def _render_beam_hook(
        rendered_events: list[dict[str, Any]],
        run_indices: list[int],
        *,
        note_index: int,
        level: int,
    ) -> tuple[list[str], dict[int, int]]:
        """Render a short beam hook for an isolated higher-level beam note."""
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

        level_indices = [
            index
            for index in run_indices
            if int(rendered_events[index]["flag_count"]) >= level
        ]
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
    def _render_dots(
        *,
        positioned_notes: list[dict[str, float | int | str | None]],
    ) -> list[str]:
        """Render augmentation dots beside dotted-duration noteheads."""
        return [
            (
                f'<circle class="note-dot" '
                f'cx="{float(note["x"]) + 10.0:.2f}" '
                f'cy="{float(note["y"]):.2f}" r="1.4" fill="#111"/>'
            )
            for note in sorted(positioned_notes, key=lambda item: (float(item["y"]), float(item["x"])))
        ]

    @staticmethod
    def _normalize_format(format: str) -> str:
        """Normalize output format names and aliases."""
        lowered = format.strip().lower()
        if lowered in {"svg", "image/svg+xml"}:
            return "svg"
        return lowered
