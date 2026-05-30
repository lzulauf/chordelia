"""Tests for SheetMusic runtime backend/display integration hooks."""

import pytest

import chordelia.sheetmusic_backends.runtime as runtime
from chordelia.notes import Note
from chordelia.scale_context import (
    get_global_scale_context,
    reset_global_scale_context,
    set_global_scale_context,
)
from chordelia.scales import Scale
from chordelia.sheet_music import SheetMusic


@pytest.fixture(autouse=True)
def _restore_runtime_state():
    """Keep runtime rendering state isolated across tests."""

    previous_config = runtime.get_sheetmusic_rendering_config()
    previous_adapters = dict(SheetMusic._RENDER_BACKEND_ADAPTERS)

    runtime.uninstall_sequenceable_sheetmusic_display_hooks()
    runtime.reset_sheetmusic_rendering_config()
    reset_global_scale_context()
    yield

    runtime.uninstall_sequenceable_sheetmusic_display_hooks()
    runtime._RENDERING_CONFIG.set(previous_config)  # type: ignore[attr-defined]
    set_global_scale_context(previous_config.scale)
    SheetMusic._RENDER_BACKEND_ADAPTERS.clear()
    SheetMusic._RENDER_BACKEND_ADAPTERS.update(previous_adapters)


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

    def test_with_sheetmusic_rendering_restores_previous_state(self):
        runtime.configure_sheetmusic_rendering(scale="C")

        with runtime.with_sheetmusic_rendering(scale="F"):
            assert str(runtime.get_sheetmusic_rendering_config().scale.root) == "F"

        assert str(runtime.get_sheetmusic_rendering_config().scale.root) == "C"

    def test_configure_sheetmusic_rendering_lilypond_delegates_backend_setup(self, monkeypatch):
        captured = {}

        def fake_configure_lilypond(executable, *, format_name, crop):
            captured["executable"] = executable
            captured["format_name"] = format_name
            captured["crop"] = crop

        monkeypatch.setattr(runtime, "configure_sheet_music_lilypond_backend", fake_configure_lilypond)

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
        }


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
