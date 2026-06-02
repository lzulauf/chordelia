"""
Example usage of Chordelia's rhythm module.

Demonstrates musical timing, durations, time signatures, tempo,
and conversions between musical time and real time.
"""

import sys

from chordelia import (
    Duration, TimeSignature, Tempo, Beat,
    dotted, triplet,
    COMMON_TIME, WALTZ_TIME, COMPOUND_DUPLE
)


# Avoid UnicodeEncodeError on Windows code pages when examples print symbols.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def basic_rhythm_examples():
    """Demonstrate basic rhythm functionality."""
    print("=== Basic Rhythm Examples ===")
    
    # Create durations
    quarter = Duration("quarter")
    eighth = Duration("eighth")
    dotted_quarter = dotted(Duration("quarter"))
    quarter_triplet = triplet(Duration("quarter"))
    
    print(f"Quarter note: {quarter}")
    print(f"Eighth note: {eighth}")
    print(f"Dotted quarter: {dotted_quarter}")
    print(f"Quarter triplet: {quarter_triplet}")
    
    # Duration arithmetic
    half_note_duration = quarter + quarter
    print(f"Quarter + quarter = {half_note_duration}")
    
    print()


def time_signature_examples():
    """Demonstrate time signature functionality."""
    print("=== Time Signature Examples ===")
    
    # Common time signatures
    print(f"Common time (4/4): {COMMON_TIME}")
    print(f"Waltz time (3/4): {WALTZ_TIME}")
    print(f"Compound duple (6/8): {COMPOUND_DUPLE}")
    
    # Create custom time signatures
    five_four = TimeSignature.from_string("5/4")
    seven_eight = TimeSignature(7, 8)
    
    print(f"Take Five time (5/4): {five_four}")
    print(f"Seven-eight time: {seven_eight}")
    
    # Analyze time signatures
    print(f"4/4 is simple time: {COMMON_TIME.is_simple_time()}")
    print(f"6/8 is compound time: {COMPOUND_DUPLE.is_compound_time()}")
    
    print()


def tempo_examples():
    """Demonstrate tempo functionality."""
    print("=== Tempo Examples ===")
    
    # Create tempos
    moderate_tempo = Tempo(120)
    fast_tempo = Tempo.from_marking("allegro")
    
    print(f"Moderate tempo: {moderate_tempo}")
    print(f"Fast tempo: {fast_tempo}")
    
    # Tempo suggestions
    slow_tempo = Tempo(70)
    print(f"70 BPM suggested marking: {slow_tempo.get_suggested_marking()}")
    
    # Beat duration
    print(f"At 120 BPM, each beat = {moderate_tempo.beat_duration_ms():.1f}ms")
    
    print()


def duration_conversion_examples():
    """Demonstrate duration to time conversions."""
    print("=== Duration Conversion Examples ===")
    
    tempo = Tempo(120)  # 120 BPM
    time_sig = COMMON_TIME  # 4/4
    
    # Convert various durations to milliseconds
    durations = [
        Duration("whole"),
        Duration("half"),
        Duration("quarter"),
        Duration("eighth"),
        dotted(Duration("quarter")),
        triplet(Duration("quarter"))
    ]
    
    for duration in durations:
        ms = duration.to_milliseconds(tempo.bpm, time_sig)
        beats = duration.beats_in_measure(time_sig)
        print(f"{duration}: {beats} beats = {ms:.0f}ms")
    
    print()


def musical_timing_example():
    """Demonstrate practical musical timing scenarios."""
    print("=== Musical Timing Example ===")
    
    # Song: "Take Five" by Dave Brubeck (5/4 time, ~174 BPM)
    take_five_tempo = Tempo(174)
    take_five_time = TimeSignature(5, 4)
    
    print(f"Take Five: {take_five_time} at {take_five_tempo}")
    
    # Calculate measure duration
    measure_duration = take_five_time.measure_duration
    measure_ms = measure_duration.to_milliseconds(take_five_tempo.bpm, take_five_time)
    
    print(f"One measure duration: {measure_ms:.0f}ms ({measure_ms/1000:.1f} seconds)")
    
    # Famous opening rhythm pattern (simplified)
    # Three quarters, one half note
    pattern = [Duration("quarter"), Duration("quarter"), Duration("quarter"), Duration("half")]
    
    print("Opening pattern timing:")
    current_time = 0
    for i, duration in enumerate(pattern):
        ms = duration.to_milliseconds(take_five_tempo.bpm, take_five_time)
        print(f"  Beat {i+1}: {duration} at {current_time:.0f}ms")
        current_time += ms
    
    print(f"Pattern total: {current_time:.0f}ms")
    print()


def beat_tracking_example():
    """Demonstrate beat position tracking."""
    print("=== Beat Tracking Example ===")
    
    time_sig = COMMON_TIME
    tempo = Tempo(120)
    
    # Start at the beginning
    current_beat = Beat(0, 0, time_sig)  # Measure 0, beat 0
    
    print(f"Starting position: {current_beat}")
    print(f"Time: {current_beat.to_milliseconds(tempo):.0f}ms")
    
    # Add various durations
    durations_to_add = [
        Duration("quarter"),
        Duration("eighth"), 
        dotted(Duration("quarter")),
        Duration("quarter")
    ]
    
    for duration in durations_to_add:
        current_beat = current_beat.add_duration(duration)
        ms = current_beat.to_milliseconds(tempo)
        print(f"After adding {duration}: {current_beat} ({ms:.0f}ms)")
    
    print()


def compound_time_example():
    """Demonstrate compound time signatures."""
    print("=== Compound Time Example ===")
    
    # 6/8 time - compound duple meter
    six_eight = COMPOUND_DUPLE
    tempo = Tempo(180)  # 180 eighth notes per minute
    
    print(f"Compound time: {six_eight}")
    print(f"Tempo: {tempo} eighth notes per minute")
    
    # In 6/8, we feel it in 2 (groups of 3 eighths)
    dotted_quarter = dotted(Duration("quarter"))  # Main beat in 6/8
    eighth = Duration("eighth")
    
    print(f"Main beat (dotted quarter): {dotted_quarter}")
    ms_main = dotted_quarter.to_milliseconds(tempo.bpm, six_eight)
    print(f"Main beat duration: {ms_main:.0f}ms")
    
    print(f"Subdivision (eighth): {eighth}")
    ms_sub = eighth.to_milliseconds(tempo.bpm, six_eight)
    print(f"Subdivision duration: {ms_sub:.0f}ms")
    
    print()


if __name__ == "__main__":
    basic_rhythm_examples()
    time_signature_examples()
    tempo_examples()
    duration_conversion_examples()
    musical_timing_example()
    beat_tracking_example()
    compound_time_example()
    
    print("=== Rhythm Module Summary ===")
    print("Chordelia's rhythm module provides:")
    print("- Precise fractional duration representation")
    print("- Time signature analysis (simple vs compound)")
    print("- Tempo with traditional markings")
    print("- Musical time to real time conversion")
    print("- Beat position tracking")
    print("- Support for complex rhythms (dotted notes, triplets)")
    print("- Algorithmic calculations for efficiency")

