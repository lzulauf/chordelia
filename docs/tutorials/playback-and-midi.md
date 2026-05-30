# Tutorial: Playback and MIDI

Back links: [Project README](../../README.md) | [Docs Index](../README.md)

This tutorial covers optional playback workflows based on the same canonical `Score`
model used by rendering.

## Prerequisites

Install optional dependencies:

```bash
pip install chordelia[audio]
pip install chordelia[midi]
```

## 1) Build a Score Once

```python
from chordelia import Chord, Score, Sequence

progression = Sequence(
    (
        (Chord("C4"), 1),
        (Chord("A4", "minor"), 1),
        (Chord("F4"), 1),
        (Chord("G4"), 1),
    )
)

score = Score.from_sequenceable(progression, tempo=104, time_signature=(4, 4), key_signature="C")
```

## 2) Audio Playback from Score

```python
from chordelia import Playback, Tempo, score_to_playback_notes

playback_notes = score_to_playback_notes(score)
with Playback(Tempo(score.metadata.tempo)) as player:
    player.play_sequence(playback_notes, blocking=True)
```

## 3) MIDI File Export

```python
from chordelia import MidiFile

MidiFile(score).to_file("progression.mid")
```

## 4) Live MIDI Playback

```python
from chordelia import MidiPlayback, get_midi_ports

ports = get_midi_ports().get("output", [])
print(ports)

if ports:
    with MidiPlayback(output_name=ports[0]) as playback:
        playback.play_score(score, blocking=True)
```

## 5) Articulation and Retrigger Control

Defaults are stored in `Score.metadata`:

- `gate_width=0.9`
- `gate_offset=0.0`
- `retrigger_policy="retrigger_all"`

Override via score metadata copy:

```python
score_delta = score.with_(gate_width=1.0, retrigger_policy="delta")
```

Or override at playback call site:

```python
if ports:
    with MidiPlayback(output_name=ports[0]) as playback:
        playback.play_score(
            score,
            blocking=True,
            gate_width=1.0,
            retrigger_policy="delta",
        )
```

## Related

- [Installation](../installation.md)
- [Quickstart](../quickstart.md)
- [API Overview](../api-overview.md#playback-and-midi-optional)
- [MIDI Playback Example](../../examples/midi_playback_example.py)
