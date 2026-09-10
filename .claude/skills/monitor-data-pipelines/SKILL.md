---
name: monitor-data-pipelines
description: >
  Track the health and performance of AEP data pipelines end-to-end — from source ingestion
  through to dataset landing. Load when the user asks "how are our pipelines doing",
  "is data flowing", "pipeline health check", "check all dataflows", "any pipeline errors",
  or "data pipeline status". Covers batch pipelines (Flow Service runs) and streaming
  throughput. Surfaces failures, delays, and stalled flows in one report.
---

# Monitor Data Pipelines

## When to Load

- "how are our pipelines doing"
- "is data flowing / pipeline health check"
- "any pipeline errors or failures"
- "data pipeline status report"
- "check all dataflows"

---

## Health Signals to Collect

| Signal | API | What It Shows |
|---|---|---|
| Dataflow run status | `mcp__aep__list_flow_runs` | Last run result per dataflow |
| Failed batches | `mcp__aep__list_batches` (status=failed) | Ingestion errors |
| Streaming throughput | Observability Insights metrics | RPS vs. capacity |
| Dataset last update | `mcp__aep__list_datasets` statsCache | Staleness |

---

## Execution

### Step 1: List all dataflows + last run

```
mcp__aep__list_dataflows
mcp__aep__list_flow_runs   — for each dataflow, get the most recent run
```

Classify each dataflow:

| Status | Criteria |
|---|---|
| Healthy | Last run succeeded within expected schedule window |
| Warning | Last run succeeded but older than 2× schedule interval |
| Failed | Last run status = `failed` |
| Stalled | No runs in past 48h for an active dataflow |

### Step 2: Surface failed batches for dataset-based ingestion

```
mcp__aep__list_batches   — status=failed, limit=10, order by -created
```

### Step 3: Check dataset freshness

Flag datasets where `daysSinceLastUpdate > 2 × expected schedule interval`.

---

## Output Format

```
Pipeline Health Report (2026-09-10)

  Dataflow                      Type      Last Run              Status   Issue
  ───────────────────────────────────────────────────────────────────────────────
  Profile Daily Load            Batch     2026-09-10 02:15 UTC  OK
  Events HTTP Streaming         Stream    Live (42 RPS)         OK
  Product Catalog Sync          Batch     2026-08-15 04:00 UTC  WARN     26 days stale
  Legacy CRM Sync               Batch     2026-06-01 00:00 UTC  STALLED  No runs in 100d

Failed Batches (last 24h):
  - Profile Dataset: batch abc123 failed · 342 records · INGEST-1210

Summary: 2 OK · 1 WARNING · 1 STALLED · 1 batch failure
```
