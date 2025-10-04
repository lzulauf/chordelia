"""
Basic examples demonstrating the core functionality of Chordelia.

This script shows how to work with notes, intervals, scales, and chords.
"""

from chordelia import Note, Interval, Scale, Chord
from chordelia import NoteName, Accidental, IntervalQuality, ScaleType, ChordQuality


def notes_example():
    """Demonstrate working with notes."""
    print("=== Notes Examples ===")
    
    # Creating notes
    c = Note(NoteName.C)
    c_sharp = Note(NoteName.C, Accidental.SHARP)
    middle_c = Note.from_string("C4")
    
    print(f"C: {c}")
    print(f"C#: {c_sharp}")
    print(f"Middle C: {middle_c} (MIDI: {middle_c.midi_number})")
    
    # Enharmonic equivalents
    d_flat = Note.from_string("Db")
    print(f"C# and Db are enharmonic: {c_sharp.is_enharmonic_with(d_flat)}")
    
    # Transposition
    perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
    g = c.transpose(perfect_fifth)
    print(f"C transposed up a perfect fifth: {g}")
    
    # Frequency calculation
    a4 = Note.from_string("A4")
    print(f"A4 frequency: {a4.frequency:.2f} Hz")
    
    print()


def intervals_example():
    """Demonstrate working with intervals."""
    print("=== Intervals Examples ===")
    
    # Creating intervals
    major_third = Interval(IntervalQuality.MAJOR, 3)
    perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
    
    print(f"Major third: {major_third.name} ({major_third.semitones} semitones)")
    print(f"Perfect fifth: {perfect_fifth.name} ({perfect_fifth.semitones} semitones)")
    print(f"Perfect fifth is consonant: {perfect_fifth.is_consonant}")
    
    # Interval arithmetic
    octave = major_third + Interval(IntervalQuality.MINOR, 6)
    print(f"Major 3rd + minor 6th = {octave.semitones} semitones")
    
    # Creating from semitones
    tritone = Interval.from_semitones(6)
    print(f"6 semitones = {tritone}")
    
    print()


def scales_example():
    """Demonstrate working with scales."""
    print("=== Scales Examples ===")
    
    # Major scales
    c_major = Scale("C", ScaleType.MAJOR)
    print(f"C major: {[str(note) for note in c_major.notes]}")
    
    # Scales with accidentals
    fs_major = Scale("F#", ScaleType.MAJOR)
    print(f"F# major: {[str(note) for note in fs_major.notes]}")
    
    # Minor scales
    a_minor = Scale("A", ScaleType.NATURAL_MINOR)
    print(f"A natural minor: {[str(note) for note in a_minor.notes]}")
    
    a_harmonic = Scale("A", ScaleType.HARMONIC_MINOR)
    print(f"A harmonic minor: {[str(note) for note in a_harmonic.notes]}")
    
    # Modes
    d_dorian = c_major.get_mode(2)
    print(f"D dorian (2nd mode of C major): {[str(note) for note in d_dorian.notes]}")
    
    # Pentatonic scales
    c_pentatonic = Scale("C", ScaleType.PENTATONIC_MAJOR)
    print(f"C major pentatonic: {[str(note) for note in c_pentatonic.notes]}")
    
    # Blues scale
    a_blues = Scale("A", ScaleType.BLUES)
    print(f"A blues: {[str(note) for note in a_blues.notes]}")
    
    print()


def chords_example():
    """Demonstrate working with chords."""
    print("=== Chords Examples ===")
    
    # Basic triads
    c_major = Chord("C", ChordQuality.MAJOR)
    a_minor = Chord("A", ChordQuality.MINOR)
    b_dim = Chord("B", ChordQuality.DIMINISHED)
    
    print(f"C major: {[str(note) for note in c_major.notes]}")
    print(f"A minor: {[str(note) for note in a_minor.notes]}")
    print(f"B diminished: {[str(note) for note in b_dim.notes]}")
    
    # Seventh chords
    c7 = Chord.from_string("C7")
    cmaj7 = Chord.from_string("Cmaj7")
    am7 = Chord.from_string("Am7")
    
    print(f"C7: {[str(note) for note in c7.notes]}")
    print(f"Cmaj7: {[str(note) for note in cmaj7.notes]}")
    print(f"Am7: {[str(note) for note in am7.notes]}")
    
    # Extended chords
    c9 = Chord.from_string("C9")
    print(f"C9: {[str(note) for note in c9.notes]}")
    
    # Suspended chords
    csus2 = Chord.from_string("Csus2")
    csus4 = Chord.from_string("Csus4")
    print(f"Csus2: {[str(note) for note in csus2.notes]}")
    print(f"Csus4: {[str(note) for note in csus4.notes]}")
    
    # Slash chords
    c_over_e = Chord.from_string("C/E")
    print(f"C/E: {[str(note) for note in c_over_e.notes]}")
    
    # Add chords
    cadd9 = Chord.from_string("C(add9)")
    print(f"C(add9): {[str(note) for note in cadd9.notes]}")
    
    print()


def chord_progressions_example():
    """Demonstrate building chord progressions."""
    print("=== Chord Progressions Examples ===")
    
    # I-vi-IV-V progression in C major
    progression = ["C", "Am", "F", "G"]
    chords = [Chord.from_string(chord_str) for chord_str in progression]
    
    print("I-vi-IV-V in C major:")
    for i, chord in enumerate(chords):
        roman = ["I", "vi", "IV", "V"][i]
        notes = [str(note) for note in chord.notes]
        print(f"  {roman}: {chord.name} = {notes}")
    
    # ii-V-I in jazz
    print("\nii-V-I in C major (jazz):")
    jazz_progression = ["Dm7", "G7", "Cmaj7"]
    jazz_chords = [Chord.from_string(chord_str) for chord_str in jazz_progression]
    
    for i, chord in enumerate(jazz_chords):
        roman = ["ii7", "V7", "Imaj7"][i]
        notes = [str(note) for note in chord.notes]
        print(f"  {roman}: {chord.name} = {notes}")
    
    # Transpose the progression to D major
    print("\nSame progression transposed to D major:")
    major_second = Interval(IntervalQuality.MAJOR, 2)
    transposed = [chord.transpose(major_second) for chord in jazz_chords]
    
    for i, chord in enumerate(transposed):
        roman = ["ii7", "V7", "Imaj7"][i]
        notes = [str(note) for note in chord.notes]
        print(f"  {roman}: {chord.name} = {notes}")
    
    print()


def harmonic_analysis_example():
    """Demonstrate harmonic analysis capabilities."""
    print("=== Harmonic Analysis Examples ===")
    
    # Analyze which chords fit in a scale
    c_major_scale = Scale("C", ScaleType.MAJOR)
    
    print("Diatonic triads in C major:")
    for i in range(1, 8):
        root = c_major_scale.degree(i)
        
        # Try major, minor, and diminished to see which fits
        for quality in [ChordQuality.MAJOR, ChordQuality.MINOR, ChordQuality.DIMINISHED]:
            try:
                chord = Chord(root, quality)
                # Check if all chord tones are in the scale
                all_in_scale = all(c_major_scale.contains_note(note) for note in chord.notes)
                
                if all_in_scale:
                    roman_numerals = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
                    notes = [str(note) for note in chord.notes]
                    print(f"  {roman_numerals[i-1]}: {chord.name} = {notes}")
                    break
            except:
                continue
    
    print()


if __name__ == "__main__":
    notes_example()
    intervals_example()
    scales_example()
    chords_example()
    chord_progressions_example()
    harmonic_analysis_example()
    
    print("=== Summary ===")
    print("Chordelia provides comprehensive music theory tools with:")
    print("- Algorithmic calculation (no lookup tables)")
    print("- Proper enharmonic spelling")
    print("- Support for octave information")
    print("- Extensive chord and scale support")
    print("- Clean, intuitive API")
