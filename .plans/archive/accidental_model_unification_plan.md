Accidental model unification plan for chordelia.

## Status
Done

**Goal**
Unify accidental handling across Note, Degree, and dependent APIs using one canonical accidental model, while preserving strong type semantics for public APIs and simple numeric arithmetic for internal music-theory calculations.

**Why this comes first**
1. Current accidental representations are mixed across modules, which increases translation logic and API inconsistency.
2. Degree support is now first-class, so accidental semantics should be aligned before further scale/chord feature growth.
3. A single accidental model simplifies long-term maintenance and reduces duplicated parsing/formatting behavior.

**Scope**
1. Define one canonical accidental domain model for all core theory objects.
2. Refactor Note and Degree to use the same accidental representation strategy.
3. Update Scale, Chord, and Interval-dependent code paths to consume the unified model.
4. Remove legacy accidental representation paths and conversion shims that become redundant.
5. Update tests, docs, and examples for the new canonical API.

**Out of scope**
1. Reworking enharmonic spelling algorithms beyond accidental-model requirements.
2. New harmony features unrelated to accidental representation.
3. Backward compatibility aliases intended to preserve legacy accidental APIs long-term.

**Technical design details**

1. Canonical accidental domain model (target contract):
   1. Canonical type:
      1. One immutable accidental value object in src/chordelia/accidentals.py.
      2. Canonical internal identity is semitone offset in range -2..2.
      3. Canonical symbol mapping:
         1. -2 -> bb
         2. -1 -> b
         3. 0 -> "" (natural)
         4. 1 -> #
         5. 2 -> ##
   2. Construction and coercion API:
      1. Accidental.coerce(value: Accidental | int | str) -> Accidental
      2. Accidental.from_offset(offset: int) -> Accidental
      3. Accidental.from_string(text: str) -> Accidental
   3. Conversion API:
      1. accidental.to_offset() -> int
      2. accidental.to_symbol() -> str
      3. __int__ and __str__ map to offset and symbol respectively.
   4. Public model contract:
      1. Note.accidental returns canonical Accidental.
      2. Degree.accidental returns canonical Accidental.
      3. Numeric access remains explicit via note.accidental_offset and degree.accidental_offset.
   5. Validation and error rules:
      1. Invalid offsets or symbols raise ValueError with accepted examples.
      2. No silent coercion outside supported forms.
   6. Equality and hashing rules:
      1. Equality is offset-based.
      2. Hashing is stable and offset-derived for immutable usage.

2. File/module touchpoint map:
   1. src/chordelia/accidentals.py:
      1. New canonical Accidental value object and coercion/conversion helpers.
   2. src/chordelia/notes.py:
      1. Replace enum-backed accidental storage and parsing with canonical accidental model.
      2. Keep public accidental behavior stable except where explicitly called out in migration notes.
   3. src/chordelia/degrees.py:
      1. Replace int accidental storage with canonical accidental model.
      2. Preserve DegreeLike and Roman-case semantics.
   4. src/chordelia/scales.py:
      1. Replace accidental comparisons and spelling branches with canonical accidental accessors.
   5. src/chordelia/chords.py:
      1. Ensure root parsing, note generation, and accidental-sensitive behavior route through canonical model.
   6. src/chordelia/__init__.py:
      1. Export canonical accidental API from package root.
   7. tests/unit/chordelia/*:
      1. Update accidental assumptions and expected types across notes/scales/chords/degrees tests.
   8. README.md, docs/*, examples/*:
      1. Replace legacy accidental representation examples with canonical API examples.

3. Compatibility and migration notes (explicit breakage contract):
   1. Public code importing accidental enum members from chordelia.notes will be broken and must migrate to the canonical accidental API.
   2. Direct enum-member equality checks in external code must migrate to canonical accidental equality or accidental_offset comparisons.
   3. Degree accidental access changes from raw int identity to canonical accidental object identity; callers needing arithmetic should use degree.accidental_offset.
   4. Any caller relying on unsupported accidental text should now receive explicit ValueError with accepted-form examples.

**Testing approach**
1. Validation type: unit and regression tests.
2. Unit tests:
   1. Accidental parsing and formatting round-trips.
   2. Note and Degree constructor/coercion behavior with all supported accidental forms.
   3. Scale/chord degree workflows that depend on accidental interpretation.
   4. Canonical accidental coercion matrix (int, symbol, object) using pytest.param ids.
3. Regression tests:
   1. Existing note spelling and transposition expectations.
   2. Chord parsing and scale harmonization behaviors that rely on accidentals.
4. Compatibility checks:
   1. Ensure unsupported legacy accidental forms fail with explicit ValueError messages.
   2. Ensure no accidental-related API silently changes behavior.
5. Mocking and fixture strategy:
   1. No external I/O or network mocking is expected for this migration.
   2. Keep accidental test fixtures local to each module unless shared setup is repeated across files.
   3. Use deterministic parameterized matrices (pytest.param with ids) for accidental conversion and parsing coverage.
6. Validation criteria:
   1. Focused suites pass for notes, scales, chords, intervals, and degrees.
   2. Full suite passes with coverage command: pytest --cov=src.

**Progress checklist**
- [x] Phase 0: Unified accidental contract and migration map finalized
- [x] Phase 1: Canonical accidental model implemented in core module
- [x] Phase 2: Note migrated to canonical accidental model
- [x] Phase 3: Degree migrated to canonical accidental model
- [x] Phase 4: Scale and Chord accidental consumption paths updated
- [x] Phase 5: Legacy accidental representations removed
- [x] Phase 6: Tests migrated and expanded for accidental unification
- [x] Phase 7: Docs and examples migrated to canonical accidental APIs
- [x] Milestone A complete
- [x] Milestone B complete
- [x] Milestone C complete

**Completion note**
Completed on 2026-05-26. Added canonical accidental value object in src/chordelia/accidentals.py, migrated Note and Degree accidental handling to the shared model, updated Scale/Chord consumers, updated tests and docs, and validated with full suite pass.

**Phases**

**Phase 0: Contract and impact inventory**
1. Finalize canonical accidental API with explicit signatures and examples.
2. Inventory all accidental touchpoints in src, tests, docs, and examples.
3. Classify each touchpoint as keep, refactor, or remove.
4. Define explicit breakage list and migration notes for removed representations.
5. Produce a touchpoint map listing each file and the accidental contract change required.

**Phase 1: Canonical accidental model implementation**
1. Implement canonical accidental model in src/chordelia/accidentals.py.
2. Ensure model supports:
   1. Symbol conversion (#, b, ##, bb, natural).
   2. Numeric offset conversion for arithmetic.
   3. Equality and hashing semantics suitable for immutable models.
3. Add coercion helpers for string and numeric accidental forms.
4. Add explicit accidental_offset property access conventions for consumer models.

**Phase 2: Note migration**
1. Refactor Note construction, parsing, and formatting to use the canonical accidental model.
2. Remove Note-specific accidental conversion branches that duplicate canonical behavior.
3. Keep Note arithmetic behavior unchanged where possible.

**Phase 3: Degree migration**
1. Refactor Degree accidental handling to use the same canonical accidental model as Note.
2. Preserve DegreeLike parsing behavior and Roman-case semantics.
3. Keep explicit numeric accidental access available where needed for harmonic computations.

**Phase 4: Scale and Chord adoption**
1. Update scale accidental comparisons and sharp/flat preference logic to use canonical accidental APIs.
2. Update chord parsing and note generation paths that read accidental semantics.
3. Remove transitional accidental conversions in harmonic helper methods.

**Phase 5: API cleanup and removal of legacy paths**
1. Remove obsolete accidental enums or duplicate accidental paths.
2. Remove compatibility-only helpers that are no longer needed.
3. Ensure all public accidental behavior is routed through the canonical model.

**Phase 6: Tests and regression coverage**
1. Update affected tests in notes, scales, chords, intervals, and degrees suites.
2. Add parameterized accidental matrix tests using pytest.param ids.
3. Add regression tests for round-trip formatting and error-message quality.
4. Run focused suites, then full suite with coverage.

**Phase 7: Documentation and examples**
1. Update README and docs guides to describe canonical accidental behavior.
2. Update examples to use canonical accidental APIs only.
3. Add migration notes for removed accidental representations.

**Execution order recommendation**
1. Finalize the canonical accidental contract before editing consumer modules.
2. Migrate Note first, then Degree, then Scale/Chord consumers.
3. Perform API cleanup only after all consumer paths are migrated.
4. Complete docs after tests confirm final behavior.

**Risks and mitigations**
1. Risk: Large breakage surface across tests and examples.
   1. Mitigation: Phase-by-phase migration with focused test runs after each phase.
2. Risk: Silent behavioral drift in accidental interpretation.
   1. Mitigation: Add regression tests that assert exact formatting and pitch-class outcomes.
3. Risk: Overly complex transitional code during migration.
   1. Mitigation: Time-box transitional adapters and remove them in Phase 5.

**Acceptance criteria**
1. One canonical accidental model is used by Note and Degree public APIs.
2. Scale and Chord accidental logic uses canonical accidental accessors only.
3. Legacy accidental representations are removed from public core paths.
4. Tests pass for focused suites and full suite with coverage.
5. Docs and examples describe and demonstrate only the canonical accidental behavior.
6. Canonical accidental contract in this plan is reflected exactly in implemented API signatures.
