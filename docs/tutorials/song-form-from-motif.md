# Tutorial: Song Form from a Motif

Back links: [Project README](../../README.md) | [Docs Index](../README.md)

This tutorial shows how to write one melodic motif and derive a complete AABA-style
form using diatonic shifting.

## What You Will Build

- A reusable motif
- Related phrases generated with `shift(...)`
- A full-form `Sequence`
- A canonical `Score` ready for rendering or playback

## Step 1: Create the Seed Motif

```python
from fractions import Fraction
from chordelia import Note, Sequence

half_beat = Fraction(1, 2)
motif = Sequence(
    (
        (Note("E4"), half_beat),
        (Note("G4"), half_beat),
        (Note("A4"), half_beat),
        (Note("G4"), half_beat),
        (Note("E4"), half_beat),
        (Note("D4"), half_beat),
        (Note("E4"), half_beat),
        (Note("G4"), half_beat),
    )
)
```

## Step 2: Derive Related Phrases with Diatonic Shift

```python
from chordelia import with_global_scale_context

with with_global_scale_context("C"):
    phrase_a = motif
    phrase_a_answer = motif.shift(2)
    phrase_b = motif.shift(4)
    turnaround = motif.shift(-1)
```

`shift(...)` is diatonic and respects scale context.

- `transpose(...)` moves by semitone count.
- `shift(...)` moves by scale degree count.

## Step 3: Assemble Song Sections with Built-In Sequence Operations

Use `Sequence.appended(...)` to concatenate sections. No custom concatenation helper is
required.

```python
verse = phrase_a.appended(*phrase_a_answer.entries)
bridge = phrase_b.appended(*turnaround.entries)
song = verse.appended(*verse.entries, *bridge.entries, *verse.entries)
```

## Step 4: Convert to a Canonical Score

```python
from chordelia import Score

score = Score.from_sequenceable(song, tempo=120, time_signature=(4, 4), key_signature="C")
print("events:", len(score.events))
print("duration:", score.duration)
print("first:", score.events[0].beat, score.events[0].spelling or score.events[0].pitches)
```

At this point, `score` is the shared data model for rendering, MIDI export, and playback.

## Step 5: Next Workflow Options

Render notation:

```python
from chordelia import SheetMusic
SheetMusic(score).to_file("song.svg")
```

Export MIDI:

```python
from chordelia import MidiFile
MidiFile(score).to_file("song.mid")
```

## Related

- [Quickstart](../quickstart.md)
- [Sequences and Score](../guides/sequences-and-score.md)
- [Sheet Music Rendering](sheet-music-rendering.md)
- [Playback and MIDI](playback-and-midi.md)
- [Shifted Melody Example Script](../../examples/shifted_melody_song_example.py)
