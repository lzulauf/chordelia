# Sequences and Score

Back links: [Project README](../../README.md) | [Docs Index](../README.md)

This guide explains Chordelia's composition backbone: immutable sequence timelines and
canonical score normalization.

## Core Concepts

- `Sequence`: ordered immutable list of scheduled entries.
- `SequenceEntry`: payload plus timing metadata (`duration`, optional `offset`).
- `Rest`: explicit silent payload.
- `Score`: canonical timeline of normalized `ScoreEvent` items.

## Sequence Entry Forms

```python
from chordelia import Chord, Rest, Sequence

sequence = Sequence(
    (
        (Chord("C4"), 1),            # (payload, duration)
        (Rest(), 0.5),                # explicit rest
        (Chord("F4"), 1, 4),         # (payload, duration, offset)
    )
)
```

## Concatenating Sections

Use `appended(...)` to build larger forms while preserving immutability.

```python
verse = Sequence((("C4", 1), ("D4", 1)))
answer = Sequence((("E4", 1), ("F4", 1)))
form = verse.appended(*answer.entries, *verse.entries)
```

## Simultaneous Layers

Iterable payloads can represent layered events.

```python
from chordelia import Chord, ScoreEventContext, Sequence

stacked = Sequence((([
    Chord.from_notes(["C4", "E4"]),
    Chord.from_notes(["G4", "B4"]),
], 1),))

rendered = stacked.render_for_context(ScoreEventContext())
print([event.pitches for event in rendered.events])
```

## Transpose vs Shift

- `transpose(interval)` is chromatic (semitone-based).
- `shift(steps, scale=...)` is diatonic (scale-degree based).

```python
from chordelia import ScoreEventContext, Sequence, with_global_scale_context

motif = Sequence((("C4", 1), ("E4", 1)))
print([event.pitches for event in motif.transpose("2").render_for_context(ScoreEventContext()).events])

with with_global_scale_context("C"):
    print([event.pitches for event in motif.shift(1).render_for_context(ScoreEventContext()).events])
```

## Normalize to Score

```python
from chordelia import Score

score = Score.from_sequenceable(form, tempo=112, time_signature=(4, 4), key_signature="C")
print(len(score.events), score.duration)
```

`Score` is the shared model used by rendering, audio conversion, and MIDI workflows.

## Score-First Wrapper Parity

Both output wrappers normalize through the same `Score` event model:

- `MidiFile(source)` and `SheetMusic(source)` accept `Score | Sequenceable`.
- Passing a `Sequenceable` source internally uses `Score.from_sequenceable(...)`.

For multi-output workflows, prefer building one score first and reusing it:

```python
from chordelia import MidiFile, Score, SheetMusic

score = Score.from_sequenceable(form, tempo=112, time_signature=(4, 4), key_signature="C")

MidiFile(score).to_file("form.mid")
SheetMusic(score).to_file("form.svg")
```

Migration note: `score_from_sequenceable(...)` remains as a compatibility helper,
but `Score.from_sequenceable(...)` is the canonical entry point.

## Related

- [Quickstart](../quickstart.md)
- [Song Form from a Motif](../tutorials/song-form-from-motif.md)
- [API Overview](../api-overview.md#sequence-score-and-conversion)
