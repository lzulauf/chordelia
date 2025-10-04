"""
Musical intervals implementation using algorithmic approaches.

This module provides classes for representing and calculating musical intervals
without relying on lookup tables, making it efficient and suitable for low-end hardware.
"""

from enum import Enum
from typing import Union
from functools import lru_cache

# Pre-computed base semitones for fast lookup
_BASE_SEMITONES = {
    1: 0,   # Unison
    2: 2,   # Major 2nd
    3: 4,   # Major 3rd
    4: 5,   # Perfect 4th
    5: 7,   # Perfect 5th
    6: 9,   # Major 6th
    7: 11,  # Major 7th
    8: 12   # Octave
}

# Perfect intervals set for fast lookup
_PERFECT_INTERVALS = frozenset({1, 4, 5, 8})




class IntervalQuality(Enum):
    """Enumeration of interval qualities."""
    PERFECT = "P"
    MAJOR = "M"
    MINOR = "m"
    AUGMENTED = "A"
    DIMINISHED = "d"
    DOUBLY_AUGMENTED = "AA"
    DOUBLY_DIMINISHED = "dd"


# Quality adjustments hash table for fast interval calculation
_QUALITY_ADJUSTMENTS = {
    # Perfect intervals
    (IntervalQuality.PERFECT, True): 0,
    (IntervalQuality.AUGMENTED, True): 1,
    (IntervalQuality.DIMINISHED, True): -1,
    (IntervalQuality.DOUBLY_AUGMENTED, True): 2,
    (IntervalQuality.DOUBLY_DIMINISHED, True): -2,
    # Major/minor intervals  
    (IntervalQuality.MAJOR, False): 0,
    (IntervalQuality.MINOR, False): -1,
    (IntervalQuality.AUGMENTED, False): 1,
    (IntervalQuality.DIMINISHED, False): -2,
    (IntervalQuality.DOUBLY_AUGMENTED, False): 2,
    (IntervalQuality.DOUBLY_DIMINISHED, False): -3,
}


class Interval:
    """
    Represents a musical interval with quality and number.
    
    Uses algorithmic calculation of semitones rather than lookup tables
    for efficiency and clarity.
    """
    
    # Perfect intervals (unison, 4th, 5th, octave)
    PERFECT_INTERVALS = {1, 4, 5, 8}
    
    # Major intervals (2nd, 3rd, 6th, 7th) in their perfect form
    MAJOR_INTERVALS = {2, 3, 6, 7}
    
    def __init__(self, quality: Union[IntervalQuality, str], number: int):
        """
        Initialize an interval.
        
        Args:
            quality: The quality of the interval (perfect, major, minor, etc.)
            number: The interval number (1-8 for simple intervals, >8 for compound)
        """
        if isinstance(quality, str):
            quality = IntervalQuality(quality)
        
        self.quality = quality
        self.number = number
        
        # Validate interval quality and number combination
        self._validate()
    
    def _validate(self):
        """Validate that the interval quality and number are compatible."""
        simple_number = ((self.number - 1) % 7) + 1
        
        if simple_number in self.PERFECT_INTERVALS:
            if self.quality in (IntervalQuality.MAJOR, IntervalQuality.MINOR):
                raise ValueError(f"Interval {self.number} cannot be {self.quality.value}")
        else:
            if self.quality == IntervalQuality.PERFECT:
                raise ValueError(f"Interval {self.number} cannot be perfect")
    
    @lru_cache(maxsize=1)
    def _calculate_semitones(self) -> int:
        """Cache semitones calculation since it never changes."""
        # Reduce to simple interval for calculation
        simple_number = ((self.number - 1) % 7) + 1
        octaves = (self.number - 1) // 7
        
        # Use pre-computed base semitones
        base = _BASE_SEMITONES[simple_number]
        
        # Fast quality adjustment using hash table
        is_perfect = simple_number in _PERFECT_INTERVALS
        adjustment = _QUALITY_ADJUSTMENTS.get((self.quality, is_perfect), 0)
        
        return base + adjustment + (octaves * 12)
    
    @property
    def semitones(self) -> int:
        """
        Calculate the number of semitones in this interval algorithmically.
        
        Returns:
            The number of semitones
        """
        return self._calculate_semitones()
    
    @classmethod
    def from_semitones(cls, semitones: int, prefer_simple: bool = True) -> 'Interval':
        """
        Create an interval from a number of semitones.
        
        Args:
            semitones: Number of semitones
            prefer_simple: Whether to prefer simple intervals over compound
            
        Returns:
            An Interval object
        """
        # For now, just handle positive semitones and let the Note class handle negative transposition
        abs_semitones = abs(semitones)
        octaves = abs_semitones // 12
        remaining = abs_semitones % 12
        
        # Map semitones to intervals within an octave
        semitone_to_interval = {
            0: (IntervalQuality.PERFECT, 1),
            1: (IntervalQuality.MINOR, 2),
            2: (IntervalQuality.MAJOR, 2),
            3: (IntervalQuality.MINOR, 3),
            4: (IntervalQuality.MAJOR, 3),
            5: (IntervalQuality.PERFECT, 4),
            6: (IntervalQuality.AUGMENTED, 4),  # or diminished 5th
            7: (IntervalQuality.PERFECT, 5),
            8: (IntervalQuality.MINOR, 6),
            9: (IntervalQuality.MAJOR, 6),
            10: (IntervalQuality.MINOR, 7),
            11: (IntervalQuality.MAJOR, 7),
        }
        
        if remaining in semitone_to_interval:
            quality, number = semitone_to_interval[remaining]
            
            # Add octaves
            if octaves > 0 and not prefer_simple:
                number += octaves * 7
            
            interval = cls(quality, number)
            
            # Store original semitones for use in transposition
            interval._original_semitones = semitones
            
            return interval
        
        raise ValueError(f"Cannot create interval from {semitones} semitones")
    
    @staticmethod
    def _invert_interval(interval: 'Interval') -> 'Interval':
        """Invert an interval (used for descending intervals)."""
        # This is a simplified version - full inversion logic would be more complex
        inverted_number = 9 - interval.number
        if interval.quality == IntervalQuality.MAJOR:
            inverted_quality = IntervalQuality.MINOR
        elif interval.quality == IntervalQuality.MINOR:
            inverted_quality = IntervalQuality.MAJOR
        elif interval.quality == IntervalQuality.PERFECT:
            inverted_quality = IntervalQuality.PERFECT
        elif interval.quality == IntervalQuality.AUGMENTED:
            inverted_quality = IntervalQuality.DIMINISHED
        elif interval.quality == IntervalQuality.DIMINISHED:
            inverted_quality = IntervalQuality.AUGMENTED
        else:
            inverted_quality = interval.quality
        
        return Interval(inverted_quality, inverted_number)
    
    @property
    def is_consonant(self) -> bool:
        """
        Determine if the interval is consonant based on music theory.
        
        Returns:
            True if consonant, False if dissonant
        """
        simple_semitones = self.semitones % 12
        
        # Perfect consonances: unison, octave, perfect 5th, perfect 4th
        # Imperfect consonances: major/minor 3rd, major/minor 6th
        consonant_semitones = {0, 3, 4, 5, 7, 8, 9, 12}
        
        return simple_semitones in consonant_semitones
    
    @property
    def name(self) -> str:
        """
        Get the full name of the interval.
        
        Returns:
            String representation of the interval name
        """
        quality_names = {
            IntervalQuality.PERFECT: "Perfect",
            IntervalQuality.MAJOR: "Major",
            IntervalQuality.MINOR: "Minor",
            IntervalQuality.AUGMENTED: "Augmented",
            IntervalQuality.DIMINISHED: "Diminished",
            IntervalQuality.DOUBLY_AUGMENTED: "Doubly Augmented",
            IntervalQuality.DOUBLY_DIMINISHED: "Doubly Diminished",
        }
        
        number_names = {
            1: "Unison", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th",
            6: "6th", 7: "7th", 8: "Octave", 9: "9th", 10: "10th",
            11: "11th", 12: "12th", 13: "13th", 14: "14th", 15: "15th"
        }
        
        quality_name = quality_names[self.quality]
        number_name = number_names.get(self.number, f"{self.number}th")
        
        return f"{quality_name} {number_name}"
    
    def __str__(self) -> str:
        """String representation of the interval."""
        return f"{self.quality.value}{self.number}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Interval({self.quality}, {self.number}) - {self.name} ({self.semitones} semitones)"
    
    def __eq__(self, other) -> bool:
        """Check equality with another interval."""
        if not isinstance(other, Interval):
            return False
        return self.quality == other.quality and self.number == other.number
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((self.quality, self.number))
    
    def __add__(self, other: 'Interval') -> 'Interval':
        """Add two intervals together."""
        if not isinstance(other, Interval):
            raise TypeError("Can only add intervals to intervals")
        
        total_semitones = self.semitones + other.semitones
        return Interval.from_semitones(total_semitones, prefer_simple=False)
    
    def __sub__(self, other: 'Interval') -> 'Interval':
        """Subtract one interval from another."""
        if not isinstance(other, Interval):
            raise TypeError("Can only subtract intervals from intervals")
        
        total_semitones = self.semitones - other.semitones
        return Interval.from_semitones(total_semitones, prefer_simple=False)


# Common interval constants for convenience
UNISON = Interval(IntervalQuality.PERFECT, 1)
MINOR_SECOND = Interval(IntervalQuality.MINOR, 2)
MAJOR_SECOND = Interval(IntervalQuality.MAJOR, 2)
MINOR_THIRD = Interval(IntervalQuality.MINOR, 3)
MAJOR_THIRD = Interval(IntervalQuality.MAJOR, 3)
PERFECT_FOURTH = Interval(IntervalQuality.PERFECT, 4)
TRITONE = Interval(IntervalQuality.AUGMENTED, 4)
PERFECT_FIFTH = Interval(IntervalQuality.PERFECT, 5)
MINOR_SIXTH = Interval(IntervalQuality.MINOR, 6)
MAJOR_SIXTH = Interval(IntervalQuality.MAJOR, 6)
MINOR_SEVENTH = Interval(IntervalQuality.MINOR, 7)
MAJOR_SEVENTH = Interval(IntervalQuality.MAJOR, 7)
OCTAVE = Interval(IntervalQuality.PERFECT, 8)
