---
name: explore-datasets
description: >
  Find and explore AEP datasets by name, schema, size, labels, or usage. Load when
  the user asks "show me our datasets", "find dataset X", "list datasets for schema Y",
  "what datasets do we have", "which datasets are profile-enabled", or "show dataset details".
  Uses mcp__aep__list_datasets and mcp__aep__get_dataset. Returns dataset name, schema,
  profile-enablement status, row count, and last ingest time.
---

# Explore Datasets

## When to Load

- "show me our datasets", "list all datasets"
- "find dataset [name]"
- "which datasets use schema X"
- "what datasets are profile-enabled"
- "show me dataset details for X"

---

## API Approach

### List datasets

```
mcp__aep__list_datasets   — list all datasets in the active sandbox
```

REST: `GET {AEP_BASE_URL}/data/catalog/dataSets?limit=100`

Key response fields:
- `name` — dataset name
- `schemaRef.$id` — schema URI
- `tags.unifiedProfile` — `["enabled:true"]` if profile-enabled
- `lastBatchStatus` — `success`, `failed`, or `processing`
- `statsCache.rowCount` — approximate row count

### Get a single dataset

```
mcp__aep__get_dataset   — full dataset details including batch history
```

---

## Output Format

**List view:**

| Dataset Name | Schema | Profile | Rows | Last Batch | Status |
|---|---|---|---|---|---|
| Profile Dataset (dev) | Individual Profile | Yes | 142,000 | 2026-09-10 | success |
| Events Dataset | ExperienceEvent | Yes | 4.2M | 2026-09-09 | success |
| Lookup Dataset | Product Catalog | No | 8,500 | 2026-08-15 | success |

**Detail view (single dataset):**

```
Name:   Profile Dataset (dev)
ID:     5f3e...
Schema: Individual Profile
Class:  XDM Individual Profile
Profile Enabled: Yes
Row Count: 142,000
Last Batch: 2026-09-10 14:32 UTC (success)
Labels: C1, C2 (data governance)
Tags: unifiedProfile:enabled, unifiedIdentity:enabled
```

---

## Filtering

- By name: case-insensitive substring match on `name`
- By schema: match `schemaRef.$id` against schema title or ID
- By profile-enabled: check `tags.unifiedProfile` contains `"enabled:true"`
- By status: filter on `lastBatchStatus`
