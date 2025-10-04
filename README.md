# Chordelia - A Comprehensive Music Theory Library

Chordelia is a Python library built around music theory concepts, designed to be clean, efficient, and capable of running on low-end hardware. It uses algorithmic approaches rather than lookup tables for maximum efficiency and clarity.

## Features

- **Intervals**: Musical intervals with names, calculations, and quality determination
- **Notes**: Musical notes with accidentals, enharmonic equivalents, double-sharps/flats, and octave information
- **Scales**: Musical scales with proper enharmonic spelling based on music theory principles
- **Chords**: Chord construction, parsing, inversions, and extensions with correct enharmonic spelling
- **Rhythm**: Musical timing, durations, time signatures, tempo, and beat tracking with real-time conversions

## Installation

### Core Library (Music Theory Only)

```bash
pip install chordelia
```

This installs the core music theory functionality with no external dependencies.

### Optional Features

For audio playback capabilities:
```bash
pip install chordelia[audio]
```

For MIDI file support:
```bash
pip install chordelia[midi]
```

For complete audio experience (playback + MIDI):
```bash
pip install chordelia[all]
```

### Development Installation

```bash
git clone https://github.com/yourusername/chordelia.git
cd chordelia
uv sync --group dev --group all
```

### What's Included

| Installation | Features Available |
|--------------|-------------------|
| `chordelia` | Core music theory: Notes, Scales, Chords, Intervals, Rhythm |
| `chordelia[audio]` | + Audio playback with multiple waveforms |
| `chordelia[midi]` | + MIDI file loading and conversion |
| `chordelia[all]` | + Complete audio experience (playback + MIDI) |

## Quick Start

### Working with Notes

```python
from chordelia import Note, NoteName, Accidental

# Create notes in different ways
c = Note(NoteName.C)
c_sharp = Note(NoteName.C, Accidental.SHARP)
middle_c = Note("C4")  # With octave
f_sharp_5 = Note.from_string("F#5")

# Notes with octave information have MIDI numbers and frequencies
print(f"Middle C MIDI: {middle_c.midi_number}")  # 60
print(f"A4 frequency: {Note('A4').frequency} Hz")  # 440.0

# Transpose notes
from chordelia import Interval, IntervalQuality
perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
g = c.transpose(perfect_fifth)
print(g)  # G

# Find intervals between notes
interval = c.interval_to(g)
print(interval)  # P5

# Work with enharmonic equivalents
c_sharp = Note("C#")
d_flat = Note("Db")
print(c_sharp.is_enharmonic_with(d_flat))  # True
print(c_sharp.enharmonic_equivalents())  # [Db, B##, etc.]

# Copy-constructor API for immutable modifications
original = Note("C4")
higher_octave = original.with_octave(5)        # C5
with_sharp = original.with_accidental("#")     # C#4
different_name = original.with_name("D")       # D4

# Combined modifications
f_sharp_6 = original.with_(name="F", accidental="#", octave=6)  # F#6

# Fluent chaining
result = Note("C").with_octave(4).with_accidental("#").with_name("F")  # F#4

# Remove octave information
pitch_class = original.with_octave(None)  # C (no octave)
```

### Working with Intervals

```python
from chordelia import Interval, IntervalQuality

# Create intervals
major_third = Interval(IntervalQuality.MAJOR, 3)
perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
minor_seventh = Interval(IntervalQuality.MINOR, 7)

# Get interval properties
print(major_third.semitones)  # 4
print(major_third.name)       # "Major 3rd"
print(major_third.is_consonant)  # True

# Create intervals from semitones
tritone = Interval.from_semitones(6)
print(tritone)  # A4 (Augmented 4th)

# Interval arithmetic
perfect_fourth = Interval(IntervalQuality.PERFECT, 4)
octave = perfect_fifth + perfect_fourth
print(octave.semitones)  # 12

# Use predefined intervals
from chordelia.intervals import MAJOR_THIRD, PERFECT_FIFTH, MINOR_SEVENTH
```

### Working with Scales

```python
from chordelia import Scale, ScaleType

# Create scales
c_major = Scale("C", ScaleType.MAJOR)
a_minor = Scale("A", ScaleType.NATURAL_MINOR)
d_dorian = Scale("D", ScaleType.DORIAN)

# Get scale notes with proper enharmonic spelling
print([str(note) for note in c_major.notes])
# ['C', 'D', 'E', 'F', 'G', 'A', 'B']

print([str(note) for note in Scale("F#", ScaleType.MAJOR).notes])
# ['F#', 'G#', 'A#', 'B', 'C#', 'D#', 'E#']

# Access specific scale degrees
print(c_major.degree(5))  # G (5th degree)

# Create modes
c_major_modes = [c_major.get_mode(i) for i in range(1, 8)]
print(c_major_modes[1].name)  # "D Dorian"

# Transpose scales
g_major = c_major.transpose(Interval(IntervalQuality.PERFECT, 5))
print([str(note) for note in g_major.notes])
# ['G', 'A', 'B', 'C', 'D', 'E', 'F#']

# Check if notes are in scale
print(c_major.contains_note(Note("E")))   # True
print(c_major.contains_note(Note("F#")))  # False

# Use convenience functions
from chordelia.scales import major_scale, minor_scale, pentatonic_major_scale
blues_scale = Scale("A", ScaleType.BLUES)
print([str(note) for note in blues_scale.notes])
# ['A', 'C', 'D', 'Eb', 'E', 'G']
```

### Working with Chords

```python
from chordelia import Chord, ChordQuality

# Create chords from components (extensions accept any iterable)
c_major = Chord("C", ChordQuality.MAJOR)
a_minor = Chord("A", ChordQuality.MINOR)
g7 = Chord("G", ChordQuality.MAJOR, extensions=["7"])           # List
g7_tuple = Chord("G", ChordQuality.MAJOR, extensions=("7",))    # Tuple
g7_set = Chord("G", ChordQuality.MAJOR, extensions={"7"})       # Set

# Parse chords from strings
chord_examples = [
    "C",           # C major
    "Am",          # A minor
    "F#dim",       # F# diminished
    "Bb+",         # Bb augmented
    "Dsus4",       # D suspended 4th
    "Cmaj7",       # C major 7th
    "Am7",         # A minor 7th
    "G9",          # G dominant 9th
    "C(add9)",     # C major add 9
    "Am/C",        # A minor over C (slash chord)
]

chords = [Chord.from_string(chord_str) for chord_str in chord_examples]
for chord in chords:
    notes = [str(note) for note in chord.notes]
    print(f"{chord.name}: {notes}")

# Immutable chord operations - all return new instances
c_major_1st = c_major.with_inversion(1)  # First inversion (E in bass)
print([str(note) for note in c_major_1st.notes])

# Add extensions with copy-constructor API
c_maj7 = c_major.with_extension("maj7")
print(c_maj7.name)  # "Cmaj7"

# Multiple modifications with fluent chaining
complex_chord = (c_major
                .with_extension("7")
                .with_bass("E")
                .with_root("F"))  # F7/E
print(complex_chord.name)

# Generic with_() method for multiple properties
modified = c_major.with_(
    root="G",
    extensions=["7", "9"],
    bass_note="B"
)  # G9/B

# Transpose chords (returns new immutable instance)
f_major = c_major.transpose(Interval(IntervalQuality.PERFECT, 4))
print(f_major.name)  # "F"

# Use convenience functions
from chordelia.chords import major_chord, minor_chord, dominant_seventh_chord
```

### Immutable Design and Copy Constructors

Chordelia's core classes (Duration, Chord, and Scale) are **immutable** - once created, their properties cannot be changed. Instead, operations return new instances with the desired modifications.

#### Duration Immutability

```python
from chordelia import Duration, NoteValue

# Durations are immutable value types
quarter = Duration(NoteValue.QUARTER)
half = quarter * 2  # Returns new Duration instance

# Original is unchanged
print(quarter)  # quarter
print(half)     # half

# Arithmetic always returns new instances
dotted = quarter + Duration(NoteValue.EIGHTH)  # New instance
triplet_quarter = quarter / 3  # New instance
```

#### Chord Copy Constructors
Chords provide rich copy-constructor APIs for fluent modifications:

```python
from chordelia import Chord, ChordQuality, ChordExtension

# Start with a basic chord
c_major = Chord("C", ChordQuality.MAJOR)

# Copy-constructor methods (all return new instances)
c7 = c_major.with_extension(ChordExtension.SEVENTH)
c_slash_e = c_major.with_bass("E")
c_first_inv = c_major.with_inversion(1)
f_major = c_major.with_root("F")

# Generic with_() method for multiple changes
complex_chord = c_major.with_(
    root="F#",
    extensions=[ChordExtension.SEVENTH, ChordExtension.NINTH],
    bass_note="A",
    inversion=None
)

# Fluent chaining
jazz_chord = (Chord("C", ChordQuality.MAJOR)
              .with_extension("maj7")
              .with_extension("9")
              .with_bass("E"))  # Cmaj9/E

# Original chord is never modified
print(c_major.name)      # "C" (unchanged)
print(jazz_chord.name)   # "Cmaj7(add9)/E"
```

#### Scale Immutability
Scales use existing method patterns that already return new instances:

```python
from chordelia import Scale, ScaleType, Interval, IntervalQuality

c_major = Scale("C", ScaleType.MAJOR)

# These methods return new Scale instances
g_major = c_major.transpose(Interval(IntervalQuality.PERFECT, 5))
d_dorian = c_major.get_mode(2)

# Original scale is unchanged
print([str(n) for n in c_major.notes])   # ['C', 'D', 'E', 'F', 'G', 'A', 'B']
print([str(n) for n in g_major.notes])   # ['G', 'A', 'B', 'C', 'D', 'E', 'F#']
print([str(n) for n in d_dorian.notes])  # ['D', 'E', 'F', 'G', 'A', 'B', 'C']
```

#### Flexible Iterables in Constructors
Constructors accept any iterable (list, tuple, set, generator, etc.) for collections:

```python
# All of these work equivalently
chord_list = Chord("C", "major", [ChordExtension.SEVENTH])           # List
chord_tuple = Chord("C", "major", (ChordExtension.SEVENTH,))         # Tuple
chord_set = Chord("C", "major", {ChordExtension.SEVENTH})            # Set
chord_gen = Chord("C", "major", (ext for ext in [ChordExtension.SEVENTH]))  # Generator

# Custom scales also accept any iterable
custom_list = CustomScale("C", [0, 2, 4, 5, 7, 9, 11])    # List
custom_tuple = CustomScale("C", (0, 2, 4, 5, 7, 9, 11))   # Tuple  
custom_range = CustomScale("C", range(0, 12, 2))          # Range (whole tone)
```

#### Immutable Collections
All collection properties return immutable tuples instead of lists:

```python
# All these return tuples (not lists)
chord_notes = c_major.notes           # tuple of Note objects
chord_extensions = c7.extensions      # tuple of ChordExtension objects
scale_notes = c_major.notes          # tuple of Note objects
scale_pattern = c_major.pattern      # tuple of integers

# Tuples support read-only operations
print(chord_notes[0])           # Indexing
print(chord_notes[1:3])         # Slicing  
print(len(chord_notes))         # Length
for note in chord_notes:        # Iteration
    print(note)

# But prevent accidental mutations
# chord_notes.append(note)      # ❌ AttributeError: 'tuple' has no attribute 'append'
# chord_notes[0] = new_note     # ❌ TypeError: 'tuple' object does not support item assignment
```

### Working with Rhythm and Timing

```python
from chordelia import (
    Duration, TimeSignature, Tempo, Beat, NoteValue,
    quarter_note, eighth_note, dotted, triplet,
    COMMON_TIME, WALTZ_TIME, COMPOUND_DUPLE
)

# Create durations
quarter = Duration(NoteValue.QUARTER)
eighth = Duration(NoteValue.EIGHTH)
dotted_quarter = dotted(quarter_note())
quarter_triplet = triplet(quarter_note())

print(f"Quarter note: {quarter}")           # quarter
print(f"Dotted quarter: {dotted_quarter}")  # dotted quarter
print(f"Quarter triplet: {quarter_triplet}") # quarter triplet

# Duration arithmetic
half_note_duration = quarter + quarter
print(f"Quarter + quarter = {half_note_duration}")  # half

# Time signatures
four_four = COMMON_TIME      # 4/4
three_four = WALTZ_TIME      # 3/4
six_eight = COMPOUND_DUPLE   # 6/8
five_four = TimeSignature.from_string("5/4")

print(f"4/4 is simple time: {four_four.is_simple_time()}")     # True
print(f"6/8 is compound time: {six_eight.is_compound_time()}")  # True

# Tempo and BPM conversions
tempo = Tempo(120)  # 120 BPM
fast_tempo = Tempo.from_marking("allegro")  # ~144 BPM

print(f"At 120 BPM, each beat = {tempo.beat_duration_ms():.1f}ms")  # 500.0ms

# Convert musical durations to real time
quarter_ms = quarter_note().to_milliseconds(tempo.bpm, four_four)
print(f"Quarter note at 120 BPM = {quarter_ms:.0f}ms")  # 500ms

# Beat position tracking
current_beat = Beat(0, 0, four_four)  # Measure 0, beat 0
current_beat = current_beat.add_duration(dotted_quarter)
print(f"After dotted quarter: {current_beat}")  # Measure 1, Beat 2.50

# Real-world example: "Take Five" timing (5/4 at 174 BPM)
take_five_tempo = Tempo(174)
take_five_time = TimeSignature(5, 4)
measure_ms = take_five_time.measure_duration.to_milliseconds(
    take_five_tempo.bpm, take_five_time
)
print(f"Take Five measure duration: {measure_ms:.0f}ms")  # 1724ms
```

### Advanced Usage: Building Progressions

```python
from chordelia import Note, Scale, Chord, ScaleType

# Create a ii-V-I progression in C major
c_major_scale = Scale("C", ScaleType.MAJOR)

# Get the chords for degrees ii, V, and I
dm7 = Chord(c_major_scale.degree(2), "minor", extensions=["7"])  # Dm7
g7 = Chord(c_major_scale.degree(5), "major", extensions=["7"])   # G7
cmaj7 = Chord(c_major_scale.degree(1), "major", extensions=["maj7"])  # Cmaj7

progression = [dm7, g7, cmaj7]
for chord in progression:
    print(f"{chord.name}: {[str(note) for note in chord.notes]}")

# Transpose the entire progression
transposed_progression = [
    chord.transpose(Interval.from_semitones(2)) 
    for chord in progression
]

print("Transposed up a whole step:")
for chord in transposed_progression:
    print(f"{chord.name}: {[str(note) for note in chord.notes]}")
```

### Complete Musical Analysis Example

```python
from chordelia import *

# Analyze "All of Me" chord progression with timing
# Key: C major, Tempo: 120 BPM, Time: 4/4

# Set up timing context
tempo = Tempo(120)
time_sig = COMMON_TIME
key = Scale("C", ScaleType.MAJOR)

# Chord progression with durations (one chord per measure)
progression = [
    ("C", whole_note()),      # I
    ("E7", whole_note()),     # V7/vi  
    ("A7", whole_note()),     # V7/ii
    ("Dm", whole_note()),     # ii
    ("G7", whole_note()),     # V7
    ("C", whole_note()),      # I
]

print("All of Me - Chord Analysis:")
print(f"Key: {key.root} {key.scale_type.value}")
print(f"Tempo: {tempo}")
print(f"Time Signature: {time_sig}")
print()

current_time = 0
for chord_name, duration in progression:
    # Parse chord
    chord = Chord.from_string(chord_name)
    
    # Get chord notes with proper voice leading
    notes = [str(note) for note in chord.notes]
    
    # Calculate timing
    duration_ms = duration.to_milliseconds(tempo.bpm, time_sig)
    
    # Analyze chord function in key
    chord_root_degree = None
    for i, scale_note in enumerate(key.notes, 1):
        if scale_note.name == chord.root.name:
            chord_root_degree = i
            break
    
    print(f"Measure {len([p for p in progression[:progression.index((chord_name, duration))+1])]}: "
          f"{chord.name} ({notes}) - "
          f"Degree: {chord_root_degree or 'chromatic'} - "
          f"Time: {current_time/1000:.1f}s - "
          f"Duration: {duration_ms/1000:.1f}s")
    
    current_time += duration_ms

print(f"\nTotal song duration: {current_time/1000:.1f} seconds")
```

### Practical Usage: Practice Metronome

```python
from chordelia import *
import time

def practice_metronome(bpm, time_signature, num_measures=4):
    """Simple practice metronome using Chordelia's timing."""
    tempo = Tempo(bpm)
    beat_duration_ms = tempo.beat_duration_ms()
    
    print(f"Metronome: {bpm} BPM in {time_signature}")
    print("Starting in 3...")
    time.sleep(1)
    print("2...")
    time.sleep(1) 
    print("1...")
    time.sleep(1)
    print("GO!")
    
    for measure in range(1, num_measures + 1):
        for beat in range(1, time_signature.numerator + 1):
            if beat == 1:
                print(f"Measure {measure}: CLICK", end="")
            else:
                print(f" click", end="")
            
            time.sleep(beat_duration_ms / 1000)  # Convert to seconds
        print()  # New line after each measure

# Example usage:
# practice_metronome(120, COMMON_TIME, 8)
```

## Design Philosophy

Chordelia is built around several key principles:

1. **Algorithmic over Lookup Tables**: All calculations are done algorithmically rather than using lookup tables, making the library lightweight and educational.

2. **Music Theory Accuracy**: Proper enharmonic spelling is maintained throughout. F# major will use F#, G#, A#, B, C#, D#, E# rather than enharmonically equivalent but theoretically incorrect names.

3. **Flexibility**: Notes, scales, and chords can work with or without octave information, making the library suitable for both abstract music theory work and concrete MIDI applications.

4. **Performance**: Designed to be efficient enough to run on low-end hardware while maintaining clarity of code.

## API Reference

### Core Classes

- **`Note`**: Represents a musical note with optional octave information
- **`Interval`**: Represents a musical interval with quality and number
- **`Scale`**: Represents a musical scale with proper enharmonic spelling
- **`Chord`**: Represents a musical chord with extensions, inversions, etc.
- **`Duration`**: Represents a musical duration with fractional precision
- **`TimeSignature`**: Represents time signatures (4/4, 3/4, 6/8, etc.)
- **`Tempo`**: Represents tempo in BPM with traditional markings
- **`Beat`**: Represents a position within a measure for beat tracking

### Enumerations

- **`NoteName`**: C, D, E, F, G, A, B
- **`Accidental`**: DOUBLE_FLAT, FLAT, NATURAL, SHARP, DOUBLE_SHARP
- **`IntervalQuality`**: PERFECT, MAJOR, MINOR, AUGMENTED, DIMINISHED, etc.
- **`ScaleType`**: MAJOR, MINOR, DORIAN, MIXOLYDIAN, PENTATONIC_MAJOR, etc.
- **`ChordQuality`**: MAJOR, MINOR, DIMINISHED, AUGMENTED, SUSPENDED_2, etc.
- **`NoteValue`**: WHOLE, HALF, QUARTER, EIGHTH, SIXTEENTH, etc.

### Convenience Functions

- **Duration Creation**: `whole_note()`, `half_note()`, `quarter_note()`, `eighth_note()`, `sixteenth_note()`
- **Duration Modification**: `dotted(duration)`, `triplet(duration)`
- **Common Time Signatures**: `COMMON_TIME` (4/4), `WALTZ_TIME` (3/4), `COMPOUND_DUPLE` (6/8)

## Real-World Applications

Chordelia is designed for practical music applications:

- **Music Education**: Teaching intervals, scales, chords, and rhythm theory
- **Composition Tools**: Building chord progressions with proper voice leading
- **MIDI Applications**: Converting between musical concepts and MIDI data
- **Practice Apps**: Metronomes, chord progression practice, timing exercises
- **Music Analysis**: Analyzing existing songs for harmonic and rhythmic content
- **Low-Resource Hardware**: Raspberry Pi music theory applications

## Testing

The library includes comprehensive tests covering all functionality:

```bash
pytest tests/  # Run all 228 tests
```

## Contributing

Contributions are welcome! Please ensure all tests pass and add tests for new functionality.

## License

MIT License - see LICENSE file for details.
