# Scales and Chords

Back links: [Project README](../../README.md) | [Docs Index](../README.md)

## Working with Scales

```python
from chordelia import Degree, Note, Scale, ScaleType

c_major = Scale("C", ScaleType.MAJOR)
print([str(note) for note in c_major.notes])
# ['C', 'D', 'E', 'F', 'G', 'A', 'B']

f_sharp_major = Scale("F#", ScaleType.MAJOR)
print([str(note) for note in f_sharp_major.notes])
# ['F#', 'G#', 'A#', 'B', 'C#', 'D#', 'E#']

print(c_major.degree(5))  # G
print(c_major.degree("ii"))  # D
print(c_major.degree(Degree(7)))  # B

# Methods return new immutable scales
d_dorian = c_major.shift(1)     # diatonic shift by one degree
e_phrygian = c_major.shift(2)   # diatonic shift by two degrees
g_major = c_major.transpose("P5")  # chromatic transpose by perfect fifth
c_sharp_major = c_major.transpose("1")  # chromatic transpose by one semitone

print(c_major.contains_note(Note("E")))   # True
print(c_major.contains_note(Note("F#")))  # False
```

## Degree-Aware Harmonization

```python
from chordelia import Scale, ScaleType

c_major = Scale("C", ScaleType.MAJOR)

ii = c_major.chord_for_degree("ii")
five = c_major.chord_for_degree(5)
one = c_major.chord_for_degree("I")

progression = c_major.chords_for_degrees("ii", "V", "I")
print([chord.name for chord in progression])
# ['Dm', 'G', 'C']

root_degree = c_major.degree_for_chord_root(ii.root)
print(root_degree, int(root_degree))
# 2 2
```

Roman case semantics:

- Uppercase Roman input (for example I, V) requests major function.
- Lowercase Roman input (for example ii, vi) requests minor/diminished function.
- Conflicts raise ValueError in chord_for_degree/chords_for_degrees.

## Scale Convenience Functions

```python
from chordelia.scales import major_scale, minor_scale, pentatonic_major_scale
```

## Working with Chords

```python
from chordelia import Chord, ChordQuality

c_major = Chord("C", ChordQuality.MAJOR)
g7 = Chord("G", ChordQuality.MAJOR).with_extension("7")

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

## Diatonic Chord Shift with Scale Context

```python
from chordelia import Chord, ChordQuality, Scale, ScaleType, with_global_scale_context

c_major = Scale("C", ScaleType.MAJOR)
e_minor = Chord("E", ChordQuality.MINOR)

explicit = e_minor.shift(2, scale=c_major)
print(explicit.name)  # Gm

with with_global_scale_context(c_major):
    fallback = e_minor.shift(2)
    print(fallback.name)  # Gm
```

## Progression Example

```python
from chordelia import Scale, ScaleType

c_major_scale = Scale("C", ScaleType.MAJOR)
progression = (
    c_major_scale.chord_for_degree("ii").with_extension("7"),
    c_major_scale.chord_for_degree("V").with_extension("7"),
    c_major_scale.chord_for_degree("I").with_extension("maj7"),
)

for chord in progression:
    print(f"{chord.name}: {[str(note) for note in chord.notes]}")
```

## Degree Helpers on Chords and Intervals

```python
from chordelia import Chord, Interval, IntervalQuality

g7 = Chord("G").with_extension("7")
print(g7.tone_at(1))      # G
print(g7.tone_at("III")) # D
print(g7.degree_for_tone(g7.tone_at(2)))  # 2

major_ninth = Interval(IntervalQuality.MAJOR, 9)
print(major_ninth.degree)        # 9
print(major_ninth.simple_degree) # 2
```

## Next Guide

- Continue with [Rhythm and Timing](rhythm-and-timing.md)
- Continue with [Sequences and Score](sequences-and-score.md)
- See [Immutability](../immutability.md)
