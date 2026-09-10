---
name: monitor-destinations
description: >
  Track the health, delivery rate, and errors of AEP activation destinations — check which
  destinations are active, when they last delivered data, how many identities were exported,
  and whether any are failing. Load when the user asks "how are our destinations doing",
  "is destination X healthy", "destination delivery errors", "check destination health",
  or "destination activation report". Uses mcp__aep__list_dataflows, list_flow_runs,
  and list_target_connections.
---

# Monitor Destinations

## When to Load

- "how are our destinations doing"
- "is destination X healthy / delivering"
- "destination errors or failures"
- "destination health / activation report"
- "when did destination X last deliver"

---

## Data Sources

### List destination dataflows

```
mcp__aep__list_dataflows          — filter by type or destinationSpec
mcp__aep__list_target_connections — target details including destination config
mcp__aep__list_flow_runs          — run history per destination dataflow
```

### Destination types

| Type | Behavior | Key Metric |
|---|---|---|
| Batch | Exports on schedule (daily/weekly) | Records exported per run |
| Streaming | Continuous identity export | Identities per second |
| Edge | Real-time personalization | Latency |

---

## Health Classification

| Status | Criteria |
|---|---|
| Healthy | Last run completed, records > 0, within schedule window |
| Warning | Last run completed but older than 2× schedule interval |
| Failed | Last run status = failed |
| Empty | Last run completed but 0 records exported |

---

## Output Format

```
Destination Health Report (sandbox: cvs-aetna · 2026-09-10)

  Destination              Type      Last Delivery        Identities  Status
  ──────────────────────────────────────────────────────────────────────────
  Adobe Campaign v8        Batch     2026-09-08 03:00     47,200      OK
  Google Customer Match    Stream    Live                  ~150/s      OK
  Amazon S3 Export         Batch     2026-08-01 00:00     12,500      WARN  40 days old
  Salesforce CRM Sync      Batch     2026-09-10 01:00     0           EMPTY

  Issues:
  - Amazon S3 Export: 40 days since last delivery — verify schedule and credentials
  - Salesforce CRM Sync: 0 identities exported on last run — check audience size and field mapping
```

---

## Common Destination Failure Causes

| Issue | Symptom | Fix |
|---|---|---|
| Expired credentials | `HTTP 401` in flow run error | Refresh API key / OAuth token in destination config |
| Audience empty | 0 records exported | Check audience size via `audience-search` |
| Schema mismatch | Field mapping error | Review Data Prep mapping for this destination |
| Rate limit | Flow run throttled | Check destination's rate limits; reduce export frequency |
