"""Tests for the SheetMusic score-backed rendering wrapper."""

from importlib import resources
from pathlib import Path

import pytest

from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.rhythm import Duration
from chordelia.scales import Scale
from chordelia.score import Score, ScoreEvent, ScoreMetadata
from chordelia.sequences import Sequence
from chordelia.sheet_music import SheetMusic


def _normalize_newlines(text: str) -> str:
    """Normalize line endings for stable cross-platform baseline comparisons."""
    return text.replace("\r\n", "\n").rstrip("\n")


def _read_baseline(name: str) -> str:
    """Load one SVG baseline fixture from package resources as normalized text."""
    baseline_text = (
        resources.files("tests.unit.chordelia.baselines")
        .joinpath(name)
        .read_text(encoding="utf-8")
    )
    return _normalize_newlines(baseline_text)


class TestSheetMusicConstruction:
    """Constructor normalization behavior for canonical SheetMusic workflows."""

    def test_constructor_accepts_existing_score_instance(self):
        score = Score.from_sequenceable(Note("C4"), tempo=96, time_signature=(3, 4))

        sheet = SheetMusic(score)

        assert sheet.score is score
        assert sheet.score.metadata.tempo == 96
        assert sheet.score.metadata.time_signature == (3, 4)

    def test_constructor_normalizes_sequenceable_source_to_score(self):
        sheet = SheetMusic(Note("E4"), tempo=110, time_signature=(6, 8), key_signature="G")

        assert isinstance(sheet.score, Score)
        assert sheet.score.events[0].pitches == (64,)
        assert sheet.score.metadata.tempo == 110
        assert sheet.score.metadata.time_signature == (6, 8)
        assert sheet.score.metadata.key_signature == "G"

    def test_constructor_rejects_non_sequenceable_values(self):
        with pytest.raises(TypeError, match="not Sequenceable"):
            SheetMusic({"bad": "payload"})


class TestSheetMusicFileOutput:
    """File output and format behavior for SheetMusic."""

    def test_to_file_writes_svg_output(self, tmp_path: Path):
        score = Score.from_sequenceable(Note("C4"), tempo=120)
        sheet = SheetMusic(score)

        output_path = sheet.to_file(tmp_path / "rendered.svg")

        assert output_path == tmp_path / "rendered.svg"
        assert output_path.exists()

        content = output_path.read_text(encoding="utf-8")
        assert content.startswith("<?xml")
        assert "<svg" in content
        assert "CHORDELIA SHEET" in content

    def test_to_file_supports_seconds_mode_timeline(self, tmp_path: Path):
        score = Score(
            source="seconds",
            metadata=ScoreMetadata(tempo=90, time_signature=(4, 4)),
            events=(
                ScoreEvent(
                    beat=Duration.from_seconds("0.5"),
                    duration=Duration.from_seconds("0.25"),
                    pitches=(60,),
                ),
            ),
        )
        sheet = SheetMusic(score)

        output_path = sheet.to_file(tmp_path / "seconds.svg")

        content = output_path.read_text(encoding="utf-8")
        assert 'class="notehead notehead-filled"' in content
        assert 'class="measure-barline"' not in content

    def test_to_file_renders_internal_measure_barlines_for_beats_mode(self, tmp_path: Path):
        score = Score(
            source="beats",
            metadata=ScoreMetadata(tempo=120, time_signature=(4, 4)),
            events=(
                ScoreEvent(beat=0, duration=1, pitches=(60,)),
                ScoreEvent(beat=5, duration=1, pitches=(62,)),
            ),
        )
        sheet = SheetMusic(score)

        output_path = sheet.to_file(tmp_path / "beats.svg")

        content = output_path.read_text(encoding="utf-8")
        assert content.count('class="measure-barline"') >= 1

    def test_to_file_renders_key_signature_from_scale(self, tmp_path: Path):
        sequence = Sequence((
            (Note("D4"), 1),
            (Note("F#4"), 1),
            (Note("A4"), 1),
        ))

        output_path = SheetMusic(
            sequence,
            scale=Scale("D", "major"),
        ).to_file(tmp_path / "with_scale_key_signature.svg")

        content = output_path.read_text(encoding="utf-8")
        assert content.count('class="key-accidental"') == 2
        assert "&#9839;" in content

    def test_to_file_renders_key_signature_from_scale_string(self, tmp_path: Path):
        sequence = Sequence((
            (Note("A4"), 1),
            (Note("C#5"), 1),
            (Note("E5"), 1),
        ))

        output_path = SheetMusic(
            sequence,
            scale="A",
        ).to_file(tmp_path / "with_key_string_signature.svg")

        content = output_path.read_text(encoding="utf-8")
        assert content.count('class="key-accidental"') == 3

    def test_to_file_renders_natural_for_out_of_key_note(self, tmp_path: Path):
        sequence = Sequence((
            (Note("F#4"), 1),
            (Note("F4"), 1),
        ))

        output_path = SheetMusic(
            sequence,
            scale=Scale("D", "major"),
        ).to_file(tmp_path / "naturals.svg")

        content = output_path.read_text(encoding="utf-8")
        assert content.count('class="note-accidental"') == 1
        assert "&#9838;" in content

    def test_constructor_rejects_invalid_scale_type(self):
        sequence = Sequence(((Note("C4"), 1),))

        with pytest.raises(TypeError, match="scale must be Scale or str"):
            SheetMusic(sequence, scale=object())

    def test_chord_renders_single_stem_and_ledger_lines(self, tmp_path: Path):
        sheet = SheetMusic(Chord.from_string("Am").with_octave(3))

        output_path = sheet.to_file(tmp_path / "a_minor.svg")

        content = output_path.read_text(encoding="utf-8")
        assert content.count('class="notehead notehead-filled"') == 3
        assert content.count('class="note-stem"') == 1
        assert content.count('class="ledger-line"') >= 2
        assert 'class="measure-barline"' not in content
        assert "&#119070;" in content

    def test_adjacent_chord_tones_are_horizontally_displaced(self, tmp_path: Path):
        sequence = Sequence(((Chord.from_string("Db(7)").with_octave(4), 1),))

        output_path = SheetMusic(sequence).to_file(tmp_path / "adjacent_tones.svg")

        content = output_path.read_text(encoding="utf-8")
        notehead_lines = [line for line in content.splitlines() if "<ellipse" in line and "class=\"notehead" in line]
        x_values = {
            line.split('cx="', 1)[1].split('"', 1)[0]
            for line in notehead_lines
            if 'cx="' in line
        }
        assert len(notehead_lines) >= 4
        assert len(x_values) >= 2

    def test_to_file_rejects_unsupported_output_format(self, tmp_path: Path):
        sheet = SheetMusic(Note("C4"))

        with pytest.raises(ValueError, match="Supported formats: svg"):
            sheet.to_file(tmp_path / "rendered.pdf", format="pdf")

    def test_score_to_file_requires_score_instance(self, tmp_path: Path):
        with pytest.raises(TypeError, match="Score instance"):
            SheetMusic.score_to_file("not-a-score", tmp_path / "bad.svg")

    def test_score_to_file_matches_instance_output(self, tmp_path: Path):
        score = Score.from_sequenceable(Note("D4"))

        from_instance = SheetMusic(score).to_file(tmp_path / "instance.svg")
        from_classmethod = SheetMusic.score_to_file(score, tmp_path / "classmethod.svg")

        assert from_instance.read_text(encoding="utf-8") == from_classmethod.read_text(encoding="utf-8")

    def test_svg_baseline_a3_major_scale_mixed_durations(self, tmp_path: Path):
        scale = Scale("A3", "major")
        durations_by_note = (1 / 8, 1 / 4, 1 / 2, 1, 3 / 2, 2, 4)
        sequence = Sequence(
            (note, duration)
            for note, duration in zip(scale.notes, durations_by_note, strict=False)
        )

        output_path = SheetMusic(sequence).to_file(tmp_path / "a3_major_mixed_durations.svg")

        rendered = _normalize_newlines(output_path.read_text(encoding="utf-8"))
        expected = _read_baseline("a3_major_mixed_durations.svg")
        assert rendered == expected

    def test_svg_baseline_db7_quarter_chord(self, tmp_path: Path):
        chord = Chord.from_string("Db(7)").with_octave(4)
        sequence = Sequence(((chord, 1),))

        output_path = SheetMusic(sequence).to_file(tmp_path / "db7_quarter_chord.svg")

        rendered = _normalize_newlines(output_path.read_text(encoding="utf-8"))
        expected = _read_baseline("db7_quarter_chord.svg")
        assert rendered == expected

    def test_svg_baseline_a3_natural_minor_scale(self, tmp_path: Path):
        sequence = Sequence(Scale("A3", "natural_minor").notes)

        output_path = SheetMusic(sequence).to_file(tmp_path / "a3_natural_minor_scale.svg")

        rendered = _normalize_newlines(output_path.read_text(encoding="utf-8"))
        expected = _read_baseline("a3_natural_minor_scale.svg")
        assert rendered == expected

    def test_svg_baseline_connected_eighth_sixteenth_notes(self, tmp_path: Path):
        notes = (
            Note("A3"),
            Note("B3"),
            Note("C4"),
            Note("D4"),
            Note("E4"),
            Note("F4"),
            Note("G4"),
            Note("A4"),
        )
        durations = (1 / 2, 1 / 2, 1 / 2, 1 / 2, 1 / 4, 1 / 4, 1 / 4, 1 / 4)
        sequence = Sequence(
            (note, duration)
            for note, duration in zip(notes, durations, strict=False)
        )

        output_path = SheetMusic(sequence).to_file(tmp_path / "connected_eighth_sixteenth_notes.svg")

        rendered = _normalize_newlines(output_path.read_text(encoding="utf-8"))
        expected = _read_baseline("connected_eighth_sixteenth_notes.svg")
        assert rendered == expected

    def test_connected_short_runs_render_beams(self, tmp_path: Path):
        notes = (
            Note("A3"),
            Note("B3"),
            Note("C4"),
            Note("D4"),
            Note("E4"),
            Note("F4"),
            Note("G4"),
            Note("A4"),
        )
        durations = (1 / 2, 1 / 2, 1 / 2, 1 / 2, 1 / 4, 1 / 4, 1 / 4, 1 / 4)
        sequence = Sequence(
            (note, duration)
            for note, duration in zip(notes, durations, strict=False)
        )

        output_path = SheetMusic(sequence).to_file(tmp_path / "beamed_notes.svg")

        content = output_path.read_text(encoding="utf-8")
        assert 'class="note-beam"' in content
        assert 'class="note-flag"' not in content

    def test_svg_baseline_connected_eighth_sixteenth_chords(self, tmp_path: Path):
        chords = (
            Chord.from_string("Am").with_octave(3),
            Chord.from_string("C").with_octave(4),
            Chord.from_string("Dm").with_octave(4),
            Chord.from_string("E").with_octave(4),
            Chord.from_string("F").with_octave(4),
            Chord.from_string("G").with_octave(4),
            Chord.from_string("Am").with_octave(4),
            Chord.from_string("C").with_octave(5),
        )
        durations = (1 / 2, 1 / 2, 1 / 2, 1 / 2, 1 / 4, 1 / 4, 1 / 4, 1 / 4)
        sequence = Sequence(
            (chord, duration)
            for chord, duration in zip(chords, durations, strict=False)
        )

        output_path = SheetMusic(sequence).to_file(tmp_path / "connected_eighth_sixteenth_chords.svg")

        rendered = _normalize_newlines(output_path.read_text(encoding="utf-8"))
        expected = _read_baseline("connected_eighth_sixteenth_chords.svg")
        assert rendered == expected

    def test_mixed_duration_sequence_renders_duration_markers(self, tmp_path: Path):
        scale = Scale("A3", "major")
        durations_by_note = (1 / 8, 1 / 4, 1 / 2, 1, 3 / 2, 2, 4)
        sequence = Sequence(
            (note, duration)
            for note, duration in zip(scale.notes, durations_by_note, strict=False)
        )

        output_path = SheetMusic(sequence).to_file(tmp_path / "duration_markers.svg")

        content = output_path.read_text(encoding="utf-8")
        assert 'class="notehead notehead-open"' in content
        assert 'class="notehead notehead-filled"' in content
        assert 'class="note-dot"' in content
        assert 'class="note-flag"' in content


class TestSheetMusicNotebookDisplay:
    """Notebook rich-display behavior and API boundaries."""

    def test_repr_mimebundle_returns_svg_and_text_fallback(self):
        sheet = SheetMusic(Note("C4"))

        mimebundle = sheet._repr_mimebundle_()

        assert "image/svg+xml" in mimebundle
        assert "text/plain" in mimebundle
        assert "SheetMusic(" in mimebundle["text/plain"]
        assert "<svg" in mimebundle["image/svg+xml"]

    def test_v1_surface_excludes_parse_load_apis(self):
        assert not hasattr(SheetMusic, "load_from_file")
        assert not hasattr(SheetMusic, "score_from_file")
