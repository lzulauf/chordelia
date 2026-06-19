"""Backend-specific wiring for sheet music runtime configuration."""

from __future__ import annotations

from chordelia.sheet_music import SheetMusic, _render_sheet_music_svg_backend
from chordelia.sheetmusic_backends.lilypond import configure_sheet_music_lilypond_backend
from chordelia.sheetmusic_runtime import (
    SheetMusicRenderingConfig,
    register_sheetmusic_backend_applier,
)


def _apply_backend(config: SheetMusicRenderingConfig) -> None:
    """Apply one backend selection to the SheetMusic adapter map."""

    if config.backend_name == "builtin_svg":
        SheetMusic._RENDER_BACKEND_ADAPTERS[config.format_name] = _render_sheet_music_svg_backend
        return

    if config.backend_name == "lilypond":
        executable = config.backend_options.get("lilypond_executable")
        if executable is None:
            raise ValueError(
                "lilypond_executable is required when backend_name='lilypond'"
            )
        configure_sheet_music_lilypond_backend(
            executable,
            format_name=config.format_name,
            crop=bool(config.backend_options.get("crop", True)),
            background=str(config.backend_options.get("background", "white")),
        )
        return

    raise ValueError(
        "backend_name must be one of {'builtin_svg', 'lilypond'}, "
        f"got {config.backend_name!r}"
    )


register_sheetmusic_backend_applier(_apply_backend)
