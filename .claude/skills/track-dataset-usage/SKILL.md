---
name: track-dataset-usage
description: >
  Show how much storage AEP datasets consume and flag unused or empty datasets.
  Load when the user asks "how much storage are datasets using", "find unused datasets",
  "which datasets have no data", "dataset storage usage", "empty datasets", or
  "which datasets haven't been updated in X days". Uses mcp__aep__list_datasets
  and mcp__aep__list_batches to compute storage and recency.
---

# Track Dataset Usage

## When to Load

- "how much storage are our datasets using"
- "find unused / empty datasets"
- "which datasets haven't been updated in 30 days"
- "dataset storage usage report"

---

## Data Sources

### Dataset list with row counts

```
mcp__aep__list_datasets   — rowCount and lastBatchStatus per dataset
```

### Batch history per dataset

```
mcp__aep__list_batches   — filter by datasetId to get last ingestion timestamp
```

`GET {AEP_BASE_URL}/data/catalog/batches?dataSet={datasetId}&orderBy=-created&limit=1`

---

## Metrics to Compute

| Metric | Source | How |
|---|---|---|
| Row count | `statsCache.rowCount` | Direct from catalog |
| Last ingestion date | `mcp__aep__list_batches` | Most recent batch `created` timestamp |
| Days since last update | Computed | Today − last batch date |
| Status | `lastBatchStatus` | `success`, `failed`, `processing` |

---

## Output Format

Rank by row count descending:

```
Dataset Storage & Usage Report (sandbox: cvs-aetna · 2026-09-10)

  Dataset                      Rows      Last Updated    Days Idle  Status
  ─────────────────────────────────────────────────────────────────────────
  Events Dataset               4,200,000  2026-09-09      1         success
  Profile Dataset (dev)          142,000  2026-09-10      0         success
  Lookup - Products                8,500  2026-08-15      26        success
  Legacy Test Dataset                  0  2026-03-01     193  IDLE  success

  Flagged:
    - Legacy Test Dataset: 0 rows, 193 days idle — candidate for archival
    - Lookup - Products: 26 days since last update — verify pipeline health
```

Flag datasets where:
- `rowCount = 0` — empty dataset
- `daysSinceUpdate > 30` — potentially stale or orphaned
- `lastBatchStatus = "failed"` — broken pipeline
