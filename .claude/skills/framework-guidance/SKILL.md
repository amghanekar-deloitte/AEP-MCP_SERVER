---
name: framework-guidance
description: Universal framework guidance for designing, maintaining, and evolving agentic coding systems across Claude Code, Cursor, VS Code, and GitHub Copilot. Use when creating, updating, or maintaining agents, commands, skills, rules, or hooks. Also use when resolving cross-surface conflicts, validating framework changes, deciding where new guidance belongs, or adapting the framework for a new platform.
---

# Framework Guidance

Use this skill when working on framework-level concerns such as:
- agent and subagent design
- skills, prompts, commands, and rules
- hook architecture and guardrails
- cross-platform framework structure
- framework maintenance and validation

This skill is the generic maintenance guide for the framework itself.
It is not project-domain guidance.

---

## Platform Documentation

Use official platform docs when the decision depends on platform behavior rather than internal framework conventions.

### Claude Code
- [Overview](https://code.claude.com/docs/en/overview)
- [Memory and project instructions](https://code.claude.com/docs/en/memory)
- [Skills](https://code.claude.com/docs/en/skills)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [MCP](https://code.claude.com/docs/en/mcp)
- [Interactive mode and slash commands](https://code.claude.com/docs/en/interactive-mode)
- [Settings](https://code.claude.com/docs/en/settings)

### Cursor
- [Docs home](https://docs.cursor.com/)
- [Rules](https://docs.cursor.com/en/context)
- [CLI usage](https://docs.cursor.com/en/cli/using)
- [Agent tools](https://docs.cursor.com/agent/tools)
- [MCP for CLI](https://docs.cursor.com/cli/mcp)
- [MCP in Cursor](https://docs.cursor.com/en/context/mcp)
- [Background agents](https://docs.cursor.com/en/background-agents)

### VS Code
- [Customize chat to your workflow](https://code.visualstudio.com/docs/copilot/copilot-customization)
- [Custom instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
- [Custom agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [Hooks](https://code.visualstudio.com/docs/copilot/customization/hooks)
- [MCP servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- [Agent plugins](https://code.visualstudio.com/docs/copilot/customization/agent-plugins)

### GitHub Copilot
- [Customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet)
- [Repository custom instructions](https://docs.github.com/en/copilot/how-tos/custom-instructions/adding-repository-custom-instructions-for-github-copilot)
- [Custom agents](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents)
- [Custom agent configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [Agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [Create skills](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-skills)
- [Hooks](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-hooks)
- [Use hooks](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/use-hooks)
- [MCP for coding agent](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/extend-coding-agent-with-mcp)

---

## Core Principles

### 1. Separation Of Concerns

Each framework surface should own one kind of responsibility:

- **Root instructions** own always-on standards, defaults, and project context
- **Agents** own role behavior, workflow, stop rules, and handoffs
- **Skills** own deep, conditional knowledge
- **Commands** own invocation shape and light user-facing framing
- **Hooks** own deterministic or lifecycle-bound enforcement
- **Prompt/reference assets** own reusable framing or support material

If two surfaces say the same thing, decide which one is authoritative and remove duplication elsewhere.

### 2. Thin Invokers, Rich Knowledge Containers

- Commands should stay thin
- Agents should coordinate work, not become encyclopedias
- Skills should hold deep knowledge and examples
- Hooks should enforce or automate, not replace good prompt design

### 3. Progressive Disclosure

Load context in layers:

1. Always-on instructions
2. Relevant skill or agent
3. Deeper references only when needed

Do not force every task to load every reference.

### 4. Decision Hierarchy

When guidance conflicts, use this order:

1. user intent and explicit task constraints
2. project conventions and repository patterns
3. framework guidance
4. platform defaults and official vendor docs

### 5. Codebase-First Adaptation

Universal frameworks should adapt to the codebase they serve:

- follow existing naming and structure unless the task is explicitly to change them
- prefer extending proven patterns over inventing new ones
- avoid prescribing one stack’s habits to every project

### 6. Boundaries Before Expansion

Do not add new agents, commands, skills, hooks, or prompts unless the need is explicit and durable.

Framework sprawl usually comes from solving local discomfort with global abstractions.

### 7. Self-Review Before Handoff

Every framework surface should verify its own output before passing work onward.

- agents should check whether they completed the assignment, not merely responded
- hooks should validate the stage they guard and return actionable failure reasons
- documentation and prompt assets should be checked for broken references, stale names, and duplicated rules

Self-review reduces avoidable loops between planning, implementation, review, and documentation.

### 8. Interoperability Over Lock-In

Framework guidance should survive across Claude Code, Cursor, VS Code, and GitHub Copilot.

- prefer generic concepts such as root instructions, agents, skills, hooks, commands, prompts, and MCP servers
- document platform differences where they matter, but keep the conceptual model stable
- use portable metadata and folder conventions where practical

### 9. Read, Understand, Then Change

Framework work should respect the current system before modifying it.

1. Read the existing framework components completely.
2. Understand what is authoritative versus derived.
3. Change the smallest surface that correctly fixes the problem.
4. Validate downstream references before considering the change complete.

---

## What Belongs Where

### Put it in root instructions when:
- it is always-on
- it applies across most or all tasks
- it defines non-optional framework or project rules

### Put it in an agent when:
- it defines a named role
- it changes execution behavior, handoffs, or stop conditions
- it is role-specific rather than globally true

### Put it in a skill when:
- it is deep, conditional knowledge
- it includes examples, references, or scripts
- it is not needed for every task

### Put it in a command when:
- it is a user-facing entry point
- it packages a common workflow shape
- it adds only light context and invocation framing

### Put it in a hook when:
- it must run at a lifecycle boundary
- it is deterministic or can be mechanically validated
- it should not depend on the model remembering to do it

### Put it in a prompt/reference asset when:
- it is reusable support material
- it helps structure work without requiring a full agent identity
- it should be cited or loaded by multiple surfaces

---

## Recommended Framework Shape

Use this as a generic anatomy, not as a claim that every framework must have identical files.

```text
project-root/
├── CLAUDE.md or AGENTS.md
├── .claude/
│   ├── agents/
│   ├── skills/
│   ├── commands/
│   ├── hooks/
│   └── prompt-library.md
├── .cursor/
│   ├── rules/
│   └── mcp.json
├── .vscode/
│   ├── settings.json
│   └── mcp.json
└── .github/
    ├── agents/
    ├── hooks/
    ├── skills/
    └── prompts/
```

Not every framework needs every directory. The point is to separate portable framework assets from platform-specific integration files.

### Core Building Blocks

- **Rules/instructions**: always-on standards, defaults, and project context
- **Agents**: named role behaviors with workflow, boundaries, and handoffs
- **Subagents**: narrow helpers for exploration, research, or bounded execution
- **Skills**: deep conditional knowledge, examples, scripts, or references
- **Commands**: user-facing entry points for stable workflow shapes
- **Prompts**: reusable task framing when a full agent identity is unnecessary
- **Hooks**: lifecycle-bound deterministic or judgment-based enforcement
- **MCP config**: explicit external tool and data-source connections

### Example Role Topology

One useful generic topology:

1. Planner interprets the task and chooses the route
2. Explorer or research helper gathers missing context
3. Implementation agent performs the change
4. Reviewer validates quality or returns findings
5. Documentation or handoff agent captures durable outcomes if needed

This is an archetype, not a mandatory SDLC.

### Skill Shape

Minimal skill:

```text
skill-name/
└── SKILL.md
```

Expanded skill:

```text
skill-name/
├── SKILL.md
├── references/
│   └── topic.md
└── scripts/
    └── helper.sh
```

For generic frameworks, prefer the minimal shape unless deeper material is truly needed.

---

## Common Anti-Patterns

### Agent Anti-Patterns

- embedding too much domain knowledge in agents
- repeating root-level rules inside every agent
- handoff prompts that re-teach the next agent’s entire job
- blurred ownership between planner, implementer, reviewer, and docs roles

### Command Anti-Patterns

- commands duplicating agent prompts
- near-duplicate commands for the same user intent
- commands hiding durable framework logic that should live elsewhere

### Skill Anti-Patterns

- too many tiny reference files
- references that are mostly links without guidance
- mandatory skills applied to unrelated work

### Hook Anti-Patterns

- using hooks for advisory guidance that belongs in prompts
- too many global hooks
- opaque hook behavior users cannot predict or inspect

### Structure Anti-Patterns

- contradictory guidance across files
- stale references after renames
- local inventories presented as universal truth

### Maintenance Anti-Patterns

- fixing symptoms in multiple places instead of the owning layer
- shipping framework edits without syntax/reference/consistency validation

---

## Hook Guidance

Hooks are for enforcement and automation at lifecycle boundaries.

Use hooks to:
- inject or refresh context
- block unsafe actions
- run lightweight post-edit or post-tool checks
- provide failure-specific recovery guidance
- verify completion before stopping

Prefer **deterministic hooks** first.
Use **prompt-based hooks** only when judgment is required.

Keep hooks:
- explicit
- narrow
- documented
- easy to disable when debugging

Do not use hooks as hidden workflow engines.

### Hook Families

#### Deterministic hooks

Use deterministic hooks when the desired behavior can be expressed as code and should run the same way every time.

- inspect files or environment state
- block unsafe actions
- run formatters, validators, or tests
- log lifecycle events
- return machine-readable outcomes

#### Judgment-based prompt hooks

Use prompt hooks when judgment is required:

- whether an agent actually completed its role
- whether a response followed required structure
- whether a handoff is missing critical context
- whether an output violates framework policy in a way simple scripts cannot detect

If a hook can be deterministic, prefer deterministic enforcement first.

### Global vs Scoped Hooks

#### Global hooks

Good uses:
- session context injection
- global security checks
- audit logging
- recovery hints after tool failures
- repo-wide pre-edit or post-edit enforcement

Avoid using global hooks for logic that only one agent or one workflow needs.

#### Scoped hooks

Good uses:
- completion checks for a reviewer
- post-edit formatting for a code-writing agent
- stricter approval rules for deployment workflows
- context loading for a research-only surface

### Common Lifecycle Points

- session start
- pre-tool / pre-action
- post-tool / post-action
- failure hooks
- compaction / context refresh
- stop / completion

### Hook Design Questions

Before adding or changing a hook, ask:
- is this deterministic or judgment-based?
- should this apply globally or only to one role/workflow?
- would this be clearer as an instruction, skill, command, or agent rule instead?
- what lifecycle event should own it?
- what will the user or agent see when the hook blocks or fails?

---

## Framework Modification Workflow

Use this workflow when changing any framework surface.

1. **Discover**
   Identify the files and framework surfaces involved.

2. **Read**
   Read the authoritative files completely before proposing a change.

3. **Analyze**
   Compare current behavior with desired behavior and identify the owning layer.

4. **Propose**
   Describe the behavioral change and why it belongs in that surface.

5. **Modify**
   Change only the approved scope. Avoid opportunistic cleanup unless it is required for consistency.

6. **Validate**
   Run syntax, reference, and consistency checks.

7. **Report**
   Summarize what changed, where it changed, and what framework behavior is now different.

When a concept appears in multiple places:
- identify the authoritative source first
- update that source first
- align dependent surfaces second

### Choosing The Right Surface

Before editing, decide where the fix belongs:

- **Root instructions**: always-on standards, defaults, and constraints
- **Agent prompt**: role definition, workflow, handoffs, stop rules
- **Skill**: deep task knowledge, examples, scripts, or references
- **Command**: user-facing invocation and light workflow framing
- **Hook**: deterministic lifecycle enforcement
- **Prompt asset**: reusable task framing without a full agent identity

If a change feels needed in multiple places, first identify which place should become authoritative.

### Common Modification Patterns

#### Update a role or behavior

- update the role definition when ownership is unclear
- update stopping rules when the role must refuse or stop under certain conditions
- update workflow when steps are skipped or occur in the wrong order
- update completion logic when the role finishes too early

#### Update handoffs

- keep target identifiers aligned with real agent names
- make handoffs explain state, not re-teach methodology
- ensure the receiving role has enough context to continue

#### Update a skill

- keep `SKILL.md` focused on when to use the skill and how to navigate it
- keep examples reusable and clearly labeled if platform-specific
- remove stale references, orphaned scripts, or link-only sections that no longer add value

#### Update a command

- preserve it as a thin entry point where possible
- keep durable logic in agents, prompts, skills, or hooks
- make arguments and scope clear to the user

#### Update hook behavior

- identify the lifecycle event and intended scope first
- confirm the logic belongs in a hook rather than in instructions or prompts
- document what the hook blocks, transforms, or validates
- keep failure messages actionable

#### Batch consistency update

Use this when one concept appears in many framework surfaces:

1. discover every affected file
2. name the authoritative source
3. update that source first
4. align dependent surfaces
5. run a global validation sweep

### Safety Rules

- never change framework behavior without understanding which layer owns it
- never silently change a component's fundamental role
- never leave syntax, links, or references half-updated after a rename
- never add a new framework primitive just to avoid improving an existing one
- never present a local repo convention as universal guidance unless labeled as an example

---

## Validation Checklist

After every framework modification, verify:

### Syntax And Structure
- frontmatter is valid
- structured prompt tags are balanced
- field names match the framework/platform convention

### References
- internal links point to real files
- referenced agents, skills, commands, hooks, and prompts exist
- stale names and old paths are gone after renames

### Consistency
- the change was applied at the authoritative layer
- agents, skills, commands, hooks, and instructions do not contradict each other
- commands remain thin where appropriate
- hook behavior is documented and scoped correctly

### Generic Quality
- content is generic unless platform-specific behavior is intentionally being described
- platform-specific examples are clearly marked as examples
- local implementation details are not presented as universal rules
- stack-specific wording is removed unless intentionally illustrative

### Reporting
- file paths are listed
- behavioral impact is described
- validation steps are listed
- assumptions or intentionally preserved platform-specific differences are called out

### Common Sweep Checks

Use targeted search to catch leftover generalization problems:

- product- or stack-specific names that should have been removed
- old agent or skill names after a rename
- deprecated paths or configuration keys
- historical implementation details presented as current truth

### Error Handling During Framework Changes

If a target file is missing:
- report the missing path
- list what exists instead
- update references only after confirming the intended target

If the request conflicts with framework ownership:
- explain the conflict in terms of role/layer ownership
- recommend the correct framework surface

If a behavior change is breaking:
- warn explicitly
- describe downstream impact
- confirm whether the change is intended before applying it

If syntax becomes invalid:
- fix syntax first
- then re-run validation before reporting success

---

## YAML And Structured Prompt Standards

### Agent frontmatter should stay simple

Typical fields:
- `name`
- `description`
- `argument-hint`
- `handoffs`

Example:

```yaml
---
name: agent-name
description: Clear description of what the agent does and what constraints matter.
argument-hint: "What the user should provide when invoking this agent."
handoffs:
  - label: Send to Reviewer
    agent: reviewer-agent
    prompt: "Summarize what changed, what remains risky, and what to review."
  - label: Return to Planner
    agent: planner-agent
    prompt: "Return with findings that require replanning."
    send: false
---
```

Rules:
- `description` should describe the role precisely
- `argument-hint` should be written for humans
- `handoffs` should reference real target identifiers
- `send: false` should be used only when the platform supports return-style navigation and that behavior is intentional
- do not invent unsupported metadata

### Skill frontmatter should stay simple

Typical fields:
- `name`
- `description`

Example:

```yaml
---
name: skill-name
description: When to use this skill, what it covers, and the trigger conditions.
---
```

Rules:
- `description` should make invocation conditions easy to infer
- `SKILL.md` should act as the entry and navigation guide

### Structured prompt tags

Recommended sections:
- `<role_definition>`
- `<stopping_rules>`
- `<workflow>`
- `<checklist_enforcement>`
- `<operating_principles>`

Use:
- `<role_definition>` for ownership and exclusions
- `<stopping_rules>` for high-priority guardrails
- `<workflow>` for execution steps
- `<checklist_enforcement>` for completion checks
- `<operating_principles>` for durable behavioral guidance

Keep severity labels few and meaningful.

### Tag Usage Guidance

- Put `<role_definition>` first after frontmatter when using structured prompts
- Keep `<stopping_rules>` for high-priority constraints only
- Use `<workflow>` for the actual execution sequence, not general values or philosophy
- Use `<checklist_enforcement>` for completion checks that prevent premature exit
- Use `<operating_principles>` for durable guidance that shapes behavior across the workflow

### Portability Guidance

When designing YAML or structured prompt standards:
- favor fields and tags that stay readable even outside one platform
- document which parts are universal and which are platform-specific
- avoid hidden assumptions about folder names, tool names, or metadata extensions
- keep examples generic unless the example is intentionally demonstrating a platform variant

---

## Final Note

This `SKILL.md` is intended to be self-contained for most framework-maintenance work.

Use the platform documentation links above when a decision depends on actual platform behavior.
For normal framework design, refactoring, validation, and maintenance work, this file should be enough on its own.
