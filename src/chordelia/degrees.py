"""
Degree value object and coercion helpers.

This module provides first-class support for scale/chord/interval degree inputs,
including integer and Roman numeral forms with optional accidental prefixes.
"""

from __future__ import annotations

import re
from typing import Literal, TypeAlias
from chordelia.accidentals import Accidental

RomanCase: TypeAlias = Literal["upper", "lower", "preserve", "auto"]

_DEGREE_NUMERIC_RE = re.compile(r"^(?P<acc>[#b]{0,2})(?P<number>\d+)$")
_DEGREE_ROMAN_RE = re.compile(
    r"^(?P<acc>[#b]{0,2})(?P<roman>[IVXLCDMivxlcdm]+)(?P<dim>[°o]?)(?P<suffix>\d*)$"
)

_ROMAN_VALUES = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}


class Degree:
    """
    Immutable value object representing a musical degree.

    Degree stores a numeric ordinal and optional accidental offset. When created
    from Roman numerals, it also preserves case metadata for contextual APIs.
    """

    __slots__ = (
        "_number",
        "_accidental",
        "_parsed_case",
        "_is_roman",
        "_had_diminished_symbol",
        "_source_roman",
    )

    def __init__(
        self,
        number: int,
        accidental: Accidental | int | str = 0,
        *,
        parsed_case: Literal["upper", "lower", "mixed", "none"] = "none",
        is_roman: bool = False,
        had_diminished_symbol: bool = False,
        source_roman: str | None = None,
    ):
        if number < 1:
            raise ValueError(f"Degree number must be >= 1, got {number}")
        accidental = Accidental.coerce(accidental)
        if parsed_case not in {"upper", "lower", "mixed", "none"}:
            raise ValueError(
                "parsed_case must be one of: 'upper', 'lower', 'mixed', 'none'"
            )
        if source_roman is not None and not is_roman:
            raise ValueError("source_roman is only valid when is_roman is True")

        self._number = number
        self._accidental = accidental
        self._parsed_case = parsed_case
        self._is_roman = is_roman
        self._had_diminished_symbol = had_diminished_symbol
        self._source_roman = source_roman

    @classmethod
    def coerce(cls, value: "DegreeLike") -> "Degree":
        """Coerce DegreeLike input into a Degree."""
        if isinstance(value, Degree):
            return value
        if isinstance(value, int):
            return cls(value)
        if isinstance(value, str):
            return cls.from_string(value)

        raise ValueError(
            "Degree value must be Degree, int, or str. "
            "Examples: 1, 'ii', 'bIII', '#iv', 'V7'."
        )

    @classmethod
    def from_string(cls, text: str) -> "Degree":
        """Create a Degree from numeric or Roman text forms."""
        normalized = text.strip()
        if not normalized:
            raise ValueError(
                "Degree string cannot be empty. "
                "Examples: '1', 'ii', 'bIII', '#iv', 'V7'."
            )

        if match := _DEGREE_NUMERIC_RE.match(normalized):
            accidental = Accidental.from_string(match.group("acc"))
            number = int(match.group("number"))
            return cls(number, accidental)

        if match := _DEGREE_ROMAN_RE.match(normalized):
            accidental = Accidental.from_string(match.group("acc"))
            roman = match.group("roman")
            diminished_symbol = match.group("dim")

            number = _roman_to_int(roman)
            if roman.isupper():
                parsed_case: Literal["upper", "lower", "mixed", "none"] = "upper"
            elif roman.islower():
                parsed_case = "lower"
            else:
                parsed_case = "mixed"

            return cls(
                number,
                accidental,
                parsed_case=parsed_case,
                is_roman=True,
                had_diminished_symbol=bool(diminished_symbol),
                source_roman=roman,
            )

        raise ValueError(
            f"Invalid degree string: {text!r}. "
            "Accepted examples: 1, 2, 3, I, ii, bIII, #iv, V7, vii°."
        )

    @property
    def number(self) -> int:
        """The numeric degree ordinal (1-based)."""
        return self._number

    @property
    def accidental(self) -> Accidental:
        """Canonical accidental enum member."""
        return self._accidental

    @property
    def accidental_offset(self) -> int:
        """Accidental semitone offset for arithmetic workflows."""
        return self._accidental.to_offset()

    @property
    def is_roman(self) -> bool:
        """Whether the input was parsed from Roman notation."""
        return self._is_roman

    @property
    def roman_case(self) -> Literal["upper", "lower", "mixed", "none"]:
        """Parsed Roman case metadata for contextual APIs."""
        return self._parsed_case

    @property
    def had_diminished_symbol(self) -> bool:
        """Whether the parsed form included a diminished marker (for example vii°)."""
        return self._had_diminished_symbol

    @property
    def has_alteration(self) -> bool:
        """Whether this degree has an accidental prefix."""
        return self.accidental_offset != 0

    @property
    def functional_hint(self) -> Literal["major", "minor_or_diminished", "diminished"] | None:
        """
        Return a context hint derived from Roman input style.

        The hint is only used by context-aware APIs (for example harmonization).
        """
        if self._had_diminished_symbol:
            return "diminished"
        if self._parsed_case == "upper":
            return "major"
        if self._parsed_case == "lower":
            return "minor_or_diminished"
        return None

    def to_int(self) -> int:
        """Return the numeric ordinal of this degree."""
        return self._number

    def shift(self, steps: int, *, span: int = 7, wrap: bool = True) -> "Degree":
        """Shift this degree by diatonic steps.

        Args:
            steps: Signed diatonic step displacement.
            span: Active degree span used for wrapping behavior.
            wrap: When True, normalize into 1..span; when False keep absolute ordinals.
        """
        if not isinstance(steps, int) or isinstance(steps, bool):
            raise TypeError(f"steps must be an int, got {type(steps).__name__}")
        if not isinstance(span, int) or isinstance(span, bool):
            raise TypeError(f"span must be an int, got {type(span).__name__}")
        if span < 1:
            raise ValueError(f"span must be >= 1, got {span}")
        if not isinstance(wrap, bool):
            raise TypeError(f"wrap must be a bool, got {type(wrap).__name__}")

        if wrap:
            start_index = self._number - 1
            shifted_number = ((start_index + steps) % span) + 1
        else:
            shifted_number = self._number + steps
            if shifted_number < 1:
                raise ValueError(
                    "Degree.shift without wrap requires resulting ordinal >= 1, "
                    f"got {shifted_number}"
                )

        source_roman = None
        if self._is_roman and self._parsed_case in {"upper", "lower"}:
            source_roman = _int_to_roman(shifted_number)
            if self._parsed_case == "lower":
                source_roman = source_roman.lower()

        return Degree(
            shifted_number,
            accidental=self._accidental,
            parsed_case=self._parsed_case,
            is_roman=self._is_roman,
            had_diminished_symbol=self._had_diminished_symbol,
            source_roman=source_roman,
        )

    def to_roman(self, case: RomanCase = "upper") -> str:
        """Convert this degree to Roman notation."""
        if case not in {"upper", "lower", "preserve", "auto"}:
            raise ValueError(
                "case must be one of: 'upper', 'lower', 'preserve', 'auto'"
            )

        roman_upper = _int_to_roman(self._number)
        if case == "upper":
            roman = roman_upper
        elif case == "lower":
            roman = roman_upper.lower()
        elif case == "preserve":
            if self._source_roman is not None:
                roman = self._source_roman
            elif self._parsed_case == "lower":
                roman = roman_upper.lower()
            else:
                roman = roman_upper
        else:
            # Without richer harmonic context, auto defaults to uppercase.
            roman = roman_upper

        dim_suffix = "°" if self._had_diminished_symbol else ""
        return f"{self._accidental.to_symbol()}{roman}{dim_suffix}"

    def __int__(self) -> int:
        return self.to_int()

    def __str__(self) -> str:
        if self._is_roman:
            return self.to_roman(case="preserve")
        return f"{self._accidental.to_symbol()}{self._number}"

    def __repr__(self) -> str:
        return (
            f"Degree(number={self._number}, accidental={self.accidental_offset}, "
            f"roman_case={self._parsed_case!r}, is_roman={self._is_roman})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Degree):
            return False
        return (
            self._number == other._number
            and self.accidental_offset == other.accidental_offset
        )

    def __hash__(self) -> int:
        return hash((self._number, self.accidental_offset))


DegreeLike: TypeAlias = Degree | int | str

def _roman_to_int(text: str) -> int:
    total = 0
    previous = 0
    for symbol in reversed(text.upper()):
        try:
            value = _ROMAN_VALUES[symbol]
        except KeyError as error:
            raise ValueError(f"Invalid Roman numeral symbol: {symbol!r}") from error

        if value < previous:
            total -= value
        else:
            total += value
            previous = value

    if total < 1:
        raise ValueError(f"Invalid Roman numeral: {text!r}")
    return total


def _int_to_roman(number: int) -> str:
    if number < 1:
        raise ValueError(f"Roman conversion requires number >= 1, got {number}")

    values = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )

    remainder = number
    parts: list[str] = []
    for value, roman in values:
        while remainder >= value:
            parts.append(roman)
            remainder -= value

    return "".join(parts)
