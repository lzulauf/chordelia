# Chordelia Documentation

This directory contains the detailed guides and reference material that complements the onboarding-focused project README.

Back links: [Project README](../README.md)

## Start Here

- [Installation](installation.md): install options for core, extras, and development.
- [Quickstart](quickstart.md): first working examples across notes, intervals, scales, chords, and rhythm.

## Guides

- [Notes and Intervals](guides/notes-and-intervals.md)
- [Scales and Chords](guides/scales-and-chords.md)
- [Rhythm and Timing](guides/rhythm-and-timing.md)
- [Immutability](immutability.md)

## Reference

- [API Overview](api-overview.md): class, value object, enum, and convenience function map.

## Sheet Rendering Workflow

- [Quickstart](quickstart.md#sheet-music-rendering): score-backed `SheetMusic` SVG export and notebook display.
- [Quickstart](quickstart.md#sheet-music-rendering): includes optional LilyPond backend configuration with executable-path injection.
- [API Overview](api-overview.md#sheet-music-workflow): canonical `SheetMusic` API and v1 write-only boundary.

## Optional MIDI Workflow

- [Quickstart](quickstart.md#midi-interface-playback-optional): Score to MidiFile workflow and interface playback entry points.
- [API Overview](api-overview.md#midi-workflow-optional): canonical MidiPlayback and MidiFile responsibilities.
- [MIDI Example Script](../examples/midi_playback_example.py): interactive example for selecting ports and auditioning file or score playback.

## Development

- [Development Guide](development.md): testing, contribution flow, versioning, and publishing.

## Documentation Ownership

- Keep `README.md` short and onboarding-first.
- Keep deep tutorials, full reference material, and maintenance procedures in `docs/`.
- Prefer linking from summary sections instead of repeating full examples in multiple files.
