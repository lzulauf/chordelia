"""
Advanced examples demonstrating sophisticated music theory applications.

This script shows more complex uses of Chordelia including modal harmony,
chord substitutions, and theoretical analysis.
"""

from chordelia import Note, Interval, Scale, Chord
from chordelia import NoteName, Accidental, IntervalQuality, ScaleType, ChordQuality


def modal_harmony_example():
    """Demonstrate modal harmony concepts."""
    print("=== Modal Harmony Examples ===")
    
    # Generate all modes of C major
    c_major = Scale("C", ScaleType.MAJOR)
    mode_names = ["Ionian", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Aeolian", "Locrian"]
    
    print("All modes of C major:")
    for i in range(1, 8):
        mode = c_major.mode_from_degree(i)
        notes = [str(note) for note in mode.notes]
        print(f"  {mode_names[i-1]} ({mode.root}): {notes}")
    
    # Show characteristic chords of each mode
    print("\nCharacteristic chords for each mode:")
    
    # Dorian: minor tonic with natural 6th
    d_dorian = c_major.mode_from_degree(2)
    dm_add6 = Chord(
        d_dorian.root,
        ChordQuality.MINOR,
        additions=["6"],
    )
    print(f"D Dorian characteristic: Dm(add6) = {[str(note) for note in dm_add6.notes]}")
    
    # Lydian: major tonic with #11
    f_lydian = c_major.mode_from_degree(4)
    f_maj_sharp11 = Chord(
        f_lydian.root,
        ChordQuality.MAJOR,
        additions=["#11"],
    )
    print(f"F Lydian characteristic: Fmaj#11 (conceptually)")
    
    # Mixolydian: dominant 7th
    g_mixolydian = c_major.mode_from_degree(5)
    g7 = Chord(g_mixolydian.root, ChordQuality.MAJOR, extension="7")
    print(f"G Mixolydian characteristic: G7 = {[str(note) for note in g7.notes]}")
    
    print()


def chord_substitutions_example():
    """Demonstrate common chord substitutions."""
    print("=== Chord Substitutions Examples ===")
    
    # Tritone substitution (bII7 for V7)
    original_v7 = Chord.from_string("G7")
    tritone_sub = Chord.from_string("Db7")  # bII7 of C
    
    print("Tritone substitution:")
    print(f"  Original V7: G7 = {[str(note) for note in original_v7.notes]}")
    print(f"  Tritone sub: Db7 = {[str(note) for note in tritone_sub.notes]}")
    
    # Show they share the same tritone (3rd and 7th)
    g7_third = Note.from_string("B")   # 3rd of G7
    g7_seventh = Note.from_string("F") # 7th of G7
    db7_third = Note.from_string("F")  # 3rd of Db7 
    db7_seventh = Note.from_string("B") # 7th of Db7 (Cb enharmonically)
    
    print(f"  Shared tritone: B-F")
    
    # Secondary dominants
    print("\nSecondary dominants in C major:")
    c_major = Scale("C", ScaleType.MAJOR)
    
    secondary_dominants = [
        ("V7/ii", "A7", "Dm"),  # A7 -> Dm
        ("V7/iii", "B7", "Em"), # B7 -> Em  
        ("V7/IV", "C7", "F"),   # C7 -> F
        ("V7/V", "D7", "G"),    # D7 -> G
        ("V7/vi", "E7", "Am"),  # E7 -> Am
    ]
    
    for function, dom_chord, target in secondary_dominants:
        dom = Chord.from_string(dom_chord)
        tgt = Chord.from_string(target)
        print(f"  {function}: {dom.name} -> {tgt.name}")
    
    print()


def circle_of_fifths_example():
    """Demonstrate the circle of fifths."""
    print("=== Circle of Fifths Examples ===")
    
    # Generate circle of fifths starting from C
    current_note = Note("C")
    perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
    
    print("Circle of fifths (sharp side):")
    for i in range(8):
        scale = Scale(current_note, ScaleType.MAJOR)
        # Count sharps in key signature
        sharps = sum(1 for note in scale.notes if note.accidental == Accidental.SHARP)
        print(f"  {current_note} major: {sharps} sharps - {[str(note) for note in scale.notes]}")
        current_note = current_note.transpose(perfect_fifth)
    
    # Generate circle of fourths (flat side)
    print("\nCircle of fourths (flat side):")
    current_note = Note("C")
    perfect_fourth = Interval(IntervalQuality.PERFECT, 4)
    
    for i in range(8):
        scale = Scale(current_note, ScaleType.MAJOR)
        # Count flats in key signature
        flats = sum(1 for note in scale.notes if note.accidental == Accidental.FLAT)
        print(f"  {current_note} major: {flats} flats - {[str(note) for note in scale.notes]}")
        current_note = current_note.transpose(perfect_fourth)
    
    print()


def voice_leading_example():
    """Demonstrate voice leading concepts."""
    print("=== Voice Leading Examples ===")
    
    # Common tone voice leading
    progression = ["C", "Am", "F", "G"]
    chords = [Chord.from_string(chord_str) for chord_str in progression]
    
    print("Voice leading analysis (I-vi-IV-V):")
    for i in range(len(chords) - 1):
        current = chords[i]
        next_chord = chords[i + 1]
        
        print(f"\n{current.name} -> {next_chord.name}:")
        
        # Find common tones
        current_pcs = {note.pitch_class for note in current.notes}
        next_pcs = {note.pitch_class for note in next_chord.notes}
        common_pcs = current_pcs & next_pcs
        
        if common_pcs:
            common_notes = []
            for pc in common_pcs:
                # Find a note name for this pitch class
                for note in current.notes:
                    if note.pitch_class == pc:
                        common_notes.append(str(note))
                        break
            print(f"  Common tones: {', '.join(common_notes)}")
        else:
            print("  No common tones")
        
        # Show voice movement
        current_notes = [str(note) for note in current.notes]
        next_notes = [str(note) for note in next_chord.notes]
        print(f"  {current_notes} -> {next_notes}")
    
    print()


def harmonic_rhythm_example():
    """Demonstrate harmonic rhythm and chord function analysis."""
    print("=== Harmonic Function Analysis ===")
    
    # Analyze a more complex progression
    progression = ["Cmaj7", "Am7", "Dm7", "G7", "Em7", "Am7", "Dm7", "G7"]
    chords = [Chord.from_string(chord_str) for chord_str in progression]
    
    # Define function categories
    tonic_chords = ["Cmaj7", "Am7", "Em7"]
    subdominant_chords = ["Dm7", "Fmaj7"]
    dominant_chords = ["G7", "E7", "B7"]
    
    print("Functional analysis of jazz progression:")
    
    functions = []
    for chord in chords:
        if chord.name in tonic_chords:
            functions.append("T")
        elif chord.name in subdominant_chords:
            functions.append("S")
        elif chord.name in dominant_chords:
            functions.append("D")
        else:
            functions.append("?")
    
    for i, (chord, function) in enumerate(zip(chords, functions)):
        notes = [str(note) for note in chord.notes]
        print(f"  {i+1}. {chord.name} ({function}): {notes}")
    
    print(f"\nHarmonic rhythm: {' - '.join(functions)}")
    
    print()


def symmetric_scales_example():
    """Demonstrate symmetric scales and their properties."""
    print("=== Symmetric Scales Examples ===")
    
    # Chromatic scale
    c_chromatic = Scale("C", ScaleType.CHROMATIC)
    print(f"C chromatic: {[str(note) for note in c_chromatic.notes]}")
    
    # Whole tone scale  
    c_whole_tone = Scale("C", ScaleType.WHOLE_TONE)
    print(f"C whole tone: {[str(note) for note in c_whole_tone.notes]}")
    
    # Diminished scale (octatonic)
    c_diminished = Scale("C", ScaleType.DIMINISHED)
    print(f"C diminished: {[str(note) for note in c_diminished.notes]}")
    
    # Show symmetrical property of whole tone scale
    print("\nWhole tone scale symmetry:")
    print("All intervals are major seconds (2 semitones)")
    for i in range(len(c_whole_tone.notes) - 1):
        note1 = c_whole_tone.notes[i]
        note2 = c_whole_tone.notes[i + 1]
        interval = note1.interval_to(note2)
        print(f"  {note1} -> {note2}: {interval.semitones} semitones")
    
    print()


def enharmonic_analysis_example():
    """Demonstrate enharmonic equivalents and their theoretical importance."""
    print("=== Enharmonic Analysis Examples ===")
    
    # Show why enharmonic spelling matters in different keys
    keys_to_compare = [
        ("C#", "major"),
        ("Db", "major"),
    ]
    
    for key, mode in keys_to_compare:
        scale = Scale(key, ScaleType.MAJOR)
        notes = [str(note) for note in scale.notes]
        print(f"{key} {mode}: {notes}")
    
    print("\nBoth scales sound identical but are spelled differently!")
    print("C# major uses sharps: C# D# E# F# G# A# B#")
    print("Db major uses flats: Db Eb F Gb Ab Bb C")
    
    # Show enharmonic chords
    print("\nEnharmonic chord equivalents:")
    enharmonic_pairs = [
        ("C#", "Db"),
        ("F#7", "Gb7"),
        ("A#m", "Bbm"),
    ]
    
    for chord1_str, chord2_str in enharmonic_pairs:
        chord1 = Chord.from_string(chord1_str)
        chord2 = Chord.from_string(chord2_str)
        
        notes1 = [str(note) for note in chord1.notes]
        notes2 = [str(note) for note in chord2.notes]
        
        # Check if they have the same pitch classes
        pcs1 = {note.pitch_class for note in chord1.notes}
        pcs2 = {note.pitch_class for note in chord2.notes}
        
        print(f"{chord1.name}: {notes1}")
        print(f"{chord2.name}: {notes2}")
        print(f"Same pitch classes: {pcs1 == pcs2}")
        print()


if __name__ == "__main__":
    modal_harmony_example()
    chord_substitutions_example()
    circle_of_fifths_example()
    voice_leading_example()
    harmonic_rhythm_example()
    symmetric_scales_example()
    enharmonic_analysis_example()
    
    print("=== Advanced Features Summary ===")
    print("Chordelia supports sophisticated music theory analysis:")
    print("- Modal harmony and chord-scale relationships")
    print("- Voice leading and common tone analysis")
    print("- Harmonic function analysis")
    print("- Symmetric and exotic scales")
    print("- Proper enharmonic spelling in all contexts")
    print("- Circle of fifths relationships")
    print("- Chord substitution analysis")
