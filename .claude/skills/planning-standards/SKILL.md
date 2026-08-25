---
name: planning-standards
description: Universal implementation planning patterns - SDLC category workflows, task classification, complexity estimation, reusability analysis, requirements intelligence, and implementation contract templates. MANDATORY for the planner agent before creating any plan. Also invoke when any agent needs to classify task complexity or evaluate reuse opportunities.
---

# Planning Standards

Universal planning patterns, contract templates, SDLC workflows, and decision frameworks for implementation planning across any tech stack.

## Before Using This Skill (MANDATORY)

This skill provides planning TEMPLATES and FRAMEWORKS — not project-specific patterns. Before applying any template:

1. Check Input-Derived Patterns (from user input — designs, specs, reference implementations, code snippets). These override everything.
2. Check `<code_standards>` in CLAUDE.md — this defines how THIS project structures code, names files, organizes modules, and writes tests.
3. Use this skill for the FRAMEWORK (task classification, complexity signals, contract structure, execution strategy) — but fill templates with project-specific values from `<code_standards>`, NOT the generic examples shown here.

Examples in this skill are FALLBACK illustrations. If the project does it differently, follow the project.

---

## 1. Task Classification

Before any planning activity, classify the task into one of these universal categories:

| Task Type | Signals | Examples |
|-----------|---------|----------|
| **Frontend / UI** | Views, templates, components, styles, client-side behavior, responsive layout, accessibility | "Build a card component", "Add responsive navigation", "Implement search UI" |
| **Backend / Service** | Server-side logic, data access, business rules, background jobs, schedulers, event handlers | "Create user service", "Add caching layer", "Build scheduler for reports" |
| **Integration / API** | External systems, REST/GraphQL endpoints, authentication, data sync, third-party SDKs | "Integrate payment gateway", "Connect to CRM API", "Build webhook handler" |
| **Configuration / Infrastructure** | Environment config, CI/CD, deployment rules, feature flags, infrastructure-as-code | "Set up staging environment", "Add feature flag", "Configure caching rules" |

**Mixed tasks** span multiple types (e.g., full-stack feature = Frontend + Backend). Classify the primary type and note secondary types. The plan must address each type with the appropriate contract template.

This classification guides research scope, contract template selection, and agent assignment.

---

## 2. Complexity Estimation

### T-Shirt Sizing

Analyze the request and research findings to estimate complexity:

**Small (S)**:
- Single file type or layer (frontend OR backend, not both)
- Extends existing code with minor additions (fewer than 3 new fields/methods)
- Uses established project patterns from `<code_standards>`
- No external integrations
- No new configuration surfaces

**Medium (M)**:
- Multiple file types or layers (e.g., component + service + config)
- New module or service following existing patterns
- One external integration using an established auth pattern
- New configuration surface
- Moderate UI complexity (multiple states, conditional rendering)

**Large (L)**:
- Cross-cutting concern (affects multiple modules/services)
- New integration with unfamiliar external system
- Complex UI (dynamic forms, drag-and-drop, real-time updates)
- New architectural pattern not yet established in the project
- Significant performance or scaling requirements
- Multi-environment configuration differences

### Escalation Signals

| Signal | Impact |
|--------|--------|
| "real-time" or "live updates" | +M to L |
| "drag and drop" or "reorderable" | +S to M |
| "user permissions" or "role-based access" | +S to M |
| "multiple languages" or "i18n" | +S to M |
| "external API" without existing client | +M to L |
| "workflow" or "approval process" | +M to L |
| "migration" or "data import/export" | +M to L |
| First implementation of a pattern in the project | +1 size |
| Multiple teams or services affected | +1 size |

**Output**: Include complexity estimate (S/M/L) with rationale in plan summary.

---

## 3. Requirements Intelligence

### Acceptance Criteria Extraction

When user provides a story, ticket, or requirements document:

1. **Parse Input**:
   - Extract: title, description, acceptance criteria (ACs), dependencies, attachments
   - Identify: user persona, business value, success metrics
   - Flag: missing ACs, vague requirements, untestable criteria

2. **AC Validation**:
   - Is each AC testable? (clear pass/fail condition)
   - Is scope bounded? (no open-ended "and more" language)
   - Are edge cases covered? (empty, null, error states)
   - Is the user-facing experience defined? (fields, validation messages, error states)

3. **Hidden Requirements Detection**:
   - **Accessibility**: if UI component, WCAG compliance is implicit
   - **Responsive**: if frontend, mobile/tablet breakpoints expected
   - **i18n**: if content-driven, translation support may be assumed
   - **Analytics**: if user-facing, tracking events may be needed
   - **Caching**: if public content, caching layer considerations
   - **Permissions**: if gated content, access control considerations
   - **Error handling**: fallback behavior when dependencies fail
   - **Security**: input validation, output encoding, auth boundaries

4. **Clarification Triggers**:
   - "Should support multiple..." — Ask: how many? What is the max limit?
   - "Users can configure..." — Ask: which users? Admin/end-user/developer?
   - "Display content from..." — Ask: what if the source is unavailable? Fallback?
   - "Integrate with..." — Ask: auth method? Rate limits? SLA requirements?
   - "Similar to..." — Ask: which specific behaviors to replicate vs. diverge from?

**Output**: List extracted ACs and any hidden/implicit requirements discovered before planning proceeds.

---

## 4. Reusability Scan

### Priority Order (non-negotiable)

1. **Project codebase** — search for existing modules, components, services, utilities FIRST
2. **Framework/platform primitives** — evaluate ONLY if the project already uses them (detected from codebase, not assumed)
3. **External libraries or best practices** — last resort, only when project and codebase provide no guidance

If the project builds custom implementations exclusively, skip framework primitive evaluation. Focus on extending what the project already has.

### Step 1: Search Project Codebase (MANDATORY)

Search the project's source directories (from `<code_standards>`) for:

**Existing modules/components**:
- Search project source directories for similar functionality
- Check module/component groups for related patterns
- Evaluate: can the existing module be extended or configured?

**Existing services/utilities**:
- Search service and utility directories for similar abstractions
- Check service interfaces for reusable contracts
- Evaluate: can the existing service be enhanced vs. creating new?

**Shared helpers**:
- Search for common patterns: HTTP clients, validators, formatters, mappers
- Evaluate: should a utility be extracted from existing implementation?

### Step 2: Evaluate Framework Primitives (CONDITIONAL)

Run this step ONLY if the project codebase shows framework/platform primitive usage:
- Check for inheritance or delegation patterns referencing framework base classes
- If found, evaluate framework primitives for the current requirement
- If not found, skip this step — the project has chosen custom development

### Step 3: Apply Decision Matrix

| Scenario | Action |
|----------|--------|
| Existing code fits 70%+ of requirement | EXTEND / CONFIGURE existing |
| Existing covers 50-69% | EVALUATE extend vs. build (document trade-offs) |
| Existing covers below 50% | BUILD new (extract shared utilities where possible) |
| No existing patterns found | BUILD new (establish pattern for future reuse) |

### Surface, Propose, Confirm (MANDATORY)

Present findings to the user BEFORE the plan proceeds:

```
Found: {module/service name} at {exact path}
Coverage: {X%} — covers {what it covers}, missing {what it does not}

Proposed approach: EXTEND existing / EVALUATE trade-offs / BUILD new
Reason: {one sentence justification}

Proceed with this approach?
```

Do NOT skip this step. Do NOT assume the user wants to build new. The user confirms. Only then does the plan proceed.

**Output**: Include "Reusability Analysis" section in plan with findings, decision, and confirmation received.

---

## 5. SDLC Category Workflows

The planner classifies every task into one of six SDLC categories, then follows the matching workflow.

### 5.1 Build Workflow

For implementation tasks: new features, enhancements, bug fixes, refactoring.

**SDLC**: Plan > Implement > Build > Review > Test > Deploy > Validate

| Phase | What Happens | Agent |
|-------|-------------|-------|
| Plan | Classification, reusability scan, implementation contract | planner |
| Implement | Write code following the plan's technical contract | schema-processor / dataset-creator / quality-analyzer / data-ingestion / data-validator |
| Build | Compile, run project build command from `<codebase_stack>` | dev agent |
| Review | Code review against standards, security, performance | code-reviewer |
| Test | Unit tests, integration tests | test-specialist |
| Deploy | Deploy to target environment | direct execution |
| Validate | Full validation of deployed implementation | direct execution (AEP APIs, curl, logs) |

**Autonomy**: S/M execute all phases end-to-end. L pauses after Plan for confirmation, asks before Deploy.

**Build-specific steps**:
1. Classify pattern category — determine which codebase pattern governs the task using code-explorer findings and `<code_standards>`
2. Run reusability scan (Section 4) — get user confirmation
3. Assess complexity (Section 2)
4. Create implementation contract (Section 6) using the appropriate task type template
5. Define execution strategy (Section 7)

### 5.2 Analysis Workflow

For discovery, requirements gathering, NFR analysis, and feasibility assessment.

**SDLC**: Plan > Research > Analyze > Document > Review

| Phase | What Happens | Agent |
|-------|-------------|-------|
| Plan | Identify analysis type, define scope and objectives | planner |
| Research | Codebase scan + external doc research | code-explorer + research-intelligence |
| Analyze | Conduct analysis per type | planner |
| Document | Produce analysis report | planner |
| Review | Self-review, present to user | planner |

**Analysis types**:
- **Discovery** — scope definition, existing solutions, gaps. Output: discovery report.
- **Requirements** — functional/non-functional extraction, AC definition. Output: requirements document.
- **NFR Analysis** — performance, security, scalability targets. Output: NFR specification.
- **Feasibility** — technical viability, risk assessment, effort estimate. Output: go/no-go recommendation.

**Autonomy**: S/M execute end-to-end. L pauses after Research to confirm scope.

### 5.3 Design Workflow

For high-level design, low-level design, architecture decisions, and pattern selection.

**SDLC**: Plan > Research > Design > Review > Document

| Phase | What Happens | Agent |
|-------|-------------|-------|
| Plan | Identify design scope, classify pattern category | planner |
| Research | Codebase exploration + external doc research | code-explorer + research-intelligence |
| Design | Create HLD/LLD/ADR/pattern recommendation | planner (+ solutions-architect if complex) |
| Review | Architecture validation, trade-off analysis | solutions-architect (if needed) |
| Document | Finalize design document | planner |

**Design types**:
- **HLD** — system architecture, component interactions, data flow
- **LLD** — detailed class/module design, interface contracts, data models
- **Architecture Decision** — specific technical choice with trade-offs (ADR format)
- **Pattern Selection** — which codebase pattern applies, with evidence

**Autonomy**: S/M execute end-to-end. L pauses after Design for architecture review.

### 5.4 Test Workflow

For test strategy, test planning, and test implementation.

**SDLC**: Plan > Implement > Build > Review > Execute > Deploy

| Phase | What Happens | Agent |
|-------|-------------|-------|
| Plan | Define test scope, discover conventions, create test plan | planner |
| Implement | Write test code | test-specialist |
| Build | Compile tests, verify build | test-specialist |
| Review | Review test quality, coverage, completeness | code-reviewer |
| Execute | Run test suite, collect results | test-specialist |
| Deploy | Deploy test infrastructure changes if any | direct execution |

**Test types**:
- **Unit Test Plan** — tests for individual modules, services, handlers
- **Integration Test Plan** — cross-service and API integration tests
- **System Test Plan** — end-to-end validation of deployed features
- **Test Strategy** — overall testing approach for a feature or project
- **Coverage Improvement** — increase coverage for existing code

**Discover conventions from codebase**: test framework, mock library, test location (co-located vs. separate), naming convention, existing test utilities, current coverage baseline.

**Autonomy**: S/M execute end-to-end. L pauses after Plan.

### 5.5 Deploy Workflow

For CI/CD setup, release management, environment configuration, and deployment execution.

**SDLC**: Plan > Build > Execute > Verify > Validate

| Phase | What Happens | Agent |
|-------|-------------|-------|
| Plan | Define deployment scope, create deployment plan | planner |
| Build | Ensure build passes, package artifacts | direct execution |
| Execute | Run deployment commands | direct execution |
| Verify | Check logs, confirm code is active | direct execution |
| Validate | Full validation of deployed environment | direct execution (AEP APIs, curl, logs) |

**Deploy types**:
- **Deployment Execution** — deploy code to an environment
- **CI/CD Setup** — pipeline configuration or updates
- **Release Management** — version, tag, changelog, rollback plan
- **Environment Config** — environment-specific configuration

**Gather context from `<codebase_stack>`**: build command, deploy command, target environments, CI/CD configuration, environment variable references.

**Autonomy**: S/M execute end-to-end. L pauses after Plan.

### 5.6 Maintain Workflow

For code review, documentation, debugging, and knowledge sharing.

Each maintenance type has its own SDLC:

- **Code Review**: Plan > Review > Fix > Build > Deploy > Verify
- **Documentation**: Plan > Draft > Review > Publish
- **Debugging**: Plan > Investigate > Fix > Build > Test > Deploy > Verify
- **Knowledge Sharing**: Plan > Create > Review

**Agent assignment by type**:
- Code Review — code-reviewer (review), schema-processor/python-expert (architectural fixes)
- Documentation — docs-scribe
- Debugging — schema-processor/python-expert (investigate + fix), test-specialist (verify)
- Knowledge Sharing — docs-scribe or direct

**Debug methodology (MANDATORY for debugging tasks)**:
1. Investigate — trace execution, examine state at failure, identify root cause
2. Hypothesize — "Issue occurs because [reason]" with evidence
3. Validate — test hypothesis before fixing
4. Fix — minimal change addressing root cause, not symptoms
5. Verify — run tests, check edge cases

FORBIDDEN: "Let's try X", "This might work", "Add null check" without understanding why.

**Autonomy**: S/M execute end-to-end. L pauses after Plan.

---

## 6. Implementation Contract Templates

These are TEMPLATES — fill them with project-specific values from `<code_standards>` and Input-Derived Patterns.

### Common Header (all task types)

```
**Task Type**: {Frontend/UI | Backend/Service | Integration/API | Configuration/Infrastructure | Mixed}
**Complexity**: {S/M/L} — {1-sentence rationale}

**Extracted Acceptance Criteria** (if story/requirements provided):
- AC1: {testable criterion with pass/fail condition}
- AC2: {testable criterion}

**Hidden/Implicit Requirements Identified**:
- {e.g., WCAG compliance, responsive breakpoints, i18n, error handling}

**Reusability Analysis**:
- Existing code evaluated: {list what was checked}
- Reuse decision: {EXTEND existing / BUILD new / CONFIGURE existing}
- Rationale: {why — feature match %, pattern alignment}
```

### Frontend / UI Contract

```
**View/Component Structure**:
Derive from `<code_standards>` — show the directory layout THIS project uses:
{project-specific directory tree with actual file types used}

**Component/View Contract**:
- Props/inputs: {data shape, types, required vs. optional}
- State management: {local state, store, context — per project pattern}
- Event handling: {user interactions, callbacks, emitted events}
- Rendering: {conditional rendering rules, loading/error/empty states}

**Styling**:
- Approach: {CSS modules, utility classes, preprocessor — from code_standards}
- Responsive: {breakpoints and behavior per breakpoint}
- Accessibility: {ARIA roles, keyboard navigation, screen reader support}

**Architecture Decision (if EXTEND)**:
- Parent/base: {what is being extended and where it lives}
- Inherited features: {what already exists — DO NOT recreate}
- Net-new scope: {ONLY what needs to be added}
```

### Backend / Service Contract

```
**Service Design**:
Interface: {namespace/path}.{ServiceName}
Implementation: {namespace/path}.{ServiceName}Impl (or per project convention)

Key Methods:
- method1(params): return type — description
- method2(params): return type — description

Dependencies:
- {ServiceA} — purpose
- {ServiceB} — purpose

**Configuration** (if configurable):
- property1: type, description, default
- property2: type, description, default

**Implementation Patterns**:
- Interface design: {single responsibility, contract-first}
- Error handling: {log, throw, fallback — per project convention}
- Resource management: {connections, sessions — cleanup strategy}
- Caching: {strategy if applicable}
```

### Integration / API Contract

```
**Integration Architecture**:
External System: {name, API version}
Authentication: {OAuth2 / API Key / mTLS / Basic Auth / Bearer}
Base URL: {URL pattern or config property name}

Key Endpoints:
- GET /endpoint1: description, response model
- POST /endpoint2: description, request/response models

**Implementation Components**:
- Config service: {stores credentials, base URL — NEVER hardcoded}
- Client service: {HTTP client wrapper}
- DTOs: {request/response data classes}
- Error handling: {fallback strategy, retry logic, timeout config}

**Security and Resilience**:
- Credential storage: {environment vars, secret manager — NEVER hardcoded}
- Timeout configuration: {connection, read timeouts}
- Retry strategy: {exponential backoff, max retries}
- Circuit breaker: {if high-volume integration}
```

### Configuration / Infrastructure Contract

```
**Configuration Structure**:
Type: {environment config / CI/CD pipeline / feature flag / infrastructure}
Location: {file path or config management system}

Properties/Rules:
- property1: value, purpose
- property2: value, purpose

**Environment Considerations**:
- Dev/staging/prod differences
- Secret management approach
- Deployment or migration steps required
```

### Common Footer (all task types)

```
**File Impact**:
- CREATE: {exact path} — {purpose}
- MODIFY: {exact path} — {what changes and why}
- REMOVE: {exact path} — {why being removed}

**Public APIs and Contracts**:
- {interfaces, method signatures, DTOs, component props — code snippets for signatures only}

**Acceptance Criteria** (validation points):
- 3-4 high-level validation points (not detailed checklists)

**Dependencies and Risks**:
- External dependencies
- Potential blockers or integration points
- Performance considerations

**Open Questions**:
- {items needing user input before implementation can proceed}
```

---

## 7. Execution Strategy

Every plan MUST include an execution strategy that defines who builds what, in what order, and what context they need.

### Agent Assignment

Decide for each piece of the plan:
- **Main agent directly** — S-complexity single-file changes where subagent overhead is not justified
- **data-analyst** — CSV profiling, quality scoring, ERD generation (Stage 0)
- **schema-processor** — XDM schema design, deployment, validation (Stages 1, 2)
- **dataset-creator** — dataset creation, AEP platform operations (Stage 3)
- **quality-analyzer** — data quality scoring, ERD generation (Stages 4, 5)
- **identity-inspector** — schema identity inspection, present identity options, apply user selections (Stage 4)
- **data-ingestion** — CSV-to-XDM transformation, batch upload, monitoring (Stage 7)
- **data-validator** — post-ingestion validation, AEP data querying, record comparison (Stage 8)

### Execution Mode

- **Parallel** (preferred when possible) — agents work on independent pipeline stages simultaneously. All agents receive the full interface contract upfront.
- **Sequential** (when one depends on the other) — e.g., schema must be deployed before dataset creation.
- **Mixed** (common for M/L tasks) — some parts parallel, some sequential.

### Context Payload Per Agent

For each assigned agent, specify exactly what they need to work independently:
- **File paths** they will create/modify
- **Interface contracts** (method signatures, return types, props) they must implement or consume
- **Input-Derived Patterns** (from user input — structure, naming, conventions, constraints)
- **Project patterns** from `<code_standards>` (file structure, naming, conventions)
- **Configuration requirements** (config keys, properties, environment vars)
- **Dependencies** on other agents' outputs (what they must wait for)

### SDLC Flow

The plan must define the full lifecycle using build/deploy commands from `<codebase_stack>`:
1. **Implement** — agent assignment and execution mode as defined above
2. **Build** — project build command immediately after code is written
3. **Review** — invoke code-reviewer on all changed files together
4. **Test** — invoke test-specialist for the project's test framework
5. **Deploy** — project deploy command to target environment
6. **Validate** — invoke validation method appropriate to the task type

Phase transition rules:
- Build FAILS — debug, fix, rebuild. PASSES — proceed to Review.
- Review finds issues — main agent applies fixes, rebuilds. Architectural issues — back to dev agent.
- Test FAILS — fix, rebuild, re-run. PASSES — proceed to Deploy.
- Deploy — verify logs, confirm code active. Environment not running — notify user and stop.
- Validate FAILS — hand back to dev agent with failure details. PASSES — complete.

### Execution Strategy Template

```
## Execution Strategy

**Complexity**: {S/M/L}
**Autonomy**: {auto end-to-end / ask before deploy}

**Agent Assignment**:
| Agent | Scope | Mode | Depends On |
|-------|-------|------|------------|
| {agent} | {what they build} | {parallel/sequential} | {nothing / other agent output} |

**Context for each agent**:
- {agent}: {interface contract, file paths, Input-Derived Patterns, config requirements}

**SDLC Flow**:
Implement > Build > Review > Test > Deploy > Validate
{any phase-specific notes}
```

---

## 8. Code Generation Principles

Include in every handoff to dev agents:

- **Read-Understand-Implement** — read existing code patterns BEFORE writing any code
- **Codebase is source of truth for reuse** — search before building, extend what exists, never duplicate. User-provided input takes priority for conventions.
- **YAGNI** — build only what is explicitly required, nothing speculative
- **Keep it simple** — simplest correct solution wins
- **DRY** — single authoritative representation for every piece of logic
- **Least astonishment** — code behaves exactly as its name suggests, no surprising side effects

---

## 9. Planning Checklist

Before presenting any plan, verify ALL of these:

1. Did I analyze user input and extract Input-Derived Patterns (names, structure, interfaces, constraints)?
2. Did I read `<code_standards>` and `<codebase_stack>` from CLAUDE.md?
3. Did I load planning-standards and apply the relevant sections?
4. Did I invoke code-explorer (for reuse) AND research-intelligence in parallel?
5. Did I run the reusability scan and get user confirmation via AskUserQuestion?
6. Did I classify the task type and assess complexity?
7. For M/L complexity, did I invoke solutions-architect for architectural review?
8. Does my plan use the correct contract template for this task type?
9. Does my plan include Input-Derived Patterns so dev agents know the conventions?
10. Does my plan include an Execution Strategy with agent assignment, execution mode, dependency order, context payloads, and SDLC flow?
11. Does my plan include file structure derived from `<code_standards>` (not from generic defaults)?
12. Am I planning for OTHERS to execute, not myself?
13. Does File Impact list exact paths with explicit CREATE/MODIFY/REMOVE actions?
14. Are SDLC tasks actionable and phase-owned (not generic milestones)?
15. Did I include Open Questions for unclear items?
16. Did I use AskUserQuestion (not plain text) for reusability confirmation, open questions, and plan approval?
17. After approval, did I use TaskCreate to create one task per SDLC phase with dependencies?

---

## 10. Plan Output Template

The plan is a technical contract that dev agents execute from. NOT a summary. Use this template as the output format.

````markdown
# Plan: {Feature/Task Name}

## Summary
{20-100 word TL;DR}

**Task Type**: {Frontend/UI | Backend/Service | Integration/API | Config/Infrastructure | Mixed}
**Complexity**: {S/M/L} — {1-sentence rationale}
**SDLC Category**: {Build | Analysis | Design | Test | Deploy | Maintain}

## Requirements and Success Criteria
- {Outcome 1 — testable pass/fail condition}
- {Outcome 2 — testable pass/fail condition}
- {Hidden/implicit requirements discovered}

## Input-Derived Patterns
{Names, interfaces, data shapes, conventions extracted from user input.}
{If none: "No direct reference input — following code_standards."}

## Reusability Analysis
- **Searched**: {what was checked, with paths}
- **Coverage**: {X%} — covers {what}, missing {what}
- **Decision**: {EXTEND existing | BUILD new | CONFIGURE existing}
- **Rationale**: {why}

## Technical Contract
{Use the task-type-specific template from Section 6.}
{This section IS the plan — not a summary of it.}

## File Impact

| Action | File Path | Purpose |
|--------|-----------|---------|
| CREATE | {exact/path/to/file} | {what and why} |
| MODIFY | {exact/path/to/file} | {what changes and why} |
| REMOVE | {exact/path/to/file} | {why being removed} |

## Dependency Graph

Include a visual diagram for M/L complexity or multi-agent tasks:

```
  Implement Backend ──┐
                      ├──> Build ──> Review ──> Test ──> Deploy ──> Validate
  Implement Frontend ─┘
```

For L complexity with parallel workstreams, show the dependency flow so agents and reviewers can see what runs in parallel vs. sequential at a glance. Prefer ASCII diagrams — they render everywhere and need no tooling. Use mermaid only if the user explicitly requests it, and always inline in the plan (never in a separate file).

## Execution Strategy

**Autonomy**: {auto end-to-end | ask before deploy}

| Agent | Scope | Mode | Depends On |
|-------|-------|------|------------|
| {agent} | {what they build} | {parallel/sequential} | {nothing / other agent output} |

**SDLC Flow**: Implement > Build > Review > Test > Deploy > Validate

### Agent Context Briefs

Each agent receives a self-contained brief so they can execute without reading the full plan:

**{agent-name}**:
- Files: {exact paths to create/modify}
- Contract: {interface signatures, props, method signatures they implement or consume}
- Patterns: {Input-Derived Patterns and code_standards conventions relevant to their scope}
- Config: {configuration keys, environment vars, dependencies}
- Blocked by: {nothing | other agent's output — what specifically}

## Risks and Mitigations

| Severity | Risk | Mitigation |
|----------|------|------------|
| HIGH | {description} | {how to address} |
| MEDIUM | {description} | {how to address} |
| LOW | {description} | {how to address} |

## Open Questions
- {Items needing user input before implementation can proceed}
````

### Plan Output Rules

- Technical contract sections ARE the plan — do NOT replace them with vague steps
- File structure MUST come from `<code_standards>` — not from generic defaults
- Include code snippets for API signatures and interface contracts ONLY
- NO preamble or postamble
- NO approval ceremony (APPROVE/REVISE/ABORT) — user provides feedback naturally
- For UI tasks: include view structure, interaction contract, state/data flow, and target files
- For backend tasks: include interfaces, schemas, runtime dependencies, and target files
- Include phase-owned tasks across SDLC with dependencies — avoid collapsing into broad milestones

### Plan Persistence (MANDATORY — after user approval)

#### Canonical Format — the HERO format (non-negotiable)

Every Detail Project Plan, for every project and every use case, MUST be produced in the **Hero format**. The single source of truth is:

- **`.claude/references/DetailProjectPlan_Hero_reference.html`** — READ this file and replicate its EXACT CSS (verbatim), colour palette, components, and Adobe + Deloitte branding. Only the content changes.
- Worked example: **`output/FXSource/UC2_DetailProjectPlan.html`**.

Never invent a new look, never match any other reference file (e.g. an older `*_DetailProjectPlan.html`), and never downgrade to markdown. "Always Hero format."

#### File Naming Convention (rule of thumb — non-negotiable)

The plan HTML file name is always: **`{ProjectName}_DetailProjectPlan.html`**

| Project | Correct filename |
|---------|------------------|
| Titan   | `Titan_DetailProjectPlan.html` |
| ClientXYZ | `ClientXYZ_DetailProjectPlan.html` |
| RetailCo | `RetailCo_DetailProjectPlan.html` |

- Project name comes from `project_config.json` → `project_name` field
- NEVER use `customer360_plan.html`, `plan.html`, kebab-case, or any other pattern
- The underscore + `DetailProjectPlan` suffix is fixed — do not vary it

#### Timing Rule (MANDATORY — generate BEFORE Stage 0)

- The `{ProjectName}_DetailProjectPlan.html` MUST be generated **before Stage 0 (data-analyst) executes**
- It is the reviewer approval artefact — no pipeline stage may run without it
- Stage 0 is blocked until this file exists at `{output_dir}/{ProjectName}_DetailProjectPlan.html`
- If this file does not exist when a pipeline stage is invoked, the first execution agent must generate it from the planner-approved handoff first, then proceed

After the user approves the plan, ALWAYS prepare it for persistence and hand off file creation to the first execution agent:

1. Read `project_config.json` at project root when it exists — extract `output_dir` (e.g., `Output/Titan/`) and `project_name`; otherwise use PROJECT_NAME and OUTPUT_DIR recorded during the Project Init Gate
2. Resolve the output path: `{output_dir}/{project_name}_DetailProjectPlan.html`
3. Record the approved plan as **rich, fully self-contained HTML** in the execution handoff payload — ALL CSS and JS inline, NO external CDN of any kind (no Mermaid, no fonts, no scripts). Published artifacts run under a CSP that blocks every external host, so a plan referencing a CDN silently breaks.
4. Instruct the first execution agent to create the HTML file at the resolved output path before Stage 0 starts — by replicating `.claude/references/DetailProjectPlan_Hero_reference.html`

#### Required HTML Structure (non-negotiable — the Hero format)

The plan HTML must replicate `.claude/references/DetailProjectPlan_Hero_reference.html`. Every section below is mandatory (order preserved; Segments/Journey/Risks are included when the use case calls for them):

| Section | Requirement |
|---------|-------------|
| **Top navigation bar** | Dark sticky bar: Adobe SVG logo (red triangles) + "Deloitte" wordmark with green dot + breadcrumb (`Adobe Experience Platform · {Project}`) + right-aligned `.tab-links` (one per section) + pulsing `.status-pill` ("Awaiting Approval"). Top tab nav — NOT a sidebar. |
| **Meta bar** | Date · centred plan title · sandbox |
| **Hero header** | Blue gradient `linear-gradient(135deg,#1473e6,#0a3d8f)` WITH a real one/two-sentence subtitle describing the work, plus a 6-item `.hero-meta` grid (project, generated, edition, sandbox, complexity, key metric) |
| **Approval banner** | `.warn.crit` stating the exact governance/approval gate |
| **Executive Summary** | Prose + `.kd-grid` approved-decisions grid + 5-card `.stats` grid |
| **Data / Use Case & Requirements** | Table(s): entity inventory per source, or user stories + general requirements |
| **Identity & Stitching Design** | Identity/namespace table + `.vflow` data flow (File → API → Lake → ID Graph → Profile → Segment) |
| **XDM Schema Field Mappings** | Per-schema `.tbl` tables, OOTB vs CUSTOM `.badge` on every field |
| **ERD** | HAND-BUILT coloured `.erd-box` entity boxes (`.profile` blue / `.event` orange / `.account` purple / `.lookup` grey), pk/fk rows, legend. NEVER Mermaid. |
| **Segment Design** (when applicable) | `.seg-grid` of `.seg-card` with `.codeblock` PQL + AEP UI steps |
| **AJO Journey Design** (conditional) | Include whenever the use case has a customer journey; populate from `journey-flow-designer`. Render as an **AJO-style branching canvas** (`.jcanvas-wrap` + hand-authored self-contained SVG) that mirrors the real Adobe Journey Optimizer canvas: entry source, condition/experiment nodes, channel-action tiles, wait timers, and connectors with Yes/No labels where paths split into lanes and reconverge. Node types colour-coded (entry blue / consent-gate red / experiment orange / condition purple / email dark-blue / web+converged green / custom-action(TLS) coral / exit grey-dashed). NEVER a plain vertical list. See the reference file's section 7 and `output/FXSource/UC2_DetailProjectPlan.html` for the worked example. |
| **Pipeline Strategy** | Horizontal `.pipe` stage flow bar (`.done`/`.gate`/`.stage`) + detailed table with `.gate`/`.crit` rows highlighted |
| **Open Questions** | `.qlist` of `.q.blocker`/`.medium`/`.low` cards (numbered circle + question + impact, or `.default` green pill when resolved-with-default) |
| **Risks & Mitigations** (when applicable) | `.tbl` with severity badges; `.crit` row for Critical |
| **Sign-off Table** | Reviewer / Role / Decision / Date / Notes columns — blank, ready to fill |
| **Reviewer Comment Section** | Interactive form + comment cards + Export to CSV button (see below) |

#### Reviewer Comment Section (MANDATORY)

The comment section must be fully interactive, built with inline JavaScript only (no external libraries at all — the entire plan is self-contained):

- **Form fields**: Reviewer Name (required), Role/Team, Comment Type (dropdown: Approved / Request Change / Question / General Note), Related Section (dropdown of all plan sections), Comment text (required)
- **On submit**: renders a colour-coded comment card (green=Approved, red=Request Change, orange=Question, blue=General) with reviewer initials avatar, timestamp, section tag, and a Delete button
- **Export to CSV button**: appears automatically once the first comment is added
  - Downloads `{ProjectName}_ReviewComments_{YYYY-MM-DD}.csv` with columns: #, Reviewer Name, Role, Comment Type, Section, Comment, Timestamp
  - UTF-8 BOM prefix so Excel opens it correctly without encoding issues
  - Implemented entirely with inline `<script>` — no fetch, no CDN, no external libraries
- **Empty state**: friendly placeholder text when no comments exist

- Confirm the target saved path to the user
- NEVER save as markdown, plain text, or any other format — HTML only, always under `Output/`

This rule applies to every plan, every project, without exception.

### Visual Diagram Guidance

Include ASCII diagrams when they add clarity. Prefer ASCII — it renders everywhere, needs no tooling, and is immediately scannable. Common uses:

- **Dependency graph** — show parallel vs. sequential execution, agent dependencies
- **SDLC flow** — show phase transitions with decision points (build fails > fix > rebuild)
- **Data flow** — show how data moves between services, APIs, or components
- **Architecture overview** — show system boundaries, integration points, component relationships

```
  Example: Data flow

  Client ──> API Gateway ──> Auth Service ──> User DB
                  │
                  └──> Cache Layer ──> Response
```

Use diagrams when the plan involves multiple agents, parallel workstreams, or complex dependency chains. Skip for S-complexity single-agent tasks where the flow is obvious. Use ASCII for the in-conversation plan contract. The persisted Detail Project Plan HTML is fully self-contained and uses HAND-BUILT components (coloured `.erd-box` ERD, `.pipe` flow bar, `.vflow` data/journey flow) — NEVER Mermaid or any external CDN.

### L-Complexity Phasing

For L-complexity tasks, break into independently deliverable phases:

- **Phase 1**: Minimum viable — smallest slice that provides value
- **Phase 2**: Core experience — complete happy path
- **Phase 3**: Edge cases — error handling, validation, polish
- **Phase 4**: Optimization — performance, monitoring, observability

Each phase should be independently buildable, testable, and deployable. Avoid plans that require all phases to complete before anything works.
