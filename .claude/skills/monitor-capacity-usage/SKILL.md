---
name: monitor-capacity-usage
description: >
  Track how much of purchased AEP capacity is being used and flag any limit breaches —
  streaming throughput (RPS), profile storage, identity graph size, and query service
  compute. Load when the user asks "how much capacity are we using", "are we hitting limits",
  "capacity usage report", "check throughput vs capacity", "RPS usage", or "are we near
  any guardrails". Uses mcp__aep__get_metrics and Observability Insights API.
---

# Monitor Capacity Usage

## When to Load

- "how much capacity are we using"
- "are we hitting any limits / guardrails"
- "capacity usage report"
- "check streaming throughput vs limits"
- "RPS usage", "are we near any limits"

---

## Capacity Surfaces to Monitor

| Capacity | API | Metric |
|---|---|---|
| Streaming throughput | Observability Insights | `timeseries.ingestion.streaming.size` |
| Profile store | Observability Insights | `timeseries.profile.profileCount` |
| Identity graph | Observability Insights | `timeseries.identity.IdentityCount` |
| Query Service compute | Observability Insights | Query hours consumed |
| Batch ingestion | `list_batches` + recordCount | Records per day |

---

## API Approach

```
mcp__aep__get_metrics   — Observability Insights metric query
```

Key metric IDs:
- `timeseries.ingestion.streaming.size` — bytes/sec or rows/sec streamed
- `timeseries.profile.profileCount` — total addressable profiles
- `timeseries.identity.IdentityCount` — total identity links

REST:
```
POST {AEP_BASE_URL}/data/infrastructure/observability/insights/metrics
Body: { "metricId": "...", "filters": [...], "granularity": "day" }
```

---

## AEP Key Guardrails (reference — verify current limits via rtcdp skill)

| Metric | Soft Limit | Hard Limit |
|---|---|---|
| Streaming throughput | Per org license | Varies by contract |
| Profile store | Per org license | Varies |
| Segments per sandbox | 500 (B2C) | 400 (B2B) |
| Datasets per sandbox | 150 | — |
| Schemas per sandbox | 2,000 | — |
| Event look-back | 30 days | Hard cap |

For exact contracted limits, check in AEP UI under License Usage.

---

## Output Format

```
Capacity Usage Report (sandbox: cvs-aetna · last 7 days)

  Metric                    Current      7d Peak      Limit        Utilization
  ─────────────────────────────────────────────────────────────────────────────
  Streaming throughput      42 RPS       87 RPS       200 RPS      43.5%
  Profile store             142,000      142,000      —            —
  Total identities          386,000      386,000      —            —
  Active segments           38           38           500          7.6%
  Active datasets           12           12           150          8.0%

  No limit breaches detected.
```

Flag any metric at >80% of its limit as WARNING, >90% as CRITICAL.
