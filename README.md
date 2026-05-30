# Chordelia - A Comprehensive Music Theory Library

Chordelia is a Python library for music theory and timing workflows. It emphasizes algorithmic correctness, immutable value objects, and practical APIs that run efficiently on low-end hardware.

## Features

- Intervals with quality/number math and naming
- Degrees with int/Roman coercion and context-aware Roman case semantics
- Notes with accidentals, enharmonics, octave, MIDI, and frequency support
- Scales with theory-correct enharmonic spelling
- Chords with parsing, extensions, inversions, and slash-chord handling
- Rhythm and timing utilities for duration, meter, tempo, and beat tracking
- Sequenceable conversion boundary for score-producing musical objects
- Sequence timelines with `Sequence`, `SequenceEntry`, and `Rest`
- Canonical score model with normalized events for downstream rendering/export
- Canonical sheet rendering with `SheetMusic` SVG export and notebook display
- Optional MIDI interface/file workflow with `MidiPlayback` and `MidiFile`

## Installation

Core package:

```bash
pip install chordelia
```

Optional extras:

```bash
pip install chordelia[audio]
pip install chordelia[midi]
pip install chordelia[all]
```

For full install details, see [docs/installation.md](docs/installation.md).

## Quick Start

```python
from chordelia import Note, Scale, ScaleType, Chord, Score, ScoreEventContext
from chordelia import SheetMusic, Sequence

c_major = Scale("C", ScaleType.MAJOR)
print([str(n) for n in c_major.notes])

ii_v_i = c_major.chords_for_degrees("ii", "V", "I")
print([chord.name for chord in ii_v_i])

c_chord = Chord("C").with_extension("maj7").with_inversion(1)
print(c_chord.name)

middle_c = Note("C4")
print(middle_c.midi_number, middle_c.frequency)

score = Score.from_sequenceable(Chord("C4"))
print(len(score.events), score.events[0].pitches)

melody = Sequence((("C4", 1), ("D4", 1), ("E4", 2)))
sheet = SheetMusic(melody, scale="C")
sheet.to_file("melody.svg")

from chordelia import Sequence, SequenceEntry

# Iterable note strings are treated as one convenience chord layer.
single_layer = Sequence(((["C4", "E4", "G4"], 1),))
print(len(single_layer.render_for_context(ScoreEventContext()).events))  # 1

# Iterable chord-like values preserve simultaneous boundaries.
stacked_layers = Sequence((([
	Chord.from_notes(["C4", "E4"]),
	Chord.from_notes(["G4", "B4"]),
], 1),))
print(len(stacked_layers.render_for_context(ScoreEventContext()).events))  # 2

# Recursive sequence transpose preserves timing metadata.
motif = Sequence((("C4", 1), ("E4", 1)))
transposed = motif.transpose("2")
print([event.pitches for event in transposed.render_for_context(ScoreEventContext()).events])

# Recursive sequence shift uses diatonic movement in a scale context.
shifted = motif.shift(1, scale="C")
print([event.pitches for event in shifted.render_for_context(ScoreEventContext()).events])

# Global scale context lets you omit scale=... across related shift calls.
from chordelia import with_global_scale_context
with with_global_scale_context("C"):
	print(Note("E4").shift(2))
	print(Chord("C4").shift(1).name)
	print([event.pitches for event in motif.shift(1).render_for_context(ScoreEventContext()).events])
```

For a fuller walkthrough, see [docs/quickstart.md](docs/quickstart.md).

## Documentation

Deep documentation is in [docs/README.md](docs/README.md).

- [Installation](docs/installation.md)
- [Quickstart](docs/quickstart.md)
- [Notes and Intervals](docs/guides/notes-and-intervals.md)
- [Scales and Chords](docs/guides/scales-and-chords.md)
- [Rhythm and Timing](docs/guides/rhythm-and-timing.md)
- [Immutability](docs/immutability.md)
- [API Overview](docs/api-overview.md)
- [Sheet Rendering Quickstart](docs/quickstart.md#sheet-music-rendering)
- [Development Guide](docs/development.md)

## Design Philosophy

- Algorithmic over lookup-table implementation
- Music theory accuracy first
- Practical performance for constrained environments

## Contributing

Contributions are welcome. Please include tests for behavior changes and keep documentation aligned with the final API behavior.

## License

MIT License. See LICENSE for details.
