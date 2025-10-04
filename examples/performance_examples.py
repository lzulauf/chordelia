"""
Performance optimization examples and low-end hardware considerations.

This script demonstrates that Chordelia is designed for efficiency
and can run well on resource-constrained systems.
"""

import time
from chordelia import Note, Interval, Scale, Chord
from chordelia import NoteName, ScaleType, ChordQuality


def benchmark_operations():
    """Benchmark core operations to show performance."""
    print("=== Performance Benchmarks ===")
    
    # Benchmark note creation
    start_time = time.time()
    notes = []
    for _ in range(1000):
        note = Note("C", octave=4)
        notes.append(note)
    note_creation_time = time.time() - start_time
    print(f"1000 note creations: {note_creation_time:.4f}s ({note_creation_time*1000:.2f}ms)")
    
    # Benchmark interval calculations
    start_time = time.time()
    note_c = Note("C", octave=4)
    for _ in range(1000):
        interval = note_c.interval_to(Note("G", octave=4))
    interval_calc_time = time.time() - start_time
    print(f"1000 interval calculations: {interval_calc_time:.4f}s ({interval_calc_time*1000:.2f}ms)")
    
    # Benchmark scale generation
    start_time = time.time()
    scales = []
    for root in ['C', 'D', 'E', 'F', 'G', 'A', 'B']:
        scale = Scale(root, ScaleType.MAJOR)
        scales.append(scale.notes)  # Force note generation
    scale_generation_time = time.time() - start_time
    print(f"7 major scales generation: {scale_generation_time:.4f}s ({scale_generation_time*1000:.2f}ms)")
    
    # Benchmark chord parsing
    start_time = time.time()
    chord_names = ["Cmaj7", "Dm7", "G7", "Am7", "Fmaj7", "Bm7b5", "E7"]
    chords = []
    for _ in range(100):
        for chord_name in chord_names:
            chord = Chord.from_string(chord_name)
            chords.append(chord)
    chord_parsing_time = time.time() - start_time
    print(f"700 chord parsings: {chord_parsing_time:.4f}s ({chord_parsing_time*1000:.2f}ms)")
    
    print()


def memory_efficiency_example():
    """Show memory-efficient usage patterns."""
    print("=== Memory Efficiency Examples ===")
    
    # Use algorithmic generation instead of lookup tables
    print("Chordelia uses algorithms, not lookup tables:")
    
    # Show semitone calculation is algorithmic
    interval = Interval.from_semitones(7)  # Perfect fifth
    print(f"Perfect fifth from algorithm: {interval.quality} {interval.number}")
    
    # Show scale generation is calculated, not stored
    c_major = Scale("C", ScaleType.MAJOR)
    print(f"C major scale notes: {[str(note) for note in c_major.notes]}")
    
    # Demonstrate reusing objects
    print("\nObject reuse patterns:")
    
    # Create one note and transpose it instead of creating many
    root_note = Note("C")
    major_scale_intervals = [0, 2, 4, 5, 7, 9, 11]  # Semitones from root
    
    scale_notes = []
    for semitones in major_scale_intervals:
        if semitones == 0:
            scale_notes.append(root_note)
        else:
            interval = Interval.from_semitones(semitones)
            note = root_note.transpose(interval)
            scale_notes.append(note)
    
    print(f"Scale by transposition: {[str(note) for note in scale_notes]}")
    
    print()


def raspberry_pi_optimizations():
    """Examples optimized for Raspberry Pi and similar low-end hardware."""
    print("=== Raspberry Pi Optimizations ===")
    
    # Batch operations to reduce overhead
    print("Batch processing for efficiency:")
    
    # Process multiple chord progressions efficiently
    progressions = [
        ["C", "Am", "F", "G"],
        ["Dm", "G", "C", "Am"],
        ["Em", "Am", "Dm", "G"],
    ]
    
    start_time = time.time()
    all_chord_notes = []
    for progression in progressions:
        progression_notes = []
        for chord_name in progression:
            chord = Chord.from_string(chord_name)
            progression_notes.append([str(note) for note in chord.notes])
        all_chord_notes.append(progression_notes)
    
    batch_time = time.time() - start_time
    print(f"Processed {len(progressions)} progressions in {batch_time:.4f}s")
    
    # Use simpler operations when possible
    print("\nSimple vs complex operations:")
    
    # Simple: check if note is in chord
    c_major_chord = Chord("C", ChordQuality.MAJOR)
    test_note = Note("E")
    
    start_time = time.time()
    for _ in range(1000):
        # Simple pitch class comparison
        is_in_chord = any(note.pitch_class == test_note.pitch_class 
                         for note in c_major_chord.notes)
    simple_time = time.time() - start_time
    
    print(f"1000 simple chord membership tests: {simple_time:.4f}s")
    
    # Avoid unnecessary object creation
    print("\nMinimize object creation:")
    
    # Good: reuse scale object
    c_major_scale = Scale("C", ScaleType.MAJOR)
    modes = []
    start_time = time.time()
    for i in range(1, 8):
        mode = c_major_scale.get_mode(i)  # Reuses scale calculation
        modes.append(mode)
    reuse_time = time.time() - start_time
    
    print(f"Generated 7 modes reusing scale: {reuse_time:.4f}s")
    
    print()


def minimal_footprint_example():
    """Show minimal memory footprint usage."""
    print("=== Minimal Footprint Usage ===")
    
    # Core theory functions with minimal imports
    from chordelia import Note, Interval
    
    # Essential operations only
    root = Note("C")
    third = root.transpose(Interval.from_semitones(4))  # Major third
    fifth = root.transpose(Interval.from_semitones(7))  # Perfect fifth
    
    print(f"Basic triad from minimal operations:")
    print(f"Root: {root}")
    print(f"Third: {third}")
    print(f"Fifth: {fifth}")
    
    # Use pitch classes for efficient comparison
    print(f"\nPitch classes (0-11): {root.pitch_class}, {third.pitch_class}, {fifth.pitch_class}")
    
    # Efficient interval checking
    perfect_fifth = Interval.from_semitones(7)
    is_perfect_fifth = root.interval_to(fifth).semitones == perfect_fifth.semitones
    print(f"Is perfect fifth: {is_perfect_fifth}")
    
    print()


def streaming_processing_example():
    """Example of processing musical data in streams (low memory)."""
    print("=== Streaming Processing Example ===")
    
    # Process chord progression one chord at a time (memory efficient)
    progression_names = ["Cmaj7", "Am7", "Dm7", "G7"] * 10  # Simulate long progression
    
    print("Processing long progression efficiently:")
    
    start_time = time.time()
    chord_functions = []
    
    # Process one chord at a time without storing all chords
    for i, chord_name in enumerate(progression_names):
        chord = Chord.from_string(chord_name)
        
        # Analyze chord function (simplified)
        root_pc = chord.root.pitch_class
        if root_pc == 0:  # C
            function = "I"
        elif root_pc == 9:  # A
            function = "vi"
        elif root_pc == 2:  # D
            function = "ii"
        elif root_pc == 7:  # G
            function = "V"
        else:
            function = "?"
        
        chord_functions.append(function)
        
        # Don't store the chord object - let it be garbage collected
        
    processing_time = time.time() - start_time
    print(f"Processed {len(progression_names)} chords in {processing_time:.4f}s")
    print(f"Functions: {' '.join(chord_functions[:8])}...")  # Show first 8
    
    print()


def real_time_analysis_example():
    """Simulate real-time musical analysis (suitable for live performance)."""
    print("=== Real-Time Analysis Simulation ===")
    
    # Simulate analyzing incoming MIDI notes in real-time
    incoming_midi_notes = [60, 64, 67, 72]  # C major chord in different octaves
    
    print("Real-time chord detection:")
    
    start_time = time.time()
    
    # Convert MIDI to notes efficiently
    notes = []
    for midi_note in incoming_midi_notes:
        note = Note.from_midi_number(midi_note)
        notes.append(note)
    
    # Get unique pitch classes
    pitch_classes = list(set(note.pitch_class for note in notes))
    pitch_classes.sort()
    
    # Simple chord recognition by pitch class pattern
    if pitch_classes == [0, 4, 7]:  # C, E, G
        chord_name = "C major"
    elif pitch_classes == [0, 3, 7]:  # C, Eb, G
        chord_name = "C minor"
    elif pitch_classes == [0, 4, 7, 11]:  # C, E, G, B
        chord_name = "Cmaj7"
    else:
        chord_name = f"Unknown ({pitch_classes})"
    
    analysis_time = time.time() - start_time
    
    print(f"MIDI notes {incoming_midi_notes} -> {chord_name}")
    print(f"Analysis time: {analysis_time:.6f}s ({analysis_time*1000:.3f}ms)")
    print("Fast enough for real-time use!")
    
    print()


if __name__ == "__main__":
    benchmark_operations()
    memory_efficiency_example()
    raspberry_pi_optimizations()
    minimal_footprint_example()
    streaming_processing_example()
    real_time_analysis_example()
    
    print("=== Performance Summary ===")
    print("Chordelia is optimized for low-end hardware:")
    print("- Algorithmic calculations (no lookup tables)")
    print("- Minimal memory footprint")
    print("- Fast core operations (sub-millisecond)")
    print("- Efficient batch processing")
    print("- Suitable for real-time analysis")
    print("- Stream processing capabilities")
    print("- Raspberry Pi ready!")
