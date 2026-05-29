Composite sequence tree model follow-up plan for chordelia.

## Status
Drafting

## Goal
Define a future composite sequence model that preserves tree structure (sections/phrases/motifs) while remaining compatible with canonical `Score` conversion and deterministic event ordering.

## Why this comes first
1. Constructor-level flattening solves immediate ergonomics for repeated motifs, but loses explicit structure.
2. Some workflows need reusable section references and tree-level transforms without early materialization.
3. A dedicated composite model avoids overloading `Sequence` with conflicting timing semantics.

## Scope
1. Introduce a dedicated composite type (working name: `CompositeSequence`) for tree composition.
2. Support ordered child references (`Sequence` and nested `CompositeSequence`) with explicit timing/span rules.
3. Define deterministic conversion from tree model into canonical flat `SequenceEntry` stream for `Score` generation.
4. Define invariants for cursor/span propagation across nested children.
5. Add explicit APIs for repetition and concatenation that preserve structure.

## Out of scope
1. Replacing current `Sequence` constructor flattening behavior.
2. UI timeline editing or DAW arrangement features.
3. Realtime transport/session behaviors.
4. Compatibility aliases for multiple competing canonical timeline types.

## Technical design details
1. Canonical models and invariants
   1. Keep `Sequence` as the flat canonical scheduling model.
   2. Add `CompositeSequence` as optional tree composition model.
   3. Require explicit child span semantics:
      1. parent child-start position
      2. child effective span used for cursor advancement
      3. optional override duration behavior (if supported)
2. API sketch
   1. `CompositeSequence(children: Iterable[CompositeChildLike])`
   2. `CompositeSequence.flatten() -> Sequence`
   3. `CompositeSequence.repeat(n: int) -> CompositeSequence`
   4. `CompositeSequence.concatenated(*others) -> CompositeSequence`
3. Conversion semantics
   1. `Score.from_sequenceable` should accept `CompositeSequence` through `Sequenceable` boundary.
   2. Tree conversion must remain deterministic and stable across runs.
4. File touchpoints
   1. `src/chordelia/sequences.py` (or sibling module if model split is clearer)
   2. `src/chordelia/score.py`
   3. `src/chordelia/__init__.py`
   4. `tests/unit/chordelia/test_sequenceable.py`
   5. docs updates in `docs/quickstart.md` and `docs/api-overview.md`
5. Error and validation semantics
   1. Invalid child span relationships raise `ValueError` with actionable guidance.
   2. Unsupported child payloads raise `TypeError` through canonical `Sequenceable` checks.

## Testing approach
Expected test delta classification: both new tests and updated tests.

1. Unit tests
   1. Tree to flat conversion ordering and beat placement.
   2. Repetition and concatenation preserving structure before flatten.
   3. Invalid span/offset combinations.
2. Regression tests
   1. Existing flat `Sequence` constructor behavior remains unchanged.
3. Validation commands
   1. Focused: `pytest tests/unit/chordelia/test_sequenceable.py`
   2. Full: `pytest`

## Documentation approach
Expected docs delta classification: both README updates and docs updates.

1. Add `CompositeSequence` usage to `docs/quickstart.md` after API is final.
2. Add reference semantics to `docs/api-overview.md`.
3. Keep README summary concise and link to docs for deep tree semantics.

## Progress checklist
- [ ] Phase 0: Composite semantics locked
- [ ] Phase 1: Model and validation implemented
- [ ] Phase 2: Tree-to-flat conversion implemented
- [ ] Phase 3: Score integration completed
- [ ] Phase 4: Tests and docs completed
- [ ] Composite sequence follow-up complete

## Phases
### Phase 0: Contract lock
1. Finalize child span/cursor semantics.
2. Lock conversion determinism guarantees.

### Phase 1: Model
1. Implement `CompositeSequence` and child types.
2. Add validation and constructor coercion.

### Phase 2: Flatten pipeline
1. Implement deterministic `flatten()` to canonical `Sequence`.
2. Validate ordering, timing, and recursive traversal behavior.

### Phase 3: Integration
1. Ensure `Score.from_sequenceable` accepts composite model cleanly.
2. Confirm no regressions for existing flat `Sequence` workflows.

### Phase 4: Verification and docs
1. Add/adjust tests.
2. Update docs with final API and examples.

## Execution order recommendation
1. Lock semantics before coding.
2. Implement model and flatten pipeline before score integration.
3. Complete tests and docs before API stabilization.

## Risks and mitigations
1. Risk: ambiguous child span semantics.
   1. Mitigation: define explicit invariants and error rules before implementation.
2. Risk: overlap with existing flat `Sequence` APIs.
   1. Mitigation: keep `Sequence` canonical for scheduling and make composite model additive.
3. Risk: runtime cost from deep trees.
   1. Mitigation: flatten to canonical `Sequence` once per conversion boundary.

## Acceptance criteria
1. Composite trees can represent repeated motifs/sections without immediate flattening.
2. Conversion to flat `Sequence` is deterministic and validated by tests.
3. Existing flat `Sequence` behavior remains intact.
4. Documentation clearly differentiates flat and composite models.
