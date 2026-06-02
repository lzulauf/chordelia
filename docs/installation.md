# Installation

Back links: [Project README](../README.md) | [Docs Index](README.md)

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

Complete audio experience:

```bash
pip install chordelia[all]
```

## Development Installation

```bash
git clone https://github.com/yourusername/chordelia.git
cd chordelia
uv sync --group dev --group all
```

## Installation Matrix

| Installation | Features Available |
|--------------|-------------------|
| `chordelia` | Core music theory: Notes, Scales, Chords, Intervals, Rhythm |
| `chordelia[audio]` | Audio playback with multiple waveforms |
| `chordelia[midi]` | MIDI file loading and conversion |
| `chordelia[all]` | Playback and MIDI support |

## Next Steps

- Continue with [Quickstart](quickstart.md)
- Explore [Scales and Chords](guides/scales-and-chords.md)
