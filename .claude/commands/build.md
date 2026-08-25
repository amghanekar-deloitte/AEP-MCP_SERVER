# Build

Invoke the appropriate AEP pipeline agent to implement from an approved plan.

## When to Use
- Starting implementation from an approved plan
- Building a specific pipeline stage independently
- Resuming an in-progress stage

## Usage
```
/build
/build schema
/build ingest
/build validate
/build <description of what to build>
```

## Workflow

### 1. Detect Scope
Read the approved plan's Execution Strategy (or the explicit `/build <scope>`) to determine which agent to invoke:

| Scope | Agent | Stage(s) |
|---|---|---|
| `analyze` / `data profiling` | `data-analyst` | Stage 0 |
| `schema` / `schema design` / `schema deploy` | `schema-processor` | Stages 1-2 |
| `dataset` / `dataset creation` | `dataset-creator` | Stage 3 |
| `identity` / `identity config` | `identity-inspector` | Stage 4 |
| `profile` / `profile enablement` | `profile-operator` | Stage 5 |
| `ingest` / `data ingestion` | `data-ingestion` | Stage 6 |
| `validate` / `data validation` | `data-validator` | Stage 7 |
| `qa` / `qa gate` | `qa-master` | Stage 8 |
| No plan exists | ask user what to build, then invoke `planner` first |

### 2. Load Skills
- Load relevant domain skills based on the task (see each agent for its required skills)
- Read `<code_standards>` from CLAUDE.md for project conventions

### 3. Execute Per Plan Strategy
Follow the plan's Execution Strategy:
- **Sequential** (default for AEP pipeline): invoke agents in stage order
- **Targeted**: invoke a single stage agent directly

### 4. After Implementation
The implementing agents handle the remaining SDLC phases automatically per CLAUDE.md:
- Build (project build command from `<codebase_stack>`)
- Code review
- Tests
- Validate (verify via AEP APIs as appropriate)

Context: $ARGUMENTS
