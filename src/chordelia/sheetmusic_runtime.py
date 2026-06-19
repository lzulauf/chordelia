"""Generic runtime configuration and display-hook integration for SheetMusic rendering."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.scale_context import (
    get_global_scale_context,
    reset_global_scale_context,
    set_global_scale_context,
)
from chordelia.scales import Scale
from chordelia.sequences import Rest, Sequence
from chordelia.sheet_music import SheetClef, SheetMusic, _render_sheet_music_svg_backend

_UNSET = object()
_MISSING = object()


@dataclass(frozen=True, slots=True)
class SheetMusicRenderingConfig:
    """Global rendering configuration used by Sequenceable notebook hooks."""

    backend_name: str = "builtin_svg"
    format_name: str = "svg"
    clef: str = "auto"
    scale: Any = None
    backend_options: dict[str, Any] = field(default_factory=dict)


_DEFAULT_RENDERING_CONFIG = SheetMusicRenderingConfig()
_RENDERING_CONFIG: ContextVar[SheetMusicRenderingConfig] = ContextVar(
    "sheetmusic_rendering_config",
    default=_DEFAULT_RENDERING_CONFIG,
)

_HOOK_TARGET_TYPES = (Note, Chord, Sequence, Rest, Scale)
_ORIGINAL_MIMEBUNDLE_METHODS: dict[type[Any], Any] = {}


def _default_backend_applier(config: SheetMusicRenderingConfig) -> None:
    """Apply built-in backend and lazily load optional backend wiring when needed."""
    if config.backend_name == "builtin_svg":
        SheetMusic._RENDER_BACKEND_ADAPTERS[config.format_name] = _render_sheet_music_svg_backend
        return

    # Importing backend runtime registers optional backend appliers.
    import chordelia.sheetmusic_backends.runtime as _backend_runtime  # noqa: F401

    if _BACKEND_APPLIER is not _default_backend_applier:
        _BACKEND_APPLIER(config)
        return

    raise ValueError(
        "backend_name must be one of {'builtin_svg', 'lilypond'}, "
        f"got {config.backend_name!r}"
    )


_BACKEND_APPLIER: Callable[[SheetMusicRenderingConfig], None] = _default_backend_applier


def register_sheetmusic_backend_applier(
    applier: Callable[[SheetMusicRenderingConfig], None],
) -> None:
    """Register backend-specific adapter application logic."""
    global _BACKEND_APPLIER
    _BACKEND_APPLIER = applier


def get_sheetmusic_rendering_config() -> SheetMusicRenderingConfig:
    """Return the active sheet music rendering configuration."""
    current = _RENDERING_CONFIG.get()
    global_scale = get_global_scale_context()
    if current.scale is global_scale:
        return current
    return SheetMusicRenderingConfig(
        backend_name=current.backend_name,
        format_name=current.format_name,
        clef=current.clef,
        scale=global_scale,
        backend_options=dict(current.backend_options),
    )


def configure_sheetmusic_rendering(
    *,
    backend_name: str | None = None,
    format_name: str | None = None,
    clef: str | SheetClef | None = None,
    scale: Any = _UNSET,
    lilypond_executable: str | Path | None = None,
    crop: bool | None = None,
    background: str | None = None,
    enable_notebook_hooks: bool = False,
    hook_target_types: tuple[type[Any], ...] | None = None,
) -> SheetMusicRenderingConfig:
    """Update global sheet music rendering configuration and apply backend wiring."""

    current = get_sheetmusic_rendering_config()

    next_backend_name = current.backend_name if backend_name is None else backend_name
    next_format_name = (
        current.format_name
        if format_name is None
        else SheetMusic._normalize_format(format_name)
    )
    next_clef = current.clef if clef is None else _normalize_runtime_clef(clef)
    if scale is _UNSET:
        next_scale = get_global_scale_context()
    else:
        next_scale = set_global_scale_context(scale)

    next_options = dict(current.backend_options)
    if lilypond_executable is not None:
        next_options["lilypond_executable"] = str(lilypond_executable)
    if crop is not None:
        next_options["crop"] = crop
    if background is not None:
        next_options["background"] = background

    if backend_name == "builtin_svg":
        next_options = {}

    next_config = SheetMusicRenderingConfig(
        backend_name=next_backend_name,
        format_name=next_format_name,
        clef=next_clef,
        scale=next_scale,
        backend_options=next_options,
    )

    _BACKEND_APPLIER(next_config)
    _RENDERING_CONFIG.set(next_config)

    if enable_notebook_hooks:
        install_sequenceable_sheetmusic_display_hooks(target_types=hook_target_types)

    return next_config


def reset_sheetmusic_rendering_config() -> SheetMusicRenderingConfig:
    """Reset runtime rendering configuration and backend wiring to defaults."""

    reset_global_scale_context()
    default_config = SheetMusicRenderingConfig(scale=get_global_scale_context())
    _BACKEND_APPLIER(default_config)
    _RENDERING_CONFIG.set(default_config)
    return default_config


@contextmanager
def with_sheetmusic_rendering(
    *,
    backend_name: str | None = None,
    format_name: str | None = None,
    clef: str | SheetClef | None = None,
    scale: Any = _UNSET,
    lilypond_executable: str | Path | None = None,
    crop: bool | None = None,
    background: str | None = None,
) -> Iterator[SheetMusicRenderingConfig]:
    """Temporarily apply rendering configuration and restore previous state afterwards."""

    previous_config = get_sheetmusic_rendering_config()
    previous_adapters = dict(SheetMusic._RENDER_BACKEND_ADAPTERS)

    applied = configure_sheetmusic_rendering(
        backend_name=backend_name,
        format_name=format_name,
        clef=clef,
        scale=scale,
        lilypond_executable=lilypond_executable,
        crop=crop,
        background=background,
    )

    try:
        yield applied
    finally:
        set_global_scale_context(previous_config.scale)
        _RENDERING_CONFIG.set(previous_config)
        SheetMusic._RENDER_BACKEND_ADAPTERS.clear()
        SheetMusic._RENDER_BACKEND_ADAPTERS.update(previous_adapters)


def install_sequenceable_sheetmusic_display_hooks(
    *,
    target_types: tuple[type[Any], ...] | None = None,
) -> None:
    """Install notebook mimebundle hooks on Sequenceable concrete types."""

    types = _HOOK_TARGET_TYPES if target_types is None else target_types
    for type_ in types:
        if type_ in _ORIGINAL_MIMEBUNDLE_METHODS:
            continue

        original_method = getattr(type_, "_repr_mimebundle_", _MISSING)
        _ORIGINAL_MIMEBUNDLE_METHODS[type_] = original_method
        setattr(type_, "_repr_mimebundle_", _sequenceable_repr_mimebundle)


def uninstall_sequenceable_sheetmusic_display_hooks(
    *,
    target_types: tuple[type[Any], ...] | None = None,
) -> None:
    """Remove previously installed Sequenceable notebook mimebundle hooks."""

    if target_types is None:
        types = tuple(_ORIGINAL_MIMEBUNDLE_METHODS)
    else:
        types = target_types

    for type_ in types:
        original_method = _ORIGINAL_MIMEBUNDLE_METHODS.pop(type_, _UNSET)
        if original_method is _UNSET:
            continue
        if original_method is _MISSING:
            if hasattr(type_, "_repr_mimebundle_"):
                delattr(type_, "_repr_mimebundle_")
            continue
        setattr(type_, "_repr_mimebundle_", original_method)


def _sequenceable_repr_mimebundle(value, include=None, exclude=None):
    """Render sequenceable values through SheetMusic for notebook display."""

    del include, exclude
    config = get_sheetmusic_rendering_config()
    sheet = SheetMusic(value, clef=config.clef, scale=config.scale)
    return sheet._repr_mimebundle_()


def _normalize_runtime_clef(clef: str | SheetClef) -> str:
    """Normalize and validate runtime clef configuration values."""
    if isinstance(clef, SheetClef):
        return clef.value

    if isinstance(clef, str):
        normalized = clef.strip().lower()
        if normalized in {"treble", "bass", "auto"}:
            return normalized

    raise ValueError(
        f"Invalid clef {clef!r}. Expected one of: 'treble', 'bass', or 'auto'."
    )
