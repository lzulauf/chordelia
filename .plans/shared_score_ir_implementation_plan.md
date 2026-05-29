Shared Score implementation and viability plan for chordelia.

## Status
Implementing

## Goal
Implement canonical `Score` as the top-level wrapper around `Sequenceable` objects and use it as the shared normalization boundary for MIDI and sheet workflows.

## Why this comes first
1. Both `MidiFile` and `SheetMusic` must consume the same canonical score representation.
2. Shared normalization avoids duplicate conversion logic and behavior drift.
3. A stable `Score` contract simplifies notebook rendering and file export APIs.

## Scope
1. Define immutable score event and metadata models.
2. Define canonical `Score` wrapper around `Sequenceable` sources.
3. Add conversion from `Sequenceable` to score events.
4. Add adapter seams for MIDI and sheet wrappers.
5. Evaluate performance and maintainability versus direct feature-specific conversion.

## Out of scope
1. Full one-phase migration of all legacy helpers.
2. DAW-grade control/automation model.
3. Full engraving parity work.
4. Breaking removal of existing public helpers in this plan.

## Technical design details
1. Canonical score types and invariants:
   1. Add/confirm score model in `src/chordelia/score.py`.
   2. Proposed core types:
      1. `ScoreEvent`: beat, duration, pitches, velocity, channel, voice, optional spelling metadata.
      2. `ScoreMetadata`: tempo, time_signature, optional key_signature, ppq.
      3. `Score`: canonical wrapper around `Sequenceable` source plus normalized ordered events.
   3. Invariants:
      1. `beat >= 0` and `duration > 0`.
      2. Event pitch collections are non-empty for sounding events.
      3. Event ordering is deterministic.
2. Public API signatures:
   1. `Score(source: Sequenceable, *, tempo=120, time_signature=(4, 4), key_signature=None)`.
   2. `Score.from_sequenceable(source: Sequenceable, *, tempo=120, time_signature=(4, 4), key_signature=None) -> Score`.
   3. Compatibility helper: `score_from_sequence(...)` delegates to `Score.from_sequenceable(...)`.
3. Wrapper adapter signatures:
   1. `MidiFile.score_to_file(score: Score, file_path) -> Path`.
   2. `SheetMusic.score_to_file(score: Score, file_path, *, format="svg") -> Path`.
4. Module/file touchpoints:
   1. `src/chordelia/score.py`.
   2. `src/chordelia/sequenceable.py`.
   3. `src/chordelia/midifile.py`.
   4. `src/chordelia/sheet_music.py` (or chosen module path).
   5. `src/chordelia/__init__.py`.
   6. `tests/unit/chordelia/test_score.py`.
5. Compatibility notes:
   1. Keep any existing `score_ir` symbols as transitional aliases where needed.
   2. Canonical docs should use `Score` terminology only.

## Cross-plan and decision links
1. `.plans/archive/first_class_sequence_support_plan.md`.
2. `.plans/sequence_to_midi_export_plan.md`.
3. `.plans/sheet_music_rendering_plan.md`.
4. `.plans/common_musical_interfaces_plan.md`.
5. `decisions/shared_score_naming_decision.md`.

## Testing approach
Expected test delta classification: both new tests and updated tests.

1. Unit tests:
   1. `Score` invariants and immutability behavior.
   2. `Sequenceable -> Score` normalization semantics.
   3. Deterministic ordering and equality/hash behavior.
2. Integration tests:
   1. `Sequence -> Score -> MidiFile` parity.
   2. `Sequence -> Score -> SheetMusic` parity for notation inputs.
3. Regression tests:
   1. Overlaps, nested sequences, and short durations.
   2. Cross-wrapper parity fixtures.
4. Validation commands:
   1. Focused: `pytest tests/unit/chordelia/test_score.py tests/unit/chordelia/test_midi_playback.py`
   2. Full: `pytest` and `python -m pytest --cov=src`

## Documentation approach
Expected docs delta classification: both README updates and docs updates.

1. Update `README.md` with canonical `Score` role.
2. Update `docs/api-overview.md` with `Score` constructors and wrapper relationships.
3. Document compatibility alias status for old score-ir naming where present.

## Progress checklist
- [x] Phase 0: Score contracts finalized
- [x] Phase 1: Score core model implemented
- [x] Phase 2: Sequenceable normalization implemented
- [ ] Phase 3: MidiFile and SheetMusic adapter seams implemented
- [ ] Phase 4: Parity and performance evaluation completed
- [ ] Phase 5: Documentation and migration notes completed
- [ ] Shared Score contract adopted as canonical

## Phases
### Phase 0: Contract lock
1. Finalize `Score`, `ScoreEvent`, and `ScoreMetadata` names and signatures.
2. Finalize `Sequenceable` entry boundary.

### Phase 1: Core score model
1. Implement immutable score structures.
2. Add deterministic ordering/validation.

### Phase 2: Normalization path
1. Implement `Score.from_sequenceable`.
2. Add compatibility helper delegation.

### Phase 3: Wrapper integration
1. Connect `MidiFile` score write path.
2. Connect `SheetMusic` score write path.

### Phase 4: Comparative validation
1. Compare direct conversions versus score-first conversions.
2. Validate complexity and runtime overhead.

### Phase 5: Docs and rollout
1. Update docs and examples.
2. Publish compatibility/migration notes.

## Execution order recommendation
1. Lock score contracts before wrapper work.
2. Complete normalization before output-specific pipelines.
3. Validate parity before broad helper deprecation.

## Risks and mitigations
1. Risk: dual naming confusion (`Score` vs legacy `score_ir`).
   1. Mitigation: canonical docs use `Score`; keep legacy as bounded alias.
2. Risk: wrapper behavior drift.
   1. Mitigation: parity tests from shared score fixtures.
3. Risk: premature API expansion.
   1. Mitigation: keep v1 surface minimal and wrapper-delegated.

## Acceptance criteria
1. `Score` is canonical top-level wrapper around `Sequenceable`.
2. Both MIDI and sheet wrappers consume score-first conversion paths.
3. Deterministic score semantics are documented and tested.
4. Compatibility path is documented where legacy naming remains.
