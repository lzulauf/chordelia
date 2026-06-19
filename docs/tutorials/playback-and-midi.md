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

## 3) MIDI File Export (Score -> File)

```python
from chordelia import MidiFile

MidiFile(score).to_file("progression.mid")
```

## 4) MIDI File Read Paths (File -> Score/Wrapper)

```python
from chordelia import MidiFile

loaded = MidiFile.load_from_file("progression.mid")
loaded_score = MidiFile.score_from_file("progression.mid")

MidiFile.score_to_file(loaded_score, "progression_copy.mid")
```

The canonical MIDI file workflow is class-based through `MidiFile` methods.
Module-level helper delegates are intentionally not part of the canonical API.

## 5) Live MIDI Playback

```python
from chordelia import MidiPlayback, get_midi_ports

ports = get_midi_ports().get("output", [])
print(ports)

if ports:
    with MidiPlayback(output_name=ports[0]) as playback:
        playback.play_score(score, blocking=True)
```

## 6) Articulation and Retrigger Control

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

## 7) Runtime MIDI Monitoring

Use a monitor session to inspect outbound MIDI messages in scripts, tests, or REPL workflows.

```python
from chordelia import MidiMonitorSession, MidiPlayback

if ports:
    with MidiPlayback(output_name=ports[0]) as playback:
        monitor = MidiMonitorSession(
            playback=playback,
            max_events=2000,
            log_file="midi_monitor.jsonl",
            include_wall_time=True,
            include_elapsed_seconds=True,
            include_elapsed_beats=True,
            tempo_bpm=score.metadata.tempo,
        ).start()

        playback.play_score(score, blocking=True)
        latest = monitor.snapshot(limit=10)
        monitor.stop()

        print(len(latest))
```

`midi_monitor.jsonl` contains deterministic line-oriented event records.

## 8) Notebook Live Monitoring

For notebooks, use `display_live(...)` to keep a live event panel while later cells run playback calls.

```python
from chordelia import MidiMonitorSession, MidiPlayback

if ports:
    playback = MidiPlayback(output_name=ports[0])

    with MidiMonitorSession(
        playback=playback,
        max_events=3000,
        tempo_bpm=score.metadata.tempo,
    ) as monitor:
        live = monitor.display_live(refresh_hz=8.0, max_rows=30)
        playback.play_score(score, blocking=True)

        # Use this in notebook cells to inspect captured events.
        monitor.snapshot(limit=20)

        # Stop live refresh explicitly if needed.
        live.stop()
```
```

## Related

- [Installation](../installation.md)
- [Quickstart](../quickstart.md)
- [API Overview](../api-overview.md#playback-and-midi-optional)
- [MIDI Playback Example](../../examples/midi_playback_example.py)
