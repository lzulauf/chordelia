"""
Tests for the rhythm module.

This module tests musical timing, durations, time signatures, tempo,
and conversions between musical time and real time.
"""

import pytest
from decimal import Decimal
from fractions import Fraction
from chordelia.rhythm import (
    Duration, TimeSignature, Tempo, Beat, NoteValue,
    whole_note, half_note, quarter_note, eighth_note, sixteenth_note,
    dotted, triplet, COMMON_TIME, CUT_TIME, WALTZ_TIME, COMPOUND_DUPLE,
    coerce_timeline_duration, context_beat_unit,
)


class TestNoteValue:
    """Test NoteValue enumeration."""
    
    def test_note_value_fractions(self):
        """Test that note values have correct fractional values."""
        assert NoteValue.WHOLE.value == Fraction(1, 1)
        assert NoteValue.HALF.value == Fraction(1, 2)
        assert NoteValue.QUARTER.value == Fraction(1, 4)
        assert NoteValue.EIGHTH.value == Fraction(1, 8)
        assert NoteValue.SIXTEENTH.value == Fraction(1, 16)
    
    def test_dotted_note_values(self):
        """Test dotted note values are 1.5x original."""
        assert NoteValue.DOTTED_QUARTER.value == Fraction(3, 8)
        assert NoteValue.DOTTED_EIGHTH.value == Fraction(3, 16)
        assert NoteValue.DOTTED_HALF.value == Fraction(3, 4)
    
    def test_triplet_note_values(self):
        """Test triplet note values are 2/3 original."""
        assert NoteValue.QUARTER_TRIPLET.value == Fraction(1, 6)
        assert NoteValue.EIGHTH_TRIPLET.value == Fraction(1, 12)
        assert NoteValue.HALF_TRIPLET.value == Fraction(1, 3)
    
    def test_note_value_string_representation(self):
        """Test string representation of note values."""
        assert str(NoteValue.QUARTER) == "quarter"
        assert str(NoteValue.DOTTED_QUARTER) == "dotted quarter"
        assert str(NoteValue.QUARTER_TRIPLET) == "quarter triplet"


class TestDuration:
    """Test Duration class."""
    
    def test_create_from_note_value(self):
        """Test creating duration from NoteValue."""
        quarter = Duration(NoteValue.QUARTER)
        assert quarter.fraction == Fraction(1, 4)
        assert quarter.decimal == 0.25
    
    def test_create_from_fraction(self):
        """Test creating duration from Fraction."""
        duration = Duration(Fraction(3, 8))
        assert duration.fraction == Fraction(3, 8)
        assert duration.decimal == 0.375
    
    def test_create_from_float(self):
        """Test creating duration from float."""
        duration = Duration(0.5)
        assert duration.fraction == Fraction(1, 2)
        assert duration.decimal == 0.5
    
    def test_create_from_string_fraction(self):
        """Test creating duration from fraction string."""
        duration = Duration("1/4")
        assert duration.fraction == Fraction(1, 4)
        
        duration = Duration("3/8")
        assert duration.fraction == Fraction(3, 8)
    
    def test_create_from_string_names(self):
        """Test creating duration from named strings."""
        quarter = Duration("quarter")
        assert quarter.fraction == Fraction(1, 4)
        
        eighth = Duration("eighth")
        assert eighth.fraction == Fraction(1, 8)
        
        dotted_quarter = Duration("dotted quarter")
        assert dotted_quarter.fraction == Fraction(3, 8)
        
        quarter_triplet = Duration("quarter triplet")
        assert quarter_triplet.fraction == Fraction(1, 6)
    
    def test_duration_arithmetic(self):
        """Test duration arithmetic operations."""
        quarter = Duration(NoteValue.QUARTER)
        eighth = Duration(NoteValue.EIGHTH)
        
        # Addition
        result = quarter + eighth
        assert result.fraction == Fraction(3, 8)
        
        # Subtraction
        result = quarter - eighth
        assert result.fraction == Fraction(1, 8)
        
        # Multiplication
        result = quarter * 2
        assert result.fraction == Fraction(1, 2)
        
        # Division
        result = quarter / 2
        assert result.fraction == Fraction(1, 8)
    
    def test_duration_comparison(self):
        """Test duration comparison operations."""
        quarter = Duration(NoteValue.QUARTER)
        eighth = Duration(NoteValue.EIGHTH)
        another_quarter = Duration(Fraction(1, 4))
        
        assert quarter == another_quarter
        assert quarter > eighth
        assert eighth < quarter
    
    def test_beats_in_measure(self):
        """Test calculating beats in measure."""
        quarter = Duration(NoteValue.QUARTER)
        eighth = Duration(NoteValue.EIGHTH)
        
        # In 4/4 time, quarter note = 1 beat
        time_sig_4_4 = TimeSignature(4, 4)
        assert quarter.beats_in_measure(time_sig_4_4) == 1  # quarter note = 1 beat  
        assert eighth.beats_in_measure(time_sig_4_4) == Fraction(1, 2)  # eighth = 0.5 beats
    
    def test_duration_immutability(self):
        """Test that Duration instances are immutable."""
        quarter = Duration(NoteValue.QUARTER)
        original_fraction = quarter.fraction
        
        # Test that arithmetic operations return new instances
        result = quarter + Duration(NoteValue.EIGHTH)
        assert result is not quarter
        assert quarter.fraction == original_fraction  # Original unchanged
        
        result = quarter * 2
        assert result is not quarter
        assert quarter.fraction == original_fraction  # Original unchanged
        
        result = quarter / 2
        assert result is not quarter
        assert quarter.fraction == original_fraction  # Original unchanged
        
        # Test that attributes cannot be modified
        with pytest.raises(AttributeError):
            quarter.fraction = Fraction(1, 2)
        
        with pytest.raises(AttributeError):
            quarter.decimal = 0.5
    
    def test_to_milliseconds(self):
        """Test conversion to milliseconds."""
        quarter = Duration(NoteValue.QUARTER)
        time_sig = TimeSignature(4, 4)
        
        # At 120 BPM in 4/4, quarter note = 1 beat unit = 500ms
        ms = quarter.to_milliseconds(120, time_sig)
        assert abs(ms - 500.0) < 0.001
        
        # At 60 BPM in 4/4, quarter note = 1 beat unit = 1000ms
        ms = quarter.to_milliseconds(60, time_sig)
        assert abs(ms - 1000.0) < 0.001
    
    def test_duration_string_representation(self):
        """Test string representation of durations."""
        quarter = Duration(NoteValue.QUARTER)
        assert str(quarter) == "quarter"
        
        custom = Duration(Fraction(5, 16))
        assert "5/16" in str(custom)

    def test_from_beats_with_none_denominator_uses_beat_count(self):
        """from_beats(..., None) should treat numerator as absolute beat count."""
        duration = Duration.from_beats(3, None)

        assert duration.mode == "beats"
        assert duration.as_beats() == Fraction(3, 1)

    def test_from_beats_with_denominator_creates_fractional_beats(self):
        """from_beats should support fractional beat counts."""
        duration = Duration.from_beats(3, 2)

        assert duration.mode == "beats"
        assert duration.as_beats() == Fraction(3, 2)

    def test_from_seconds_creates_time_based_duration(self):
        """Time-based durations should preserve decimal precision and mode."""
        duration = Duration.from_seconds("1.25")

        assert duration.mode == "seconds"
        assert duration.as_seconds() == Decimal("1.25")
        assert abs(duration.to_milliseconds(120, TimeSignature(4, 4)) - 1250.0) < 0.001

    def test_mixed_mode_duration_arithmetic_raises_type_error(self):
        """Mixed beat/time arithmetic must be explicit via conversion context."""
        beats = Duration.from_beats(1)
        seconds = Duration.from_seconds("0.5")

        with pytest.raises(TypeError):
            _ = beats + seconds


class TestTimelineCoercion:
    """Tests for shared timeline coercion helpers."""

    def test_coerce_timeline_duration_from_note_value_uses_beat_unit(self):
        duration = coerce_timeline_duration(
            NoteValue.QUARTER,
            field_name="duration",
            beat_unit=4,
        )
        assert duration == Duration.from_beats(1)

    def test_coerce_timeline_duration_converts_note_fraction_duration(self):
        duration = coerce_timeline_duration(
            Duration("quarter"),
            field_name="duration",
            beat_unit=8,
        )
        assert duration == Duration.from_beats(2)

    def test_coerce_timeline_duration_accepts_fraction_beat_counts(self):
        duration = coerce_timeline_duration(
            Fraction(3, 2),
            field_name="duration",
        )
        assert duration == Duration.from_beats(Fraction(3, 2))

    def test_coerce_timeline_duration_preserves_seconds_mode(self):
        duration = Duration.from_seconds("0.5")

        coerced = coerce_timeline_duration(duration, field_name="duration")

        assert coerced is duration
        assert coerced.mode == "seconds"

    def test_coerce_timeline_duration_rejects_bool(self):
        with pytest.raises(TypeError, match="duration must be Duration"):
            coerce_timeline_duration(True, field_name="duration")

    def test_context_beat_unit_from_time_signature(self):
        assert context_beat_unit((6, 8)) == 8

    def test_context_beat_unit_defaults_when_missing(self):
        assert context_beat_unit(None) == 4

    def test_context_beat_unit_rejects_invalid_denominator(self):
        with pytest.raises(ValueError, match="denominator must be > 0"):
            context_beat_unit((4, 0))


class TestTimeSignature:
    """Test TimeSignature class."""
    
    def test_create_time_signature(self):
        """Test creating time signatures."""
        four_four = TimeSignature(4, 4)
        assert four_four.beats_per_measure == 4
        assert four_four.beat_unit == 4
        
        six_eight = TimeSignature(6, 8)
        assert six_eight.beats_per_measure == 6
        assert six_eight.beat_unit == 8
    
    def test_create_from_string(self):
        """Test creating from string representation."""
        four_four = TimeSignature.from_string("4/4")
        assert four_four.beats_per_measure == 4
        assert four_four.beat_unit == 4
        
        three_four = TimeSignature.from_string("3/4")
        assert three_four.beats_per_measure == 3
        assert three_four.beat_unit == 4
    
    def test_invalid_time_signatures(self):
        """Test error handling for invalid time signatures."""
        with pytest.raises(ValueError):
            TimeSignature(0, 4)  # Zero beats
        
        with pytest.raises(ValueError):
            TimeSignature(4, 3)  # Non-power-of-2 beat unit
        
        with pytest.raises(ValueError):
            TimeSignature.from_string("invalid")
    
    def test_measure_duration(self):
        """Test measure duration calculation."""
        four_four = TimeSignature(4, 4)
        assert four_four.measure_duration.fraction == Fraction(4, 4)
        
        six_eight = TimeSignature(6, 8)
        assert six_eight.measure_duration.fraction == Fraction(6, 8)
    
    def test_beat_duration(self):
        """Test beat duration calculation."""
        four_four = TimeSignature(4, 4)
        assert four_four.beat_duration.fraction == Fraction(1, 4)
        
        six_eight = TimeSignature(6, 8)
        assert six_eight.beat_duration.fraction == Fraction(1, 8)
    
    def test_simple_vs_compound_time(self):
        """Test identification of simple vs compound time."""
        four_four = TimeSignature(4, 4)
        assert four_four.is_simple_time()
        assert not four_four.is_compound_time()
        
        six_eight = TimeSignature(6, 8)
        assert not six_eight.is_simple_time()
        assert six_eight.is_compound_time()
        
        nine_eight = TimeSignature(9, 8)
        assert not nine_eight.is_simple_time()
        assert nine_eight.is_compound_time()
    
    def test_beats_to_measure_position(self):
        """Test converting beat numbers to measure positions."""
        four_four = TimeSignature(4, 4)
        
        # Beat 0 = measure 0, beat 0
        measure, beat = four_four.beats_to_measure_position(0)
        assert measure == 0 and beat == 0
        
        # Beat 3 = measure 0, beat 3
        measure, beat = four_four.beats_to_measure_position(3)
        assert measure == 0 and beat == 3
        
        # Beat 4 = measure 1, beat 0  
        measure, beat = four_four.beats_to_measure_position(4)
        assert measure == 1 and beat == 0
        
        # Beat 6.5 = measure 1, beat 2.5
        measure, beat = four_four.beats_to_measure_position(6.5)
        assert measure == 1 and abs(beat - 2.5) < 0.001
    
    def test_time_signature_equality(self):
        """Test time signature equality."""
        ts1 = TimeSignature(4, 4)
        ts2 = TimeSignature(4, 4)
        ts3 = TimeSignature(3, 4)
        
        assert ts1 == ts2
        assert ts1 != ts3
    
    def test_string_representation(self):
        """Test string representation."""
        four_four = TimeSignature(4, 4)
        assert str(four_four) == "4/4"


class TestTempo:
    """Test Tempo class."""
    
    def test_create_tempo(self):
        """Test creating tempo."""
        tempo = Tempo(120)
        assert tempo.bpm == 120
        assert tempo.marking is None
        
        marked_tempo = Tempo(120, "moderato")
        assert marked_tempo.bpm == 120
        assert marked_tempo.marking == "moderato"
    
    def test_create_from_marking(self):
        """Test creating tempo from traditional marking."""
        allegro = Tempo.from_marking("allegro")
        assert 120 <= allegro.bpm <= 168  # Allegro range
        assert allegro.marking == "allegro"
        
        andante = Tempo.from_marking("andante")
        assert 76 <= andante.bpm <= 108  # Andante range
        assert andante.marking == "andante"
    
    def test_invalid_tempo(self):
        """Test error handling for invalid tempo."""
        with pytest.raises(ValueError):
            Tempo(0)  # Zero BPM
        
        with pytest.raises(ValueError):
            Tempo(-60)  # Negative BPM
        
        with pytest.raises(ValueError):
            Tempo.from_marking("invalid_marking")
    
    def test_beat_duration_ms(self):
        """Test beat duration in milliseconds."""
        tempo_120 = Tempo(120)
        assert abs(tempo_120.beat_duration_ms() - 500.0) < 0.001
        
        tempo_60 = Tempo(60)
        assert abs(tempo_60.beat_duration_ms() - 1000.0) < 0.001
    
    def test_duration_to_ms(self):
        """Test converting duration to milliseconds."""
        tempo = Tempo(120)
        quarter = Duration(NoteValue.QUARTER)
        time_sig = TimeSignature(4, 4)
        
        ms = tempo.duration_to_ms(quarter, time_sig)
        assert abs(ms - 500.0) < 0.001  # Quarter note at 120 BPM = 1 beat = 500ms
    
    def test_ms_to_beats(self):
        """Test converting milliseconds to beats."""
        tempo = Tempo(120)  # 120 BPM = 2 beats per second
        
        beats = tempo.ms_to_beats(1000)  # 1 second
        assert abs(beats - 2.0) < 0.001
        
        beats = tempo.ms_to_beats(30000)  # 30 seconds
        assert abs(beats - 60.0) < 0.001
    
    def test_get_suggested_marking(self):
        """Test getting suggested tempo marking."""
        slow_tempo = Tempo(50)
        assert slow_tempo.get_suggested_marking() == "largo"
        
        fast_tempo = Tempo(150)
        assert fast_tempo.get_suggested_marking() == "allegro"
        
        very_fast_tempo = Tempo(300)
        assert very_fast_tempo.get_suggested_marking() == "very fast"
    
    def test_string_representation(self):
        """Test string representation."""
        tempo = Tempo(120)
        assert "120" in str(tempo)
        
        marked_tempo = Tempo(120, "moderato")
        assert "moderato" in str(marked_tempo)
        assert "120" in str(marked_tempo)


class TestBeat:
    """Test Beat class."""
    
    def test_create_beat(self):
        """Test creating beat positions."""
        time_sig = TimeSignature(4, 4)
        beat = Beat(0, 0, time_sig)
        assert beat.measure == 0
        assert beat.beat == 0
        assert beat.time_signature == time_sig
    
    def test_invalid_beat_positions(self):
        """Test error handling for invalid beat positions."""
        time_sig = TimeSignature(4, 4)
        
        with pytest.raises(ValueError):
            Beat(-1, 0, time_sig)  # Negative measure
        
        with pytest.raises(ValueError):
            Beat(0, 4, time_sig)  # Beat >= beats_per_measure
        
        with pytest.raises(ValueError):
            Beat(0, -1, time_sig)  # Negative beat
    
    def test_absolute_beat(self):
        """Test absolute beat calculation."""
        time_sig = TimeSignature(4, 4)
        
        beat1 = Beat(0, 0, time_sig)
        assert beat1.absolute_beat == 0
        
        beat2 = Beat(0, 2, time_sig)
        assert beat2.absolute_beat == 2
        
        beat3 = Beat(1, 1, time_sig)
        assert beat3.absolute_beat == 5  # 4 beats in first measure + 1
    
    def test_to_milliseconds(self):
        """Test conversion to milliseconds."""
        time_sig = TimeSignature(4, 4)
        tempo = Tempo(120)  # 500ms per beat
        
        beat1 = Beat(0, 0, time_sig)
        assert beat1.to_milliseconds(tempo) == 0
        
        beat2 = Beat(0, 2, time_sig)
        assert abs(beat2.to_milliseconds(tempo) - 1000.0) < 0.001
        
        beat3 = Beat(1, 0, time_sig)
        assert abs(beat3.to_milliseconds(tempo) - 2000.0) < 0.001
    
    def test_add_duration(self):
        """Test adding duration to beat position."""
        time_sig = TimeSignature(4, 4)
        beat = Beat(0, 0, time_sig)
        quarter = Duration(NoteValue.QUARTER)
        
        new_beat = beat.add_duration(quarter)
        assert new_beat.measure == 0
        assert abs(new_beat.beat - 1.0) < 0.001  # Quarter note = 1 beat in 4/4
        
        # Add enough to cross measure boundary
        whole = Duration(NoteValue.WHOLE)
        new_beat = beat.add_duration(whole)
        assert new_beat.measure == 1
        assert abs(new_beat.beat - 0.0) < 0.001
    
    def test_string_representation(self):
        """Test string representation."""
        time_sig = TimeSignature(4, 4)
        beat = Beat(0, 1.5, time_sig)
        assert "Measure 1" in str(beat)
        assert "Beat 2.50" in str(beat)


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_note_creation_functions(self):
        """Test note duration creation functions."""
        assert whole_note().fraction == Fraction(1, 1)
        assert half_note().fraction == Fraction(1, 2)
        assert quarter_note().fraction == Fraction(1, 4)
        assert eighth_note().fraction == Fraction(1, 8)
        assert sixteenth_note().fraction == Fraction(1, 16)
    
    def test_dotted_function(self):
        """Test dotted duration function."""
        quarter = quarter_note()
        dotted_quarter = dotted(quarter)
        assert dotted_quarter.fraction == Fraction(3, 8)
        
        eighth = eighth_note()
        dotted_eighth = dotted(eighth)
        assert dotted_eighth.fraction == Fraction(3, 16)
    
    def test_triplet_function(self):
        """Test triplet duration function."""
        quarter = quarter_note()
        quarter_triplet = triplet(quarter)
        assert quarter_triplet.fraction == Fraction(1, 6)
        
        eighth = eighth_note()
        eighth_triplet = triplet(eighth)
        assert eighth_triplet.fraction == Fraction(1, 12)


class TestCommonTimeSignatures:
    """Test predefined common time signatures."""
    
    def test_common_time_signatures(self):
        """Test common time signature constants."""
        assert COMMON_TIME.beats_per_measure == 4
        assert COMMON_TIME.beat_unit == 4
        
        assert CUT_TIME.beats_per_measure == 2
        assert CUT_TIME.beat_unit == 2
        
        assert WALTZ_TIME.beats_per_measure == 3
        assert WALTZ_TIME.beat_unit == 4
        
        assert COMPOUND_DUPLE.beats_per_measure == 6
        assert COMPOUND_DUPLE.beat_unit == 8


class TestRealWorldExamples:
    """Test real-world rhythm scenarios."""
    
    def test_song_timing_calculation(self):
        """Test calculating song timing."""
        # "Take Five" - 5/4 time signature at 140 BPM
        time_sig = TimeSignature(5, 4)
        tempo = Tempo(140)
        
        # How long is one measure?
        measure_duration = time_sig.measure_duration  # 5/4 note
        measure_ms = tempo.duration_to_ms(measure_duration, time_sig)
        
        # 5/4 note = 5 quarter notes, each quarter = 1 beat at 140 BPM
        expected_ms = 5 * (60000.0 / 140)  # 5 beats * ms per beat
        assert abs(measure_ms - expected_ms) < 0.001
    
    def test_complex_rhythm_calculation(self):
        """Test complex rhythm calculations."""
        time_sig = TimeSignature(4, 4)
        tempo = Tempo(120)
        
        # Syncopated rhythm: quarter, eighth, dotted quarter, eighth
        rhythm = [
            quarter_note(),     # 1/4
            eighth_note(),      # 1/8  
            dotted(quarter_note()),  # 3/8
            eighth_note()       # 1/8
        ]
        # Total: 1/4 + 1/8 + 3/8 + 1/8 = 2/8 + 1/8 + 3/8 + 1/8 = 7/8
        
        # Calculate total duration
        total_duration = sum(rhythm, Duration(0))
        assert total_duration.fraction == Fraction(7, 8)  # 7/8 note
        
        # Calculate timing in milliseconds
        total_ms = tempo.duration_to_ms(total_duration, time_sig)
        # 7/8 note at 120 BPM in 4/4: 7/8 * 4 beats = 3.5 beats, at 500ms per beat = 1750ms
        assert abs(total_ms - 1750.0) < 0.001  # 7/8 note at 120 BPM in 4/4
    
    def test_metric_modulation(self):
        """Test metric modulation scenarios."""
        # Start in 4/4 at 120 BPM
        time_sig_1 = TimeSignature(4, 4)
        tempo_1 = Tempo(120)
        
        # Switch to 3/4 where the quarter note stays the same
        time_sig_2 = TimeSignature(3, 4)
        tempo_2 = tempo_1  # Same BPM since quarter note = quarter note
        
        quarter = quarter_note()
        
        # Quarter note duration should be same in both time signatures
        ms_1 = tempo_1.duration_to_ms(quarter, time_sig_1)
        ms_2 = tempo_2.duration_to_ms(quarter, time_sig_2)
        
        # Quarter note duration should be same time-wise in both signatures
        assert abs(ms_1 - ms_2) < 0.001
        
        # But the context of beats in measure is the same for quarter notes
        beat_context_1 = quarter.beats_in_measure(time_sig_1)
        beat_context_2 = quarter.beats_in_measure(time_sig_2)
        
        assert beat_context_1 == beat_context_2  # Quarter note = 1 beat in both 4/4 and 3/4
