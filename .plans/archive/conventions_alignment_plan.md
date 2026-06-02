Pre-degree conventions alignment plan for chordelia.

## Status
Done

**Goal**
Align existing types and functions to the current naming and immutability conventions before starting degree support implementation.

**Why this comes first**
1. Reduces naming churn while degree APIs are being introduced.
2. Prevents parallel legacy/canonical names from spreading into new code.
3. Keeps tests/docs consistent with one naming strategy.

**Scope**
1. Existing APIs in Note, Scale, Chord, Interval, Rhythm, MIDI-facing modules.
2. Naming conventions from skills/function-naming.md.
3. Immutable-model constraints from skills/immutable-types.md.

**Out of scope**
1. Implementing Degree itself (tracked in .plans/degree_support.md).
2. Behavioral rewrites unrelated to naming/immutability conventions.

**Progress Checklist**
- [x] Phase 0: Inventory and classification complete
- [x] Phase 1: Core model canonical names selected
- [x] Phase 2: Legacy aliases removed and migration notes published
- [x] Phase 3: Tests migrated to canonical names
- [x] Phase 4: Documentation/examples migrated
- [x] Phase 5: Degree plan references synchronized
- [x] Conventions alignment complete (ready for degree implementation)

**Completion note**
Completed on 2026-05-25. Legacy Scale names were migrated to canonical APIs, Chord legacy aliases were removed, tests/examples/docs were updated, and degree plan synchronization was validated.

**Phase 0: Inventory and classification**
1. Classify every public API as construct, convert, query, transform, cross-type relation, or copy-constructor.
2. Mark each function as:
   1. Keep as-is
   2. Rename to canonical
   3. Remove legacy name after migration
3. Record rationale for each rename or exception.

**Phase 1: Canonical naming decisions**
1. Scale
   1. Rename get_mode -> mode_from_degree.
   2. Rename get_chord_scale_degrees -> degree_for_chord_root.
2. Chord
   1. Keep with_inversion as canonical (copy-constructor).
   2. Keep with_extension as canonical (copy-constructor).
   3. Remove invert and add_extension after migrating call sites.
3. Degree-related naming readiness
   1. Reserve canonical names used by degree plan:
      1. chord_for_degree
      2. chords_for_degrees
      3. tone_at
      4. degree_for_tone
4. Non-core query-style APIs
   1. Review get_available_features, get_midi_ports, get_track_notes, get_suggested_marking.
   2. Keep if they are true query/access patterns and renaming adds little value.
   3. Rename only if they violate intent clarity.

**Proposed rename matrix**
1. Scale.get_mode -> Scale.mode_from_degree (canonical)
2. Scale.get_chord_scale_degrees -> Scale.degree_for_chord_root (canonical)
3. Chord.invert -> Chord.with_inversion (canonical copy-constructor; remove legacy alias)
4. Chord.add_extension -> Chord.with_extension (canonical copy-constructor; remove legacy alias)

**Phase 2: Legacy alias removal policy**
1. Do not retain compatibility aliases for Chord.invert and Chord.add_extension.
2. Remove legacy alias methods after tests/docs/examples are migrated.
3. Add clear migration notes in changelog/release notes.
4. Include before/after examples for renamed APIs.

**Phase 3: Test migration**
1. Update tests to use canonical names first.
2. Remove alias tests for retired names.
3. Add naming regression tests for canonical methods.

**Phase 4: Documentation migration**
1. Update README and examples to canonical names.
2. Add a short migration section listing removed aliases and replacements.
3. Ensure tutorial snippets avoid legacy names.

**Phase 5: Synchronize with degree plan**
1. Ensure .plans/degree_support.md references only canonical names.
2. Confirm degree plan checklist assumes conventions-aligned baseline.
3. Add cross-reference between plans.

**Execution order recommendation**
1. Scale rename pair first (highest impact on degree APIs).
2. Chord canonicalization and alias removal second.
3. Docs/tests third.
4. Degree implementation begins after checklist completion.

**Acceptance criteria**
1. No new public APIs use legacy naming patterns when canonical names exist.
2. Canonical names are used in tests and docs by default.
3. Chord.invert and Chord.add_extension are removed from the public API.
4. Degree plan can be implemented without additional naming churn.
