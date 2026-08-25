# Plan Implementation

Invoke the `planner` agent to create detailed implementation plans.

## When to Use
- Planning a new feature, module, service, interface, workflow, or integration
- Need structured implementation contracts before coding
- Want context gathered from requirement references, schemas, design/spec inputs, or related artifacts

## Mandatory Skill Loading
Planning-standards is mandatory for every planning request.
- Always invoke planning-standards skill first.
- Always read all relevant sections for the classified task type before drafting the plan.
- Never produce a plan until skill loading and section reading are complete.

## Workflow
1. Analyze user input — extract Input-Derived Patterns (names, interfaces, structures, data shapes, reference constraints, and runtime constraints) if reference input is provided
2. Read code_standards and codebase_stack from CLAUDE.md
3. Load planning-standards skill — read all relevant sections for the classified category
4. If a supported design or reference-spec input is provided → invoke the relevant context skill
5. If a supported work item or requirements reference is provided → invoke the relevant context skill
6. Invoke code-explorer AND research-intelligence in parallel — DO NOT proceed until both return
7. Validate research findings, fill gaps with WebFetch or Grep
8. Reusability scan — use AskUserQuestion to present findings and get user confirmation before proceeding
9. Classify task type and assess complexity (S/M/L)
10. For AEP pipeline tasks: route to the appropriate stage agent per the pipeline routing table in the planner agent. For non-AEP tasks: assess if additional review is needed.
11. Define Execution Strategy — agent assignment, execution mode, context payloads, SDLC flow.
12. Present plan using the plan output template from planning-standards (Section 10) — use AskUserQuestion for open questions and plan approval
13. After user approves — use TaskCreate to create one task per SDLC phase with dependencies, then use handoff buttons to start implementation

## Plan Output Contract (Required)
The produced plan must follow the plan output template from planning-standards (Section 10). Key requirements:
- Summary with task type and complexity (S/M/L)
- Input-Derived Patterns (exact values where reference inputs define them)
- Reusability Analysis with extend-vs-build recommendation
- Technical Contract using the task-type-specific template from planning-standards (Section 6)
- File Impact as a table (Action / File Path / Purpose) with exact paths and CREATE/MODIFY/REMOVE per file
- Dependency Graph as ASCII diagram for M/L complexity or multi-agent tasks
- Execution Strategy with agent assignment, execution mode, Agent Context Briefs per agent, and SDLC flow
- Risks as a table (Severity / Risk / Mitigation)
- Open Questions for unresolved decisions

Reject and regenerate if any section is missing.

## Tool Usage (Mandatory)
- AskUserQuestion — use for reusability confirmation (Step 8), open questions, and plan approval (Step 12). Never print a question as plain text.
- TaskCreate — use after plan approval (Step 13) to create one task per SDLC phase: Implement, Build, Review, Test, Deploy, Validate. Each task must have subject, description (with agent assignment and context), and activeForm. Set dependencies: Build blockedBy Implement, Review blockedBy Build, Test blockedBy Review, Deploy blockedBy Test, Validate blockedBy Deploy.

## Checklist Enforcement
Before returning any plan, the planner must pass all checks from planning-standards (Section 9) and the planner agent's checklist. Key items:
1. User input analyzed and Input-Derived Patterns extracted?
2. code_standards and codebase_stack read from CLAUDE.md?
3. Planning-standards loaded and relevant sections read?
4. code-explorer AND research-intelligence invoked in parallel?
5. Reusability scan done and user confirmed via AskUserQuestion?
6. Task type classified and complexity assessed?
7. For AEP pipeline tasks, correct stage agent will be invoked per pipeline routing table?
8. Plan uses correct contract template for the task type?
9. Plan includes Input-Derived Patterns?
10. Plan includes Execution Strategy with Agent Context Briefs?
11. File Impact uses table format with exact paths and CREATE/MODIFY/REMOVE?
12. ASCII dependency graph included (for M/L complexity)?
13. Risks table and Open Questions included?
14. File structure derived from code_standards (not generic defaults)?
15. Plan describes work for OTHERS to execute, not the planner?
16. AskUserQuestion used (not plain text) for reusability confirmation, open questions, and plan approval?
17. After approval, TaskCreate used to create SDLC phase tasks with dependencies?

If any checklist item fails, do not finalize — regenerate with missing details.

The `planner` agent handles task classification, complexity estimation, reusability scanning, and contract generation. This command activates the workflow.

Context: $ARGUMENTS
