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
- Canonical score model with normalized events for downstream rendering/export

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
from chordelia import Note, Scale, ScaleType, Chord, Score

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
- [Development Guide](docs/development.md)

## Design Philosophy

- Algorithmic over lookup-table implementation
- Music theory accuracy first
- Practical performance for constrained environments

## Contributing

Contributions are welcome. Please include tests for behavior changes and keep documentation aligned with the final API behavior.

## License

MIT License. See LICENSE for details.
