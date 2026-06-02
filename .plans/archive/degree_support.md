First-class degree support plan for chordelia.

## Status
Done

**Goal**
Establish first-class degree support across the library, with one consistent Degree model and DegreeLike coercion at API boundaries. Scale-to-chord workflows remain a major use case, but the scope now includes Scale, Chord, and Interval ergonomics overall.

**Prerequisite**
Complete the conventions alignment plan in .plans/archive/conventions_alignment_plan.md before starting implementation work in this plan.

**Core Principles**
1. One canonical degree type: Degree.
2. One canonical input alias: DegreeLike = Degree | int | str.
3. Coerce at method boundaries, keep internals normalized.
4. Follow existing core-model conventions: explicit immutable classes with __slots__ and explicit methods (not dataclass-first design).

**Progress Checklist**
- [x] Phase 1: Degree foundations (object model, coercion, conversion helpers, roman grammar semantics)
- [x] Phase 2: Scale API adoption (degree widening, mode/chord helpers, chord-generation rules)
- [x] Phase 3: Chord API adoption (tone_at and degree_for_tone helpers)
- [x] Phase 4: Interval ergonomics (degree and simple_degree aliases)
- [x] Phase 5: API simplification (consistency cleanup and canonicalization)
- [x] Phase 6: Test plan coverage
- [x] Phase 7: Documentation updates
- [x] Milestone A complete
- [x] Milestone B complete
- [x] Milestone C complete
- [x] Milestone D complete

**Completion note**
Completed on 2026-05-26. Added first-class Degree support with DegreeLike coercion across Scale/Chord/Interval entrypoints, implemented degree-aware diatonic harmonization APIs, updated tests (full suite passing), and documented new degree-focused workflows.

**API Contract (Explicit Signatures and Return Types)**
1. Type aliases:
	1. DegreeLike = Degree | int | str
	2. RomanCase = "upper" | "lower" | "preserve" | "auto"
2. Degree core:
	1. Degree.coerce(value: DegreeLike) -> Degree
	2. Degree.from_string(text: str) -> Degree
	3. Degree.to_int() -> int
	4. Degree.to_roman(case: RomanCase = "upper") -> str
3. Scale methods:
	1. Scale.degree(degree: DegreeLike) -> Note
	2. Scale.mode_from_degree(degree: DegreeLike) -> Scale
	3. Scale.chord_for_degree(degree: DegreeLike) -> Chord
	4. Scale.chords_for_degrees(*degrees: DegreeLike) -> tuple[Chord, ...]
	5. Scale.degree_for_chord_root(chord_root: Note) -> Degree | None
4. Chord methods:
	1. Chord.tone_at(degree: DegreeLike) -> Note
	2. Chord.degree_for_tone(note: Note) -> Degree | None (optional helper)
5. Interval methods/properties:
	1. interval.degree -> Degree (property)
	2. interval.simple_degree -> Degree (property, normalized 1-7)
6. Return type conventions:
	1. Collection-returning APIs for core models should return tuples, not lists.
	2. Scale.chords_for_degrees preserves input order exactly.
	3. Invalid input raises ValueError (never returns partial progression results).
7. Input conventions for Scale.chords_for_degrees:
	1. Canonical call form: scale.chords_for_degrees(1, 4, 5)
	2. Avoid ambiguous single-tuple overload unless explicitly documented and tested.

**Phase 1: Degree Foundations**
1. Introduce immutable Degree value object using core type style (explicit class with __slots__, explicit validation and conversion methods).
2. Implement Degree.coerce(value: DegreeLike) as the only coercion entrypoint.
3. Implement conversion helpers: from_string, to_int, to_roman, __int__, __str__.
4. Define grammar and validation explicitly:
	1. Supported forms: 1, 2, 3, I, ii, bIII, #iv, V7 (where relevant).
	2. Clear errors with accepted examples.
5. Define Roman case semantics explicitly:
	1. Input parsing must preserve whether the roman token was uppercase, lowercase, or mixed.
	2. Uppercase roman input is interpreted as a major/perfect functional hint when used in chord-function contexts.
	3. Lowercase roman input is interpreted as a minor/diminished functional hint when used in chord-function contexts.
	4. Degree parsing itself remains numeric/ordinal at the core; quality interpretation happens in context-aware APIs (for example Scale.chord_for_degree/chords_for_degrees).
	5. Provide explicit handling for diminished symbols (for example vii°) and document what forms are accepted initially.
6. Define Roman output behavior:
	1. Degree.to_roman(case="upper"|"lower"|"preserve"|"auto").
	2. preserve uses original parsed case when available.
	3. auto uses context-aware rendering rules (for example chord quality/function when available), otherwise defaults to upper.

**Phase 2: Scale API Adoption**
1. Widen Scale.degree to accept DegreeLike.
2. Widen Scale.mode_from_degree to accept DegreeLike.
3. Add Scale.chord_for_degree(degree: DegreeLike) returning the default diatonic triad for that scale degree.
4. Add Scale.chords_for_degrees(*degrees: DegreeLike) returning default diatonic triads in input order.
5. Scope rule: the 7-note limitation applies only to harmonic chord-generation methods (Scale.chord_for_degree and Scale.chords_for_degrees), not to Scale.degree or Scale.mode_from_degree.
6. In Scale.chord_for_degree/chords_for_degrees, when roman input is provided, honor uppercase/lowercase functional intent by default, and raise explicit errors when the requested function conflicts with scale-derived harmony rules.
7. Seventh and richer sonorities are created after construction using existing Chord APIs (for example with_extension), not via selector parameters on Scale.chord_for_degree/chords_for_degrees.

**Phase 3: Chord API Adoption**
1. Add chord-tone accessor: Chord.tone_at(degree: DegreeLike).
2. Add optional helper returning chord-function degree for a given note.
3. Keep additions/omissions interval-based for now; defer DegreeLike there until scale-context semantics are designed.
4. Use existing copy-constructor style methods (with_extension, with_inversion, with_bass, with_) for post-construction refinement of chords created from scales.

**Phase 4: Interval Ergonomics**
1. Keep Interval.number behavior unchanged.
2. Add interval.degree as alias returning Degree from interval number semantics.
3. Add interval.simple_degree for 1-7 normalized degree.
4. Avoid key-dependent accidental semantics in Interval-level degree APIs.

**Phase 5: API Simplification (Pre-1.0 Breaking Changes Allowed)**
1. Replace int-based degree returns with Degree where that improves consistency.
2. For methods like Scale.degree_for_chord_root, switch directly to Optional[Degree].
3. Prefer one canonical API over temporary parallel methods.

**Phase 6: Test Plan**
1. Degree round-trip tests: int <-> Degree <-> roman.
2. Degree coercion tests across Scale, Chord, and Interval entrypoints.
3. Scale harmonization tests for default triads (major and natural minor).
4. Roman parsing tests including accidentals and invalid forms.
5. Non-heptatonic error tests for Scale.chord_for_degree/chords_for_degrees only.
6. Immutability regression tests for affected objects.
7. Post-construction refinement tests: scale.chord_for_degree(...).with_extension("7") and related copy-constructor workflows.

8. Roman case behavior tests:
	1. Input case preservation (I vs i, IV vs iv, bIII vs biii).
	2. Context interpretation in chord-generation APIs (uppercase/lowercase functional hints).
	3. Output casing modes (upper, lower, preserve, auto).
	4. Diminished symbol forms (vii° and accepted aliases).

**Phase 7: Documentation**
1. Add Degree section to README with accepted formats and examples.
2. Add examples:
	1. scale.chord_for_degree("I") and scale.chord_for_degree(4)
	2. scale.chords_for_degrees("ii", "V", "I")
	3. chord.tone_at(3)
	4. interval.simple_degree
3. Document updated canonical degree APIs and input formats.
4. Add a Roman case semantics section with concrete examples of interpretation and output formatting.

**Target Sites To Update**
1. src/chordelia/scales.py: degree, mode_from_degree, degree_for_chord_root, new chord_for_degree/chords_for_degrees.
2. src/chordelia/chords.py: new tone_at/degree_for_tone helpers, DegreeLike boundary coercion where applicable.
3. src/chordelia/intervals.py: degree aliases and helper constructors if needed.
4. tests/unit/chordelia/test_scales.py, tests/unit/chordelia/test_chords.py, tests/unit/chordelia/test_intervals.py: add Degree-focused coverage.

**Milestones**
1. Milestone A: Degree object + coercion + Scale int-based chord generation.
2. Milestone B: Roman numeral parsing with explicit case semantics.
3. Milestone C: Chord tone-degree accessors and Interval degree aliases.
4. Milestone D: API cleanup, docs, and full test coverage.
