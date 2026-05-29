# API Overview

Back links: [Project README](../README.md) | [Docs Index](README.md)

## Core Classes

- `Note`: Musical note with optional octave support.
- `Interval`: Interval quality and number with semitone math.
- `Degree`: Degree value object with numeric and Roman coercion helpers.
- `Scale`: Scale generation with theory-aware note spelling.
- `Chord`: Chord quality, extensions, inversions, and slash chords.
- `Sequenceable`: Protocol for objects that can emit normalized score events.
- `Score`: Canonical wrapper around a source and ordered normalized events.
- `Duration`: Fractional note duration utilities.
- `TimeSignature`: Meter representation such as 4/4, 3/4, 6/8.
- `Tempo`: BPM and traditional marking helpers.
- `Beat`: Position tracking within and across measures.

## Enumerations and Value Objects

- `NoteName`: C, D, E, F, G, A, B
- `Accidental`: enum with canonical constants (`DOUBLE_FLAT`, `FLAT`, `NATURAL`, `SHARP`, `DOUBLE_SHARP`) and conversion helpers (`coerce`, `from_offset`, `from_string`, `to_offset`, `to_symbol`)
- `IntervalQuality`: PERFECT, MAJOR, MINOR, AUGMENTED, DIMINISHED, and more
- `ScaleType`: MAJOR, MINOR, DORIAN, MIXOLYDIAN, PENTATONIC_MAJOR, and more
- `ChordQuality`: MAJOR, MINOR, DIMINISHED, AUGMENTED, SUSPENDED_2, and more
- `NoteValue`: WHOLE, HALF, QUARTER, EIGHTH, SIXTEENTH, and more
- `ScoreEvent`: Timed event with beat, duration, pitches, and playback metadata
- `ScoreEventContext`: Context used to convert sequenceable values into score events
- `ScoreMetadata`: Score-level metadata such as tempo, time signature, key, and ppq

## Convenience Functions

- Duration creation: `whole_note()`, `half_note()`, `quarter_note()`, `eighth_note()`, `sixteenth_note()`
- Duration modification: `dotted(duration)`, `triplet(duration)`
- Common time signatures: `COMMON_TIME`, `WALTZ_TIME`, `COMPOUND_DUPLE`
- Score conversion: `score_from_sequenceable(...)`

## Score Conversion Workflow

- Use `Score.from_sequenceable(...)` or `score_from_sequenceable(...)` for canonical normalization.
- `Note` and `Chord` implement `Sequenceable` and provide `score_events_for_context(...)`.
- `Score.events` are sorted deterministically for downstream consistency.

Example:

```python
from chordelia import Chord, Score

score = Score.from_sequenceable(
	Chord("C4"),
	tempo=96,
	time_signature=(3, 4),
)

first_event = score.events[0]
print(first_event.beat, first_event.duration, first_event.pitches)
```

## Degree-Aware APIs

- `Degree.coerce(...)`, `Degree.from_string(...)`, `Degree.to_int()`, `Degree.to_roman(...)`
- `Degree.accidental`, `Degree.accidental_offset`
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
