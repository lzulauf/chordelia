# AGENTS.md

Guidance for coding agents and contributors working in this repository.

## Purpose

Use skills as the primary source of detailed implementation conventions. Keep this file focused on where those conventions live and when to load them.

## Available Skills

### test-writing

- Path: skills/test-writing.md
- Use when:
	- Writing or updating unit tests
	- Adding regression coverage for bug fixes
	- Expanding edge-case/validation matrices with parametrization
	- Testing optional dependency paths with deterministic mocks

### test-running

- Path: skills/test-running.md
- Use when:
	- Running full or focused pytest commands
	- Reproducing and triaging test failures
	- Running slow tests with --runslow intentionally
	- Checking coverage with pytest --cov=src

### plan-use

- Path: skills/plan-use.md
- Use when:
	- Creating or updating plans in .plans before implementation starts
	- Breaking initiatives into phases, milestones, and checklists
	- Defining scope, out-of-scope, prerequisites, and acceptance criteria
	- Coordinating dependency order between multiple plans

### readme-writing

- Path: skills/readme-writing.md
- Use when:
	- Creating or restructuring README and docs content
	- Splitting a large README into focused docs pages
	- Defining ownership boundaries between README.md and docs/
	- Reducing duplicated documentation content and improving cross-links

### skill-writing

- Path: skills/skill-writing.md
- Use when:
	- Creating a new skill in skills/
	- Refactoring existing skills for clarity and concision
	- Reviewing skills to remove redundant instructions
	- Updating AGENTS.md routing for new or changed skills

### decision-writing

- Path: skills/decision-writing.md
- Use when:
	- Creating architecture or approach decision documents
	- Comparing alternative technical strategies and tradeoffs
	- Recommending a specific approach/technology
	- Linking decisions to implementation plans when execution should proceed

### function-naming

- Path: skills/function-naming.md
- Use when:
	- Naming or renaming public APIs
	- Choosing between query, transform, conversion, and constructor names
	- Defining relation-based cross-type names (for, at, on, from)
	- Picking canonical names and alias/deprecation strategy

### immutable-types

- Path: skills/immutable-types.md
- Use when:
	- Adding or refactoring immutable value objects
	- Defining __slots__ and deciding whether __dict__ is needed
	- Implementing copy-constructor APIs (with_*)
	- Applying immutable-specific copy-constructor naming constraints
	- Enforcing tuple-backed collection returns and immutable conventions

### Skill Selection Rule

- If a task is primarily about test coverage or test refactoring, load test-writing.
- If a task is primarily about running tests, triaging failures, or checking coverage, load test-running.
- If a task is primarily about creating, updating, or restructuring execution plans, load plan-use.
- If a task is primarily about choosing between implementation approaches, load decision-writing.
- If a task is primarily about README/docs structure or documentation ownership boundaries, load readme-writing.
- If a task is primarily about creating or reviewing skill files, load skill-writing.
- If a task is primarily about naming strategy, load function-naming.
- If a task is primarily about immutable model design, load immutable-types.
- If both apply, load both skills: function-naming for global naming and immutable-types for immutable-specific constraints.
- If plan work includes naming or immutable model constraints, load plan-use with the relevant companion skill(s).
- If plan work includes documentation restructuring, load plan-use with readme-writing.
- If plan work includes skill creation or skill refactoring, load plan-use with skill-writing.
- If plan work includes unresolved approach choices, load plan-use with decision-writing and create a decision doc in decisions/.
- If test work includes naming or immutable constraints, load test-writing with function-naming and/or immutable-types as needed.
- If test work includes both authoring and execution, load test-writing with test-running.

## Maintenance Rule

- Keep test authoring and coverage conventions in skills/test-writing.md.
- Keep test execution and coverage command conventions in skills/test-running.md.
- Keep plan authoring and execution standards in skills/plan-use.md.
- Keep README/docs structuring conventions in skills/readme-writing.md.
- Keep skill authoring/review conventions in skills/skill-writing.md.
- Keep decision-document conventions in skills/decision-writing.md.
- Keep global naming conventions in skills/function-naming.md.
- Keep immutable-specific modeling constraints in skills/immutable-types.md.
- Keep AGENTS.md focused on skill discovery and when to load each skill.
