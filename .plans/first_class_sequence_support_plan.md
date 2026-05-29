First-class sequence support plan for chordelia.

## Status
Implementing

## Goal
Implement `Sequence` as the primary composition building block for ordering and layering `Sequenceable` objects (including nested `Sequence`), with deterministic timing and seamless conversion into canonical `Score`.

## Why this comes first
1. Composition semantics must be stable before MIDI and sheet wrappers can be consistent.
2. Nested reusable sequences are required for larger-form workflows (motifs, phrases, sections).
3. `Sequence` is the primary user-facing structure that feeds both `MidiFile` and `SheetMusic` through `Score`.

## Scope
1. Define `Sequence` and `SequenceEntry` immutable models.
2. Define `Sequenceable` payload requirements for sequence entries.
3. Support duration-paired entries with optional absolute offsets from sequence start.
4. Support recursive sequences (sequence entries containing child sequences).
5. Support sequence transforms (transpose first).
6. Ensure sequence normalization cleanly delegates into canonical `Score`.

## Out of scope
1. Full DAW arrangement semantics.
2. Interactive timeline editing UI.
3. Full harmonic-context transforms for non-sequenceable types in v1.
4. Breaking removal of existing helper APIs in one step.

## Technical design details
1. Canonical model and invariants:
   1. Add immutable sequence model in `src/chordelia/sequences.py`.
   2. Public types:
      1. `Sequence`: immutable container of `SequenceEntry`.
      2. `SequenceEntry`: payload plus duration plus optional offset.
      3. `Rest`: explicit silent placeholder payload.
   3. `SequenceEntry.payload` type:
      1. `Sequenceable | Rest`.
   4. Invariants:
      1. `duration > 0`.
      2. `offset >= 0` when provided.
      3. Entries stored as tuple for deterministic behavior.
      4. Flattened ordering is deterministic by `(start, insertion_index, payload_order)`.
2. Scheduling semantics:
   1. Sequential mode (no offset):
      1. Entry starts at current cursor.
      2. Cursor advances by entry duration.
   2. Absolute-offset mode:
      1. Entry starts at explicit offset from sequence start.
      2. Cursor updates via `max(cursor, start + duration)`.
   3. Mixed mode in one sequence is supported.
3. Recursive semantics:
   1. `Sequence` implements `Sequenceable`.
   2. Child sequence events are translated by parent start and flattened recursively.
4. Transform semantics:
   1. `Sequence.transpose(interval) -> Sequence` as canonical transform method in this plan.
   2. Transpose applies recursively to sequenceable payloads.
   3. Unsupported payload transform paths raise actionable `ValueError`.
5. Interface alignment:
   1. `Sequenceable` is canonical interface for payloads.
   2. Initial required implementers: `Note`, `Chord`, `Sequence`.
   3. Non-implementing types may use explicit adapter/coercion only as a temporary migration path.
   4. Registry decommission target: once required native migrations in `.plans/common_musical_interfaces_plan.md` are complete, sequence paths must not depend on adapter registration.
6. Score alignment:
   1. `Score` is canonical top-level wrapper around `Sequenceable`.
   2. `Sequence` conversion boundary is `Score(sequence)` or `Score.from_sequenceable(sequence)`.
   3. Avoid parallel normalized timeline object names in public APIs.
7. API signatures (proposed):
   1. `sequence(*entries) -> Sequence` convenience constructor.
   2. `entry(payload: Sequenceable | Rest, duration, *, offset=None) -> SequenceEntry`.
   3. `Sequence.appended(*entries) -> Sequence`.
   4. `Sequence.transpose(interval) -> Sequence`.
   5. `Score.from_sequenceable(source: Sequenceable, *, tempo=120, time_signature=(4, 4), key_signature=None) -> Score`.
8. Module/file touchpoints:
   1. `src/chordelia/sequences.py`.
   2. `src/chordelia/sequenceable.py`.
   3. `src/chordelia/score.py`.
   4. `src/chordelia/__init__.py`.
   5. `tests/unit/chordelia/test_sequences.py`.
9. Error and validation semantics:
   1. Invalid duration/offset values raise `ValueError`.
   2. Non-sequenceable payload insertion raises `TypeError` with guidance.
   3. Transform failures from payload capability gaps raise `ValueError`.

## Naming lock for this plan
1. Canonical top-level wrapper: `Score`.
2. Canonical sequencing object: `Sequence`.
3. Canonical payload capability interface: `Sequenceable`.
4. `Song`, `Phrase`, and `Timeline` remain non-canonical aliases/ideas and are not used as core API type names in v1.

## Cross-plan references and dependency alignment
1. `.plans/shared_score_ir_implementation_plan.md`:
   1. `Score`/event model boundary consumed by this plan.
2. `.plans/sequence_to_midi_export_plan.md`:
   1. `MidiFile` should consume `Score` produced from `Sequence`.
3. `.plans/sheet_music_rendering_plan.md`:
   1. `SheetMusic` should consume `Score` produced from `Sequence`.
4. `.plans/common_musical_interfaces_plan.md`:
   1. Owns the `Sequenceable` contract details and adapter-registry decommission gates.

## Testing approach
Expected test delta classification: both new tests and updated tests.

1. Unit tests:
   1. `SequenceEntry` validation for duration and offset.
   2. Sequential and absolute scheduling behavior.
   3. Mixed scheduling behavior and deterministic ordering.
   4. Recursive flattening of nested sequences.
   5. Recursive transpose behavior.
2. Integration tests:
   1. `Sequence -> Score` conversion parity.
   2. `Sequence -> Score -> MidiFile` delegation sanity.
3. Regression tests:
   1. Overlap and nesting fixtures.
   2. Error-message fixtures for invalid payloads.
4. Validation commands:
   1. Focused: `pytest tests/unit/chordelia/test_sequences.py tests/unit/chordelia/test_rhythm.py`
   2. Full: `pytest` and `python -m pytest --cov=src`

## Documentation approach
Expected docs delta classification: both README updates and docs updates.

1. Update `README.md` with `Sequence` and `Score` relationship.
2. Update `docs/api-overview.md` for `Sequence` APIs.
3. Add/refresh sequence composition guide examples:
   1. Sequential composition.
   2. Offset-based overlap.
   3. Nested sequence reuse.
4. Ensure docs use canonical names only (`Score`, `Sequence`, `Sequenceable`).

## Progress checklist
- [ ] Phase 0: Contracts and naming locked
- [ ] Phase 1: Core Sequence and SequenceEntry implemented
- [ ] Phase 2: Scheduler and recursive flattening implemented
- [ ] Phase 3: Transform behavior implemented
- [ ] Phase 4: Score integration completed
- [ ] Phase 5: Tests and docs completed
- [ ] First-class sequence support complete

## Phases
### Phase 0: Contract finalization
1. Lock `Sequenceable` payload requirement.
2. Lock scheduling and recursion semantics.
3. Lock `Score` conversion boundary.

### Phase 1: Composition model
1. Implement immutable `Sequence` and `SequenceEntry`.
2. Implement constructors and coercion helpers.
3. Implement validation rules.

### Phase 2: Scheduler and flattening
1. Implement sequential cursor scheduling.
2. Implement absolute offset handling.
3. Implement recursive flattening.

### Phase 3: Transform support
1. Implement recursive `Sequence.transpose`.
2. Ensure payload-capability failures are explicit.

### Phase 4: Score integration
1. Route conversion through canonical `Score`.
2. Validate deterministic event parity.

### Phase 5: Verification and docs
1. Complete tests.
2. Update docs/examples and cross-links.

## Execution order recommendation
1. Lock contract names first.
2. Implement core model before wrappers.
3. Integrate with `Score` before pipeline-specific work.
4. Complete tests/docs before API stability declaration.

## Risks and mitigations
1. Risk: payload capability ambiguity.
   1. Mitigation: strict `Sequenceable` checks and actionable errors.
2. Risk: recursive timing bugs.
   1. Mitigation: deterministic flattening tests and golden fixtures.
3. Risk: transform behavior drift across payload types.
   1. Mitigation: shared transform contract and integration tests.

## Acceptance criteria
1. Users can compose nested `Sequence` instances from `Sequenceable` payloads.
2. Offsets and sequential timing semantics are deterministic and tested.
3. `Sequence` can be wrapped in `Score` without ambiguous conversion paths.
4. Sequence transform semantics are implemented and tested.
5. Documentation reflects canonical naming and workflows.
