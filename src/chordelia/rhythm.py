"""
Musical rhythm and timing implementation with algorithmic duration calculations.

This module provides classes for representing musical time signatures, note durations,
tempo, and conversions between musical time and real time (milliseconds).
All calculations are done algorithmically for precision and efficiency.
"""

from enum import Enum
from decimal import Decimal, InvalidOperation
from typing import Optional, Union, Tuple, TypeAlias
from fractions import Fraction
import math


class NoteValue(Enum):
    """Enumeration of standard note duration values."""
    WHOLE = Fraction(1, 1)
    HALF = Fraction(1, 2)
    QUARTER = Fraction(1, 4)
    EIGHTH = Fraction(1, 8)
    SIXTEENTH = Fraction(1, 16)
    THIRTY_SECOND = Fraction(1, 32)
    SIXTY_FOURTH = Fraction(1, 64)
    
    # Dotted notes (1.5x original duration)
    DOTTED_WHOLE = Fraction(3, 2)
    DOTTED_HALF = Fraction(3, 4)
    DOTTED_QUARTER = Fraction(3, 8)
    DOTTED_EIGHTH = Fraction(3, 16)
    DOTTED_SIXTEENTH = Fraction(3, 32)
    
    # Triplet notes (2/3 of original duration)
    WHOLE_TRIPLET = Fraction(2, 3)
    HALF_TRIPLET = Fraction(1, 3)
    QUARTER_TRIPLET = Fraction(1, 6)
    EIGHTH_TRIPLET = Fraction(1, 12)
    SIXTEENTH_TRIPLET = Fraction(1, 24)

    def __str__(self) -> str:
        """String representation of note value."""
        names = {
            Fraction(1, 1): "whole",
            Fraction(1, 2): "half",
            Fraction(1, 4): "quarter",
            Fraction(1, 8): "eighth",
            Fraction(1, 16): "sixteenth",
            Fraction(1, 32): "thirty-second",
            Fraction(1, 64): "sixty-fourth",
            Fraction(3, 2): "dotted whole",
            Fraction(3, 4): "dotted half",
            Fraction(3, 8): "dotted quarter",
            Fraction(3, 16): "dotted eighth",
            Fraction(3, 32): "dotted sixteenth",
            Fraction(2, 3): "whole triplet",
            Fraction(1, 3): "half triplet",
            Fraction(1, 6): "quarter triplet",
            Fraction(1, 12): "eighth triplet",
            Fraction(1, 24): "sixteenth triplet",
        }
        return names.get(self.value, f"{self.value} note")


class Duration:
    """
    Represents a musical duration with precise fractional representation.
    
    This class is immutable for performance and safety - all arithmetic
    operations return new Duration instances.
    
    Can represent standard notes, dotted notes, triplets, and custom durations.
    
    Examples:
        Creating durations:
        >>> duration = Duration(NoteValue.QUARTER)
        >>> duration = Duration(Fraction(1, 4))  
        >>> duration = Duration("quarter")
        >>> duration = Duration(0.25)
        
        Duration arithmetic (returns new instances):
        >>> quarter = Duration("quarter")
        >>> dotted_quarter = quarter * Fraction(3, 2)  # 3/8 note
        >>> triplet = quarter * Fraction(2, 3)         # 1/6 note
        >>> half_length = quarter + quarter            # 1/2 note
        
        All operations preserve immutability - the original duration is never modified.
    """
    
    __slots__ = ('_mode', '_fraction', '_beats', '_seconds')

    _MODE_NOTE_FRACTION = 'note_fraction'
    _MODE_BEATS = 'beats'
    _MODE_SECONDS = 'seconds'
    
    def __init__(self, value: Union[NoteValue, Fraction, float, str]):
        """
        Initialize an immutable duration.
        
        Args:
            value: Note value, fraction, float, or string representation
                  String examples: "1/4", "quarter", "dotted quarter", "1/8 triplet"
        """
        if isinstance(value, NoteValue):
            fraction = value.value
        elif isinstance(value, (Fraction, float, int)):
            fraction = Fraction(value).limit_denominator()
        elif isinstance(value, str):
            fraction = self._parse_duration_string(value)
        else:
            raise ValueError(f"Invalid duration value: {value}")

        self._mode = self._MODE_NOTE_FRACTION
        self._fraction = fraction
        self._beats = None
        self._seconds = None

    @classmethod
    def _from_note_fraction(cls, fraction: Fraction) -> 'Duration':
        """Internal constructor for note-fraction mode."""
        instance = cls.__new__(cls)
        instance._mode = cls._MODE_NOTE_FRACTION
        instance._fraction = fraction
        instance._beats = None
        instance._seconds = None
        return instance

    @classmethod
    def _from_beats(cls, beats: Fraction) -> 'Duration':
        """Internal constructor for beat-count mode."""
        instance = cls.__new__(cls)
        instance._mode = cls._MODE_BEATS
        instance._fraction = None
        instance._beats = beats
        instance._seconds = None
        return instance

    @classmethod
    def _from_seconds(cls, seconds: Decimal) -> 'Duration':
        """Internal constructor for wall-clock seconds mode."""
        instance = cls.__new__(cls)
        instance._mode = cls._MODE_SECONDS
        instance._fraction = None
        instance._beats = None
        instance._seconds = seconds
        return instance

    @classmethod
    def from_beats(cls, numerator: Union[int, float, Fraction], denominator: Optional[int] = 1) -> 'Duration':
        """
        Create a beat-based duration.

        Args:
            numerator: Number of beats or beat numerator
            denominator: Optional beat denominator. When None, numerator is treated
                as whole beats.
        """
        if denominator is None:
            beats = Fraction(numerator).limit_denominator()
        else:
            if denominator <= 0:
                raise ValueError(f"Beat denominator must be positive, got {denominator}")
            beats = Fraction(numerator).limit_denominator() / denominator
        return cls._from_beats(beats)

    @classmethod
    def from_seconds(cls, seconds: Union[Decimal, float, int, str]) -> 'Duration':
        """Create a time-based duration in wall-clock seconds."""
        try:
            decimal_seconds = seconds if isinstance(seconds, Decimal) else Decimal(str(seconds))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"Invalid seconds value: {seconds!r}") from exc

        if decimal_seconds.is_nan() or decimal_seconds.is_infinite():
            raise ValueError(f"Invalid seconds value: {seconds!r}")

        return cls._from_seconds(decimal_seconds)

    @classmethod
    def from_milliseconds(cls, milliseconds: Union[Decimal, float, int, str]) -> 'Duration':
        """Create a time-based duration from milliseconds."""
        return cls.from_seconds((Decimal(str(milliseconds))) / Decimal("1000"))

    @property
    def mode(self) -> str:
        """Get the timing mode for this duration."""
        return self._mode

    @property
    def is_tempo_relative(self) -> bool:
        """True when this duration scales with tempo changes."""
        return self._mode in (self._MODE_NOTE_FRACTION, self._MODE_BEATS)
    
    def _parse_duration_string(self, duration_str: str) -> Fraction:
        """Parse a duration string into a fraction."""
        duration_str = duration_str.lower().strip()
        
        # Handle fraction strings like "1/4", "3/8"
        if '/' in duration_str and not any(word in duration_str for word in ['quarter', 'eighth', 'half', 'whole']):
            return Fraction(duration_str)
        
        # Handle named durations
        duration_map = {
            'whole': Fraction(1, 1),
            'half': Fraction(1, 2),
            'quarter': Fraction(1, 4),
            'eighth': Fraction(1, 8),
            'sixteenth': Fraction(1, 16),
            'thirty-second': Fraction(1, 32),
            'sixty-fourth': Fraction(1, 64),
        }
        
        # Handle dotted notes
        if 'dotted' in duration_str:
            base_duration = duration_str.replace('dotted', '').strip()
            if base_duration in duration_map:
                return duration_map[base_duration] * Fraction(3, 2)
        
        # Handle triplets
        if 'triplet' in duration_str:
            base_duration = duration_str.replace('triplet', '').strip()
            if base_duration in duration_map:
                return duration_map[base_duration] * Fraction(2, 3)
        
        # Handle standard durations
        if duration_str in duration_map:
            return duration_map[duration_str]
        
        raise ValueError(f"Cannot parse duration string: {duration_str}")
    
    @property
    def fraction(self) -> Fraction:
        """Get the note-fraction representation of this duration."""
        if self._mode != self._MODE_NOTE_FRACTION:
            raise ValueError("fraction is only available for note-fraction durations")
        return self._fraction

    def as_beats(self, beat_unit: int = 4) -> Fraction:
        """
        Convert this duration to beat units.

        Args:
            beat_unit: Denominator note value for one beat (4=quarter, 8=eighth)
        """
        if self._mode == self._MODE_BEATS:
            return self._beats
        if self._mode == self._MODE_NOTE_FRACTION:
            if beat_unit <= 0:
                raise ValueError("beat_unit must be positive")
            return self._fraction / Fraction(1, beat_unit)
        raise ValueError("Cannot convert time-based durations to beats without tempo context")

    def as_seconds(self) -> Decimal:
        """Return this duration in wall-clock seconds mode."""
        if self._mode != self._MODE_SECONDS:
            raise ValueError("as_seconds is only available for time-based durations")
        return self._seconds
    
    @property
    def decimal(self) -> float:
        """Get the decimal representation of this duration."""
        return float(self._raw_value())
    
    def beats_in_measure(self, time_signature: 'TimeSignature') -> Fraction:
        """
        Calculate how many beats this duration represents in a given time signature.
        
        Args:
            time_signature: The time signature context
            
        Returns:
            Number of beats as a fraction
        """
        # Duration as fraction of a whole note
        # In 4/4 time, a quarter note (1/4) represents 1 beat
        # Beat unit fraction: 1/4 for quarter note beats, 1/8 for eighth note beats
        if self._mode == self._MODE_BEATS:
            return self._beats
        if self._mode == self._MODE_NOTE_FRACTION:
            beat_unit_fraction = Fraction(1, time_signature.beat_unit)
            return self._fraction / beat_unit_fraction
        raise ValueError("beats_in_measure is not defined for time-based durations")
    
    def to_milliseconds(self, bpm: float, time_signature: 'TimeSignature') -> float:
        """
        Convert this duration to milliseconds given a tempo and time signature.
        
        Args:
            bpm: Beats per minute (refers to the beat unit of the time signature)
            time_signature: The time signature context
            
        Returns:
            Duration in milliseconds
        """
        if self._mode == self._MODE_SECONDS:
            return float(self._seconds * Decimal("1000"))

        beat_units = self.beats_in_measure(time_signature)
        minutes = float(beat_units) / bpm
        return minutes * 60 * 1000
    
    def __add__(self, other: 'Duration') -> 'Duration':
        """Add two durations."""
        self._ensure_compatible(other, operation="add")
        if self._mode == self._MODE_NOTE_FRACTION:
            return Duration._from_note_fraction(self._fraction + other._fraction)
        if self._mode == self._MODE_BEATS:
            return Duration._from_beats(self._beats + other._beats)
        return Duration._from_seconds(self._seconds + other._seconds)
    
    def __sub__(self, other: 'Duration') -> 'Duration':
        """Subtract two durations."""
        self._ensure_compatible(other, operation="subtract")
        if self._mode == self._MODE_NOTE_FRACTION:
            return Duration._from_note_fraction(self._fraction - other._fraction)
        if self._mode == self._MODE_BEATS:
            return Duration._from_beats(self._beats - other._beats)
        return Duration._from_seconds(self._seconds - other._seconds)
    
    def __mul__(self, scalar: Union[int, float, Fraction]) -> 'Duration':
        """Multiply duration by a scalar."""
        if self._mode == self._MODE_NOTE_FRACTION:
            return Duration._from_note_fraction(self._fraction * scalar)
        if self._mode == self._MODE_BEATS:
            return Duration._from_beats(self._beats * scalar)
        return Duration._from_seconds(self._seconds * Decimal(str(scalar)))
    
    def __truediv__(self, scalar: Union[int, float, Fraction]) -> 'Duration':
        """Divide duration by a scalar."""
        if self._mode == self._MODE_NOTE_FRACTION:
            return Duration._from_note_fraction(self._fraction / scalar)
        if self._mode == self._MODE_BEATS:
            return Duration._from_beats(self._beats / scalar)
        return Duration._from_seconds(self._seconds / Decimal(str(scalar)))
    
    def __eq__(self, other: 'Duration') -> bool:
        """Check equality with another duration."""
        return (
            isinstance(other, Duration)
            and self._mode == other._mode
            and self._raw_value() == other._raw_value()
        )
    
    def __lt__(self, other: 'Duration') -> bool:
        """Compare if this duration is less than another."""
        self._ensure_compatible(other, operation="compare")
        return self._raw_value() < other._raw_value()

    def __le__(self, other: 'Duration') -> bool:
        """Compare if this duration is less than or equal to another."""
        return self == other or self < other

    def __gt__(self, other: 'Duration') -> bool:
        """Compare if this duration is greater than another."""
        return not self <= other

    def __ge__(self, other: 'Duration') -> bool:
        """Compare if this duration is greater than or equal to another."""
        return not self < other

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self._mode, self._raw_value()))
    
    def __str__(self) -> str:
        """String representation of duration."""
        if self._mode == self._MODE_BEATS:
            return f"{self._beats} beats"
        if self._mode == self._MODE_SECONDS:
            return f"{self._seconds} seconds"

        # Try to match common note values
        for note_value in NoteValue:
            if note_value.value == self._fraction:
                return str(note_value)
        
        # Fallback to fraction representation
        return f"{self._fraction} note"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        if self._mode == self._MODE_NOTE_FRACTION:
            return f"Duration({self._fraction})"
        if self._mode == self._MODE_BEATS:
            return f"Duration.from_beats({self._beats.numerator}, {self._beats.denominator})"
        return f"Duration.from_seconds('{self._seconds}')"

    def _ensure_compatible(self, other: 'Duration', *, operation: str) -> None:
        """Ensure two durations can be combined/computed together."""
        if not isinstance(other, Duration):
            raise TypeError(f"Can only {operation} Duration with Duration")
        if self._mode != other._mode:
            raise TypeError(
                f"Cannot {operation} durations with different timing modes: "
                f"{self._mode!r} and {other._mode!r}"
            )

    def _raw_value(self) -> Union[Fraction, Decimal]:
        """Return the underlying comparable numeric value for this mode."""
        if self._mode == self._MODE_NOTE_FRACTION:
            return self._fraction
        if self._mode == self._MODE_BEATS:
            return self._beats
        return self._seconds


TimelineLike: TypeAlias = Duration | NoteValue | int | float | Fraction


def context_beat_unit(
    time_signature: tuple[int, int] | None,
    *,
    default: int = 4,
) -> int:
    """Resolve denominator beat unit from an optional time signature."""
    if time_signature is None:
        return default
    if len(time_signature) != 2:
        raise ValueError("time_signature must be (numerator, denominator)")
    _numerator, denominator = time_signature
    if denominator <= 0:
        raise ValueError(f"time signature denominator must be > 0, got {denominator}")
    return denominator


def coerce_timeline_duration(
    value: TimelineLike,
    *,
    field_name: str,
    beat_unit: int = 4,
) -> Duration:
    """Coerce scheduling-boundary values into beat/time Duration modes."""
    if beat_unit <= 0:
        raise ValueError(f"beat_unit must be > 0, got {beat_unit}")

    if isinstance(value, Duration):
        if value.mode == "note_fraction":
            return Duration.from_beats(value.as_beats(beat_unit=beat_unit), None)
        return value

    if isinstance(value, NoteValue):
        return Duration.from_beats(value.value / Fraction(1, beat_unit), None)

    if isinstance(value, (int, float, Fraction)) and not isinstance(value, bool):
        return Duration.from_beats(value, None)

    raise TypeError(
        f"{field_name} must be Duration, NoteValue, int, float, or Fraction; "
        f"got {type(value).__name__}"
    )


class TimeSignature:
    """
    Represents a musical time signature.
    
    Handles common time signatures like 4/4, 3/4, 6/8, as well as complex signatures.
    """
    
    def __init__(self, beats_per_measure: int, beat_unit: int):
        """
        Initialize a time signature.
        
        Args:
            beats_per_measure: Number of beats per measure (numerator)
            beat_unit: Note value that gets one beat (denominator)
                      e.g., 4 for quarter note, 8 for eighth note
        """
        if beats_per_measure <= 0:
            raise ValueError("Beats per measure must be positive")
        if beat_unit <= 0 or (beat_unit & (beat_unit - 1)) != 0:
            raise ValueError("Beat unit must be a positive power of 2")
        
        self.beats_per_measure = beats_per_measure
        self.beat_unit = beat_unit
    
    @classmethod
    def from_string(cls, time_sig_str: str) -> 'TimeSignature':
        """
        Create a time signature from a string like "4/4" or "6/8".
        
        Args:
            time_sig_str: String representation like "4/4"
            
        Returns:
            TimeSignature object
        """
        if '/' not in time_sig_str:
            raise ValueError(f"Invalid time signature format: {time_sig_str}")
        
        try:
            numerator, denominator = time_sig_str.split('/')
            return cls(int(numerator), int(denominator))
        except ValueError:
            raise ValueError(f"Invalid time signature format: {time_sig_str}")
    
    @property
    def measure_duration(self) -> Duration:
        """Get the duration of one complete measure."""
        # Measure duration = beats_per_measure / beat_unit
        return Duration(Fraction(self.beats_per_measure, self.beat_unit))
    
    @property
    def beat_duration(self) -> Duration:
        """Get the duration of one beat."""
        return Duration(Fraction(1, self.beat_unit))
    
    def is_simple_time(self) -> bool:
        """Check if this is simple time (beats not grouped in threes)."""
        # Simple time: 2/4, 3/4, 4/4, etc. - beats are not subdivided into groups of 3
        # Compound time: 6/8, 9/8, 12/8, etc. - beats are subdivided into groups of 3
        return not self.is_compound_time()
    
    def is_compound_time(self) -> bool:
        """Check if this is compound time (beats divisible by 3, grouped in threes)."""
        # Compound time signatures have numerators divisible by 3 (except 3 itself)
        # and typically use eighth notes (8) as the beat unit
        return (self.beats_per_measure % 3 == 0 and 
                self.beats_per_measure > 3 and 
                self.beat_unit >= 8)
    
    def beats_to_measure_position(self, beat_number: float) -> Tuple[int, float]:
        """
        Convert a beat number to measure and beat within measure.
        
        Args:
            beat_number: Absolute beat number (0-based)
            
        Returns:
            Tuple of (measure_number, beat_within_measure)
        """
        measure_number = int(beat_number // self.beats_per_measure)
        beat_within_measure = beat_number % self.beats_per_measure
        return measure_number, beat_within_measure
    
    def __str__(self) -> str:
        """String representation of time signature."""
        return f"{self.beats_per_measure}/{self.beat_unit}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"TimeSignature({self.beats_per_measure}, {self.beat_unit})"
    
    def __eq__(self, other: 'TimeSignature') -> bool:
        """Check equality with another time signature."""
        return (isinstance(other, TimeSignature) and 
                self.beats_per_measure == other.beats_per_measure and
                self.beat_unit == other.beat_unit)


class Tempo:
    """
    Represents musical tempo with BPM and tempo markings.
    
    Provides conversions between BPM and traditional tempo markings.
    """
    
    # Traditional tempo markings with approximate BPM ranges
    TEMPO_MARKINGS = {
        'largo': (40, 60),
        'larghetto': (60, 66),
        'adagio': (66, 76),
        'andante': (76, 108),
        'moderato': (108, 120),
        'allegro': (120, 168),
        'presto': (168, 200),
        'prestissimo': (200, 250),
    }
    
    def __init__(self, bpm: float, marking: Optional[str] = None):
        """
        Initialize a tempo.
        
        Args:
            bpm: Beats per minute
            marking: Optional tempo marking (e.g., "allegro")
        """
        if bpm <= 0:
            raise ValueError("BPM must be positive")
        
        self.bpm = bpm
        self.marking = marking
    
    @classmethod
    def from_marking(cls, marking: str) -> 'Tempo':
        """
        Create a tempo from a traditional marking.
        
        Args:
            marking: Tempo marking like "allegro", "andante"
            
        Returns:
            Tempo object with average BPM for that marking
        """
        marking = marking.lower()
        if marking not in cls.TEMPO_MARKINGS:
            raise ValueError(f"Unknown tempo marking: {marking}")
        
        min_bpm, max_bpm = cls.TEMPO_MARKINGS[marking]
        avg_bpm = (min_bpm + max_bpm) / 2
        return cls(avg_bpm, marking)
    
    def beat_duration_ms(self) -> float:
        """Get the duration of one beat in milliseconds."""
        return 60000.0 / self.bpm  # 60 seconds * 1000 ms / bpm
    
    def duration_to_ms(self, duration: Duration, time_signature: TimeSignature) -> float:
        """
        Convert a musical duration to milliseconds.
        
        Args:
            duration: Musical duration
            time_signature: Time signature context
            
        Returns:
            Duration in milliseconds
        """
        return duration.to_milliseconds(self.bpm, time_signature)
    
    def ms_to_beats(self, milliseconds: float) -> float:
        """
        Convert milliseconds to number of beats.
        
        Args:
            milliseconds: Time in milliseconds
            
        Returns:
            Number of beats
        """
        return (milliseconds / 1000.0) * (self.bpm / 60.0)
    
    def get_suggested_marking(self) -> str:
        """Get the traditional tempo marking that best fits this BPM."""
        for marking, (min_bpm, max_bpm) in self.TEMPO_MARKINGS.items():
            if min_bpm <= self.bpm <= max_bpm:
                return marking
        
        if self.bpm < 40:
            return "very slow"
        else:
            return "very fast"
    
    def __str__(self) -> str:
        """String representation of tempo."""
        if self.marking:
            return f"{self.marking} (♩ = {self.bpm})"
        else:
            return f"♩ = {self.bpm}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Tempo({self.bpm}, {repr(self.marking)})"


class Beat:
    """
    Represents a specific beat position within a measure.
    
    Useful for tracking rhythmic positions and beat subdivisions.
    """
    
    def __init__(self, measure: int, beat: float, time_signature: TimeSignature):
        """
        Initialize a beat position.
        
        Args:
            measure: Measure number (0-based)
            beat: Beat within measure (0-based, can be fractional)
            time_signature: Time signature context
        """
        if measure < 0:
            raise ValueError("Measure must be non-negative")
        if beat < 0 or beat >= time_signature.beats_per_measure:
            raise ValueError(f"Beat must be between 0 and {time_signature.beats_per_measure}")
        
        self.measure = measure
        self.beat = beat
        self.time_signature = time_signature
    
    @property
    def absolute_beat(self) -> float:
        """Get the absolute beat number from the start."""
        return self.measure * self.time_signature.beats_per_measure + self.beat
    
    def to_milliseconds(self, tempo: Tempo) -> float:
        """
        Convert this beat position to milliseconds from the start.
        
        Args:
            tempo: Tempo context
            
        Returns:
            Time in milliseconds
        """
        return self.absolute_beat * tempo.beat_duration_ms()
    
    def add_duration(self, duration: Duration) -> 'Beat':
        """
        Add a duration to this beat position.
        
        Args:
            duration: Duration to add
            
        Returns:
            New Beat object at the resulting position
        """
        beats_to_add = float(duration.beats_in_measure(self.time_signature))
        new_absolute_beat = self.absolute_beat + beats_to_add
        
        new_measure, new_beat = self.time_signature.beats_to_measure_position(new_absolute_beat)
        return Beat(new_measure, new_beat, self.time_signature)
    
    def __str__(self) -> str:
        """String representation of beat."""
        return f"Measure {self.measure + 1}, Beat {self.beat + 1:.2f}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Beat({self.measure}, {self.beat}, {self.time_signature})"


# Convenience functions for common durations
def whole_note() -> Duration:
    """Create a whole note duration."""
    return Duration(NoteValue.WHOLE)

def half_note() -> Duration:
    """Create a half note duration."""
    return Duration(NoteValue.HALF)

def quarter_note() -> Duration:
    """Create a quarter note duration."""
    return Duration(NoteValue.QUARTER)

def eighth_note() -> Duration:
    """Create an eighth note duration."""
    return Duration(NoteValue.EIGHTH)

def sixteenth_note() -> Duration:
    """Create a sixteenth note duration."""
    return Duration(NoteValue.SIXTEENTH)

def dotted(duration: Duration) -> Duration:
    """Create a dotted version of a duration (1.5x length)."""
    return duration * Fraction(3, 2)

def triplet(duration: Duration) -> Duration:
    """Create a triplet version of a duration (2/3 length)."""
    return duration * Fraction(2, 3)


# Common time signatures
COMMON_TIME = TimeSignature(4, 4)  # 4/4
CUT_TIME = TimeSignature(2, 2)    # 2/2 (alla breve)
WALTZ_TIME = TimeSignature(3, 4)  # 3/4
COMPOUND_DUPLE = TimeSignature(6, 8)  # 6/8
