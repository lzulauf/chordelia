# Sequences and Score

Back links: [Project README](../../README.md) | [Docs Index](../README.md)

This guide explains Chordelia's composition backbone: immutable sequence timelines and
canonical score normalization.

## Core Concepts

- `Sequence`: ordered immutable list of scheduled entries.
- `ParallelSequence`: immutable simultaneous composition with optional per-child offsets.
- `SequenceEntry`: payload plus timing metadata (`duration`, optional `offset`).
- `Rest`: explicit silent payload.
- `Score`: canonical timeline of normalized `ScoreEvent` items.

## Sequence vs ParallelSequence

Use `Sequence` when cursor-advancing order is the main intent, and
`ParallelSequence` when layering simultaneous parts is the main intent.

```python
from chordelia import ParallelSequence, Score, Sequence

lead = Sequence((("E4", 1), ("G4", 1), ("A4", 2)))
bass = Sequence((("E3", 4),))

song = ParallelSequence(
    (
        ("lead", lead, 0),
        ("bass", bass, 0),
    ),
    name="song",
)

score = Score.from_parallel_sequences(song, tempo=112, time_signature=(4, 4), key_signature="E minor")
```

`Score.from_sequenceable(...)` remains strict single-source normalization.
Use `Score.from_parallel_sequences(...)` for explicit simultaneous source sets.

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

For larger structures, prefer `ParallelSequence` over implicit iterable-layer
payloads so part identity and offsets remain explicit.

## Named Immutable Recomposition

Both `Sequence` and `ParallelSequence` support optional names for direct and
nested immutable edits.

```python
from chordelia import ParallelSequence, Sequence

lead = Sequence((("E4", 1), ("G4", 1)), name="lead_line")
bass = Sequence((("E3", 2),), name="bass_line")

arrangement = ParallelSequence(
    (
        ("lead", lead, 0),
        ("bass", bass, 0),
    ),
    name="section",
)

updated = arrangement.replace_child_by_path("lead", lead.transpose(12))
```

Path segments are dot-separated child names. Missing segments raise a `KeyError`
that includes the nearest resolved path segment.

## Transpose vs Shift

- `transpose(interval)` is chromatic (semitone-based).
- `shift(steps, scale=...)` is diatonic (scale-degree based), with optional global scale context fallback.

```python
from chordelia import ScoreEventContext, Sequence, with_global_scale_context

motif = Sequence((("C4", 1), ("E4", 1)))
print([event.pitches for event in motif.transpose(1).render_for_context(ScoreEventContext()).events])

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

Boundary note: immutable composition APIs are intentionally separate from future
runtime mutable channel controls tracked in
[Interactive Live Song Channels Plan](../../.plans/interactive_live_song_channels_plan.md).

## Related

- [Quickstart](../quickstart.md)
- [Song Form from a Motif](../tutorials/song-form-from-motif.md)
- [API Overview](../api-overview.md#sequence-score-and-conversion)
