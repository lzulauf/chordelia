# API Overview

Back links: [Project README](../README.md) | [Docs Index](README.md)

Use this page as a symbol map. It tells you where each API area lives and where to
find deeper behavior docs.

## Core Theory

Main classes:

- `Note`, `NoteName`, `Accidental`
- `Interval`, `IntervalQuality`
- `Degree`, `RomanCase`
- `Scale`, `ScaleType`
- `Chord`, `ChordQuality`, `ChordExtension`

Related deep docs:

- [Notes and Intervals](guides/notes-and-intervals.md)
- [Scales and Chords](guides/scales-and-chords.md)

## Rhythm and Timing

Main classes:

- `Duration`, `TimeSignature`, `Tempo`, `Beat`

Helpers/constants:

- `Duration("whole")`, `Duration("half")`, `Duration("quarter")`, `Duration("eighth")`, `Duration("sixteenth")`
- `dotted(duration)`, `triplet(duration)`
- `COMMON_TIME`, `WALTZ_TIME`, `COMPOUND_DUPLE`

Related deep docs:

- [Rhythm and Timing](guides/rhythm-and-timing.md)

## Randomization

Main APIs:

- `Random(seed=None, engine=None)`
- `Random.choice(...)`, `Random.weighted_choice(...)`, `Random.weighted_choice_map(...)`
- `Random.scale(...)`, `Random.degree(...)`, `Random.note(...)`, `Random.chord(...)`
- `Random.chromatic_note(...)`, `Random.chromatic_chord(...)`, `Random.interval(...)`
- `Random.sequence(...)`
- `SequenceRandomizationAlgorithm`
- `PureRandomSequenceAlgorithm`, `MotifVariationSequenceAlgorithm`, `ScaleWalkSequenceAlgorithm`, `ChordAnchorWalkSequenceAlgorithm`
- `get_global_random()`, `configure_global_random(...)`, `reset_global_random()`

Key behaviors:

- Uniform selectors sample from non-empty candidate sets.
- Weighted selectors use relative numeric values (integers are fine; totals do not need to sum to 1 or 100) and reject negative, non-finite, or all-zero inputs.
- Scale-aware selectors (`degree`, `note`, `chord`) resolve scale in this order: explicit `scale=...`, then global context helpers.
- Chromatic selectors ignore scale context by design.
- `Random.engine` exposes the wrapped stdlib engine so direct engine calls share state with Random selectors.
- Selector methods support both instance and class calls; class calls route through the lazy global singleton.
- `Random.sequence(...)` requires a positive beat-length timeline value and returns a `Sequence` that consumes exactly that beat span.
- Sequence algorithm resolution order is: explicit algorithm instance, algorithm name token, then weighted random selection (only when `algorithm` is omitted).
- Built-in sequence algorithms accept optional tuning parameters, but each works with no required algorithm-specific arguments.
- Reusing the same algorithm object instance allows stateful continuity across calls (for example motif carry-forward).
- Sequence continuation behavior is playback-equivalent duration extension of the previous pitched entry, not notation-specific tie modeling.

Usage note:

- Prefer `rng = Random(seed=...)` for isolated reproducible workflows.
- Use `Random.scale(...)` and other class calls when a shared process-global random stream is desired.

Related deep docs:

- [Cookbook](cookbook.md)

## Sequence, Score, and Conversion

Timeline and conversion types:

- `Sequence`, `SequenceEntry`, `SequenceEntryLike`, `Rest`
- `Sequenceable`, `NotesLike`
- `Score`, `ScoreEvent`, `ScoreEventContext`, `ScoreMetadata`

Score conversion entry points:

- `Score.from_sequenceable(...)`
- `score_from_sequenceable(...)`

Scale context helpers for diatonic workflows:

- `set_global_scale_context(...)`
- `get_global_scale_context()`
- `reset_global_scale_context()`
- `with_global_scale_context(...)`

Key behaviors:

- `Sequence.appended(...)` composes forms immutably.
- `Sequence.transpose(...)` is chromatic (semitones).
- `Sequence.shift(...)` is diatonic (scale steps).
- `Note.shift(...)` and `Chord.shift(...)` use `scale=...` when provided and otherwise use global scale context helpers.
- `Score.duration` returns normalized timeline span.
- `Score.with_(...)` returns immutable metadata/source/event updates.
- `MidiFile(...)` and `SheetMusic(...)` both normalize through the same score-first conversion path.

Compatibility note:

- `score_from_sequenceable(...)` is retained as a compatibility helper.
- `Score.from_sequenceable(...)` is the canonical constructor-style entry point.
- Direct conversion sources must be `Score` or `Sequenceable` values (for example `Note`, `Chord`, `Sequence`, `Rest`); `Scale` and `Degree` are not accepted as direct score-wrapper inputs.

Related deep docs:

- [Sequences and Score](guides/sequences-and-score.md)
- [Song Form from a Motif](tutorials/song-form-from-motif.md)

## Sheet Music and Rendering

Core rendering API:

- `SheetMusic(source, scale=None)`
- `SheetMusic.to_file(path, format="svg")`
- `SheetMusic.score_to_file(score, path, format="svg")`

Runtime backend APIs (from `chordelia.sheetmusic_backends`):

- `configure_sheetmusic_rendering(...)`
- `with_sheetmusic_rendering(...)`
- `get_sheetmusic_rendering_config()`
- `reset_sheetmusic_rendering_config()`
- `install_sequenceable_sheetmusic_display_hooks()`
- `uninstall_sequenceable_sheetmusic_display_hooks()`

Notes:

- Built-in SVG rendering is part of the core package.
- `SheetMusic` is write-only in v1 (render/export, no parse/load API).

Related deep docs:

- [Sheet Music Rendering](tutorials/sheet-music-rendering.md)

## Playback and MIDI (Optional)

Audio APIs (audio extra):

- `Playback`, `PlaybackNote`, `Waveform`
- `score_to_playback_notes(...)`, `midi_tracks_to_playback_notes(...)`
- `play_scale(...)`, `play_chord(...)`, `play_melody(...)`, `create_chord_notes(...)`

MIDI APIs (midi extra):

- `MidiPlayback`, `MidiFile`, `MidiTrackInfo`
- `get_midi_ports()`, `is_midi_available()`
- `midi_play_chord(...)`, `midi_play_melody(...)`

Canonical `MidiFile` workflow:

- `MidiFile(source)` where `source` is `Score | Sequenceable`
- `MidiFile.to_file(path)`
- `MidiFile.score_to_file(score, path)`
- `MidiFile.load_from_file(path)`
- `MidiFile.score_from_file(path)`

Notes:

- MIDI read/write workflows are class-based via `MidiFile`; legacy helper delegates are intentionally not part of the canonical API surface.
- Notebook rendering remains tracked separately in [MIDI Notebook Rendering Plan](../.plans/midi_notebook_rendering_plan.md).

Articulation controls:

- `ScoreMetadata.gate_width`, `ScoreMetadata.gate_offset`
- `ScoreMetadata.retrigger_policy` (`"retrigger_all"` or `"delta"`)
- Per-call overrides on `MidiPlayback.play_score(...)`

Related deep docs:

- [Playback and MIDI](tutorials/playback-and-midi.md)

## Immutability Pattern

Chordelia public value objects are immutable. Methods return copies instead of mutating
in place.

Common copy-constructor style:

- `with_...(...)` methods (for example `with_extension`, `with_inversion`)
- aggregate update methods (for example `with_(...)`)

Related deep docs:

- [Immutability](immutability.md)

## Related

- [Quickstart](quickstart.md)
- [Development Guide](development.md)

