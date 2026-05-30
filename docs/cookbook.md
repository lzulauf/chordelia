# Cookbook

Back links: [Project README](../README.md) | [Docs Index](README.md)

Use this page for practical, copy-paste workflows. Recipes are intentionally short and
focus on common tasks you can adapt quickly.

## 1) Build a ii-V-I in any key

```python
from chordelia import Scale, ScaleType

key = "Eb"
scale = Scale(key, ScaleType.MAJOR)
progression = scale.chords_for_degrees("ii", "V", "I")
print([chord.name for chord in progression])
```

## 2) Reuse one motif to build longer forms

```python
from chordelia import Sequence, with_global_scale_context

motif = Sequence((("E4", 1), ("G4", 1), ("A4", 2)))

with with_global_scale_context("C"):
    a = motif
    a_answer = motif.shift(2)
    b = motif.shift(4)

song = a.appended(*a_answer.entries, *b.entries, *a.entries)
print(len(song.entries))
```

## 3) Layer simultaneous voicings in a timeline

```python
from chordelia import Chord, ScoreEventContext, Sequence

stacked = Sequence((([
    Chord.from_notes(["C4", "E4"]),
    Chord.from_notes(["G4", "B4"]),
], 1),))

rendered = stacked.render_for_context(ScoreEventContext())
print([event.pitches for event in rendered.events])
```

## 4) Convert any sequenceable source to canonical score

```python
from chordelia import Chord, Score, Sequence

progression = Sequence(((Chord("C4"), 1), (Chord("F4"), 1), (Chord("G4"), 1), (Chord("C4"), 1)))
score = Score.from_sequenceable(progression, tempo=112, time_signature=(4, 4), key_signature="C")

print(len(score.events), score.duration)
print(score.events[0].beat, score.events[0].pitches)
```

## 5) Keep full note lengths and use delta retrigger behavior

```python
score_delta = score.with_(gate_width=1.0, retrigger_policy="delta")
```

Use at playback time instead of changing metadata:

```python
from chordelia import MidiPlayback, get_midi_ports

ports = get_midi_ports().get("output", [])
if ports:
    with MidiPlayback(output_name=ports[0]) as playback:
        playback.play_score(
            score,
            blocking=True,
            gate_width=1.0,
            retrigger_policy="delta",
        )
```

## 6) Export both notation and MIDI from one score

```python
from chordelia import MidiFile, SheetMusic

SheetMusic(score).to_file("song.svg")
MidiFile(score).to_file("song.mid")
```

## 7) Configure LilyPond rendering once

```python
from chordelia.sheetmusic_backends import configure_sheetmusic_rendering

configure_sheetmusic_rendering(
    backend_name="lilypond",
    lilypond_executable="C:/path/to/lilypond.exe",
    crop=True,
)
```

Enable notebook hooks for direct Note/Chord/Sequence rendering:

```python
configure_sheetmusic_rendering(enable_notebook_hooks=True, scale="C")
```

## 8) Check optional feature availability at runtime

```python
import chordelia as c

print(c.get_available_features())
c.print_feature_status()
```

## 9) Quick audio audition from score

```python
from chordelia import Playback, Tempo, score_to_playback_notes

playback_notes = score_to_playback_notes(score)
with Playback(Tempo(score.metadata.tempo)) as player:
    player.play_sequence(playback_notes, blocking=True)
```

## Related

- [Quickstart](quickstart.md)
- [Song Form from a Motif](tutorials/song-form-from-motif.md)
- [Playback and MIDI](tutorials/playback-and-midi.md)
- [Sequences and Score](guides/sequences-and-score.md)
- [API Overview](api-overview.md)
