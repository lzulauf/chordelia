# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2026-06-02

### Added
- New theory primitives and exports for accidentals and degrees.
- New score-first conversion boundary with Score, ScoreEvent, ScoreEventContext, and ScoreMetadata.
- New sequence composition foundation with Sequenceable, Sequence, SequenceEntry, and related helpers.
- New explicit parallel composition APIs with ParallelSequence, ParallelChild, and Score.from_parallel_sequences(...).
- New randomization APIs and modular sequence algorithms:
  - Pure random
  - Motif variation
  - Scale walk
  - Chord anchor walk
- New sheet music stack with SheetMusic, SVG rendering support, and LilyPond backend integration.
- New playback conversion helpers in playback_notes.

### Changed
- Shift and transpose semantics were clarified and disambiguated across core theory and sequence workflows.
- Duration coercion and timing behavior were unified across score, sequence, playback, and export boundaries.
- Scale context handling was unified to make diatonic transformations and context-driven workflows more predictable.
- Sequence rendering and score-backed playback controls were refined for deterministic normalization.
- Parallel composition validation and error reporting were hardened with better child-level context.

### Documentation
- Added broad docs coverage including API overview, quickstart, cookbook, installation/development guides, and tutorials.
- Added explicit guidance for sequential vs simultaneous composition and immutable path-based recomposition.
- Added upgrade guidance around score-first workflows and composition boundaries.

### Testing
- Expanded unit coverage across theory, rhythm/timing, score conversion, playback/MIDI, randomization, and sequence algorithms.
- Added sheet-music baseline rendering tests and focused tests for parallel composition behavior.

### Upgrade Notes
- Prefer Score.from_sequenceable(...) as the canonical normalization entry point.
- Use Score.from_parallel_sequences(...) for explicit simultaneous layering.
- Use shift(...) for diatonic movement and transpose(...) for chromatic movement.
- Keep composition models (Sequence, ParallelSequence) separate from future runtime channel control concerns.

**Full Changelog**: https://github.com/lzulauf/chordelia/compare/v0.3.1...v0.4.0

[0.4.0]: https://github.com/lzulauf/chordelia/compare/v0.3.1...v0.4.0
