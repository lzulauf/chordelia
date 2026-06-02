"""SheetMusic backend adapters for optional rendering integrations."""

from chordelia.sheetmusic_backends.lilypond import (
    configure_sheet_music_lilypond_backend,
    make_lilypond_svg_renderer,
)
from chordelia.sheetmusic_backends.runtime import (
    SheetMusicRenderingConfig,
    configure_sheetmusic_rendering,
    get_sheetmusic_rendering_config,
    install_sequenceable_sheetmusic_display_hooks,
    reset_sheetmusic_rendering_config,
    uninstall_sequenceable_sheetmusic_display_hooks,
    with_sheetmusic_rendering,
)

__all__ = [
    "configure_sheet_music_lilypond_backend",
    "make_lilypond_svg_renderer",
    "SheetMusicRenderingConfig",
    "configure_sheetmusic_rendering",
    "get_sheetmusic_rendering_config",
    "install_sequenceable_sheetmusic_display_hooks",
    "reset_sheetmusic_rendering_config",
    "uninstall_sequenceable_sheetmusic_display_hooks",
    "with_sheetmusic_rendering",
]
