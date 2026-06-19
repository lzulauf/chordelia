# Installation

Back links: [Project README](../README.md) | [Docs Index](README.md)

## Requirements

- Python 3.10+

Runtime support policy:

- CI-required support: Python 3.10, 3.11, 3.12, 3.13
- Preview support: Python 3.14 (non-blocking CI signal)

## Core Library

Install core music theory functionality with no optional dependencies:

```bash
pip install chordelia
```

## Optional Features

Audio playback:

```bash
pip install chordelia[audio]
```

MIDI file support:

```bash
pip install chordelia[midi]
```

Notebook UI support:

```bash
pip install chordelia[notebook]
```

Complete audio experience:

```bash
pip install chordelia[all]
```

## Development Installation

```bash
git clone https://github.com/yourusername/chordelia.git
cd chordelia
uv sync --group dev --extra all
```

## Installation Matrix

| Installation | Features Available |
|--------------|-------------------|
| `chordelia` | Core music theory + sequence/score + built-in SVG sheet rendering (`SheetMusic`) |
| `chordelia[audio]` | Audio playback with multiple waveforms |
| `chordelia[midi]` | MIDI interface playback and MIDI file workflows |
| `chordelia[notebook]` | Notebook UI dependencies for interactive panels/widgets |
| `chordelia[all]` | Audio + MIDI optional workflows |

## Verify Optional Feature Availability

```python
import chordelia as c

print(c.get_available_features())
c.print_feature_status()
```

## Next Steps

- Continue with [Quickstart](quickstart.md)
- Explore [Song Form from a Motif](tutorials/song-form-from-motif.md)
- Explore [Scales and Chords](guides/scales-and-chords.md)
