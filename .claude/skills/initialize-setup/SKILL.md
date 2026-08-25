---
name: initialize-setup
description: Scans any project to detect its architecture, tech stack, conventions, and code standards, then populates CLAUDE.md with project context. Supports two modes - architect's standards document (PDF/markdown) or automatic codebase scan. Use at the start of a project or when onboarding onto an unfamiliar codebase. Works across backend, frontend, API, data, platform, and mixed-stack systems.
---

# Initialize Setup

Populate `CLAUDE.md` so all agents operate with accurate project knowledge instead of generic defaults.

Who should run this:
- the project architect
- the tech lead
- or whoever owns the project’s technical standards and conventions

## When To Use

- First time working on a project
- Onboarding onto an existing codebase
- After major architectural changes
- When `CLAUDE.md` still shows `[Run /initialize-setup to populate]`

## Mode Selection

Choose one mode before doing anything else:

- **Mode A — Architect's Document**
  The user provided a standards document, architecture document, onboarding guide, or technical handbook in PDF/markdown form.

- **Mode B — Codebase Scan**
  No document was provided. Infer conventions directly from the repository.

- **Mode C — Hybrid**
  A document was provided, but it is incomplete or stale. Use the document as the primary source and fill gaps from the codebase.

---

## Mode A / C — Document-Led Setup

### 1. Read The Document

Read the provided PDF or markdown file.

Extract:
- project identity, purpose, architecture, constraints
- runtimes, frameworks, build/test/deploy commands
- coding conventions, file structure, interface patterns, testing expectations

### 2. Map To CLAUDE.md Sections

Map findings into:

- **`<project_context>`**
  Project name, organization, purpose, architecture style, critical constraints, important team rules.

- **`<codebase_stack>`**
  Primary runtimes, frameworks, build toolchain, deploy/test commands, infrastructure, environment URLs.

- **`<code_standards>`**
  Naming conventions, module/file structure, architecture boundaries, interface patterns, service patterns, testing patterns, pattern categories, and anti-patterns.

### 3. Validate Against The Codebase

Do not trust the document blindly. Validate key claims against the repo:

- tech stack matches dependency/build files
- build/deploy/test commands are real
- naming conventions match existing code
- documented architecture matches actual modules and boundaries

If the document and codebase disagree, report:

```text
DISCREPANCY:
- Document says: {X}
- Codebase shows: {Y}
- Proposed source of truth: {document | codebase}
- Reason: {why}
```

If the discrepancy changes behavior or conventions materially, ask the user to resolve it before finalizing.

---

## Mode B / C — Codebase Scan

### 1. Scan Repository Structure

Read the actual repository and identify:

- build/config files
  `package.json`, `pom.xml`, `build.gradle`, `go.mod`, `pyproject.toml`, `Cargo.toml`, `Makefile`, etc.
- source roots
  `src/`, `app/`, `packages/`, `services/`, `backend/`, `frontend/`, `infra/`, etc.
- test roots
- CI/CD configuration
- runtime/deployment configuration
- docs that describe architecture or conventions

Never infer a fact you have not grounded in the repository.

### 2. Detect Tech Stack

Determine, with evidence:

- **Runtime / backend**
  language, framework, build tool, dependency management, API style, persistence layer

- **Interface / frontend**
  framework, rendering model, styling approach, scripting language, build tool, preview/showcase tooling if any

- **Infrastructure / operations**
  hosting model, cloud platform, CI/CD, containerization, orchestration, deployment model

- **Testing**
  unit/integration/E2E tools, coverage tooling, type/lint tooling if present

If something cannot be determined, mark it explicitly:

```text
unknown -- verify with team
```

### 3. Discover Conventions

Scan real files to extract:

- **Naming conventions**
  types/classes, functions/methods, files, routes, packages/modules, tables/schemas, variables, and any relevant CSS/UI naming

- **File structure**
  how modules, features, services, endpoints, jobs, tests, and configs are organized

- **Code patterns**
  dependency injection, state management, error handling, logging, configuration, data access, API contracts, integration boundaries

- **Pattern categories**
  separate different kinds of work if the repo clearly treats them differently, for example:
  - shared primitives / framework base
  - product features / user-facing flows
  - services / integrations / jobs
  - infrastructure / deployment automation

- **Interface / config patterns**
  rendering patterns, API patterns, schema patterns, workflow patterns, admin/config surfaces

- **Test patterns**
  location, naming, assertion style, mocking style, isolation expectations

Describe what the project actually does. Do not prescribe what it should do.

---

## Write To CLAUDE.md

Update only these sections:

- `<project_context>`
- `<codebase_stack>`
- `<code_standards>`

Do not modify any other framework-level sections.

### `<project_context>`

Write as single-line pointers:

- Project: ...
- Org: ...
- Purpose: ...
- Architecture: ...
- Constraints: ...
- Project rules: ...

### `<codebase_stack>`

Write as single-line pointers:

- Backend: ...
- Frontend: ...
- Build command: ...
- Deploy command: ...
- Test command: ...
- Infrastructure: ...
- Environment URLs: ...

Use the terms `Backend` and `Frontend` as the framework’s standard output labels even if the project is API-only or backend-only. If one side does not exist, state it clearly.

### `<code_standards>`

Write as MUST / MUST NOT / SHOULD rules grouped by relevant headings such as:

- Naming Conventions
- File Structure
- Module Patterns
- Service Patterns
- Interface Patterns
- Test Patterns
- Pattern Categories
- Anti-Patterns

Each rule must be:
- one line
- enforceable
- derived from the real project or the source document

### Required Output Shape

The resulting `CLAUDE.md` sections must follow this exact structure:

```text
<project_context>
Project: ...
Org: ...
Purpose: ...
Architecture: ...
Constraints: ...
Project rules: ...
</project_context>

<codebase_stack>
Backend: ...
Frontend: ...
Build command: ...
Deploy command: ...
Test command: ...
Infrastructure: ...
Environment URLs: ...
</codebase_stack>

<code_standards>
## Naming Conventions
- MUST ...

## File Structure
- MUST ...

## Module Patterns
- MUST ...

## Service Patterns
- MUST ...

## Interface Patterns
- MUST ...

## Test Patterns
- MUST ...

## Pattern Categories
- ...

## Anti-Patterns
- MUST NOT ...
</code_standards>
```

If the project does not have a meaningful `Frontend` or `Backend` surface, still keep the field and state that it is not applicable.

---

## Validate Before Finishing

Confirm:

- all three target sections are populated
- placeholder text is gone
- build/deploy/test commands are present
- no unrelated parts of `CLAUDE.md` were changed
- no decorative or misleading text was introduced

### Conflict Check

After writing the sections:

- compare discovered conventions against the framework rules in `CLAUDE.md`
- identify contradictions
- if a contradiction exists, report it explicitly

Use this format:

```text
CONFLICT DETECTED:
- Framework says: {rule}
- Project uses: {actual pattern}
- Recommendation: {follow project pattern | update project to match framework}
```

Per framework priority, project conventions win over framework defaults unless the user says otherwise.

---

## Final Output

Report:

- Mode used
- whether `CLAUDE.md` was updated successfully
- detected project architecture
- detected runtimes/frameworks
- detected infrastructure/deployment model
- any `unknown -- verify with team` values
- any discrepancies or conflicts found

## Supporting Reference

If the user needs a structured source document to seed this process, use:

- `.claude/references/architect-standards-template.md`

That file is a project guidance prompt, not a questionnaire.
