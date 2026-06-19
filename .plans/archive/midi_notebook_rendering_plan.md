MIDI notebook rendering plan for chordelia.

## Status
Rejected

## Goal
Provide optional notebook rich-display support for `MidiFile` using `_repr_mimebundle_`, including graceful fallback behavior when notebook extras are unavailable.

## Why this comes first
1. Notebook rendering is orthogonal to core MIDI read/write and should not block wrapper API completion.
2. Optional dependency boundaries are easier to validate when isolated in one plan.
3. Keeping notebook concerns separate reduces risk of read/write regressions in `MidiFile`.

## Scope
1. Define and implement `MidiFile` notebook MIME rendering contract.
2. Keep notebook dependencies optional (`midi-notebook`).
3. Implement fallback text output when notebook extras are missing.
4. Add tests for MIME output and fallback behavior.
5. Add docs/examples for notebook usage.

## Out of scope
1. Core MIDI read/write and score normalization contracts.
2. Live MIDI interface playback behavior.
3. Audio playback transport behavior.

## Technical design details
1. Canonical behavior
   1. `MidiFile._repr_mimebundle_` returns notebook-displayable content when optional extras are available.
   2. Fallback path returns text-only representation when notebook extras are unavailable.
2. Dependency policy
   1. `midi` remains sufficient for read/write behavior.
   2. `midi-notebook` adds notebook display helpers only.
   3. Missing notebook extras must not break core `MidiFile` workflows.
3. Module/file touchpoints
   1. `src/chordelia/midifile.py`
   2. `src/chordelia/__init__.py` (exports/optional import boundaries as needed)
   3. `tests/unit/chordelia/test_midifile.py`
   4. `docs/api-overview.md`
   5. `docs/quickstart.md`
4. Error and validation semantics
   1. MIME rendering should never raise for missing notebook extras in normal usage.
   2. Fallback representation should remain deterministic and informative.
5. Implementation pseudocode
   1. `if notebook_helpers_available: return rich_mime_bundle`
   2. `else: return plain_text_bundle`

## Testing approach
Expected test delta classification: both new tests and updated tests.

1. Unit tests
   1. `_repr_mimebundle_` returns expected MIME keys with notebook extras available.
   2. `_repr_mimebundle_` fallback path works when notebook extras are unavailable.
2. Regression tests
   1. Core `MidiFile` read/write tests pass without notebook extras.
3. Validation commands
   1. Focused: `pytest tests/unit/chordelia/test_midifile.py`
   2. Full: `pytest`

## Documentation approach
Expected docs delta classification: docs updates.

1. Document notebook rendering as optional behavior in `docs/api-overview.md`.
2. Add notebook example snippet to `docs/quickstart.md`.
3. Clarify dependency split between `midi` and `midi-notebook`.

## Progress checklist
- [ ] Phase 0: Notebook API contract finalized
- [ ] Phase 1: `_repr_mimebundle_` implementation added
- [ ] Phase 2: Fallback behavior implemented
- [ ] Phase 3: Tests completed
- [ ] Phase 4: Docs and examples completed
- [ ] Midi notebook rendering adopted

## Phases
### Phase 0: Contract lock
1. Lock MIME and fallback behavior expectations.

### Phase 1: MIME implementation
1. Implement rich MIME bundle path with optional helpers.

### Phase 2: Fallback behavior
1. Implement deterministic text fallback behavior.

### Phase 3: Verification
1. Add and run focused tests.
2. Confirm no impact to core read/write behavior.

### Phase 4: Documentation
1. Update docs and examples with optional notebook usage.

## Execution order recommendation
1. Lock contract before coding.
2. Implement MIME and fallback before docs.
3. Validate core read/write independence before completion.

## Risks and mitigations
1. Risk: optional dependency bleed into core runtime.
   1. Mitigation: strict optional import boundaries and fallback tests.
2. Risk: inconsistent notebook output across environments.
   1. Mitigation: deterministic fallback and narrow MIME contract.

## Implementation notes
### 2026-06-05 - Rejection rationale
- Decision: reject this plan and archive it without shipping browser-embedded MIDI player behavior.
- Primary blocker: modern browsers (including Chrome) do not provide reliable native General MIDI audio decoding for raw `.mid` payloads in standard HTML audio controls.
- Technical challenges identified:
   - Browser playback requires a separate synth layer (WebAudio + SoundFont/sample engine), not just MIME embedding.
   - Cross-browser behavior is inconsistent; UI controls may render while playback remains inactive.
   - Optional dependency boundary would grow significantly to support a robust JS synth path and asset management.
   - Maintenance complexity is high for timing/scheduling, instrument mapping, and notebook integration compared to project value.
- Outcome: defer notebook audio playback to future work that explicitly scopes a JS synth or server-side MIDI-to-audio rendering strategy.

## Acceptance criteria
1. Notebook MIME rendering works when optional extras are installed.
2. Fallback output works when notebook extras are missing.
3. Core MIDI read/write remains functional without notebook extras.
4. Notebook behavior and dependencies are documented.
