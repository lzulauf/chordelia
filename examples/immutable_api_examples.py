"""
Immutable API Examples for Chordelia

This script demonstrates the immutable design and copy-constructor patterns
used throughout Chordelia for Duration, Chord, and Scale classes.
"""

from chordelia import Duration, Chord, Scale, Note
from chordelia import NoteValue, ChordQuality, ChordExtension, ScaleType, Interval, IntervalQuality


def duration_immutability_examples():
    """Demonstrate Duration immutability and arithmetic."""
    print("=== Duration Immutability Examples ===")
    
    # Create basic durations
    quarter = Duration(NoteValue.QUARTER)
    eighth = Duration(NoteValue.EIGHTH)
    
    print(f"Original quarter note: {quarter}")
    print(f"Original eighth note: {eighth}")
    
    # Arithmetic operations return new instances
    half = quarter * 2
    dotted_quarter = quarter + eighth
    triplet_quarter = quarter / 3
    
    print(f"Quarter * 2 = {half}")
    print(f"Quarter + eighth = {dotted_quarter}")  
    print(f"Quarter / 3 = {triplet_quarter}")
    
    # Verify originals are unchanged
    print(f"Original quarter still: {quarter}")
    print(f"Original eighth still: {eighth}")
    
    # Chain operations
    complex_duration = quarter + eighth + Duration(NoteValue.SIXTEENTH)
    print(f"Complex duration: {complex_duration}")
    
    print()


def chord_copy_constructor_examples():
    """Demonstrate Chord copy-constructor APIs."""
    print("=== Chord Copy-Constructor Examples ===")
    
    # Start with a basic chord
    c_major = Chord("C", ChordQuality.MAJOR)
    print(f"Original chord: {c_major.name}")
    print(f"Original notes: {[str(note) for note in c_major.notes]}")
    
    # Demonstrate flexible iterable support
    print("\nFlexible iterable support in constructors:")
    
    # Different ways to specify extensions
    chord_list = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH])  # List
    chord_tuple = Chord("C", ChordQuality.MAJOR, (ChordExtension.SEVENTH,))  # Tuple  
    chord_set = Chord("C", ChordQuality.MAJOR, {ChordExtension.SEVENTH})   # Set
    
    print(f"From list: {chord_list.extensions}")
    print(f"From tuple: {chord_tuple.extensions}")
    print(f"From set: {chord_set.extensions}")
    
    # Individual copy-constructor methods
    print("\nIndividual modifications (each returns new instance):")
    
    c7 = c_major.with_extension(ChordExtension.SEVENTH)
    print(f"with_extension(7): {c7.name} = {[str(note) for note in c7.notes]}")
    
    c_slash_e = c_major.with_bass("E")
    print(f"with_bass(E): {c_slash_e.name} = {[str(note) for note in c_slash_e.notes]}")
    
    c_first_inv = c_major.with_inversion(1)
    print(f"with_inversion(1): {c_first_inv.name} = {[str(note) for note in c_first_inv.notes]}")
    
    f_major = c_major.with_root("F")
    print(f"with_root(F): {f_major.name} = {[str(note) for note in f_major.notes]}")
    
    # Generic with_() method for multiple changes
    print("\nGeneric with_() method:")
    complex_chord = c_major.with_(
        root="F#",
        extensions=[ChordExtension.SEVENTH, ChordExtension.NINTH],
        bass_note="A"
    )
    print(f"Multiple changes: {complex_chord.name} = {[str(note) for note in complex_chord.notes]}")
    
    # Fluent chaining
    print("\nFluent chaining:")
    jazz_chord = (Chord("C", ChordQuality.MAJOR)
                  .with_extension(ChordExtension.MAJOR_SEVENTH)
                  .with_extension(ChordExtension.NINTH)
                  .with_bass("E"))
    print(f"Chained: {jazz_chord.name} = {[str(note) for note in jazz_chord.notes]}")
    
    # Verify original is unchanged
    print(f"\nOriginal chord unchanged: {c_major.name} = {[str(note) for note in c_major.notes]}")
    
    print()


def chord_voice_leading_examples():
    """Demonstrate chord voice leading with immutable modifications."""
    print("=== Chord Voice Leading Examples ===")
    
    # Create a chord progression using copy constructors
    c_maj7 = Chord("C4", ChordQuality.MAJOR).with_extension(ChordExtension.MAJOR_SEVENTH)
    
    # Voice leading: keep common tones, move others smoothly
    a_min7 = c_maj7.with_(root="A", quality=ChordQuality.MINOR, extensions=[ChordExtension.SEVENTH])
    f_maj7 = a_min7.with_(root="F", quality=ChordQuality.MAJOR, extensions=[ChordExtension.MAJOR_SEVENTH])
    g7 = f_maj7.with_(root="G", quality=ChordQuality.MAJOR, extensions=[ChordExtension.SEVENTH])
    
    progression = [c_maj7, a_min7, f_maj7, g7]
    chord_names = ["Cmaj7", "Am7", "Fmaj7", "G7"]
    
    print("Jazz progression with voice leading:")
    for name, chord in zip(chord_names, progression):
        notes = [str(note) for note in chord.notes]
        print(f"  {name}: {notes}")
    
    print()


def scale_immutability_examples():
    """Demonstrate Scale immutability."""
    print("=== Scale Immutability Examples ===")
    
    # Create original scale
    c_major = Scale("C", ScaleType.MAJOR)
    print(f"Original scale: {c_major.name}")
    print(f"Original notes: {[str(note) for note in c_major.notes]}")
    
    # Demonstrate flexible iterable support for CustomScale
    print("\nCustom scales with different iterable types:")
    from chordelia.scales import CustomScale
    
    custom_list = CustomScale("C", [0, 2, 4, 5, 7, 9, 11])    # List
    custom_tuple = CustomScale("C", (0, 2, 4, 5, 7, 9, 11))   # Tuple
    custom_range = CustomScale("C", range(0, 12, 2))          # Range (whole tone)
    
    print(f"From list: {custom_list.pattern}")
    print(f"From tuple: {custom_tuple.pattern}")
    print(f"From range: {custom_range.pattern} (whole tone scale)")
    
    # Transpose returns new instance
    g_major = c_major.transpose(Interval(IntervalQuality.PERFECT, 5))
    print(f"Transposed: {g_major.name}")
    print(f"Transposed notes: {[str(note) for note in g_major.notes]}")
    
    # Get mode returns new instance
    d_dorian = c_major.mode_from_degree(2)
    print(f"Mode: {d_dorian.name}")
    print(f"Mode notes: {[str(note) for note in d_dorian.notes]}")
    
    # Verify original unchanged
    print(f"Original unchanged: {[str(note) for note in c_major.notes]}")
    
    print()


def immutable_collections_examples():
    """Demonstrate immutable collections (tuples) returned by properties."""
    print("=== Immutable Collections Examples ===")
    
    # Chord collections
    c7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH, ChordExtension.NINTH])
    
    print("Chord collections are tuples:")
    print(f"extensions type: {type(c7.extensions)} = {c7.extensions}")
    print(f"notes type: {type(c7.notes)} = {[str(note) for note in c7.notes]}")
    
    # Scale collections  
    c_major = Scale("C", ScaleType.MAJOR)
    
    print("\nScale collections are tuples:")
    print(f"notes type: {type(c_major.notes)} = {[str(note) for note in c_major.notes]}")
    print(f"pattern type: {type(c_major.pattern)} = {c_major.pattern}")
    
    # Tuples support read-only operations
    print("\nTuple operations (read-only):")
    print(f"First note: {c_major.notes[0]}")           # Indexing
    print(f"First three: {[str(n) for n in c_major.notes[0:3]]}")  # Slicing
    print(f"Length: {len(c_major.notes)}")             # Length
    print(f"Contains C: {Note('C') in c_major.notes}") # Membership
    
    # But prevent mutations
    print("\nMutation attempts fail safely:")
    try:
        c_major.notes[0] = Note("D")  # This would fail
    except TypeError as e:
        print(f"✓ Indexing assignment blocked: {e}")
    
    try:
        c_major.notes.append(Note("C#"))  # This would fail
    except AttributeError as e:
        print(f"✓ Append blocked: {e}")
    
    print()


def practical_progressions_example():
    """Demonstrate building progressions with immutable operations."""
    print("=== Practical Progressions Example ===")
    
    # Build a ii-V-I-vi progression in multiple keys using copy constructors
    base_chords = [
        Chord("D", ChordQuality.MINOR).with_extension(ChordExtension.SEVENTH),     # ii7
        Chord("G", ChordQuality.MAJOR).with_extension(ChordExtension.SEVENTH),     # V7  
        Chord("C", ChordQuality.MAJOR).with_extension(ChordExtension.MAJOR_SEVENTH), # Imaj7
        Chord("A", ChordQuality.MINOR).with_extension(ChordExtension.SEVENTH),     # vi7
    ]
    
    roman_numerals = ["ii7", "V7", "Imaj7", "vi7"]
    
    print("ii-V-I-vi progression in C major:")
    for roman, chord in zip(roman_numerals, base_chords):
        notes = [str(note) for note in chord.notes]
        print(f"  {roman}: {chord.name} = {notes}")
    
    # Transpose to different keys using immutable operations
    keys = [
        ("F major", Interval(IntervalQuality.PERFECT, 4)),
        ("Bb major", Interval(IntervalQuality.MINOR, 7)),
        ("Eb major", Interval(IntervalQuality.MINOR, 3)),
    ]
    
    for key_name, interval in keys:
        print(f"\nSame progression in {key_name}:")
        transposed_chords = [chord.transpose(interval) for chord in base_chords]
        
        for roman, chord in zip(roman_numerals, transposed_chords):
            notes = [str(note) for note in chord.notes]
            print(f"  {roman}: {chord.name} = {notes}")
    
    print()


if __name__ == "__main__":
    duration_immutability_examples()
    chord_copy_constructor_examples()
    chord_voice_leading_examples()
    scale_immutability_examples()
    immutable_collections_examples()
    practical_progressions_example()
    
    print("=== Summary ===")
    print("Chordelia's immutable design provides:")
    print("- Thread safety and predictable behavior")
    print("- Copy-constructor APIs for fluent modifications")
    print("- Immutable collections (tuples) preventing accidental mutations")
    print("- Clean separation between original and modified instances")
    print("- Functional programming style compatibility")
