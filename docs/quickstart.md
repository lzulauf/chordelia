# Quickstart

Back links: [Project README](../README.md) | [Docs Index](README.md)

This quickstart is intentionally short: one end-to-end workflow in about 10 minutes.
For deeper walkthroughs, jump to [Tutorials](README.md#document-map).

## 1) Build notes, scales, and chords

```python
from chordelia import Chord, Note, Scale, ScaleType

c_major = Scale("C", ScaleType.MAJOR)
print([str(note) for note in c_major.notes])

ii_v_i = c_major.chords_for_degrees("ii", "V", "I")
print([chord.name for chord in ii_v_i])

middle_c = Note("C4")
print(middle_c.midi_number, middle_c.frequency)
print(Chord("C").with_extension("maj7").name)
```

## 2) Compose a short sequence

```python
from chordelia import Sequence, with_global_scale_context

motif = Sequence((("E4", 1), ("G4", 1), ("A4", 2)))

with with_global_scale_context("C"):
    answer = motif.shift(2)

phrase = motif.appended(*answer.entries)
print(len(phrase.entries))
```

## 3) Layer parts simultaneously when needed

```python
from chordelia import ParallelSequence, Sequence

bass = Sequence((("C3", 4),))
arrangement = ParallelSequence(
    (
        ("lead", phrase, 0),
        ("bass", bass, 0),
    ),
    name="song",
)
```

## 4) Convert to a canonical score

```python
from chordelia import Score

score = Score.from_parallel_sequences(arrangement, tempo=120, time_signature=(4, 4), key_signature="C")
print(len(score.events), score.duration)
print(score.events[0].beat, score.events[0].pitches)
```

## 5) Target immutable deep updates

```python
updated = arrangement.replace_child_by_path("lead", phrase.transpose(12))
updated_score = Score.from_sequenceable(updated)
```

## 6) Render notation to SVG

```python
from chordelia import SheetMusic

SheetMusic(score).to_file("phrase.svg")
```

## 7) Optional playback and export

```python
from chordelia import MidiFile

MidiFile(score).to_file("phrase.mid")
```

Install optional features when needed:

```bash
pip install chordelia[audio]
pip install chordelia[midi]
pip install chordelia[notebook]
```

Immutable composition (`Sequence`, `ParallelSequence`) is separate from future
runtime mutable channels tracked in
[Interactive Live Song Channels Plan](../.plans/interactive_live_song_channels_plan.md).

## Continue Learning

- [Cookbook](cookbook.md)
- [Song Form from a Motif](tutorials/song-form-from-motif.md)
- [Sheet Music Rendering](tutorials/sheet-music-rendering.md)
- [Playback and MIDI](tutorials/playback-and-midi.md)
- [Notes and Intervals](guides/notes-and-intervals.md)
- [Scales and Chords](guides/scales-and-chords.md)
- [Rhythm and Timing](guides/rhythm-and-timing.md)
- [Sequences and Score](guides/sequences-and-score.md)
- [API Overview](api-overview.md)
