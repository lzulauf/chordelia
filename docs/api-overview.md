# API Overview

Back links: [Project README](../README.md) | [Docs Index](README.md)

## Core Classes

- `Note`: Musical note with optional octave support.
- `Interval`: Interval quality and number with semitone math.
- `Degree`: Degree value object with numeric and Roman coercion helpers.
- `Scale`: Scale generation with theory-aware note spelling.
- `Chord`: Chord quality, extensions, inversions, and slash chords.
- `Duration`: Fractional note duration utilities.
- `TimeSignature`: Meter representation such as 4/4, 3/4, 6/8.
- `Tempo`: BPM and traditional marking helpers.
- `Beat`: Position tracking within and across measures.

## Enumerations

- `NoteName`: C, D, E, F, G, A, B
- `Accidental`: DOUBLE_FLAT, FLAT, NATURAL, SHARP, DOUBLE_SHARP
- `IntervalQuality`: PERFECT, MAJOR, MINOR, AUGMENTED, DIMINISHED, and more
- `ScaleType`: MAJOR, MINOR, DORIAN, MIXOLYDIAN, PENTATONIC_MAJOR, and more
- `ChordQuality`: MAJOR, MINOR, DIMINISHED, AUGMENTED, SUSPENDED_2, and more
- `NoteValue`: WHOLE, HALF, QUARTER, EIGHTH, SIXTEENTH, and more

## Convenience Functions

- Duration creation: `whole_note()`, `half_note()`, `quarter_note()`, `eighth_note()`, `sixteenth_note()`
- Duration modification: `dotted(duration)`, `triplet(duration)`
- Common time signatures: `COMMON_TIME`, `WALTZ_TIME`, `COMPOUND_DUPLE`

## Degree-Aware APIs

- `Degree.coerce(...)`, `Degree.from_string(...)`, `Degree.to_int()`, `Degree.to_roman(...)`
- `Scale.degree(...)`, `Scale.mode_from_degree(...)`
- `Scale.chord_for_degree(...)`, `Scale.chords_for_degrees(...)`
- `Scale.degree_for_chord_root(...) -> Degree | None`
- `Chord.tone_at(...)`, `Chord.degree_for_tone(...) -> Degree | None`
- `Interval.degree`, `Interval.simple_degree`

## Real-World Applications

- Music education and theory tooling
- Composition and progression building
- MIDI conversion and tooling
- Practice apps and metronome workflows
- Harmonic and rhythmic analysis
- Low-resource hardware deployments

## Related

- [Quickstart](quickstart.md)
- [Development Guide](development.md)
