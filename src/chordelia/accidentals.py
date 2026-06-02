"""Canonical accidental enum and coercion helpers."""

from __future__ import annotations

from enum import Enum


class Accidental(Enum):
    """Finite accidental enum backed by semitone offsets."""

    DOUBLE_FLAT = -2
    FLAT = -1
    NATURAL = 0
    SHARP = 1
    DOUBLE_SHARP = 2

    @classmethod
    def coerce(cls, value: "Accidental | int | str") -> "Accidental":
        """Coerce an accidental input to an Accidental instance."""
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls.from_offset(value)
        if isinstance(value, str):
            return cls.from_string(value)

        raise ValueError(
            "Accidental must be Accidental, int, or str. "
            "Accepted examples: -1, 0, 1, 'b', '#', 'bb', '##', ''."
        )

    @classmethod
    def from_offset(cls, offset: int) -> "Accidental":
        """Create an accidental from semitone offset."""
        try:
            return cls(offset)
        except ValueError as err:
            raise ValueError(f"Accidental offset must be between -2 and 2, got {offset}") from err

    @classmethod
    def from_string(cls, text: str) -> "Accidental":
        """Create an accidental from symbol or natural aliases."""
        normalized = text.strip()
        if normalized in {"", "n", "N", "natural", "NATURAL"}:
            return cls.NATURAL

        if set(normalized) == {"#"}:
            return cls.from_offset(len(normalized))
        if set(normalized) == {"b"}:
            return cls.from_offset(-len(normalized))

        raise ValueError(
            f"Invalid accidental: {text!r}. Accepted examples: '', '#', '##', 'b', 'bb', 'natural'."
        )

    def to_offset(self) -> int:
        """Convert accidental to integer semitone offset."""
        return int(self.value)

    def to_symbol(self) -> str:
        """Convert accidental to symbolic text form."""
        offset = int(self.value)
        if offset == 0:
            return ""
        if offset > 0:
            return "#" * offset
        return "b" * (-offset)

    def __int__(self) -> int:
        return int(self.value)

    def __str__(self) -> str:
        return self.to_symbol()

    def __repr__(self) -> str:
        return f"Accidental({self.name}, offset={int(self.value)})"
