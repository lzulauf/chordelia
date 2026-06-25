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
from chordelia.sheetmusic_backends.helpers import key_accidental_map_from_scale
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
        self._staff_key_accidental_map = key_accidental_map_from_scale(self._staff_scale)

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

    @staticmethod
    def _normalize_format(format: str) -> str:
        """Normalize output format names and aliases."""
        lowered = format.strip().lower()
        if lowered in {"svg", "image/svg+xml"}:
            return "svg"
        return lowered
