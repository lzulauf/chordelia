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

Enable notebook hooks for direct Note/Chord/Sequence/Scale rendering:

```python
configure_sheetmusic_rendering(enable_notebook_hooks=True, scale="C")
```

Render a scale directly in a notebook cell as a quarter-note progression:

```python
from chordelia import Scale, ScaleType

c_major = Scale("C", ScaleType.MAJOR)
c_major  # notebook display renders like Sequence(c_major.notes)
```

Render a whole list of renderable objects in one output:

```python
from chordelia import Random, SheetMusic

sheet = SheetMusic([Random.scale() for _ in range(10)])
sheet
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

## 10) Seeded random progression generation

```python
from chordelia import Random

rng = Random(seed=202606)
scale = rng.scale()
progression = tuple(rng.chord(scale=scale) for _ in range(4))

print(scale.name)
print([chord.name for chord in progression])
```

## 11) Weighted scale type selection

```python
from chordelia import Random, ScaleType

rng = Random(seed=99)
weighted_scale = rng.scale(
    root_weights={"C": 1, "D": 10},
    scale_type_weights={ScaleType.MAJOR: 8, ScaleType.NATURAL_MINOR: 2},
)

print(weighted_scale.name)
```

Weights are relative scores, so `8:2` behaves the same as `80:20`.

## 12) Use global scale context for random degrees, notes, and chords

```python
from chordelia import Random, with_global_scale_context

rng = Random(seed=7)
with with_global_scale_context("D minor"):
    print(rng.degree())
    print(rng.note())
    print(rng.chord())
```

## 13) Compare scale-aware and chromatic random selectors

```python
from chordelia import Random, Scale, ScaleType

rng = Random(seed=12)
c_major = Scale("C", ScaleType.MAJOR)

print(rng.note(scale=c_major))          # constrained to C major
print(rng.chromatic_note())             # unconstrained chromatic choice
print(rng.interval())                   # unconstrained interval choice
print(rng.chromatic_chord().name)       # unconstrained root/quality choice
```

## 14) Choose between instance and global singleton workflows

```python
from chordelia import Random, configure_global_random, get_global_random, reset_global_random

# Isolated reproducible stream
instance_rng = Random(seed=111)
print(instance_rng.chromatic_note())

# Shared process-wide singleton stream
configure_global_random(seed=111)
print(Random.chromatic_note())
print(get_global_random().chromatic_note())

reset_global_random()
```

## Related

- [Quickstart](quickstart.md)
- [Song Form from a Motif](tutorials/song-form-from-motif.md)
- [Playback and MIDI](tutorials/playback-and-midi.md)
- [Sequences and Score](guides/sequences-and-score.md)
- [API Overview](api-overview.md)
