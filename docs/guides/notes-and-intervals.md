# Notes and Intervals

Back links: [Project README](../../README.md) | [Docs Index](../README.md)

## Working with Notes

```python
from chordelia import Note, NoteName, Accidental

# Create notes in different ways
c = Note(NoteName.C)
c_sharp = Note(NoteName.C, Accidental.SHARP)
middle_c = Note("C4")
f_sharp_5 = Note.from_string("F#5")

print(f"Middle C MIDI: {middle_c.midi_number}")  # 60
print(f"A4 frequency: {Note('A4').frequency} Hz")  # 440.0
```

## Transposition and Interval Detection

```python
from chordelia import Note, Interval, IntervalQuality

c = Note("C")
perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
g = c.transpose(perfect_fifth)

print(g)  # G
print(c.interval_to(g))  # P5
```

## Shift vs Transpose

```python
from chordelia import Note, Scale, ScaleType, with_global_scale_context

c_major = Scale("C", ScaleType.MAJOR)
note = Note("E4")

print(note.shift(2, scale=c_major))  # G4 (diatonic shift)

with with_global_scale_context(c_major):
	print(note.shift(2))  # G4 (same result via global fallback)

print(note.transpose(1))   # F4 (one semitone)
print(note.transpose("P5"))  # B4 (explicit interval quality)
```

## Enharmonic Equivalents

```python
from chordelia import Note

c_sharp = Note("C#")
d_flat = Note("Db")

print(c_sharp.is_enharmonic_with(d_flat))  # True
print(c_sharp.enharmonic_equivalents())
```

## Immutable Note Modifications

```python
from chordelia import Note

original = Note("C4")
higher_octave = original.with_octave(5)        # C5
with_sharp = original.with_accidental("#")     # C#4
different_name = original.with_name("D")       # D4

combined = original.with_(name="F", accidental="#", octave=6)  # F#6
chained = Note("C").with_octave(4).with_accidental("#").with_name("F")  # F#4
pitch_class = original.with_octave(None)  # Remove octave
```

## Working with Intervals

```python
from chordelia import Interval, IntervalQuality

major_third = Interval(IntervalQuality.MAJOR, 3)
perfect_fifth = Interval(IntervalQuality.PERFECT, 5)

print(major_third.semitones)      # 4
print(major_third.name)           # Major 3rd
print(major_third.is_consonant)   # True

tritone = Interval.from_semitones(6)
print(tritone)  # A4

perfect_fourth = Interval(IntervalQuality.PERFECT, 4)
octave = perfect_fifth + perfect_fourth
print(octave.semitones)  # 12
```

## Convenience Constants

```python
from chordelia.intervals import MAJOR_THIRD, PERFECT_FIFTH, MINOR_SEVENTH
```

## Next Guide

- Continue with [Scales and Chords](scales-and-chords.md)
