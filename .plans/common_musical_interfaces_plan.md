Common musical interface plan for chordelia.

## Status
Implementing

## Dependency state
1. Core `Sequenceable` contract, context model, and adapter fallback behavior are implemented in the common boundary.
2. Phase 3 is dependency-gated and deferred to wrapper plans:
   1. `.plans/sequence_to_midi_export_plan.md`
   2. `.plans/sheet_music_rendering_plan.md`
3. Phase 5 is dependency-gated and deferred until Phase 3 wrapper integration and Phase 4 native migration gates are complete.

## Goal
Define and adopt `Sequenceable` as the canonical capability interface for objects that can be wrapped by `Score` and consumed uniformly by `MidiFile` and `SheetMusic`.

## Why this comes first
1. A single capability seam removes duplicated per-type conversion checks.
2. `Score` depends on a stable contract for converting mixed musical objects into score events.
3. Canonical wrappers (`MidiFile`, `SheetMusic`) rely on this contract for consistent behavior.

## Scope
1. Define `Sequenceable` protocol/interface contract.
2. Implement `Sequenceable` on `Note`, `Chord`, and `Sequence`.
3. Define conversion context model used by `Sequenceable` methods.
4. Provide temporary adapter strategy for migration-only non-sequenceable objects.
5. Align wrappers and plans with this canonical contract.
6. Remove adapter registry APIs after required type migration and contract lock.

## Out of scope
1. Requiring all domain types (for example `Scale`, `Degree`) to implement `Sequenceable` in v1.
2. Broad capability taxonomy expansion as canonical API (for example global `Playable`/`Renderable` interfaces).
3. Breaking removal of existing helper methods in one step.
4. Removing adapter registry before migration gates pass.

## Technical design details
1. Canonical interface:
   1. Add `src/chordelia/sequenceable.py`.
   2. Protocol surface:
      1. `score_events_for_context(context: ScoreEventContext) -> tuple[ScoreEvent, ...]`.
2. Canonical implementers (v1):
   1. `Note`.
   2. `Chord`.
   3. `Sequence`.
3. Context model:
   1. Add `ScoreEventContext` in `src/chordelia/score.py` or dedicated context module.
   2. Include tempo, time signature, start offset, default duration, velocity, channel, voice, key context.
4. Adapter strategy:
   1. Add lightweight adapter registry for migration compatibility.
   2. Non-sequenceable values raise `TypeError` unless explicit adapter exists.
   3. Treat adapters as transitional and internal-first, not long-term extension surface.
   4. Track every adapter registration and owner in tests and docs.
5. Wrapper integration:
   1. `Score` accepts `Sequenceable`.
   2. `MidiFile` accepts `Score | Sequenceable`.
   3. `SheetMusic` accepts `Score | Sequenceable`.
6. Naming guidance for non-canonical capability ideas:
   1. `Playable` and `Renderable` are useful conceptual terms but remain non-canonical interface names in v1.
   2. Prefer concrete wrappers (`MidiFile`, `SheetMusic`) over broad ambiguous interface names.

## API signatures (proposed)
1. `class Sequenceable(Protocol):`
   1. `def score_events_for_context(self, context: ScoreEventContext) -> tuple[ScoreEvent, ...]: ...`
2. Adapter API:
   1. `register_sequenceable_adapter(type_, adapter)`.
   2. `score_events_for(value, context)`.

## Adapter registry decommission plan
1. Ordered native-conversion requirements before removal:
   1. `Sequence` (highest priority): must be fully `Sequenceable` because it is the canonical composition container.
   2. `Rest`: must have a native no-op conversion path through sequence flattening (or direct `Sequenceable` behavior) without adapters.
   3. Any type currently accepted by public `Score`/`MidiFile`/`SheetMusic` constructors must be native `Sequenceable`.
   4. Any internal type currently using a registered adapter in non-test code must be migrated to native `Sequenceable`.
2. Explicit type policy for currently debated domain types:
   1. `Note`: already native `Sequenceable`.
   2. `Chord`: already native `Sequenceable`.
   3. `Scale`: either (a) add native `Sequenceable` before decommissioning, or (b) explicitly remove direct wrapper acceptance and require coercion to `Note`/`Chord`/`Sequence` first.
   4. `Degree`: either (a) add native context-aware `Sequenceable` behavior before decommissioning, or (b) explicitly remove direct wrapper acceptance and require coercion first.
3. Decommission gates:
   1. Zero adapter registrations in non-test runtime paths.
   2. Public docs list only native `Sequenceable` accepted inputs.
   3. `score_events_for(...)` no longer consults `_ADAPTER_REGISTRY`.
   4. `register_sequenceable_adapter`, `unregister_sequenceable_adapter`, and `clear_sequenceable_adapters` are removed from public exports.
4. Decommission implementation sequence:
   1. Lock accepted-input contract for `Score`, `MidiFile`, and `SheetMusic`.
   2. Land native conversions for required types.
   3. Remove adapter registry usage from conversion path.
   4. Remove adapter API functions and related tests.
   5. Update docs and migration notes.

## Module and file touchpoints
1. New/updated:
   1. `src/chordelia/sequenceable.py`.
   2. `src/chordelia/score.py`.
   3. `src/chordelia/sequences.py`.
   4. `src/chordelia/notes.py`.
   5. `src/chordelia/chords.py`.
   6. `src/chordelia/midifile.py`.
   7. `src/chordelia/sheet_music.py`.
   8. `src/chordelia/__init__.py`.
2. Tests:
   1. `tests/unit/chordelia/test_sequenceable.py`.

## Cross-plan references
1. `.plans/first_class_sequence_support_plan.md`.
2. `.plans/shared_score_ir_implementation_plan.md`.
3. `.plans/sequence_to_midi_export_plan.md`.
4. `.plans/sheet_music_rendering_plan.md`.

## Testing approach
Expected test delta classification: both new tests and updated tests.

1. Unit tests:
   1. Runtime protocol conformance for `Note`, `Chord`, `Sequence`.
   2. Adapter dispatch and fallback errors.
   3. Deterministic score-event ordering contract.
2. Integration tests:
   1. Mixed `Sequenceable` payloads through `Score`.
   2. Shared conversion boundary feeding both wrappers.
3. Regression tests:
   1. Existing transpose and note/chord semantics remain unchanged.

## Documentation approach
Expected docs delta classification: both README updates and docs updates.

1. Add `Sequenceable` contract section in API docs.
2. Document canonical wrappers and why they replace broad `Playable`/`Renderable` interfaces in v1.
3. Provide examples for mixed `Sequenceable` composition and output.

## Progress checklist
- [x] Phase 0: Sequenceable contract and context finalized
- [x] Phase 1: Note/Chord/Sequence conformance implemented
- [x] Phase 2: Adapter registry and fallback behavior implemented
- [ ] Phase 3: Score and wrapper integration completed (deferred: wrapper plans)
- [ ] Phase 4: Required native type migrations completed
- [ ] Phase 5: Adapter registry removed from runtime and public API (deferred: depends on Phase 3 and Phase 4)
- [ ] Phase 6: Tests/docs completed
- [ ] Sequenceable adopted as canonical capability seam without adapter registry

## Phases
### Phase 0: Contract lock
1. Finalize protocol signature and context type.
2. Finalize implementer set for v1.

### Phase 1: Core conformance
1. Implement `Sequenceable` behavior in `Note`, `Chord`, `Sequence`.
2. Verify deterministic conversion behavior.

### Phase 2: Adapter and fallback
1. Implement adapter registration API.
2. Enforce explicit errors for unsupported values.

### Phase 3: Pipeline integration (dependency-gated)
1. Keep `Score` on the canonical interface path in this plan.
2. Defer `MidiFile` constructor integration to `.plans/sequence_to_midi_export_plan.md`.
3. Defer `SheetMusic` constructor integration to `.plans/sheet_music_rendering_plan.md`.

### Phase 4: Native migration gates
1. Convert required types to native `Sequenceable` in priority order:
   1. `Sequence`.
   2. `Rest` conversion path.
   3. Publicly accepted wrapper input types.
2. Resolve `Scale` and `Degree` policy explicitly (native conversion or explicit non-acceptance).

### Phase 5: Registry decommission (dependency-gated)
1. Remove adapter lookup from `score_events_for` runtime path after Phase 3 and Phase 4 gates pass.
2. Remove adapter API functions and public exports after wrapper accepted-input contracts are locked.
3. Replace adapter tests with direct-conformance tests.

### Phase 6: Verification and docs
1. Complete test coverage.
2. Update docs/examples and plan links.

## Execution order recommendation
1. Lock interface first.
2. Implement domain conformance before wrappers.
3. Integrate wrappers only after score-event parity tests pass.
4. Remove registry only after native migration gates pass.

## Risks and mitigations
1. Risk: interface too broad for v1.
   1. Mitigation: keep one required method and grow only with proven need.
2. Risk: ambiguous broad capability names.
   1. Mitigation: keep wrappers canonical, not generic capability interfaces.
3. Risk: adapter and direct implementations diverge.
   1. Mitigation: parity tests across both paths.
4. Risk: registry removed before all accepted types are native.
   1. Mitigation: explicit gate requiring zero non-test adapter usage and locked accepted-input contract.

## Acceptance criteria
1. `Sequenceable` exists as canonical interface.
2. `Note`, `Chord`, and `Sequence` implement it.
3. `Score` and wrappers consume `Sequenceable` uniformly with no adapter registry dependency.
4. Required type migration order is completed and documented (`Sequence`, `Rest`, then remaining accepted wrapper-input types).
5. Adapter registry APIs are removed from runtime and public exports.
