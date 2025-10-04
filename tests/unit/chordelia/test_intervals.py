"""
Test suite for the intervals module.

Tests all interval functionality including calculation, validation,
arithmetic operations, and edge cases.
"""

import pytest
from chordelia.intervals import Interval, IntervalQuality
from chordelia.intervals import (
    UNISON, MINOR_SECOND, MAJOR_SECOND, MINOR_THIRD, MAJOR_THIRD,
    PERFECT_FOURTH, TRITONE, PERFECT_FIFTH, MINOR_SIXTH, MAJOR_SIXTH,
    MINOR_SEVENTH, MAJOR_SEVENTH, OCTAVE
)


class TestIntervalQuality:
    """Test IntervalQuality enum."""
    
    def test_interval_quality_values(self):
        """Test that interval qualities have correct string values."""
        assert IntervalQuality.PERFECT.value == "P"
        assert IntervalQuality.MAJOR.value == "M"
        assert IntervalQuality.MINOR.value == "m"
        assert IntervalQuality.AUGMENTED.value == "A"
        assert IntervalQuality.DIMINISHED.value == "d"


class TestIntervalCreation:
    """Test interval creation and validation."""
    
    def test_create_perfect_intervals(self):
        """Test creation of perfect intervals."""
        unison = Interval(IntervalQuality.PERFECT, 1)
        assert unison.quality == IntervalQuality.PERFECT
        assert unison.number == 1
        
        fourth = Interval(IntervalQuality.PERFECT, 4)
        assert fourth.quality == IntervalQuality.PERFECT
        assert fourth.number == 4
        
        fifth = Interval(IntervalQuality.PERFECT, 5)
        assert fifth.quality == IntervalQuality.PERFECT
        assert fifth.number == 5
        
        octave = Interval(IntervalQuality.PERFECT, 8)
        assert octave.quality == IntervalQuality.PERFECT
        assert octave.number == 8
    
    def test_create_major_minor_intervals(self):
        """Test creation of major and minor intervals."""
        major_second = Interval(IntervalQuality.MAJOR, 2)
        assert major_second.quality == IntervalQuality.MAJOR
        assert major_second.number == 2
        
        minor_third = Interval(IntervalQuality.MINOR, 3)
        assert minor_third.quality == IntervalQuality.MINOR
        assert minor_third.number == 3
        
        major_sixth = Interval(IntervalQuality.MAJOR, 6)
        assert major_sixth.quality == IntervalQuality.MAJOR
        assert major_sixth.number == 6
        
        minor_seventh = Interval(IntervalQuality.MINOR, 7)
        assert minor_seventh.quality == IntervalQuality.MINOR
        assert minor_seventh.number == 7
    
    def test_create_augmented_diminished(self):
        """Test creation of augmented and diminished intervals."""
        aug_fourth = Interval(IntervalQuality.AUGMENTED, 4)
        assert aug_fourth.quality == IntervalQuality.AUGMENTED
        assert aug_fourth.number == 4
        
        dim_fifth = Interval(IntervalQuality.DIMINISHED, 5)
        assert dim_fifth.quality == IntervalQuality.DIMINISHED
        assert dim_fifth.number == 5
    
    def test_string_quality_input(self):
        """Test creating intervals with string quality input."""
        interval = Interval("P", 5)
        assert interval.quality == IntervalQuality.PERFECT
        assert interval.number == 5
        
        interval = Interval("M", 3)
        assert interval.quality == IntervalQuality.MAJOR
        assert interval.number == 3
    
    def test_invalid_combinations(self):
        """Test that invalid quality/number combinations raise errors."""
        # Perfect intervals cannot be major or minor
        with pytest.raises(ValueError):
            Interval(IntervalQuality.MAJOR, 1)
        
        with pytest.raises(ValueError):
            Interval(IntervalQuality.MINOR, 4)
        
        with pytest.raises(ValueError):
            Interval(IntervalQuality.MAJOR, 5)
        
        # Major/minor intervals cannot be perfect
        with pytest.raises(ValueError):
            Interval(IntervalQuality.PERFECT, 2)
        
        with pytest.raises(ValueError):
            Interval(IntervalQuality.PERFECT, 3)
        
        with pytest.raises(ValueError):
            Interval(IntervalQuality.PERFECT, 6)
        
        with pytest.raises(ValueError):
            Interval(IntervalQuality.PERFECT, 7)


class TestIntervalSemitones:
    """Test semitone calculation for intervals."""
    
    def test_perfect_intervals_semitones(self):
        """Test semitone values for perfect intervals."""
        assert Interval(IntervalQuality.PERFECT, 1).semitones == 0
        assert Interval(IntervalQuality.PERFECT, 4).semitones == 5
        assert Interval(IntervalQuality.PERFECT, 5).semitones == 7
        assert Interval(IntervalQuality.PERFECT, 8).semitones == 12
    
    def test_major_intervals_semitones(self):
        """Test semitone values for major intervals."""
        assert Interval(IntervalQuality.MAJOR, 2).semitones == 2
        assert Interval(IntervalQuality.MAJOR, 3).semitones == 4
        assert Interval(IntervalQuality.MAJOR, 6).semitones == 9
        assert Interval(IntervalQuality.MAJOR, 7).semitones == 11
    
    def test_minor_intervals_semitones(self):
        """Test semitone values for minor intervals."""
        assert Interval(IntervalQuality.MINOR, 2).semitones == 1
        assert Interval(IntervalQuality.MINOR, 3).semitones == 3
        assert Interval(IntervalQuality.MINOR, 6).semitones == 8
        assert Interval(IntervalQuality.MINOR, 7).semitones == 10
    
    def test_augmented_diminished_semitones(self):
        """Test semitone values for augmented and diminished intervals."""
        assert Interval(IntervalQuality.AUGMENTED, 1).semitones == 1
        assert Interval(IntervalQuality.AUGMENTED, 4).semitones == 6
        assert Interval(IntervalQuality.AUGMENTED, 5).semitones == 8
        
        assert Interval(IntervalQuality.DIMINISHED, 1).semitones == -1
        assert Interval(IntervalQuality.DIMINISHED, 4).semitones == 4
        assert Interval(IntervalQuality.DIMINISHED, 5).semitones == 6
        assert Interval(IntervalQuality.DIMINISHED, 8).semitones == 11
    
    def test_compound_intervals_semitones(self):
        """Test semitone values for compound intervals."""
        major_ninth = Interval(IntervalQuality.MAJOR, 9)
        assert major_ninth.semitones == 14  # Octave + major second
        
        perfect_eleventh = Interval(IntervalQuality.PERFECT, 11)
        assert perfect_eleventh.semitones == 17  # Octave + perfect fourth
        
        major_thirteenth = Interval(IntervalQuality.MAJOR, 13)
        assert major_thirteenth.semitones == 21  # Octave + major sixth


class TestIntervalFromSemitones:
    """Test creating intervals from semitone values."""
    
    def test_simple_intervals_from_semitones(self):
        """Test creating simple intervals from semitones."""
        unison = Interval.from_semitones(0)
        assert unison.quality == IntervalQuality.PERFECT
        assert unison.number == 1
        
        minor_second = Interval.from_semitones(1)
        assert minor_second.quality == IntervalQuality.MINOR
        assert minor_second.number == 2
        
        major_third = Interval.from_semitones(4)
        assert major_third.quality == IntervalQuality.MAJOR
        assert major_third.number == 3
        
        perfect_fifth = Interval.from_semitones(7)
        assert perfect_fifth.quality == IntervalQuality.PERFECT
        assert perfect_fifth.number == 5
        
        octave = Interval.from_semitones(12)
        assert octave.quality == IntervalQuality.PERFECT
        assert octave.number == 1  # Simple interval preferred
    
    def test_compound_intervals_from_semitones(self):
        """Test creating compound intervals from semitones."""
        ninth = Interval.from_semitones(14, prefer_simple=False)
        assert ninth.quality == IntervalQuality.MAJOR
        assert ninth.number == 9
        
        eleventh = Interval.from_semitones(17, prefer_simple=False)
        assert eleventh.quality == IntervalQuality.PERFECT
        assert eleventh.number == 11


class TestIntervalProperties:
    """Test interval properties and methods."""
    
    def test_consonance(self):
        """Test consonance determination."""
        # Perfect consonances
        assert Interval(IntervalQuality.PERFECT, 1).is_consonant
        assert Interval(IntervalQuality.PERFECT, 4).is_consonant
        assert Interval(IntervalQuality.PERFECT, 5).is_consonant
        assert Interval(IntervalQuality.PERFECT, 8).is_consonant
        
        # Imperfect consonances
        assert Interval(IntervalQuality.MAJOR, 3).is_consonant
        assert Interval(IntervalQuality.MINOR, 3).is_consonant
        assert Interval(IntervalQuality.MAJOR, 6).is_consonant
        assert Interval(IntervalQuality.MINOR, 6).is_consonant
        
        # Dissonances
        assert not Interval(IntervalQuality.MAJOR, 2).is_consonant
        assert not Interval(IntervalQuality.MINOR, 2).is_consonant
        assert not Interval(IntervalQuality.MAJOR, 7).is_consonant
        assert not Interval(IntervalQuality.MINOR, 7).is_consonant
        assert not Interval(IntervalQuality.AUGMENTED, 4).is_consonant
    
    def test_interval_names(self):
        """Test interval name generation."""
        assert Interval(IntervalQuality.PERFECT, 1).name == "Perfect Unison"
        assert Interval(IntervalQuality.MINOR, 2).name == "Minor 2nd"
        assert Interval(IntervalQuality.MAJOR, 3).name == "Major 3rd"
        assert Interval(IntervalQuality.PERFECT, 4).name == "Perfect 4th"
        assert Interval(IntervalQuality.AUGMENTED, 4).name == "Augmented 4th"
        assert Interval(IntervalQuality.PERFECT, 5).name == "Perfect 5th"
        assert Interval(IntervalQuality.MAJOR, 6).name == "Major 6th"
        assert Interval(IntervalQuality.MINOR, 7).name == "Minor 7th"
        assert Interval(IntervalQuality.PERFECT, 8).name == "Perfect Octave"
        assert Interval(IntervalQuality.MAJOR, 9).name == "Major 9th"


class TestIntervalArithmetic:
    """Test interval arithmetic operations."""
    
    def test_interval_addition(self):
        """Test adding intervals together."""
        major_third = Interval(IntervalQuality.MAJOR, 3)
        minor_third = Interval(IntervalQuality.MINOR, 3)
        
        # Major third + minor third = perfect fifth
        result = major_third + minor_third
        assert result.semitones == 7  # 4 + 3 = 7
        
        perfect_fourth = Interval(IntervalQuality.PERFECT, 4)
        major_second = Interval(IntervalQuality.MAJOR, 2)
        
        # Perfect fourth + major second = perfect fifth
        result = perfect_fourth + major_second
        assert result.semitones == 7  # 5 + 2 = 7
    
    def test_interval_subtraction(self):
        """Test subtracting intervals."""
        perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
        major_third = Interval(IntervalQuality.MAJOR, 3)
        
        # Perfect fifth - major third = minor third
        result = perfect_fifth - major_third
        assert result.semitones == 3  # 7 - 4 = 3
    
    def test_invalid_arithmetic(self):
        """Test that invalid arithmetic operations raise errors."""
        interval = Interval(IntervalQuality.PERFECT, 5)
        
        with pytest.raises(TypeError):
            interval + 5
        
        with pytest.raises(TypeError):
            interval - "test"


class TestIntervalEquality:
    """Test interval equality and hashing."""
    
    def test_equality(self):
        """Test interval equality comparison."""
        interval1 = Interval(IntervalQuality.PERFECT, 5)
        interval2 = Interval(IntervalQuality.PERFECT, 5)
        interval3 = Interval(IntervalQuality.MAJOR, 3)
        
        assert interval1 == interval2
        assert interval1 != interval3
        assert interval2 != interval3
    
    def test_hashing(self):
        """Test that intervals can be used in sets and dicts."""
        intervals = {
            Interval(IntervalQuality.PERFECT, 5),
            Interval(IntervalQuality.MAJOR, 3),
            Interval(IntervalQuality.PERFECT, 5),  # Duplicate
        }
        
        assert len(intervals) == 2  # Duplicate should be removed


class TestIntervalConstants:
    """Test predefined interval constants."""
    
    def test_constant_values(self):
        """Test that interval constants have correct values."""
        assert UNISON.semitones == 0
        assert MINOR_SECOND.semitones == 1
        assert MAJOR_SECOND.semitones == 2
        assert MINOR_THIRD.semitones == 3
        assert MAJOR_THIRD.semitones == 4
        assert PERFECT_FOURTH.semitones == 5
        assert TRITONE.semitones == 6
        assert PERFECT_FIFTH.semitones == 7
        assert MINOR_SIXTH.semitones == 8
        assert MAJOR_SIXTH.semitones == 9
        assert MINOR_SEVENTH.semitones == 10
        assert MAJOR_SEVENTH.semitones == 11
        assert OCTAVE.semitones == 12
    
    def test_constant_types(self):
        """Test that constants are proper intervals."""
        assert isinstance(UNISON, Interval)
        assert isinstance(PERFECT_FIFTH, Interval)
        assert isinstance(MAJOR_THIRD, Interval)


class TestIntervalStringRepresentation:
    """Test string representations of intervals."""
    
    def test_str_representation(self):
        """Test __str__ method."""
        assert str(Interval(IntervalQuality.PERFECT, 5)) == "P5"
        assert str(Interval(IntervalQuality.MAJOR, 3)) == "M3"
        assert str(Interval(IntervalQuality.MINOR, 7)) == "m7"
        assert str(Interval(IntervalQuality.AUGMENTED, 4)) == "A4"
        assert str(Interval(IntervalQuality.DIMINISHED, 5)) == "d5"
    
    def test_repr_representation(self):
        """Test __repr__ method."""
        interval = Interval(IntervalQuality.PERFECT, 5)
        repr_str = repr(interval)
        
        assert "Interval" in repr_str
        assert "Perfect 5th" in repr_str
        assert "7 semitones" in repr_str
