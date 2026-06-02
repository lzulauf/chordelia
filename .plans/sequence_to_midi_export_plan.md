Sequence-to-MIDI export plan for chordelia.

## Status
Implementing

## Goal
Make `MidiFile` the canonical MIDI wrapper class around `Score` (and therefore `Sequenceable` inputs), with explicit read/write APIs.

## Why this comes first
1. MIDI file read and write behavior must share one canonical score model.
2. Class-based wrapper APIs simplify stateful metadata handling.
3. A score-first MIDI layer reduces drift from sheet rendering semantics.

## Scope
1. Define canonical `MidiFile` class surface for reading/writing.
2. Route write paths through `Score`.
3. Route file reads through `score_from_file`.

## Out of scope
1. Real-time playback refactors beyond export/read contracts.
2. DAW-grade MIDI editing features.
3. Notebook MIME rendering (tracked in `.plans/midi_notebook_rendering_plan.md`).

## Technical design details
1. Canonical class contract:
   1. `MidiFile` owns an internal `score: Score` reference for normalized representation.
   2. Constructor accepts `Score | Sequenceable` and normalizes to `Score`.
2. Required class and instance APIs:
   1. `MidiFile.score_from_file(file_path) -> Score`.
   2. `MidiFile.load_from_file(file_path) -> MidiFile`.
   3. `MidiFile.to_file(self, file_path) -> Path`.
   4. `MidiFile.score_to_file(score: Score, file_path) -> Path`.
3. API surface strategy:
   1. Use `MidiFile` class APIs as the only canonical public workflow for MIDI read/write.
   2. Remove function-style helper delegates to keep the wrapper surface explicit and score-first.
4. Dependency policy:
   1. `midi`: core read/write support.
5. Module/file touchpoints:
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
5. `.plans/midi_notebook_rendering_plan.md`.

## Testing approach
Expected test delta classification: both new tests and updated tests.

1. Unit tests:
   1. `load_from_file` constructs `MidiFile` with internal `Score`.
   2. `score_from_file` parsing invariants.
   3. `to_file` and `score_to_file` deterministic event output.
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
2. Document migration away from removed helper delegates to class-based APIs.
3. Cross-link notebook rendering work tracked in `.plans/midi_notebook_rendering_plan.md`.

## Progress checklist
- [x] Phase 0: Canonical MidiFile API finalized
- [x] Phase 1: Score-backed constructor and write path implemented
- [x] Phase 2: File-read to Score path implemented
- [x] Phase 3: Class-only API surface adopted (legacy helper delegates removed)
- [x] Phase 4: Notebook rendering scope moved to dedicated plan
- [ ] Phase 5: Tests/docs completed for read/write scope
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

### Phase 3: API hardening
1. Remove helper delegates and keep class APIs canonical.

### Phase 4: Notebook handoff
1. Track notebook rendering in `.plans/midi_notebook_rendering_plan.md`.

### Phase 5: Verification
1. Add tests and docs.
2. Validate core read/write behavior.

## Execution order recommendation
1. Lock API names first.
2. Implement write path before documentation/migration cleanup.
3. Complete read path before migration docs.

## Risks and mitigations
1. Risk: class constructor overload confusion.
   1. Mitigation: keep constructor narrow (`Score | Sequenceable`) and keep file loading as explicit classmethod.
2. Risk: notebook concerns delaying core wrapper completion.
   1. Mitigation: track notebook rendering in a separate dedicated plan.
3. Risk: migration friction from helper-removal changes.
   1. Mitigation: explicit migration notes and examples using class APIs.

## Acceptance criteria
1. `MidiFile` is canonical MIDI wrapper with internal `Score`.
2. Required methods (`score_from_file`, `load_from_file`, `to_file`, `score_to_file`) are implemented and documented.
3. Core MIDI read/write works without notebook extras.
4. Notebook rendering scope is explicitly tracked in `.plans/midi_notebook_rendering_plan.md`.
