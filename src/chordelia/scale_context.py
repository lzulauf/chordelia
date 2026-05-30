"""Core runtime context helpers for scale and default-duration workflows."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from fractions import Fraction
import re
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from chordelia.rhythm import Duration
    from chordelia.scales import Scale


_UNSET = object()


@dataclass(frozen=True, slots=True)
class ChordeliaContext:
    """Scoped runtime defaults for APIs that accept contextual behavior."""

    scale: Scale | None = None
    default_note_duration: Duration | None = None


_DEFAULT_CONTEXT = ChordeliaContext()
_CHORDELIA_CONTEXT: ContextVar[ChordeliaContext] = ContextVar(
    "chordelia_runtime_context",
    default=_DEFAULT_CONTEXT,
)


def coerce_default_note_duration_value(value: Duration | int | float | Fraction | None) -> Duration | None:
    """Coerce supported default-duration inputs into beat/time Duration values."""
    from chordelia.rhythm import Duration

    if value is None:
        return None
    if isinstance(value, Duration):
        if value.mode == "note_fraction":
            return Duration.from_beats(value.as_beats(), None)
        return value
    if isinstance(value, (int, float, Fraction)) and not isinstance(value, bool):
        return Duration.from_beats(value, None)
    raise TypeError(
        "default note duration context must be Duration, int, float, Fraction, or None; "
        f"got {type(value).__name__}"
    )


def coerce_scale_context_value(value: Scale | str | None) -> Scale | None:
    """Coerce supported global scale context inputs into a Scale instance."""
    from chordelia.scales import Scale

    if value is None:
        return None
    if isinstance(value, Scale):
        return value
    if isinstance(value, str):
        return _scale_from_string(value)
    raise TypeError(f"scale context must be Scale, str, or None; got {type(value).__name__}")


def get_chordelia_context() -> ChordeliaContext:
    """Return the active runtime context for the current logical scope."""
    return _CHORDELIA_CONTEXT.get()


def set_chordelia_context(
    *,
    scale: Scale | str | None | object = _UNSET,
    default_note_duration: Duration | int | float | Fraction | None | object = _UNSET,
) -> ChordeliaContext:
    """Set runtime context values with sparse overrides and return applied context."""
    current = get_chordelia_context()

    updates: dict[str, Any] = {}
    if scale is not _UNSET:
        updates["scale"] = coerce_scale_context_value(scale)
    if default_note_duration is not _UNSET:
        updates["default_note_duration"] = coerce_default_note_duration_value(default_note_duration)

    next_context = replace(current, **updates) if updates else current
    _CHORDELIA_CONTEXT.set(next_context)
    return next_context


def reset_chordelia_context() -> None:
    """Reset all runtime context defaults to their baseline values."""
    _CHORDELIA_CONTEXT.set(_DEFAULT_CONTEXT)


@contextmanager
def with_chordelia_context(
    *,
    scale: Scale | str | None | object = _UNSET,
    default_note_duration: Duration | int | float | Fraction | None | object = _UNSET,
) -> Iterator[ChordeliaContext]:
    """Temporarily apply sparse runtime context overrides and restore previous state."""
    previous = get_chordelia_context()
    applied = set_chordelia_context(
        scale=scale,
        default_note_duration=default_note_duration,
    )
    try:
        yield applied
    finally:
        _CHORDELIA_CONTEXT.set(previous)


def get_global_scale_context() -> Scale | None:
    """Return the active global scale context for the current logical context."""
    return get_chordelia_context().scale


def set_global_scale_context(scale: Scale | str | None) -> Scale | None:
    """Set and return the active global scale context."""
    return set_chordelia_context(scale=scale).scale


def reset_global_scale_context() -> None:
    """Clear only the active global scale context value."""
    set_chordelia_context(scale=None)


@contextmanager
def with_global_scale_context(scale: Scale | str | None) -> Iterator[Scale | None]:
    """Temporarily apply a global scale context and restore previous state."""
    with with_chordelia_context(scale=scale) as applied:
        yield applied.scale


def get_default_note_duration_context() -> Duration | None:
    """Return the active default note duration for current logical context."""
    return get_chordelia_context().default_note_duration


def _scale_from_string(text: str) -> Scale:
    """Parse compact scale strings like 'D', 'Bb', 'Am', or 'E minor'."""
    from chordelia.scales import Scale

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
