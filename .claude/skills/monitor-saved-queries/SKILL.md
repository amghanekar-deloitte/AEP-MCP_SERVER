---
name: monitor-saved-queries
description: >
  Track the status, schedule, and performance of saved AEP Query Service queries — list
  scheduled queries, check when they last ran, find failed runs, and inspect query output.
  Load when the user asks "show scheduled queries", "did my scheduled query run", "query
  schedule status", "find failed query runs", "when did query X last execute", or "monitor
  Query Service jobs". Uses mcp__aep__list_scheduled_queries and mcp__aep__list_query_runs.
---

# Monitor Saved Queries

## When to Load

- "show scheduled queries"
- "did my scheduled query run"
- "find failed query runs"
- "when did query X last run"
- "Query Service job status"

---

## API Approach

### List all scheduled queries

```
mcp__aep__list_scheduled_queries   — all scheduled query definitions
```

Key fields per schedule:
- `id` — schedule ID
- `query.sql` — the SQL being run
- `schedule.startDate`, `schedule.frequency`, `schedule.interval` — schedule config
- `state` — `ENABLED`, `DISABLED`

### List query runs for a schedule

```
mcp__aep__list_query_runs   — recent execution history for a scheduled query
```

Key run fields:
- `status` — `SUCCESS`, `FAILED`, `IN_PROGRESS`
- `startedAt`, `completedAt` — timing
- `rowsResult` — row count produced
- `error.message` — failure reason when status=FAILED

### View results of a completed query

```
mcp__aep__view_query_results   — retrieve output from a completed query run
```

---

## Output Format

```
Scheduled Query Status (sandbox: cvs-aetna)

  Schedule Name                Frequency   Last Run           Status    Rows    Duration
  ──────────────────────────────────────────────────────────────────────────────────────
  Daily Profile Snapshot       Daily 01:00  2026-09-10 01:04   SUCCESS   142,000  3m 52s
  Weekly Loyalty Report        Weekly Mon   2026-09-08 00:30   SUCCESS   8,400    1m 12s
  Event Summary                Daily 03:00  2026-09-09 03:02   FAILED    —        —

  Failed Run Detail — Event Summary (2026-09-09):
    Error: column "_cvs.personlizedVisits" does not exist
    Fix:   Load sandbox-schema-context skill and use find_field helper to discover
           the correct visits column name for this sandbox
```

---

## Notes

- Scheduled query results land in a designated output dataset; use `view_query_results` to inspect
- A query that was never scheduled appears in `list_queries`, not `list_scheduled_queries`
- Field name errors across sandboxes are the most common failure mode — see `sandbox-schema-context` skill
