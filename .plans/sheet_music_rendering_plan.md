Sheet-music rendering plan for chordelia.

## Status
Drafting

## Goal
Make `SheetMusic` the canonical sheet-rendering wrapper around `Score` (and therefore `Sequenceable` inputs), supporting file output (SVG/image) and notebook rendering, without file parsing/read support in v1.

## Why this comes first
1. Sheet output should consume the same canonical score path as MIDI.
2. Wrapper-based APIs give consistent user ergonomics with `MidiFile`.
3. Notebook-first rendering requires a stable output object contract.

## Scope
1. Define canonical `SheetMusic` class surface.
2. Accept `Score | Sequenceable` inputs and normalize through `Score`.
3. Support file write outputs (SVG first, optional raster export).
4. Add notebook rich-display hooks.
5. Keep notebook dependencies optional and independent from MIDI notebook extras.

## Out of scope
1. Reading/parsing notation files into score objects in v1.
2. Full professional engraving feature parity.
3. Interactive notation editor UI.

## Technical design details
1. Canonical class contract:
   1. `SheetMusic` wraps internal `score: Score`.
   2. Constructor accepts `Score | Sequenceable`.
2. Required class and instance APIs:
   1. `SheetMusic.to_file(self, file_path, *, format="svg") -> Path`.
   2. `SheetMusic.score_to_file(score: Score, file_path, *, format="svg") -> Path`.
   3. Explicitly no `load_from_file`/parse method in v1.
3. Notebook rendering contract:
   1. `_repr_mimebundle_` renders SVG/HTML when optional sheet notebook extras are installed.
   2. Text fallback when optional deps are missing.
4. Backend strategy alignment:
   1. Keep renderer backend adapter-driven (in-house SVG primary, optional bridge path).
   2. `SheetMusic` remains backend-agnostic at API surface.
5. Dependency policy:
   1. `sheet`: core rendering.
   2. `sheet-notebook`: notebook rendering helpers only.
   3. No dependency from `sheet-notebook` to `midi-notebook`.
6. Module/file touchpoints:
   1. `src/chordelia/sheet_music.py` (or chosen module path).
   2. `src/chordelia/score.py`.
   3. `src/chordelia/sequenceable.py`.
   4. `src/chordelia/__init__.py`.
   5. `tests/unit/chordelia/test_sheet_music.py` (new/expanded).

## Cross-plan references
1. `.plans/shared_score_ir_implementation_plan.md`.
2. `.plans/first_class_sequence_support_plan.md`.
3. `.plans/sequence_to_midi_export_plan.md`.
4. `.plans/common_musical_interfaces_plan.md`.
5. `decisions/sheet_music_rendering_strategy_decision.md`.

## Testing approach
Expected test delta classification: both new tests and updated tests.

1. Unit tests:
   1. `SheetMusic` constructor normalization to internal `Score`.
   2. `to_file` output generation for SVG and selected formats.
   3. `score_to_file` parity with instance write path.
   4. Notebook MIME rendering/fallback behavior.
2. Integration tests:
   1. `Sequence -> Score -> SheetMusic.to_file` path.
   2. `Note/Chord -> Score -> SheetMusic` path parity.
3. Visual regression tests:
   1. Stable SVG snapshots for canonical cases.
4. Dependency-isolation tests:
   1. `sheet` works without `sheet-notebook`.
   2. `sheet-notebook` works without `midi-notebook`.

## Documentation approach
Expected docs delta classification: both README/docs updates and API updates.

1. Document `SheetMusic` as canonical output wrapper for notation.
2. Document lack of parse/read APIs in v1.
3. Add notebook examples for inline sheet rendering.

## Progress checklist
- [ ] Phase 0: Canonical SheetMusic API finalized
- [ ] Phase 1: Score-backed write path implemented
- [ ] Phase 2: Backend adapter integration completed
- [ ] Phase 3: Notebook hooks implemented
- [ ] Phase 4: Tests and visual regression completed
- [ ] Phase 5: Docs/examples completed
- [ ] Canonical SheetMusic workflow adopted

## Phases
### Phase 0: API lock
1. Lock class and method signatures.
2. Lock no-parse/read boundary for v1.

### Phase 1: Score-backed writing
1. Implement constructor normalization.
2. Implement `to_file` and `score_to_file`.

### Phase 2: Backend adapters
1. Connect canonical output to selected rendering backend(s).
2. Validate format support and deterministic output.

### Phase 3: Notebook rendering
1. Implement rich-display hooks and fallbacks.

### Phase 4: Verification
1. Add unit/integration/visual regression tests.
2. Add dependency-isolation validation.

### Phase 5: Documentation
1. Update docs and examples.
2. Clarify boundaries and optional extras.

## Execution order recommendation
1. Lock API before backend expansion.
2. Implement write path before notebook rendering.
3. Finish visual regression before stability declaration.

## Risks and mitigations
1. Risk: confusion with `MidiFile` read/write parity.
   1. Mitigation: clearly document `SheetMusic` as write-only in v1.
2. Risk: backend drift in output semantics.
   1. Mitigation: adapter contract plus snapshot tests.
3. Risk: optional dependency bleed.
   1. Mitigation: strict extras boundaries and isolation tests.

## Acceptance criteria
1. `SheetMusic` is canonical notation wrapper around `Score`/`Sequenceable`.
2. `to_file` and `score_to_file` are implemented and documented.
3. No parse/read API is exposed in v1.
4. Notebook rendering works with optional extras and degrades gracefully without them.
