# API Overview

Back links: [Project README](../README.md) | [Docs Index](README.md)

## Core Classes

- `Note`: Musical note with optional octave support.
- `Interval`: Interval quality and number with semitone math.
- `Degree`: Degree value object with numeric and Roman coercion helpers.
- `Scale`: Scale generation with theory-aware note spelling.
- `Chord`: Chord quality, extensions, inversions, and slash chords.
- `Sequenceable`: Protocol for objects that render normalized score events/consumed span and support transpose transforms.
- `NotesLike`: Protocol for values that can represent zero or more notes.
- `Sequence`: Immutable ordered timeline of sequence entries.
- `SequenceEntry`: One payload plus duration/offset timing metadata.
- `Rest`: Explicit silent payload marker for sequence timelines.
- `Score`: Canonical wrapper around a source and ordered normalized events; includes `score.duration` for normalized timeline span.
- `SheetMusic`: Canonical sheet wrapper for score-backed SVG output and notebook MIME display.
- `MidiPlayback`: Live MIDI output transport for chord, note, and score playback.
- `MidiFile`: MIDI wrapper for score conversion, file IO, and interface playback.
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
- MIDI ports: `get_midi_ports()`

## Score Conversion Workflow

- Use `Score.from_sequenceable(...)` or `score_from_sequenceable(...)` for canonical normalization.
- `Note` and `Chord` implement `Sequenceable` and provide `render_for_context(...)`.
- `Sequence` and `Rest` implement `Sequenceable` and can be converted the same way.
- Timing fields in score APIs use `Duration` objects, typically with `Duration.from_beats(...)`.
- Use `Duration.from_seconds(...)` only for fixed wall-clock offsets that should not adapt to tempo changes.
- `Score.events` are sorted deterministically for downstream consistency.
- `Score.with_tempo(...)` returns an immutable score copy with updated tempo.
- `Score.with_(...)` supports multi-field metadata updates (tempo, time signature, key signature, ppq) and optional source/events replacement in one call.
- `ScoreMetadata` includes playback articulation defaults: `gate_width` (default `0.9`), `gate_offset` (default `0.0`), and `retrigger_policy` (default `retrigger_all`; options `delta` or `retrigger_all`).
- `ScoreEvent` supports optional per-event `gate_width` and `gate_offset` overrides without changing notated duration.

### Sequence Payload Coercion

- `SequenceEntry.payload` accepts any `Sequenceable` value directly.
- Iterable payloads are interpreted as simultaneous layers.
- Iterable note strings or `Note` values are kept as one convenience chord layer.
- Iterable values containing chord-like boundaries (for example `Chord`, `Rest`, or mixed `Note` and `Chord`) preserve each item as its own simultaneous layer.
- Constructor input can include bare `Sequenceable` values, which coerce to default 1-beat entries.
- Constructor input can include child `Sequence` values, which are treated as sequenceable payloads and consume their rendered span.
- `Sequence.transpose(interval)` recursively transposes payloads while preserving entry duration and offset timing metadata.
- Empty iterables coerce to `Rest`.

Example:

```python
from chordelia import Chord, Score, ScoreEventContext, Duration

score = Score.from_sequenceable(
	Chord("C4"),
	tempo=96,
	time_signature=(3, 4),
)

first_event = score.events[0]
print(first_event.beat, first_event.duration, first_event.pitches)

context = ScoreEventContext(
	start_offset=Duration.from_beats(1, 2),
	default_duration=Duration.from_beats(3, 4),
)
```

## Degree-Aware APIs

- `Degree.coerce(...)`, `Degree.from_string(...)`, `Degree.to_int()`, `Degree.to_roman(...)`
- `Degree.accidental`, `Degree.accidental_offset`
- `Scale.degree(...)`, `Scale.mode_from_degree(...)`
- `Scale.chord_for_degree(...)`, `Scale.chords_for_degrees(...)`
- `Scale.degree_for_chord_root(...) -> Degree | None`
- `Chord.tone_at(...)`, `Chord.degree_for_tone(...) -> Degree | None`
- `Interval.degree`, `Interval.simple_degree`

## MIDI Workflow (Optional)

- Use `Score.from_sequenceable(...)` to normalize composition data.
- Use `MidiFile(score)` when you want file export and wrapper methods.
- Use `MidiFile.to_file(path)` to write a `.mid` file.
- Use `score_to_playback_notes(score, ...)` for score-backed audio-note conversion with retrigger policy (`retrigger_all` default, `delta` optional override).
- Use `MidiPlayback` directly for repeated live transport sessions and `play_score(...)`.
- `MidiPlayback.play_score(...)` accepts optional `gate_width`, `gate_offset`, and `retrigger_policy` overrides.
- Install optional dependencies with `pip install chordelia[midi]`.

Example overrides:

```python
from chordelia import MidiPlayback, Score

score = Score.from_sequenceable(sequence, tempo=112)

# Keep full written durations (100% gate) and preserve delta-style note continuity.
score = score.with_(gate_width=1.0, retrigger_policy="delta")

# Or override at playback call site only.
with MidiPlayback() as playback:
	playback.play_score(score, gate_width=1.0, retrigger_policy="delta")
```

## Sheet Music Workflow

- Use `SheetMusic(source, scale=None)` where `source` is `Score` or any `Sequenceable` input accepted by `Score.from_sequenceable(...)`.
- Use `SheetMusic.to_file(path, format="svg")` to write deterministic SVG output.
- Use `SheetMusic.score_to_file(score, path, format="svg")` for direct score-based export.
- Use notebook display via `_repr_mimebundle_` (returns `image/svg+xml` plus plain-text fallback).
- v1 boundary: write-only output; no parse/load APIs are exposed.

Example:

```python
from chordelia import Note, Sequence, SheetMusic

phrase = Sequence(((Note("C4"), 1), (Note("D4"), 1), (Note("E4"), 2)))
sheet = SheetMusic(phrase, scale="C")
sheet.to_file("phrase.svg")
```

- `SheetMusic` is part of the core package (`pip install chordelia`), with no dependency on MIDI extras.

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
