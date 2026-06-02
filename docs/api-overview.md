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

- `Duration`, `TimeSignature`, `Tempo`, `Beat`, `NoteValue`

Helpers/constants:

- `whole_note()`, `half_note()`, `quarter_note()`, `eighth_note()`, `sixteenth_note()`
- `dotted(duration)`, `triplet(duration)`
- `COMMON_TIME`, `WALTZ_TIME`, `COMPOUND_DUPLE`

Related deep docs:

- [Rhythm and Timing](guides/rhythm-and-timing.md)

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
- `Score.duration` returns normalized timeline span.
- `Score.with_(...)` returns immutable metadata/source/event updates.

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
