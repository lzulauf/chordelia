# Chordelia

Chordelia is a Python toolkit for music theory, composition, notation, and playback.
It focuses on theory-correct results, immutable value objects, and deterministic
score conversion.

## Why Chordelia

- Theory-correct spellings for scales, intervals, and chord construction.
- Immutable, copy-constructor style APIs that compose cleanly.
- Sequence to Score normalization for a single canonical timeline model.
- Built-in SVG sheet rendering plus optional LilyPond backend integration.
- Optional audio and MIDI workflows layered on top of the same score model.

## Installation

```bash
pip install chordelia
```

Optional extras:

```bash
pip install chordelia[audio]
pip install chordelia[midi]
pip install chordelia[all]
```

Python requirement: 3.13+

## Quick Feature Tour

### 1) Build a song form from one motif

```python
from fractions import Fraction
from chordelia import *

scale = Scale("E4", ScaleType.HARMONIC_MINOR)
set_global_scale_context(scale)
degrees = (1, 3, 4, 5, 4, 3, 2, 1)
half = Fraction(1, 2)

a = Sequence(tuple((scale.degree(d), half) for d in degrees))

chord_hit = scale.chord_for_degree("V")
b = a.shift(2)
c = Sequence(((chord_hit, half), a.shift(4)))

song = Sequence((a, b, c, a))
score = Score.from_sequenceable(song, tempo=120, time_signature=(4, 4), key_signature="E minor")
```

Movement contract quick check:

```python
with with_global_scale_context(scale):
	print(Note("E4").shift(2))   # G4 (diatonic)

print(Note("E4").transpose(1))  # F4 (one semitone)
```

Use `shift(...)` for diatonic scale-step movement and `transpose(...)` for chromatic semitone movement.

Seeded random workflow quick check:

```python
rng = Random(seed=202606)
scale = rng.scale()
motif = MotifVariationSequenceAlgorithm(motif_beats=2)
phrase = rng.sequence(8, algorithm=motif, scale=scale)
progression = [rng.chord(scale=scale).name for _ in range(4)]

print(len(phrase.entries))
```

For weighted algorithm selection, stateful motif reuse, and global-singleton randomization recipes, see [Cookbook](docs/cookbook.md).
For `Random.sequence(...)`, pass algorithm-specific per-call tuning values as direct keyword arguments.

The resulting `Score` is the canonical shared boundary for both rendering and MIDI export.

### 2) Render that same song as sheet music

```python
# Continue from block 1 in the same Python session.
SheetMusic(score, scale=scale).to_file("song.svg")
```

### 3) Export and play that same song via MIDI

```python
# Continue from block 1 in the same Python session.
MidiFile(score).to_file("song.mid")

MidiPlayback().play_score(score, blocking=True)
```

## Documentation

Start here:

- [Installation](docs/installation.md)
- [Quickstart](docs/quickstart.md)
- [Docs Index](docs/README.md)

In-depth tutorials:

- [Song Form from a Motif](docs/tutorials/song-form-from-motif.md)
- [Sheet Music Rendering](docs/tutorials/sheet-music-rendering.md)
- [Playback and MIDI](docs/tutorials/playback-and-midi.md)

Guides and reference:

- [Cookbook](docs/cookbook.md)
- [Notes and Intervals](docs/guides/notes-and-intervals.md)
- [Scales and Chords](docs/guides/scales-and-chords.md)
- [Rhythm and Timing](docs/guides/rhythm-and-timing.md)
- [Sequences and Score](docs/guides/sequences-and-score.md)
- [Immutability](docs/immutability.md)
- [API Overview](docs/api-overview.md)
- [Development Guide](docs/development.md)

Additional runnable examples: [examples](examples)

## Contributing

Contributions are welcome. Include tests for behavior changes and keep docs aligned
with final API behavior.

## License

MIT License. See LICENSE for details.
