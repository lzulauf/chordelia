"""Core global scale context helpers for diatonic workflows."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import re
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from chordelia.scales import Scale


_GLOBAL_SCALE_CONTEXT: ContextVar[Any | None] = ContextVar(
    "chordelia_global_scale_context",
    default=None,
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


def get_global_scale_context() -> Scale | None:
    """Return the active global scale context for the current logical context."""
    return _GLOBAL_SCALE_CONTEXT.get()


def set_global_scale_context(scale: Scale | str | None) -> Scale | None:
    """Set and return the active global scale context."""
    coerced = coerce_scale_context_value(scale)
    _GLOBAL_SCALE_CONTEXT.set(coerced)
    return coerced


def reset_global_scale_context() -> None:
    """Clear the active global scale context."""
    _GLOBAL_SCALE_CONTEXT.set(None)


@contextmanager
def with_global_scale_context(scale: Scale | str | None) -> Iterator[Scale | None]:
    """Temporarily apply a global scale context and restore previous state."""
    previous = get_global_scale_context()
    applied = set_global_scale_context(scale)
    try:
        yield applied
    finally:
        _GLOBAL_SCALE_CONTEXT.set(previous)


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
