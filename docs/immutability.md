# Immutability

Back links: [Project README](../README.md) | [Docs Index](README.md)

Chordelia core value objects are immutable: operations return new instances instead of mutating existing objects.

## Duration Immutability

```python
from chordelia import Duration, NoteValue

quarter = Duration(NoteValue.QUARTER)
half = quarter * 2

print(quarter)  # quarter
print(half)     # half
```

## Chord Copy Constructors

```python
from chordelia import Chord, ChordQuality, ChordExtension

c_major = Chord("C", ChordQuality.MAJOR)

c7 = c_major.with_extension(ChordExtension.SEVENTH)
c_slash_e = c_major.with_bass("E")
c_first_inv = c_major.with_inversion(1)
f_major = c_major.with_root("F")

complex_chord = c_major.with_(
    root="F#",
    extensions=[ChordExtension.SEVENTH, ChordExtension.NINTH],
    bass_note="A",
    inversion=None,
)
```

## Scale Immutability

```python
from chordelia import Scale, ScaleType, Interval, IntervalQuality

c_major = Scale("C", ScaleType.MAJOR)
g_major = c_major.transpose(Interval(IntervalQuality.PERFECT, 5))
d_dorian = c_major.mode_from_degree(2)

print([str(n) for n in c_major.notes])
print([str(n) for n in g_major.notes])
print([str(n) for n in d_dorian.notes])
```

## Flexible Iterables in Constructors

Constructors accept any iterable for collection-style inputs.

```python
from chordelia import Chord, ChordExtension, CustomScale

chord_list = Chord("C", "major", [ChordExtension.SEVENTH])
chord_tuple = Chord("C", "major", (ChordExtension.SEVENTH,))
chord_set = Chord("C", "major", {ChordExtension.SEVENTH})
chord_gen = Chord("C", "major", (ext for ext in [ChordExtension.SEVENTH]))

custom_list = CustomScale("C", [0, 2, 4, 5, 7, 9, 11])
custom_tuple = CustomScale("C", (0, 2, 4, 5, 7, 9, 11))
custom_range = CustomScale("C", range(0, 12, 2))
```

## Immutable Collection Returns

Collection properties return tuples.

```python
chord_notes = c_major.notes
print(chord_notes[0])
print(len(chord_notes))
```

## Related

- [Scales and Chords](guides/scales-and-chords.md)
- [API Overview](api-overview.md)
