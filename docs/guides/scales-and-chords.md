# Scales and Chords

Back links: [Project README](../../README.md) | [Docs Index](../README.md)

## Working with Scales

```python
from chordelia import Scale, ScaleType, Note, Interval, IntervalQuality

c_major = Scale("C", ScaleType.MAJOR)
print([str(note) for note in c_major.notes])
# ['C', 'D', 'E', 'F', 'G', 'A', 'B']

f_sharp_major = Scale("F#", ScaleType.MAJOR)
print([str(note) for note in f_sharp_major.notes])
# ['F#', 'G#', 'A#', 'B', 'C#', 'D#', 'E#']

print(c_major.degree(5))  # G

# Methods return new immutable scales
g_major = c_major.transpose(Interval(IntervalQuality.PERFECT, 5))
d_dorian = c_major.mode_from_degree(2)

print(c_major.contains_note(Note("E")))   # True
print(c_major.contains_note(Note("F#")))  # False
```

## Scale Convenience Functions

```python
from chordelia.scales import major_scale, minor_scale, pentatonic_major_scale
```

## Working with Chords

```python
from chordelia import Chord, ChordQuality

c_major = Chord("C", ChordQuality.MAJOR)
g7 = Chord("G", ChordQuality.MAJOR, extensions=["7"])

examples = ["C", "Am", "F#dim", "Bb+", "Dsus4", "Cmaj7", "G9", "Am/C"]
parsed = [Chord.from_string(ch) for ch in examples]
for chord in parsed:
    print(chord.name, [str(note) for note in chord.notes])
```

## Immutable Chord Transformations

```python
from chordelia import Chord, Interval

c_major = Chord("C")
c_first_inv = c_major.with_inversion(1)
c_maj7 = c_major.with_extension("maj7")

complex_chord = (
    c_major
    .with_extension("7")
    .with_bass("E")
    .with_root("F")
)

modified = c_major.with_(root="G", extensions=["7", "9"], bass_note="B")
f_major = c_major.transpose(Interval.from_semitones(5))
```

## Progression Example

```python
from chordelia import Scale, ScaleType, Chord, Interval

c_major_scale = Scale("C", ScaleType.MAJOR)
progression = [
    Chord(c_major_scale.degree(2), "minor", extensions=["7"]),
    Chord(c_major_scale.degree(5), "major", extensions=["7"]),
    Chord(c_major_scale.degree(1), "major", extensions=["maj7"]),
]

for chord in progression:
    print(f"{chord.name}: {[str(note) for note in chord.notes]}")

transposed = [chord.transpose(Interval.from_semitones(2)) for chord in progression]
```

## Next Guide

- Continue with [Rhythm and Timing](rhythm-and-timing.md)
- See [Immutability](../immutability.md)
