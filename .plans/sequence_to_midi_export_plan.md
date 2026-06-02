Sequence-to-MIDI export plan for chordelia.

## Status
Implementing

## Goal
Make `MidiFile` the canonical MIDI wrapper class around `Score` (and therefore `Sequenceable` inputs), with explicit read/write APIs and notebook playback rendering.

## Why this comes first
1. MIDI file read and write behavior must share one canonical score model.
2. Class-based wrapper APIs simplify notebook ergonomics and stateful metadata handling.
3. A score-first MIDI layer reduces drift from sheet rendering semantics.

## Scope
1. Define canonical `MidiFile` class surface for reading/writing.
2. Route write paths through `Score`.
3. Route file reads through `score_from_file`.
4. Add notebook rich-display hooks for browser-playable MIDI output.
5. Keep notebook dependencies optional (`midi-notebook`).

## Out of scope
1. Real-time playback refactors beyond export/read contracts.
2. DAW-grade MIDI editing features.
3. Mandatory notebook dependencies for core MIDI operations.

## Technical design details
1. Canonical class contract:
   1. `MidiFile` owns an internal `score: Score` reference for normalized representation.
   2. Constructor accepts `Score | Sequenceable` and normalizes to `Score`.
2. Required class and instance APIs:
   1. `MidiFile.score_from_file(file_path) -> Score`.
   2. `MidiFile.load_from_file(file_path) -> MidiFile`.
   3. `MidiFile.to_file(self, file_path) -> Path`.
   4. `MidiFile.score_to_file(score: Score, file_path) -> Path`.
3. Compatibility API strategy:
   1. Existing function-style helpers (`midi_file_from_sequence`, etc.) remain as thin delegates to canonical class methods.
4. Notebook rendering contract:
   1. Implement `_repr_mimebundle_` on `MidiFile` to produce embeddable browser player output when optional deps are installed.
   2. Provide text fallback when notebook extras are missing.
   3. Keep player asset source configurable (CDN default, optional local override).
5. Dependency policy:
   1. `midi`: core read/write support.
   2. `midi-notebook`: notebook display helpers only.
   3. Core read/write must work without `midi-notebook`.
6. Module/file touchpoints:
   1. `src/chordelia/midifile.py`.
   2. `src/chordelia/score.py`.
   3. `src/chordelia/sequenceable.py`.
   4. `src/chordelia/__init__.py`.
   5. `tests/unit/chordelia/test_midifile.py` (new/expanded).

## Cross-plan references
1. `.plans/shared_score_ir_implementation_plan.md`.
2. `.plans/archive/first_class_sequence_support_plan.md`.
3. `.plans/sheet_music_rendering_plan.md`.
4. `.plans/common_musical_interfaces_plan.md`.

## Testing approach
Expected test delta classification: both new tests and updated tests.

1. Unit tests:
   1. `load_from_file` constructs `MidiFile` with internal `Score`.
   2. `score_from_file` parsing invariants.
   3. `to_file` and `score_to_file` deterministic event output.
   4. Notebook mime bundle rendering and fallback behavior.
2. Integration tests:
   1. Round-trip: file -> score -> file semantic parity.
   2. `Sequence -> Score -> MidiFile.to_file` pipeline behavior.
3. Regression tests:
   1. Overlap, short durations, channels, and velocity edge cases.
4. Validation commands:
   1. Focused: `pytest tests/unit/chordelia/test_midifile.py tests/unit/chordelia/test_midi_playback.py`
   2. Full: `pytest` and `python -m pytest --cov=src`

## Documentation approach
Expected docs delta classification: both README/docs updates and API updates.

1. Document canonical `MidiFile` methods and class workflow.
2. Document compatibility function delegates.
3. Add notebook examples for embedded playable MIDI outputs.

## Progress checklist
- [x] Phase 0: Canonical MidiFile API finalized
- [x] Phase 1: Score-backed constructor and write path implemented
- [x] Phase 2: File-read to Score path implemented
- [x] Phase 3: Compatibility delegates implemented
- [ ] Phase 4: Notebook display hooks implemented
- [ ] Phase 5: Tests/docs completed
- [ ] Canonical MidiFile workflow adopted

## Phases
### Phase 0: API lock
1. Finalize required canonical methods and signatures.

### Phase 1: Score-backed write path
1. Implement constructor normalization to internal `Score`.
2. Implement `to_file` and `score_to_file`.

### Phase 2: File-read path
1. Implement `score_from_file`.
2. Implement `load_from_file` delegation.

### Phase 3: Compatibility shims
1. Route function helpers to class APIs.

### Phase 4: Notebook rendering
1. Implement playable HTML MIME output and fallback behavior.

### Phase 5: Verification
1. Add tests and docs.
2. Validate optional dependency behavior.

## Execution order recommendation
1. Lock API names first.
2. Implement write path before notebook hooks.
3. Complete read path before migration docs.

## Risks and mitigations
1. Risk: class constructor overload confusion.
   1. Mitigation: keep constructor narrow (`Score | Sequenceable`) and keep file loading as explicit classmethod.
2. Risk: notebook hook dependency bleed.
   1. Mitigation: strict optional extra checks and fallback text output.
3. Risk: behavior drift versus compatibility helpers.
   1. Mitigation: delegate-only implementation and parity tests.

## Acceptance criteria
1. `MidiFile` is canonical MIDI wrapper with internal `Score`.
2. Required methods (`score_from_file`, `load_from_file`, `to_file`, `score_to_file`) are implemented and documented.
3. Notebook playable rendering works when optional extras are installed.
4. Core MIDI read/write works without notebook extras.
