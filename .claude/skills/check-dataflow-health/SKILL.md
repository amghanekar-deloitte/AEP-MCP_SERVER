---
name: check-dataflow-health
description: >
  Show the status, schedule, and health of a specific AEP dataflow — last run result,
  next scheduled run, error detail, and run history. Load when the user asks "is dataflow X
  healthy", "check dataflow Y", "when did this dataflow last run", "why is this dataflow
  failing", or "show me run history for dataflow X". Uses mcp__aep__get_dataflow and
  mcp__aep__list_flow_runs for a single targeted dataflow inspection.
---

# Check Dataflow Health

## When to Load

- "is dataflow [name/ID] healthy"
- "check dataflow X"
- "when did this dataflow last run"
- "why is this dataflow failing"
- "run history for dataflow X"

---

## API Approach

### Get dataflow config

```
mcp__aep__get_dataflow   — schedule, state, source/target connections
```

Key fields:
- `state` — `enabled` or `disabled`
- `scheduleParams.startTime`, `frequency`, `interval` — schedule config
- `sourceConnectionIds`, `targetConnectionIds` — linked connections

### Get run history

```
mcp__aep__list_flow_runs   — filter by flowId, order by startedAtUTC desc, limit=10
mcp__aep__get_flow_run     — detail for a specific run
```

Key run fields:
- `status` — `completed`, `failed`, `inProgress`, `queued`
- `startedAtUTC`, `endedAtUTC` — timing
- `metrics.recordsReceived`, `metrics.recordsUpserted`, `metrics.recordsFailed`
- `errorInfo.message` — failure message when status=failed

---

## Output Format

```
Dataflow Health: Profile Daily Load
ID: abc123-...

Config:
  State:     enabled
  Schedule:  daily at 02:00 UTC
  Source:    Amazon S3 · s3://deloitte-cvs-aetna/profile-exports/
  Target:    Profile Dataset (dev)

Run History (last 5 runs):
  Run Date        Duration  Records In   Upserted   Failed  Status
  ──────────────────────────────────────────────────────────────────
  2026-09-10 02   3m 42s    142,000      141,658    342     FAILED (partial)
  2026-09-09 02   3m 12s    140,000      140,000    0       completed
  2026-09-08 02   3m 05s    138,500      138,500    0       completed
  2026-09-07 02   4m 01s    141,200      141,200    0       completed
  2026-09-06 02   3m 28s    139,800      139,800    0       completed

Last Failure:
  2026-09-10: 342 records failed — INGEST-1210: identity field null
  → Run /analyze-data-import-failures for full error detail
```
