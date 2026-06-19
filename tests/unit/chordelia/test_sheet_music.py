"""Tests for the SheetMusic score-backed rendering wrapper."""

import builtins
from importlib import resources
from pathlib import Path
import re
import subprocess

import pytest

import chordelia.sheetmusic_backends.lilypond as lilypond_backend
from chordelia.chords import Chord
from chordelia.degrees import Degree
from chordelia.notes import Note
from chordelia.rhythm import Duration
from chordelia.scales import Scale
from chordelia.score import Score, ScoreEvent, ScoreMetadata
from chordelia.sequences import Rest, Sequence
from chordelia.sheet_music import SheetClef, SheetMusic


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

    def test_constructor_accepts_iterable_of_renderables(self):
        sheet = SheetMusic([Note("C4"), Note("E4"), Note("G4")])

        assert isinstance(sheet.score, Score)
        assert [event.pitches for event in sheet.score.events] == [(60,), (64,), (67,)]
        assert [float(event.beat.as_beats()) for event in sheet.score.events] == [0.0, 4.0, 8.0]

    def test_constructor_accepts_iterable_of_sheetmusic_instances(self):
        values = [
            SheetMusic(Note("C4"), tempo=96, time_signature=(3, 4)),
            SheetMusic(Note("D4"), tempo=96, time_signature=(3, 4)),
        ]

        sheet = SheetMusic(values, tempo=96, time_signature=(3, 4))

        assert isinstance(sheet.score, Score)
        assert [event.pitches for event in sheet.score.events] == [(60,), (62,)]
        assert [float(event.beat.as_beats()) for event in sheet.score.events] == [0.0, 3.0]

    def test_constructor_accepts_iterable_of_scales(self):
        sheet = SheetMusic([Scale("D", "major"), Scale("Bb", "major")])

        mimebundle = sheet._repr_mimebundle_()
        assert "image/svg+xml" in mimebundle
        assert mimebundle["image/svg+xml"].count("<svg") == 1
        assert mimebundle["image/svg+xml"].count('class="key-accidental"') == 4
        assert mimebundle["image/svg+xml"].count('class="scale-label"') == 2
        assert "D Major" in mimebundle["image/svg+xml"]
        assert "Bb Major" in mimebundle["image/svg+xml"]

    def test_constructor_rejects_non_renderable_iterable_values(self):
        with pytest.raises(TypeError, match="not Sequenceable"):
            SheetMusic(["C4", "D4"])

    def test_constructor_rejects_non_sequenceable_values(self):
        with pytest.raises(TypeError, match="not Sequenceable"):
            SheetMusic({"bad": "payload"})

    def test_constructor_accepts_direct_scale_source(self):
        sheet = SheetMusic(Scale("C", "major"))

        assert isinstance(sheet.score, Score)
        assert len(sheet.score.events) == 8

    def test_constructor_accepts_explicit_clef_enum(self):
        sheet = SheetMusic(Note("E2"), clef=SheetClef.BASS)

        assert sheet.clef is SheetClef.BASS

    def test_constructor_rejects_invalid_clef_value(self):
        with pytest.raises(ValueError, match="Invalid clef"):
            SheetMusic(Note("C4"), clef="alto")

    @pytest.mark.parametrize(
        "source",
        (
            Degree(1),
        ),
    )
    def test_constructor_rejects_non_sequenceable_theory_types(self, source):
        with pytest.raises(TypeError, match="not Sequenceable"):
            SheetMusic(source)


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

    def test_svg_renders_tempo_only_for_score_sources(self, tmp_path: Path):
        score_sheet = SheetMusic(Score.from_sequenceable(Note("C4"), tempo=104))
        note_sheet = SheetMusic(Note("C4"), tempo=104)

        score_content = score_sheet.to_file(tmp_path / "score_source.svg").read_text(encoding="utf-8")
        note_content = note_sheet.to_file(tmp_path / "note_source.svg").read_text(encoding="utf-8")

        assert "tempo 104" in score_content
        assert "tempo 104" not in note_content

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

    def test_to_file_renders_key_signature_from_pentatonic_minor_scale(self, tmp_path: Path):
        sequence = Sequence((
            (Note("G4"), 1),
            (Note("Bb4"), 1),
            (Note("D5"), 1),
        ))

        output_path = SheetMusic(
            sequence,
            scale=Scale("G", "pentatonic_minor"),
        ).to_file(tmp_path / "with_pentatonic_minor_key_signature.svg")

        content = output_path.read_text(encoding="utf-8")
        assert content.count('class="key-accidental"') == 2
        assert "&#9837;" in content

    def test_scale_source_uses_its_own_global_scale_before_explicit_override(self):
        mimebundle = SheetMusic(
            Scale("G", "pentatonic_minor"),
            scale=Scale("C", "major"),
        )._repr_mimebundle_()

        assert mimebundle["image/svg+xml"].count('class="key-accidental"') == 2

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

    def test_auto_clef_selects_bass_when_median_unique_pitch_is_below_middle_c(self, tmp_path: Path):
        sequence = Sequence(((Note("E2"), 1), (Note("A2"), 1), (Note("B2"), 1)))

        output_path = SheetMusic(sequence).to_file(tmp_path / "auto_bass.svg")

        content = output_path.read_text(encoding="utf-8")
        assert "&#119074;" in content
        assert "&#119070;" not in content

    def test_auto_clef_uses_bass_when_median_unique_pitch_is_below_middle_c(self):
        sequence = Sequence(((Note("B2"), 1), (Note("C4"), 1)))

        sheet = SheetMusic(sequence)

        assert sheet.clef is SheetClef.BASS

    def test_auto_clef_uses_treble_when_median_unique_pitch_is_middle_c(self):
        sequence = Sequence(((Note("B3"), 1), (Note("C4"), 1), (Note("C#4"), 1)))

        sheet = SheetMusic(sequence)

        assert sheet.clef is SheetClef.TREBLE

    def test_auto_clef_uses_bass_for_even_median_between_b3_and_c4(self):
        sequence = Sequence(((Note("B3"), 1), (Note("C4"), 1)))

        sheet = SheetMusic(sequence)

        assert sheet.clef is SheetClef.BASS

    def test_auto_clef_defaults_to_treble_for_empty_scores(self):
        empty_score = Score(source="empty", metadata=ScoreMetadata(), events=())

        sheet = SheetMusic(empty_score)

        assert sheet.clef is SheetClef.TREBLE

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

    def test_to_file_dispatches_through_backend_adapter_map(self, tmp_path: Path, monkeypatch):
        sheet = SheetMusic(Note("C4"))

        def fake_svg_renderer(_sheet):
            return "<svg data-renderer=\"fake\"></svg>"

        monkeypatch.setattr(SheetMusic, "_RENDER_BACKEND_ADAPTERS", {"svg": fake_svg_renderer})

        output_path = sheet.to_file(tmp_path / "adapter.svg")

        content = output_path.read_text(encoding="utf-8")
        assert "data-renderer=\"fake\"" in content

    def test_to_file_raises_for_misconfigured_backend_adapter(self, tmp_path: Path, monkeypatch):
        sheet = SheetMusic(Note("C4"))
        monkeypatch.setattr(SheetMusic, "_RENDER_BACKEND_ADAPTERS", {"svg": "_missing_renderer"})

        with pytest.raises(RuntimeError, match="not callable"):
            sheet.to_file(tmp_path / "broken.svg")

    def test_configure_lilypond_backend_sets_svg_adapter(self, monkeypatch):
        def fake_renderer_factory(_path, *, crop, background):
            assert crop is True
            assert background == "white"
            return lambda _sheet: "<svg data-renderer=\"lilypond\"></svg>"

        monkeypatch.setattr(
            lilypond_backend,
            "make_lilypond_svg_renderer",
            fake_renderer_factory,
        )

        original_adapter = SheetMusic._RENDER_BACKEND_ADAPTERS.get("svg")
        try:
            lilypond_backend.configure_sheet_music_lilypond_backend("C:/tools/lilypond.exe")
            configured = SheetMusic._RENDER_BACKEND_ADAPTERS["svg"]
            assert callable(configured)
            assert configured(SheetMusic(Note("C4"))).startswith("<svg")
        finally:
            SheetMusic._RENDER_BACKEND_ADAPTERS["svg"] = original_adapter

    def test_lilypond_renderer_invokes_executable_and_reads_cropped_svg(self, monkeypatch):
        sheet = SheetMusic(Note("C4"))

        monkeypatch.setattr(lilypond_backend.shutil, "which", lambda _name: None)

        def fake_run(command, **kwargs):
            assert kwargs["capture_output"] is True
            assert kwargs["text"] is True
            assert kwargs["check"] is False
            assert "-dcrop" in command
            out_index = command.index("-o") + 1
            output_prefix = Path(command[out_index])
            normal_svg = output_prefix.parent / f"{output_prefix.name}.svg"
            normal_svg.write_text("<svg id=\"lilypond-normal\"/>", encoding="utf-8")
            cropped_svg = output_prefix.parent / f"{output_prefix.name}.cropped.svg"
            cropped_svg.write_text("<svg id=\"lilypond-cropped\"/>", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        monkeypatch.setattr(lilypond_backend.subprocess, "run", fake_run)

        renderer = lilypond_backend.make_lilypond_svg_renderer("C:/tools/lilypond.exe")
        rendered = renderer(sheet)
        assert "lilypond-cropped" in rendered
        assert 'class="chordelia-lilypond-bg"' in rendered

    def test_lilypond_renderer_can_disable_cropping(self, monkeypatch):
        sheet = SheetMusic(Note("C4"))

        monkeypatch.setattr(lilypond_backend.shutil, "which", lambda _name: None)

        def fake_run(command, **kwargs):
            assert kwargs["capture_output"] is True
            assert kwargs["text"] is True
            assert kwargs["check"] is False
            assert "-dcrop" not in command
            out_index = command.index("-o") + 1
            output_prefix = Path(command[out_index])
            svg_path = output_prefix.parent / f"{output_prefix.name}.svg"
            svg_path.write_text("<svg id=\"lilypond-uncropped\"/>", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        monkeypatch.setattr(lilypond_backend.subprocess, "run", fake_run)

        renderer = lilypond_backend.make_lilypond_svg_renderer(
            "C:/tools/lilypond.exe",
            crop=False,
        )
        rendered = renderer(sheet)
        assert "lilypond-uncropped" in rendered
        assert 'class="chordelia-lilypond-bg"' in rendered

    def test_lilypond_renderer_can_use_transparent_background(self, monkeypatch):
        sheet = SheetMusic(Note("C4"))

        monkeypatch.setattr(lilypond_backend.shutil, "which", lambda _name: None)

        def fake_run(command, **kwargs):
            assert kwargs["capture_output"] is True
            assert kwargs["text"] is True
            assert kwargs["check"] is False
            out_index = command.index("-o") + 1
            output_prefix = Path(command[out_index])
            svg_path = output_prefix.parent / f"{output_prefix.name}.cropped.svg"
            svg_path.write_text("<svg id=\"lilypond-transparent\"/>", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        monkeypatch.setattr(lilypond_backend.subprocess, "run", fake_run)

        renderer = lilypond_backend.make_lilypond_svg_renderer(
            "C:/tools/lilypond.exe",
            background="transparent",
        )
        rendered = renderer(sheet)

        assert "lilypond-transparent" in rendered
        assert 'class="chordelia-lilypond-bg"' not in rendered

    def test_lilypond_renderer_rejects_unsupported_background(self):
        with pytest.raises(ValueError, match="Unsupported background"):
            lilypond_backend.make_lilypond_svg_renderer(
                "C:/tools/lilypond.exe",
                background="cream",
            )

    def test_lilypond_source_for_iterable_scales_includes_measure_keys_and_labels(self):
        sheet = SheetMusic([Scale("D", "major"), Scale("Bb", "major")])

        source = lilypond_backend._sheet_to_lilypond_source(sheet)

        assert "\\set Staff.printKeyCancellation = ##f" in source
        assert "\\omit Staff.KeyCancellation" in source
        assert "\\set Staff.keyAlterations = #`((3 . ,SHARP) (0 . ,SHARP))" in source
        assert "\\set Staff.keyAlterations = #`((6 . ,FLAT) (2 . ,FLAT))" in source
        assert source.count("\\mark \\markup") >= 2
        assert "D Major" in source
        assert "Bb Major" in source

    def test_lilypond_source_emits_bass_clef_when_selected(self):
        source = lilypond_backend._sheet_to_lilypond_source(SheetMusic(Note("E2"), clef="bass"))

        assert "\\clef bass" in source

    def test_lilypond_source_keeps_treble_clef_when_explicitly_selected(self):
        source = lilypond_backend._sheet_to_lilypond_source(SheetMusic(Note("C4"), clef="treble"))

        assert "\\clef treble" in source

    def test_lilypond_source_for_pentatonic_minor_scale_uses_custom_key_alterations(self):
        sheet = SheetMusic([Scale("G", "pentatonic_minor")])

        source = lilypond_backend._sheet_to_lilypond_source(sheet)

        assert "\\set Staff.keyAlterations = #`((6 . ,FLAT) (2 . ,FLAT))" in source
        assert "G Minor Pentatonic" in source

    def test_lilypond_source_omits_tempo_for_non_score_wrappers(self):
        source = lilypond_backend._sheet_to_lilypond_source(SheetMusic(Note("C4"), tempo=101))

        assert "\\tempo 4 =" not in source

    def test_lilypond_source_keeps_tempo_for_score_sources(self):
        score = Score.from_sequenceable(Note("C4"), tempo=101)
        source = lilypond_backend._sheet_to_lilypond_source(SheetMusic(score))

        assert "\\tempo 4 = 101" in source

    def test_score_to_file_requires_score_instance(self, tmp_path: Path):
        with pytest.raises(TypeError, match="Score instance"):
            SheetMusic.score_to_file("not-a-score", tmp_path / "bad.svg")

    def test_score_to_file_matches_instance_output(self, tmp_path: Path):
        score = Score.from_sequenceable(Note("D4"))

        from_instance = SheetMusic(score).to_file(tmp_path / "instance.svg")
        from_classmethod = SheetMusic.score_to_file(score, tmp_path / "classmethod.svg")

        assert from_instance.read_text(encoding="utf-8") == from_classmethod.read_text(encoding="utf-8")

    def test_score_to_file_supports_explicit_clef_override(self, tmp_path: Path):
        score = Score.from_sequenceable(Note("E2"))

        output_path = SheetMusic.score_to_file(score, tmp_path / "bass_score.svg", clef="bass")

        content = output_path.read_text(encoding="utf-8")
        assert "&#119074;" in content

    def test_sequenceable_and_prebuilt_score_render_identical_svg(self, tmp_path: Path):
        sequence = Sequence(
            (
                (Note("C4"), 1),
                (Rest(), 1 / 2),
                (Chord("G4"), 1),
            )
        )
        score = Score.from_sequenceable(
            sequence,
            tempo=108,
            time_signature=(3, 4),
            key_signature="C",
            ppq=480,
        )

        direct_output = SheetMusic(
            sequence,
            tempo=108,
            time_signature=(3, 4),
            key_signature="C",
            ppq=480,
        ).to_file(tmp_path / "direct.svg")
        score_output = SheetMusic(score).to_file(tmp_path / "score.svg")

        assert direct_output.read_text(encoding="utf-8") == score_output.read_text(encoding="utf-8")

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

    def test_mixed_short_run_renders_partial_beam_hook(self, tmp_path: Path):
        sequence = Sequence(((Note("A3"), 1 / 2), (Note("B3"), 1 / 4), (Note("C4"), 1 / 2)))

        output_path = SheetMusic(sequence).to_file(tmp_path / "partial_beam_hook.svg")

        content = output_path.read_text(encoding="utf-8")
        assert 'class="note-beam note-beam-hook"' in content
        assert 'class="note-flag"' not in content

    def test_mid_run_isolated_hooks_choose_contextual_direction(self, tmp_path: Path):
        sequence = Sequence(
            (
                (Note("A3"), 1 / 2),
                (Note("B3"), 1 / 4),
                (Note("C4"), 1 / 2),
                (Note("D4"), 1 / 4),
                (Note("E4"), 1 / 2),
            )
        )

        output_path = SheetMusic(sequence).to_file(tmp_path / "contextual_hook_direction.svg")

        content = output_path.read_text(encoding="utf-8")
        hook_lines = [
            line for line in content.splitlines() if 'class="note-beam note-beam-hook"' in line
        ]
        assert len(hook_lines) >= 2

        directions: set[str] = set()
        for line in hook_lines:
            match = re.search(r'points="([^"]+)"', line)
            assert match is not None
            points = match.group(1).split()
            first_x = float(points[0].split(",", 1)[0])
            second_x = float(points[1].split(",", 1)[0])
            directions.add("right" if second_x > first_x else "left")

        assert "right" in directions
        assert "left" in directions

    def test_svg_baseline_contextual_hook_direction(self, tmp_path: Path):
        sequence = Sequence(
            (
                (Note("A3"), 1 / 2),
                (Note("B3"), 1 / 4),
                (Note("C4"), 1 / 2),
                (Note("D4"), 1 / 4),
                (Note("E4"), 1 / 2),
            )
        )

        output_path = SheetMusic(sequence).to_file(tmp_path / "contextual_hook_direction.svg")

        rendered = _normalize_newlines(output_path.read_text(encoding="utf-8"))
        expected = _read_baseline("contextual_hook_direction.svg")
        assert rendered == expected

    def test_svg_baseline_internal_rests_various_lengths(self, tmp_path: Path):
        sequence = Sequence(
            (
                (Note("C4"), 1 / 2),
                (Rest(), 1 / 4),
                (Note("D4"), 1 / 2),
                (Rest(), 3 / 4),
                (Note("E4"), 1),
                (Rest(), 2),
                (Note("F4"), 1 / 2),
            )
        )

        output_path = SheetMusic(sequence).to_file(tmp_path / "internal_rests_various_lengths.svg")

        rendered = _normalize_newlines(output_path.read_text(encoding="utf-8"))
        expected = _read_baseline("internal_rests_various_lengths.svg")
        assert rendered == expected

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
        assert ('class="note-flag"' in content) or ('class="note-beam"' in content)


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

    def test_repr_mimebundle_uses_backend_adapter_dispatch(self, monkeypatch):
        original_adapter = SheetMusic._RENDER_BACKEND_ADAPTERS.get("svg")
        try:
            monkeypatch.setattr(
                SheetMusic,
                "_RENDER_BACKEND_ADAPTERS",
                {
                    "svg": lambda _sheet: "<svg data-renderer=\"notebook-adapter\"></svg>",
                },
            )
            mimebundle = SheetMusic(Note("C4"))._repr_mimebundle_()
            assert "notebook-adapter" in mimebundle["image/svg+xml"]
        finally:
            SheetMusic._RENDER_BACKEND_ADAPTERS["svg"] = original_adapter


class TestSheetMusicDependencyIsolation:
    """Dependency-isolation boundaries for sheet core and notebook display helpers."""

    def test_repr_mimebundle_does_not_import_optional_notebook_or_midi_modules(self, monkeypatch):
        blocked_prefixes = (
            "chordelia.midi_playback",
            "IPython",
            "matplotlib",
            "music21",
            "pretty_midi",
            "mido",
        )
        original_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if any(name == prefix or name.startswith(f"{prefix}.") for prefix in blocked_prefixes):
                raise AssertionError(f"Unexpected optional dependency import attempted: {name}")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", guarded_import)

        mimebundle = SheetMusic(Note("C4"))._repr_mimebundle_()

        assert "image/svg+xml" in mimebundle
        assert "text/plain" in mimebundle
