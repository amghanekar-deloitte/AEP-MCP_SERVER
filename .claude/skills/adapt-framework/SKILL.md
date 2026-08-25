---
name: adapt-framework
description: Adapt this framework to a target platform, engineering stack, or team operating model. Use when the user wants to make the framework generic, stack-aware, platform-aware, or project-aware by updating agents, commands, skills, and rules in a controlled way.
---

# Adapt Framework

Use this skill when the user wants to adapt the framework itself.

Examples:
- make the framework work for a new stack
- adapt the framework for Cursor, Claude Code, or GitHub Copilot
- make prompts more generic or more stack-specific
- create or revise platform-specific rules
- decide which skills to keep, create, or remove
- align agents, commands, skills, and rules around a target use case

This skill is for **framework adaptation**, not feature delivery inside a normal application.

---

## Core Principles

1. Adaptation is staged: detect → ask → analyze → synthesize → approve → edit → validate.
2. Do not ask too many questions at once. Ask only high-leverage questions first.
3. Infer what you can from the existing framework before asking the user.
4. Use parallel analyzers for read-only framework analysis, not for immediate edits.
5. Never edit the framework until the adaptation plan is approved.
6. Keep the framework coherent across agents, commands, skills, rules, and platform folders.
7. Use existing framework assets before creating new ones.

---

## Mandatory Supporting Skills

Always load these first:

- `framework-guidance`
  Use this for:
  - change ownership
  - where the adaptation belongs
  - anti-pattern avoidance
  - hook decisions
  - validation after changes

Load these only when needed:

- `skill-creator`
  Use only if the approved plan requires creating a new skill

- `skill-review`
  Use only if the approved plan includes auditing or tightening an existing skill

Do not load extra skills speculatively.

---

## What This Skill Adapts

This skill may adapt:

- agents
- commands
- skills
- rules
- prompt/reference assets
- platform-specific folders such as `.claude/`, `.cursor/`, `.vscode/`, `.github/`

It may also decide that some surfaces should remain unchanged.

---

## Questions Strategy

Do not interrogate the user.

Use staged questioning:

### Round 1 — mandatory

Ask only the minimum needed to classify the adaptation:

- target platform
  - Claude Code
  - Cursor
  - GitHub Copilot
  - VS Code
  - multi-platform

- adaptation scope
  - generic core
  - stack-adapted framework
  - project-adapted framework

- target engineering shape
  - backend
  - frontend
  - full-stack
  - API/platform
  - data/workflows
  - mixed

### Round 2 — conditional

Ask only if the answer changes the adaptation plan:

- should rules be generated for platform-specific folders?
- should existing skills be reused as-is, adapted, or should new ones be created?
- should prompts stay generic by default, with stack specialization moved into skills?
- should the framework support one platform only or stay portable across multiple clients?

### Round 3 — only if ambiguity remains

Ask only for blocking uncertainty such as:

- review strictness
- testing expectations
- delivery/runtime expectations
- whether hooks are allowed or should remain minimal

Never ask low-value stylistic questions during the first pass.

---

## Read-Only Analysis Phase

Before proposing changes, inspect the current framework state.

Always inspect:

- current agents
- current commands
- current skills
- current rules folders
- current platform-specific integration folders
- root instruction files

Infer what you can before asking the user.

---

## Parallel Analyzer Model

After Round 1 questions are answered, run three parallel read-only analyzers.

These are analysis threads, not implementation workers.

### 1. Agent Analyzer

Responsibility:
- inspect current agents
- identify stack assumptions, platform assumptions, and prompt mismatches
- determine which agent roles should be kept, revised, split, merged, or left alone
- determine what prompt changes are needed for the target adaptation

Output:
- current state summary
- problems found
- recommended changes
- risks if unchanged

### 2. Command Analyzer

Responsibility:
- inspect current commands
- identify commands that are core, optional, obsolete, too stack-specific, or too platform-specific
- determine whether commands should be kept, removed, renamed, or rewritten
- determine whether platform-specific command behavior belongs elsewhere

Output:
- current command map
- keep/remove/rename recommendations
- command-to-agent alignment issues
- risks if unchanged

### 3. Skill And Rules Analyzer

Responsibility:
- inspect current skills and rule folders
- identify which skills are already reusable
- identify which skills are missing
- determine whether new rules should be created for `.claude`, `.cursor`, `.vscode`, or `.github`
- determine whether the framework should emit common rules plus platform-specific overlays

Output:
- current reusable skill set
- missing skill recommendations
- rule generation recommendations
- risks if unchanged

### Research-Intelligence Support

If the target platform behavior is uncertain, use `research-intelligence` as a supporting agent.

Use it only for:
- official platform behavior
- hook capability differences
- agent/command/rules support differences
- MCP/platform integration behavior

Do not rename or rewrite `research-intelligence`. Use it as support when needed.

---

## Synthesis Phase

After the three analyzers return, combine the findings into one adaptation plan.

The synthesis step must answer:

- what should change
- why it should change
- where the change belongs
- what should be created vs edited vs deleted
- what should remain untouched
- which changes are shared across all target platforms
- which changes are platform-specific

Do not jump from analysis straight into edits.

---

## Adaptation Plan Format

Present the plan in this structure:

### 1. Adaptation Goal
- what the framework is being adapted for

### 2. Detected Current State
- what exists now across agents, commands, skills, and rules

### 3. User Constraints
- platform targets
- stack targets
- keep/remove restrictions
- hook tolerance

### 4. Proposed Changes
- Agents
- Commands
- Skills
- Rules
- Platform-specific folders

### 5. Create / Edit / Delete Map
- exact file-level intent

### 6. Execution Strategy
- which edits can happen in parallel
- which edits must happen in sequence
- what needs re-validation before the next phase

### 7. Risks And Blockers
- anything that can break framework coherence

### 8. Approval Gate
- wait for explicit user approval before editing

---

## Approval Rule

Never edit the framework before the user approves the adaptation plan.

If the user asks to revise the plan:
- revise first
- re-present
- then wait again

---

## Parallel Edit Phase

After approval, run parallel edit workers where possible.

Recommended edit workers:

### 1. Agent Editor
- updates agent prompts
- preserves role separation
- removes or adds stack/platform assumptions as approved

### 2. Command Editor
- updates commands
- keeps commands thin
- aligns them with the revised agents

### 3. Skill / Rules Editor
- updates or creates skills if approved
- creates or revises rules if approved
- aligns platform-specific folders with the target client(s)

Only create new skills or rules when the approved plan explicitly requires them.

---

## Rules Generation Guidance

If the approved plan includes rule creation:

- create shared/common rules only for truly universal expectations
- create platform-specific rules only when the target platform needs them
- avoid duplicating the same rule across multiple places unless the platform genuinely requires separate files
- prefer a shared conceptual rule model with thin platform-specific packaging

Examples of acceptable rule categories:
- development workflow
- testing expectations
- security expectations
- hook policy
- coding style
- platform-specific guardrails

Examples of unacceptable rule creation:
- generating large rule sets before the user confirms the platform target
- duplicating agent instructions into rules
- creating rules for platforms the user is not targeting

---

## Validation Phase

After edits, validate the framework as a system.

Validate:

- syntax
- frontmatter
- structured prompt tags
- stale references after renames
- agent/command alignment
- command/skill alignment
- rule placement correctness
- platform-specific folder coherence
- no accidental stack- or product-specific leftovers

Also verify:

- generic core remains generic
- platform-specific adaptations exist only where intended
- the framework still has clear ownership boundaries

Use `framework-guidance` validation principles while doing this.

---

## Final Report

After validation, report:

- what changed
- what was created
- what was removed
- which platforms/stacks are now supported by the adaptation
- what remains intentionally untouched
- any follow-up decisions still needed from the user

---

## Guardrails

- Do not adapt by randomly patching multiple surfaces without a plan.
- Do not ask many low-value questions early.
- Do not rewrite everything if only one surface needs adaptation.
- Do not create new skills or rules just because a gap exists unless it is durable and approved.
- Do not change `research-intelligence` unless the user explicitly asks for that agent itself to change.
- Do not add hooks casually. If hooks are considered, justify why prompt/rule-based guidance is insufficient.

---

## Success Criteria

This skill is successful when:

- the user’s target platform(s) and stack(s) are clearly understood
- the adaptation plan is structured, scoped, and approved
- the framework is edited coherently across the right surfaces
- the resulting framework is more aligned, not more fragmented
- no unnecessary platform or stack assumptions remain in the generic core
