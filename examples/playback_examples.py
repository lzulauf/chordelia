"""
Chordelia Playback Examples

Demonstrates the playback module functionality with musical examples.
Requires sounddevice and numpy: pip install sounddevice numpy

Examples include:
- Playing scales and arpeggios
- Chord progressions with proper timing
- Melodies with varying rhythms
- Different waveforms and velocities
"""

import time
from chordelia import *

# Check if playback is available
try:
    from chordelia import Playback, PlaybackNote, Waveform, play_scale, play_chord, play_melody
    PLAYBACK_AVAILABLE = True
    print("Playback module available - audio examples will work!")
except ImportError as e:
    PLAYBACK_AVAILABLE = False
    print(f"Playback module not available: {e}")
    print("Install dependencies: pip install sounddevice numpy")


def basic_playback_examples():
    """Demonstrate basic playback functionality."""
    if not PLAYBACK_AVAILABLE:
        print("Skipping basic playback examples - dependencies not available")
        return
        
    print("\n=== Basic Playback Examples ===")
    
    tempo = Tempo(120)
    
    # Example 1: Play a C major scale
    print("1. Playing C major scale...")
    c_major = Scale("C", ScaleType.MAJOR)
    play_scale(c_major, tempo, quarter_note(), octave=4)
    
    time.sleep(0.5)  # Brief pause between examples
    
    # Example 2: Play a C major chord
    print("2. Playing C major chord...")
    c_chord = Chord.from_string("C")
    play_chord(c_chord, tempo, whole_note(), octave=4)
    
    time.sleep(0.5)
    
    # Example 3: Play a simple melody
    print("3. Playing simple melody (C-D-E-F-G)...")
    melody = [
        (Note("C4"), quarter_note()),
        (Note("D4"), quarter_note()),
        (Note("E4"), quarter_note()),
        (Note("F4"), quarter_note()),
        (Note("G4"), half_note()),
    ]
    play_melody(melody, tempo)
    
    print("Basic examples complete!\n")


def chord_progression_example():
    """Demonstrate playing a chord progression with proper timing."""
    if not PLAYBACK_AVAILABLE:
        print("Skipping chord progression example - dependencies not available")
        return
        
    print("=== Chord Progression Example ===")
    print("Playing I-vi-IV-V progression in C major...")
    
    # Classic progression: C - Am - F - G
    progression_chords = ["C", "Am", "F", "G"]
    tempo = Tempo(100)  # Slightly slower for chord changes
    
    notes = []
    current_time = Duration(0)
    chord_duration = whole_note()
    
    for chord_name in progression_chords:
        chord = Chord.from_string(chord_name)
        print(f"  {chord.name}: {[str(note) for note in chord.notes]}")
        
        # Add each chord note starting at the same time
        for i, chord_note in enumerate(chord.notes):
            # Distribute notes across octaves for better voice leading
            octave = 4 + (i // 7)
            note = Note(chord_note.name, chord_note.accidental, octave)
            
            notes.append(PlaybackNote(
                start_time=current_time,
                note=note,
                duration=chord_duration,
                velocity=0.4  # Quieter for chord playback
            ))
        
        current_time = current_time + chord_duration
    
    # Play the progression
    with Playback(tempo) as player:
        player.play_sequence(notes)
    
    print("Chord progression complete!\n")


def melody_with_rhythm_example():
    """Demonstrate melody with complex rhythms."""
    if not PLAYBACK_AVAILABLE:
        print("Skipping melody example - dependencies not available")
        return
        
    print("=== Melody with Rhythm Example ===")
    print("Playing 'Mary Had a Little Lamb' with proper rhythm...")
    
    # Mary Had a Little Lamb - simplified version
    melody_notes = [
        (Note("E4"), quarter_note()),  # Ma-
        (Note("D4"), quarter_note()),  # ry
        (Note("C4"), quarter_note()),  # had
        (Note("D4"), quarter_note()),  # a
        (Note("E4"), quarter_note()),  # lit-
        (Note("E4"), quarter_note()),  # tle
        (Note("E4"), half_note()),     # lamb
        
        (Note("D4"), quarter_note()),  # lit-
        (Note("D4"), quarter_note()),  # tle
        (Note("D4"), half_note()),     # lamb
        
        (Note("E4"), quarter_note()),  # lit-
        (Note("G4"), quarter_note()),  # tle
        (Note("G4"), half_note()),     # lamb
    ]
    
    tempo = Tempo(120)
    
    print("Notes and rhythms:")
    for note, duration in melody_notes:
        print(f"  {note} - {duration}")
    
    play_melody(melody_notes, tempo)
    print("Melody complete!\n")


def arpeggio_example():
    """Demonstrate playing arpeggios across octaves."""
    if not PLAYBACK_AVAILABLE:
        print("Skipping arpeggio example - dependencies not available")
        return
        
    print("=== Arpeggio Example ===")
    print("Playing C major arpeggio across multiple octaves...")
    
    # C major arpeggio: C-E-G ascending through octaves
    tempo = Tempo(144)  # Faster tempo for arpeggios
    
    notes = []
    current_time = Duration(0)
    note_duration = eighth_note()
    
    # Arpeggio pattern
    pattern = ["C", "E", "G"]
    octaves = [3, 4, 5, 6]  # Ascending through octaves
    
    for octave in octaves:
        for note_name in pattern:
            note = Note(f"{note_name}{octave}")
            notes.append(PlaybackNote(
                start_time=current_time,
                note=note,
                duration=note_duration,
                velocity=0.6
            ))
            current_time = current_time + note_duration
    
    # Add descending pattern
    for octave in reversed(octaves):
        for note_name in reversed(pattern):
            note = Note(f"{note_name}{octave}")
            notes.append(PlaybackNote(
                start_time=current_time,
                note=note,
                duration=note_duration,
                velocity=0.6
            ))
            current_time = current_time + note_duration
    
    with Playback(tempo) as player:
        player.play_sequence(notes)
    
    print("Arpeggio complete!\n")


def advanced_timing_example():
    """Demonstrate advanced timing with triplets and dotted notes."""
    if not PLAYBACK_AVAILABLE:
        print("Skipping advanced timing example - dependencies not available")
        return
        
    print("=== Advanced Timing Example ===")
    print("Playing rhythm with triplets and dotted notes...")
    
    tempo = Tempo(120)
    
    # Complex rhythm pattern
    rhythm_pattern = [
        (Note("C4"), quarter_note()),      # Regular quarter
        (Note("D4"), dotted(quarter_note())),  # Dotted quarter
        (Note("E4"), eighth_note()),       # Eighth to complete the dotted quarter
        (Note("F4"), triplet(quarter_note())),  # Quarter triplet
        (Note("G4"), triplet(quarter_note())),  # Quarter triplet  
        (Note("A4"), triplet(quarter_note())),  # Quarter triplet
        (Note("B4"), half_note()),         # Half note
    ]
    
    print("Complex rhythm pattern:")
    for note, duration in rhythm_pattern:
        print(f"  {note} - {duration}")
    
    play_melody(rhythm_pattern, tempo)
    print("Advanced timing complete!\n")


def different_waveforms_example():
    """Demonstrate different waveforms using the AudioBackend directly."""
    if not PLAYBACK_AVAILABLE:
        print("Skipping waveforms example - dependencies not available")
        return
        
    print("=== Different Waveforms Example ===")
    print("Playing the same note (A4 - 440Hz) with different waveforms...")
    
    # Import and use AudioBackend directly for waveform control
    from chordelia.audio_playback import AudioBackend
    
    backend = AudioBackend()
    backend.start()
    
    try:
        note = Note("A4")  # 440 Hz
        frequency = note.frequency
        duration = 1.0  # 1 second per waveform
        velocity = 0.6  # Moderate volume
        
        # Play the same note with each waveform
        waveforms = [
            (Waveform.SINE, "Sine Wave (smooth, pure tone)"),
            (Waveform.SQUARE, "Square Wave (hollow, 8-bit sound)"),
            (Waveform.SAWTOOTH, "Sawtooth Wave (bright, buzzy)"),
            (Waveform.TRIANGLE, "Triangle Wave (mellow, flute-like)")
        ]
        
        for waveform, description in waveforms:
            print(f"Playing {description}...")
            backend.play_note(frequency, duration, velocity, waveform)
            time.sleep(duration + 0.3)  # Wait for note to finish plus a brief pause
            
    finally:
        backend.stop()
    
    print("Waveform example complete!\n")


def tempo_comparison_example():
    """Demonstrate the same melody at different tempos."""
    if not PLAYBACK_AVAILABLE:
        print("Skipping tempo comparison - dependencies not available")
        return
        
    print("=== Tempo Comparison Example ===")
    print("Playing the same scale at different tempos...")
    
    scale = Scale("G", ScaleType.MAJOR)
    note_duration = quarter_note()
    
    tempos = [Tempo(60), Tempo(120), Tempo(180)]  # Slow, medium, fast
    
    for tempo in tempos:
        print(f"Playing G major scale at {tempo.bpm} BPM...")
        play_scale(scale, tempo, note_duration, octave=4)
        time.sleep(0.5)  # Brief pause between tempos
    
    print("Tempo comparison complete!\n")


def jazz_chord_voicing_example():
    """Demonstrate jazz chord voicings."""
    if not PLAYBACK_AVAILABLE:
        print("Skipping jazz chord example - dependencies not available")
        return
        
    print("=== Jazz Chord Voicing Example ===")
    print("Playing jazz chord progression: Cmaj7 - Am7 - Dm7 - G7...")
    
    # Jazz ii-V-I with extensions
    jazz_chords = ["Cmaj7", "Am7", "Dm7", "G7"]
    tempo = Tempo(80)  # Slower jazz tempo
    
    for chord_name in jazz_chords:
        print(f"Playing {chord_name}...")
        chord = Chord.from_string(chord_name)
        play_chord(chord, tempo, dotted(half_note()), octave=4)
        time.sleep(0.2)  # Brief pause between chords
    
    print("Jazz chord example complete!\n")


def real_time_composition_example():
    """Demonstrate building a sequence programmatically."""
    if not PLAYBACK_AVAILABLE:
        print("Skipping composition example - dependencies not available")
        return
        
    print("=== Real-time Composition Example ===")
    print("Generating and playing a procedural melody...")
    
    # Generate a simple melody using scale degrees
    scale = Scale("C", ScaleType.MAJOR)
    tempo = Tempo(140)
    
    # Simple melody pattern: 1-3-5-3-2-4-3-1
    scale_degrees = [1, 3, 5, 3, 2, 4, 3, 1]
    durations = [quarter_note(), eighth_note(), eighth_note(), quarter_note(),
                eighth_note(), eighth_note(), quarter_note(), half_note()]
    
    melody = []
    for degree, duration in zip(scale_degrees, durations):
        scale_note = scale.degree(degree)
        note = Note(scale_note.name, scale_note.accidental, 4)
        melody.append((note, duration))
    
    print("Generated melody:")
    for note, duration in melody:
        degree = scale.degree_for_chord_root(note)
        degree_str = str(degree) if degree else "?"  
        print(f"  {note} (degree {degree_str}) - {duration}")
    
    play_melody(melody, tempo)
    print("Composition example complete!\n")


def main():
    """Run all playback examples."""
    print("Chordelia Playback Examples")
    print("=" * 40)
    
    if not PLAYBACK_AVAILABLE:
        print("Audio dependencies not available.")
        print("To hear these examples, install: pip install sounddevice numpy")
        print("\nRunning examples in demonstration mode (no audio)...\n")
    
    try:
        # basic_playback_examples()
        # chord_progression_example()
        # melody_with_rhythm_example()
        # arpeggio_example()
        # advanced_timing_example()
        # different_waveforms_example()
        tempo_comparison_example()
        jazz_chord_voicing_example()
        real_time_composition_example()
        
        print("All examples complete!")
        
        if PLAYBACK_AVAILABLE:
            print("\nTip: Try modifying the examples above to create your own musical sequences!")
        else:
            print("\nInstall audio dependencies to hear the examples: pip install sounddevice numpy")
            
    except KeyboardInterrupt:
        print("\nExamples interrupted by user.")
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure audio dependencies are installed: pip install sounddevice numpy")


if __name__ == "__main__":
    main()
