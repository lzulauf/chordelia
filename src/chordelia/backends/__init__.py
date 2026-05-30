"""Compatibility shim for legacy backend imports."""

from chordelia.sheetmusic_backends import (
    configure_sheet_music_lilypond_backend,
    make_lilypond_svg_renderer,
)

__all__ = [
    "configure_sheet_music_lilypond_backend",
    "make_lilypond_svg_renderer",
]
