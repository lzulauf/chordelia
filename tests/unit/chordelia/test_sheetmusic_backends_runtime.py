"""Tests for SheetMusic runtime backend/display integration hooks."""

import pytest

import chordelia.sheetmusic_backends.runtime as backend_runtime
import chordelia.sheetmusic_runtime as runtime
from chordelia.notes import Note
from chordelia.scale_context import (
    get_global_scale_context,
    set_global_scale_context,
)
from chordelia.scales import Scale
from chordelia.sheet_music import SheetMusic


pytestmark = pytest.mark.usefixtures(
    "restore_sheetmusic_runtime_rendering_config_state",
    "reset_global_scale_context_state",
    "restore_sheetmusic_backend_adapters_state",
)


class TestSheetMusicRuntimeConfig:
    """Global rendering context and backend wiring behavior."""

    def test_configure_sheetmusic_rendering_updates_scale(self):
        config = runtime.configure_sheetmusic_rendering(scale="D")

        assert isinstance(config.scale, Scale)
        assert str(config.scale.root) == "D"
        assert str(get_global_scale_context().root) == "D"
        assert str(runtime.get_sheetmusic_rendering_config().scale.root) == "D"

    def test_runtime_config_reads_global_scale_context(self):
        set_global_scale_context("F")

        config = runtime.get_sheetmusic_rendering_config()

        assert isinstance(config.scale, Scale)
        assert str(config.scale.root) == "F"

    def test_configure_sheetmusic_rendering_updates_clef(self):
        config = runtime.configure_sheetmusic_rendering(clef="bass")

        assert config.clef == "bass"
        assert runtime.get_sheetmusic_rendering_config().clef == "bass"

    def test_configure_sheetmusic_rendering_rejects_invalid_clef(self):
        with pytest.raises(ValueError, match="Invalid clef"):
            runtime.configure_sheetmusic_rendering(clef="alto")

    def test_with_sheetmusic_rendering_restores_previous_state(self):
        runtime.configure_sheetmusic_rendering(scale="C")

        with runtime.with_sheetmusic_rendering(scale="F"):
            assert str(runtime.get_sheetmusic_rendering_config().scale.root) == "F"

        assert str(runtime.get_sheetmusic_rendering_config().scale.root) == "C"

    def test_configure_sheetmusic_rendering_lilypond_delegates_backend_setup(self, monkeypatch):
        captured = {}

        def fake_configure_lilypond(executable, *, format_name, crop, background):
            captured["executable"] = executable
            captured["format_name"] = format_name
            captured["crop"] = crop
            captured["background"] = background

        monkeypatch.setattr(backend_runtime, "configure_sheet_music_lilypond_backend", fake_configure_lilypond)

        config = runtime.configure_sheetmusic_rendering(
            backend_name="lilypond",
            lilypond_executable="C:/tools/lilypond.exe",
            crop=False,
        )

        assert config.backend_name == "lilypond"
        assert captured == {
            "executable": "C:/tools/lilypond.exe",
            "format_name": "svg",
            "crop": False,
            "background": "white",
        }

    def test_configure_sheetmusic_rendering_lilypond_allows_transparent_background(self, monkeypatch):
        captured = {}

        def fake_configure_lilypond(executable, *, format_name, crop, background):
            captured["executable"] = executable
            captured["format_name"] = format_name
            captured["crop"] = crop
            captured["background"] = background

        monkeypatch.setattr(backend_runtime, "configure_sheet_music_lilypond_backend", fake_configure_lilypond)

        config = runtime.configure_sheetmusic_rendering(
            backend_name="lilypond",
            lilypond_executable="C:/tools/lilypond.exe",
            background="transparent",
        )

        assert config.backend_options["background"] == "transparent"
        assert captured["background"] == "transparent"


class TestSequenceableDisplayHooks:
    """Startup-installable notebook display hooks for Sequenceable types."""

    def test_install_sequenceable_hooks_renders_note_as_sheetmusic(self):
        runtime.configure_sheetmusic_rendering(scale="D")
        runtime.install_sequenceable_sheetmusic_display_hooks(target_types=(Note,))

        mimebundle = Note("D4")._repr_mimebundle_()

        assert "image/svg+xml" in mimebundle
        assert "text/plain" in mimebundle
        assert mimebundle["image/svg+xml"].count('class="key-accidental"') == 2

    def test_configure_sheetmusic_rendering_can_install_hooks(self):
        config = runtime.configure_sheetmusic_rendering(
            scale="Bb",
            enable_notebook_hooks=True,
            hook_target_types=(Note,),
        )

        mimebundle = Note("Bb4")._repr_mimebundle_()

        assert isinstance(config.scale, Scale)
        assert str(config.scale.root) == "Bb"
        assert "image/svg+xml" in mimebundle
        assert mimebundle["image/svg+xml"].count('class="key-accidental"') == 2

    def test_install_sequenceable_hooks_renders_scale_as_sheetmusic(self):
        runtime.configure_sheetmusic_rendering(scale="C")
        runtime.install_sequenceable_sheetmusic_display_hooks(target_types=(Scale,))

        mimebundle = Scale("C", "major")._repr_mimebundle_()

        assert "image/svg+xml" in mimebundle
        assert "text/plain" in mimebundle

    def test_scale_display_uses_wrapped_scale_over_global_scale_context(self):
        runtime.configure_sheetmusic_rendering(scale="C")
        runtime.install_sequenceable_sheetmusic_display_hooks(target_types=(Scale,))

        mimebundle = Scale("G", "pentatonic_minor")._repr_mimebundle_()

        assert mimebundle["image/svg+xml"].count('class="key-accidental"') == 2

    def test_configure_sheetmusic_rendering_hook_install_is_idempotent(self):
        runtime.configure_sheetmusic_rendering(
            enable_notebook_hooks=True,
            hook_target_types=(Note,),
        )
        runtime.configure_sheetmusic_rendering(
            scale="D",
            enable_notebook_hooks=True,
            hook_target_types=(Note,),
        )

        mimebundle = Note("D4")._repr_mimebundle_()
        assert "image/svg+xml" in mimebundle

    def test_sequenceable_hooks_respect_configured_clef(self):
        runtime.configure_sheetmusic_rendering(clef="treble")
        runtime.install_sequenceable_sheetmusic_display_hooks(target_types=(Note,))

        mimebundle = Note("E2")._repr_mimebundle_()

        assert "&#119070;" in mimebundle["image/svg+xml"]
        assert "&#119074;" not in mimebundle["image/svg+xml"]

    def test_sequenceable_hooks_default_to_auto_clef_when_unspecified(self):
        runtime.configure_sheetmusic_rendering()
        runtime.install_sequenceable_sheetmusic_display_hooks(target_types=(Note,))

        mimebundle = Note("E2")._repr_mimebundle_()

        assert "&#119074;" in mimebundle["image/svg+xml"]

    def test_uninstall_sequenceable_hooks_restores_original_methods(self):
        had_original = hasattr(Note, "_repr_mimebundle_")
        original = getattr(Note, "_repr_mimebundle_", None)

        runtime.install_sequenceable_sheetmusic_display_hooks(target_types=(Note,))
        runtime.uninstall_sequenceable_sheetmusic_display_hooks(target_types=(Note,))

        if had_original:
            assert getattr(Note, "_repr_mimebundle_") is original
        else:
            assert not hasattr(Note, "_repr_mimebundle_")

    def test_sequenceable_hooks_follow_sheetmusic_backend_dispatch(self, monkeypatch):
        runtime.install_sequenceable_sheetmusic_display_hooks(target_types=(Note,))
        monkeypatch.setattr(
            SheetMusic,
            "_RENDER_BACKEND_ADAPTERS",
            {"svg": lambda _sheet: "<svg id=\"runtime-dispatch\"/>"},
        )

        mimebundle = Note("C4")._repr_mimebundle_()

        assert "runtime-dispatch" in mimebundle["image/svg+xml"]


class TestSheetMusicIterableRendering:
    """Notebook helper behavior for rendering iterable collections."""

    def test_sheetmusic_for_sequenceable_list(self):
        sheet = SheetMusic([Scale("C", "major"), Scale("D", "major")])

        mimebundle = sheet._repr_mimebundle_()

        assert "image/svg+xml" in mimebundle
        assert "text/plain" in mimebundle
        assert mimebundle["image/svg+xml"].count("<svg") == 1

    def test_sheetmusic_for_sheetmusic_list(self):
        sheets = [SheetMusic(Scale("C", "major")), SheetMusic(Scale("D", "major"))]

        sheet = SheetMusic(sheets)
        mimebundle = sheet._repr_mimebundle_()

        assert "image/svg+xml" in mimebundle
        assert mimebundle["image/svg+xml"].count("<svg") == 1

    def test_sheetmusic_iterable_to_file_writes_svg(self, tmp_path):
        sheet = SheetMusic([Scale("C", "major"), Scale("D", "major")])

        output_path = sheet.to_file(tmp_path / "iterable.svg")
        content = output_path.read_text(encoding="utf-8")

        assert output_path.suffix == ".svg"
        assert content.count("<svg") == 1

    def test_sheetmusic_iterable_to_file_rejects_non_svg(self, tmp_path):
        sheet = SheetMusic([Scale("C", "major")])

        with pytest.raises(ValueError, match="Supported formats: svg"):
            sheet.to_file(tmp_path / "iterable.html", format="html")

    def test_sheetmusic_rejects_non_sequenceable_string(self):
        with pytest.raises(TypeError, match="not Sequenceable"):
            SheetMusic("not-a-renderable-list")
