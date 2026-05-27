---
name: plan-use
description: 'Create and run implementation plans in .plans with clear scope, phases, checklists, milestones, acceptance criteria, and cross-links to related plans or skills. Use when preparing and executing work.'
argument-hint: 'Describe the initiative and constraints to generate a phased execution plan'
user-invocable: true
---

# Plan Use

Use this skill to draft clear, execution-ready planning documents and keep them actively updated during implementation.

Companion skills: function-naming for naming standards, immutable-types for immutable-model constraints, decision-writing for approach-selection docs, and readme-writing for README/docs ownership and update flow.

## When To Use

- Starting a multi-step feature or refactor
- Aligning existing APIs to conventions before a major change
- Breaking large work into phases and milestones
- Creating prerequisite plans and dependency ordering
- Defining success criteria before coding
- Updating plan checklist status as implementation progresses
- Re-scoping phases when requirements change
- Planning public API or behavior changes that require documentation updates

## Plan Location and Naming

- Store plan files in .plans.
- Keep active/in-progress plans at the .plans root.
- Archive finished plans under .plans/archive/.
- Use concise snake_case names ending in _plan.md when possible.
- Keep one primary goal per plan.
- Add cross-links when one plan depends on another.

Examples:
- .plans/conventions_alignment_plan.md
- .plans/archive/degree_support.md

## Required Plan Sections

Include these sections in order unless there is a strong reason not to:

1. Goal
2. Why this comes first (optional but recommended)
3. Scope
4. Out of scope
5. Technical design details
6. Testing approach
7. Documentation approach
8. Progress checklist
9. Phases (numbered, with concrete deliverables)
10. Execution order recommendation
11. Risks and mitigations (optional)
12. Acceptance criteria

## Technical Design Details Rules

- Include an explicit section named "Technical design details" for any plan that changes code.
- This section should be specific enough that implementation can begin without rediscovering major design choices.
- Cover at least:
	- Canonical types/data models and invariants.
	- API signatures for new or changed public methods.
	- Module/file touchpoints (where each change will occur).
	- Error and validation semantics (what raises, accepted forms).
	- Compatibility and migration notes (what breaks, what is removed, and when).
- Prefer explicit examples for ambiguous contracts (for example input and output forms).
- If design uncertainty remains after this section, create/link a decision doc before coding.

## Testing Approach Section Rules

- Include an explicit section named "Testing approach" in each plan.
- Describe intended coverage by type (for example unit, integration, regression).
- Identify key test targets and critical edge cases.
- Describe mocking/fixture strategy and whether shared fixtures are needed.
- Include how tests will be run and what constitutes passing validation.
- Include expected test delta classification: new tests, updated tests, both, or no test delta.
- If no test changes are expected, state that explicitly with rationale under a "No test delta rationale" note.

## Documentation Approach Section Rules

- Include an explicit section named "Documentation approach" for plans that change public APIs, parsing behavior, validation behavior, examples, or user-facing workflows.
- Identify documentation touchpoints directly (for example README.md, docs/README.md, docs/api-overview.md, and affected guides).
- Include expected docs delta classification: README updates, docs updates, both, or no docs delta.
- If no documentation changes are expected, state that explicitly with rationale under a "No docs delta rationale" note.
- Include how documentation changes will be validated (for example example snippets updated, link paths checked, terminology consistency verified).

## Progress Checklist Rules

- Use markdown checkboxes.
- Keep items outcome-based, not vague activity labels.
- Include both phase-level and milestone-level checks when relevant.
- Keep checklist wording stable so it can be updated over time.
- Keep checklist status up to date as work progresses.
- Mark checklist items complete immediately when the corresponding outcome is met.

Checklist style example:
- [ ] Phase 0: Inventory complete
- [ ] Phase 1: Canonical names selected
- [ ] Milestone A complete

## Phase Design Rules

- Each phase should answer: what changes, where, and how success is verified.
- Prefer small, testable phase boundaries.
- Put compatibility and migration phases before cleanup/removal phases.
- Explicitly call out docs and tests phases.
- Include technical deliverables in each phase (for example signature updates, type migrations, parser behavior).
- For model/API phases, list target files/modules directly.

## Naming and API Planning Rules

- Use canonical names in new plan sections.
- If aliases are needed, mark them as compatibility aliases with retirement intent.
- Avoid planning parallel permanent APIs that do the same thing.
- For naming decisions, load function-naming.

## Pre-Implementation Dependency Rules

- If a conventions or migration prerequisite exists, state it near the top as Prerequisite.
- Link dependent plans directly.
- Do not start downstream feature phases until prerequisite checklist gates are met.
- If a plan depends on unresolved approach choices, create a decision document in decisions/ as a Markdown file and link it from the plan.

## Plan Review Checklist

- Sections are complete and in logical order.
- Scope and out-of-scope are explicit.
- Technical design details are explicit, concrete, and implementation-ready.
- Testing approach section is explicit and actionable.
- Testing approach explicitly states expected test delta classification.
- Any "no test delta" claim includes rationale and is consistent with the planned code changes.
- Documentation approach section is explicit and actionable when user-facing behavior or APIs change.
- Documentation approach explicitly states expected docs delta classification.
- Any "no docs delta" claim includes rationale and is consistent with the planned code changes.
- Checklist is actionable and measurable.
- Checklist status is current and reflects real execution progress.
- Phases map to concrete files/modules.
- Test and documentation work are included.
- Acceptance criteria are unambiguous.
- Acceptance criteria include test validation evidence expectations (focused and full test runs, or justified exception).
- Acceptance criteria include documentation validation expectations (updated references/examples or justified exception).
- Dependencies and prerequisites are linked.
- Finished plans are moved to .plans/archive/.

## Update Procedure for Existing Plans

1. Preserve plan intent and existing completed checklist items.
2. Apply minimal edits for consistency with current conventions.
3. Update all internal references after renames.
4. Update testing and documentation approach if scope, risk, or validation strategy has changed.
5. Update checklist states to reflect the current project state.
6. Re-read full plan to ensure no stale names remain.
7. Note major deltas in commit/PR summary.

## Plan Completion and Archiving

- Treat a plan as finished when acceptance criteria are met and the progress checklist is complete.
- Add a brief completion note before archiving when useful (for example: completed date and any key follow-up links).
- Move the plan from .plans/ to .plans/archive/.
- Update references from active plans so links point to the archived file path.
- Keep archived plans as historical records and avoid substantive rewrites after archival.
