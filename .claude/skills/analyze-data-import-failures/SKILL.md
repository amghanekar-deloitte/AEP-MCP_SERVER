---
name: analyze-data-import-failures
description: >
  Find out why data failed to load into AEP and which sources are affected. Load when
  the user asks "why did my data not ingest", "find failed batches", "ingestion errors",
  "data import failures", "why is data missing from my dataset", or "batch failed — what happened".
  Uses mcp__aep__list_batches, mcp__aep__get_batch, and Flow Service run history to surface
  failure reasons, error codes, and affected record counts.
---

# Analyze Data Import Failures

## When to Load

- "why did my data not load / ingest"
- "find failed batches"
- "ingestion errors for dataset X"
- "data is missing — what happened"
- "batch failed — why"

---

## Diagnosis Flow

### Step 1: Find failed batches

```
mcp__aep__list_batches   — filter status=failed, limit=20
```

REST: `GET {AEP_BASE_URL}/data/catalog/batches?status=failed&orderBy=-created&limit=20`

Optionally scope to one dataset: add `&dataSet={datasetId}`.

Key batch fields:
- `id` — batch ID
- `datasetIds` — which dataset(s) were targeted
- `status` — `failed`, `stagingSucceed` (partial), `retrying`
- `failedRecordCount` — how many records failed
- `recordCount` — total records attempted
- `errors` — array of `{ code, description, rows }` objects

### Step 2: Get batch detail

```
mcp__aep__get_batch   — full error detail for a specific batch
```

REST: `GET {AEP_BASE_URL}/data/catalog/batches/{batchId}`

### Step 3: Check flow run failures (for connector-based ingestion)

```
mcp__aep__list_flow_runs   — list runs for a dataflow, filter status=failed
mcp__aep__get_flow_run     — detail for a specific run including error message
```

---

## Common Failure Codes

| Code | Meaning | Fix |
|---|---|---|
| `INGEST-1000` | Required field missing | Add field to source data or mapping |
| `INGEST-1004` | Schema validation failure | Source value doesn't match field type |
| `INGEST-1210` | Identity missing | Ensure identity field is present and non-null |
| `INGEST-1300` | File format error | Check CSV/JSON encoding, delimiters, BOM |
| `INGEST-1500` | Batch too large | Split into smaller batches (max 512 MB per file) |
| `DCUE-0006`   | Dataset not found | Verify datasetId is correct and in the right sandbox |

---

## Output Format

```
Import Failure Report (last 20 failed batches)

Batch ID          Dataset                  Date        Failed/Total  Top Error
─────────────────────────────────────────────────────────────────────────────────
abc123...         Profile Dataset (dev)    2026-09-10  342 / 10,000  INGEST-1210: identity missing
def456...         Events Dataset           2026-09-09  1 / 85,000    INGEST-1000: required field

Detail — batch abc123:
  Error: INGEST-1210 — Identity field `_deloitte_digitalengage.proxyId` is null or missing
  Rows affected: 342
  Recommendation: Verify source CSV has proxyId populated for all rows before re-upload
```
