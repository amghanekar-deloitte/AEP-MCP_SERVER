# Project Guidance Prompt

Use this file as a structured project reference when running `/initialize-setup`.

Purpose:
- give the framework accurate project context
- define architecture, boundaries, and constraints
- describe repository conventions in a way agents can follow directly
- reduce guesswork during planning, implementation, review, testing, and deployment

This is a **prompt artifact**, not a questionnaire.
Write concise, direct guidance using real project facts.
Remove any placeholder text before using it.

---

## How To Use

1. Replace placeholders with real project guidance.
2. Keep the structure, but remove sections that are genuinely not applicable.
3. Prefer short, factual statements over prose.
4. If the repository already shows a pattern, document that pattern instead of prescribing a new one.
5. After updating this file, run:

```text
/initialize-setup /path/to/this-file.md
```

---

## 1. Project Intent

Provide the minimum context needed for agents to understand what they are working on.

```text
Project:
- <project name>

Organization:
- <team or org name>

Purpose:
- <what this system does>
- <who it serves>

Primary outcomes:
- <key business or technical outcomes>

Non-goals:
- <what this system is not responsible for>
```

---

## 2. Architecture And Boundaries

Describe the real architecture and the boundaries agents must respect.

```text
Architecture:
- <monolith / modular monolith / microservices / API platform / SPA / hybrid / event-driven / data platform / internal tooling / other>

System shape:
- <high-level structure in 2-5 lines>

Boundaries:
- <what belongs in backend/runtime>
- <what belongs in frontend/interface>
- <what belongs in infrastructure/platform>
- <what belongs in data/storage/integration layers>

Critical architecture rules:
- <rule 1>
- <rule 2>
- <rule 3>

Extension strategy:
- <prefer extend existing / build new only when needed / wrap third-party / etc.>
```

Use this section to define ownership boundaries clearly enough that agents can avoid scope drift.

---

## 3. Technology Context

Describe the actual stack and toolchain, not aspirational choices.

```text
Runtimes and languages:
- <language/runtime + version>
- <language/runtime + version>

Frameworks and platforms:
- <framework/platform + version>
- <framework/platform + version>

Build and package tools:
- <tooling in use>

Testing tools:
- <unit/integration/e2e/type/lint tools>

Infrastructure:
- <cloud / hosting / orchestration / CI/CD>

Operational surfaces:
- <API / UI / jobs / workers / CLI / data pipelines / admin tooling / none>
```

If something is intentionally absent, say so explicitly.

---

## 4. Commands The Project Actually Uses

Agents should not guess commands.
List the commands that are real for this repository.

```text
Build command:
- <exact command>

Test command:
- <exact command>

Deploy command:
- <exact command>

Type-check command:
- <exact command or "none">

Lint command:
- <exact command or "none">

Local run / preview command:
- <exact command or "none">
```

If commands vary by module, document the split:

```text
Module-specific commands:
- <module/path>: <build/test/deploy commands>
```

---

## 5. Repository Shape

Describe how this repository is organized so agents know where to look first.

```text
Primary source roots:
- <path>: <what lives here>
- <path>: <what lives here>

Test roots:
- <path>: <what tests live here>

Config roots:
- <path>: <what config lives here>

Infrastructure roots:
- <path>: <what infra/deploy code lives here>

Docs roots:
- <path>: <what docs live here>
```

Also document any important multi-package or multi-service boundaries:

```text
Module boundaries:
- <module/package/service>: <responsibility>
- <module/package/service>: <responsibility>
```

---

## 6. Implementation Conventions

This section should tell agents how the project actually builds things.

```text
Naming conventions:
- <types/classes>
- <functions/methods>
- <files/directories>
- <routes/endpoints/jobs/events>
- <UI selectors/classes if relevant>

File structure conventions:
- <how a typical feature/module/service is laid out>
- <what files are expected together>

Code patterns:
- <dependency injection style>
- <error handling style>
- <state management style>
- <configuration pattern>
- <logging/observability style>
- <data-access pattern>
- <integration/client pattern>

Reuse rules:
- <when to extend existing code>
- <when to create new modules>
- <what must not be duplicated>
```

Prefer rules grounded in actual repository usage.

---

## 7. Interface Or Contract Conventions

Use this section only for surfaces the project actually has.

```text
If the project has a UI:
- <rendering conventions>
- <interaction/state conventions>
- <accessibility expectations>
- <performance expectations>

If the project exposes APIs:
- <response conventions>
- <request validation conventions>
- <versioning / backward compatibility expectations>

If the project uses events, jobs, or workflows:
- <message/job/workflow conventions>
- <retry/idempotency expectations>

If the project uses admin/config surfaces:
- <how configuration is defined, validated, and promoted>
```

Skip irrelevant subsections instead of forcing UI/API assumptions onto every project.

---

## 8. Testing And Verification Expectations

Tell agents what “done” means in this project.

```text
Testing expectations:
- <what kinds of tests are required>
- <coverage threshold if any>
- <what must always be tested>
- <what can be validated manually>

Test conventions:
- <test file naming>
- <test file location>
- <mocking/fake strategy>
- <isolation requirements>

Verification expectations:
- <build must pass>
- <type/lint checks if applicable>
- <runtime validation expectations>
- <release readiness expectations>
```

If the project has no formal test culture yet, say that explicitly instead of inventing one.

---

## 9. Security, Reliability, And Compliance Constraints

Document only the constraints that materially affect implementation decisions.

```text
Security requirements:
- <secret handling>
- <input validation>
- <auth/authz expectations>
- <data handling expectations>

Reliability requirements:
- <timeouts / retries / idempotency / rollback expectations>

Compliance or policy constraints:
- <audit / privacy / regulatory / legal / internal controls>
```

If a requirement is optional or context-specific, say so.

---

## 10. Delivery And Runtime Notes

Give agents the context they need to plan deployment-safe work.

```text
Environments:
- <local>
- <dev>
- <stage>
- <prod>

Runtime URLs or endpoints:
- <if relevant>

Release model:
- <manual / CI-driven / staged rollout / blue-green / canary / scheduled / other>

Operational cautions:
- <production-sensitive areas>
- <rollback expectations>
- <health-check expectations>
```

---

## 11. Project Anti-Patterns

Call out the mistakes agents must avoid.

```text
Do not:
- <anti-pattern 1>
- <anti-pattern 2>
- <anti-pattern 3>
```

This section is high-value. Keep it short and specific.

---

## 12. Optional Examples

If helpful, include one or two short examples from the real codebase.

Good examples:
- representative module layout
- representative API contract
- representative test pattern
- representative config pattern

Keep examples short and factual.
Do not dump large code blocks unless they are genuinely the clearest way to express the convention.

---

## Authoring Notes

Before using this file:
- remove placeholders
- remove irrelevant sections
- keep only real, durable guidance
- prefer accuracy over completeness

The framework should be able to read this file and answer:
- what this system is
- how it is structured
- how work should be implemented
- how quality is verified
- what must never be violated
