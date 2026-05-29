Documentation split plan for chordelia README decomposition.

## Status
Done

**Goal**
Create a docs directory and split README.md into logical documents so onboarding stays fast while deeper guidance remains easy to find.

**Why this comes first**
1. The current README mixes quick-start and deep reference material, which makes scanning harder.
2. A docs-first structure reduces maintenance churn when examples and module details change.
3. Clear ownership boundaries prevent future documentation bloat in the main README.

**Scope**
1. Create a top-level docs directory with focused markdown guides.
2. Refactor existing README content into main README plus sub-readmes.
3. Add clear cross-links between README.md and docs pages.
4. Preserve all useful existing documentation content (no feature-level info loss).
5. Create a README-writing skill that standardizes future README and docs structure updates.

**Out of scope**
1. Major API rewrites or feature changes.
2. Rewriting all examples for new behavior (content move and light edits only).
3. Hosting/publishing docs on a separate site.

**Testing approach**
1. Validation type: documentation regression and navigation validation.
2. Link validation:
   1. Verify all links in README.md and docs/*.md resolve correctly.
   2. Verify every sub-readme links back to README.md or docs index.
3. Content coverage validation:
   1. Confirm key onboarding flows remain in README.md (install, minimal quick start, where to go next).
   2. Confirm deep sections moved to docs pages are discoverable from README.md.
4. Formatting validation:
   1. Confirm markdown rendering in VS Code preview for all new files.
   2. Confirm code blocks keep language tags and still read correctly.
5. If no automated markdown-link checker is introduced in this phase, perform manual link checks and document completion in the checklist.

**Progress checklist**
- [x] Phase 0: README inventory and chunk map complete
- [x] Phase 1: docs information architecture finalized
- [x] README skill created and wired into AGENTS guidance
- [x] Phase 2: Main README reduced to onboarding-first content
- [x] Phase 3: Sub-readmes created and populated
- [x] Phase 4: Cross-links and navigation validated
- [x] Phase 5: Final review for duplication and clarity complete
- [x] Docs split complete

**Implemented move matrix**
1. README installation details -> docs/installation.md (summary retained in README.md)
2. README long quickstart walkthroughs -> docs/quickstart.md and docs/guides/*
3. README notes and intervals deep examples -> docs/guides/notes-and-intervals.md
4. README scales/chords and progression examples -> docs/guides/scales-and-chords.md
5. README rhythm/timing and metronome examples -> docs/guides/rhythm-and-timing.md
6. README immutable design deep dive -> docs/immutability.md
7. README API class and enum catalog -> docs/api-overview.md
8. README testing/versioning/publishing details -> docs/development.md
9. Future README/docs ownership rules -> skills/readme-writing.md

**Phases**

**Phase 0: Inventory and chunk map**
1. Label current README sections as one of:
   1. Keep in main README
   2. Move to docs sub-readme
   3. Keep in both (short summary in README, full detail in docs)
2. Identify duplicate examples and overlapping explanations to remove.
3. Produce a "source -> destination" move matrix for each major section.

**Phase 1: Docs information architecture**
1. Create docs directory and docs index page at docs/README.md.
2. Define initial sub-readmes:
   1. docs/installation.md
   2. docs/quickstart.md
   3. docs/guides/notes-and-intervals.md
   4. docs/guides/scales-and-chords.md
   5. docs/guides/rhythm-and-timing.md
   6. docs/immutability.md
   7. docs/api-overview.md
   8. docs/development.md
3. Add a short ownership note at the top of README.md and docs/README.md.
4. Create skills/readme-writing.md with:
   1. Main README ownership rules (what stays short and top-level).
   2. Sub-readme ownership rules (what moves to docs/*).
   3. Cross-linking and anti-duplication guidance.
5. Update AGENTS.md skill index to include readme-writing for documentation restructuring tasks.

**Phase 2: Main README content ownership**
1. Keep in README.md:
   1. Project identity and value proposition.
   2. High-level feature summary.
   3. Minimal installation commands (core plus optional extras summary).
   4. One compact quick-start example (or short snippet set) to show immediate value.
   5. Docs navigation section linking to all sub-readmes.
   6. Contribution, license, and high-level development entry points.
2. Move out of README.md (replace with links):
   1. Long module-by-module tutorials.
   2. Extended immutable design deep dive.
   3. Full API class and enum listings.
   4. Advanced analysis/practical usage walkthroughs.
   5. Detailed versioning and publishing procedure.

**Phase 3: Sub-readme content ownership**
1. docs/installation.md
   1. Full install matrix (core, extras, dev).
   2. Environment and dependency notes.
2. docs/quickstart.md
   1. Expanded beginner workflow (notes, intervals, scales, chords, rhythm).
   2. Copy-paste examples optimized for first successful run.
3. docs/guides/*
   1. Domain-specific practical guides with deeper examples.
4. docs/immutability.md
   1. Copy-constructor semantics, with_ patterns, tuple-return conventions.
5. docs/api-overview.md
   1. Class and enum catalog with short purpose statements.
6. docs/development.md
   1. Testing commands and contributor workflow.
   2. Version bump and publishing steps.

**Phase 4: Link and navigation pass**
1. Add "Next steps" links in README.md to top docs pages.
2. Add breadcrumb-style links in docs pages back to docs/README.md and README.md.
3. Ensure no orphan docs page exists without an inbound link.

**Phase 5: Concision and redundancy cleanup**
1. Remove repeated examples that appear in multiple files unless intentionally brief in README and full in docs.
2. Ensure each doc has one clear purpose and minimal overlap.
3. Keep README.md target length onboarding-focused (roughly 2-4 screens before deep links).
4. Validate final structure against skills/readme-writing.md.

**Execution order recommendation**
1. Complete inventory and architecture before moving text.
2. Create docs index, skill file, and skeleton docs before trimming README.
3. Move content in small batches, validating links each batch.
4. Finish with redundancy cleanup and final readability pass.

**Risks and mitigations**
1. Risk: Broken links after content moves.
   1. Mitigation: Run a dedicated link pass and manual markdown preview check.
2. Risk: Losing discoverability of advanced features.
   1. Mitigation: Add explicit "Learn more" links from README sections.
3. Risk: Duplicate content diverges over time.
   1. Mitigation: Keep summaries in README and single source of truth in docs pages.

**Acceptance criteria**
1. README.md is concise, onboarding-first, and links to deeper docs.
2. docs directory exists with a docs/README.md index and the agreed sub-readmes.
3. Each major original README section has a clear destination (kept, moved, or summarized+linked).
4. No critical user journey depends on hidden/orphaned documentation.
5. Documentation structure is maintainable and non-redundant.
6. A readme-writing skill exists in skills/readme-writing.md and is referenced by AGENTS.md.
