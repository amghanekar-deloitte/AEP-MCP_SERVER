---
name: audience-size-estimate
description: >
  Estimate AEP audience size for a PQL expression using the Segmentation Preview API.
  Load when the user asks how many profiles match a PQL expression, wants to estimate
  audience size before creating a segment, asks "how big would this audience be", or
  needs a count of qualifying profiles. Uses POST /data/core/ups/preview (async job)
  and polls until complete. Reports estimated count and percentage of total profiles.
---

# Audience Size Estimate

## When to Load

- "how many profiles match this PQL"
- "estimate audience size for ..."
- "how big would this audience be"
- "preview this segment"

---

## API Flow — Preview (Async)

### Step 1: Submit preview job

```
POST {AEP_BASE_URL}/data/core/ups/preview
Content-Type: application/json
Headers: Authorization, x-api-key, x-gw-ims-org-id, x-sandbox-name

Body:
{
  "predicateExpression": "<PQL expression>",
  "predicateType": "pql/text",
  "predicateModel": "_xdm.context.profile",
  "graphType": "none",
  "mergeStrategy": "timestampOrdered_union"
}
```

Response: `{ "state": "RUNNING", "previewQueryId": "...", "id": "...", ... }`

### Step 2: Poll for results

```
GET {AEP_BASE_URL}/data/core/ups/preview/{previewQueryId}
```

Poll every 2 seconds. States: `RUNNING` → `RESULT_READY` (or `ERROR`).

### Step 3: Read result

When `state = "RESULT_READY"`:

```json
{
  "totalRows": 47382,
  "totalFilteredRows": 47382,
  "state": "RESULT_READY",
  "standardError": 0,
  "error": { "description": "" },
  "previewQueryId": "...",
  "previewDataSetId": "..."
}
```

Key field: `totalFilteredRows` — this is the estimated qualifying profile count.

---

## Output Format

```
Estimated audience size: 47,382 profiles
As % of total: 4.7% (based on sandbox total)
PQL evaluated: loyalty.tier = "Gold" and consents.marketing.email.val = "y"
State: RESULT_READY
```

To get sandbox total profiles: `GET {AEP_BASE_URL}/data/core/ups/preview` with no body returns global stats.

---

## Constraints and Caveats

- Preview is an **estimate** — actual batch evaluation may differ by ±5%
- On B2B-simplification orgs: preview may return 0 or be unavailable for account-schema predicates; mention this caveat
- Event predicates with look-back > 30 days return 0 — warn the user
- Allow up to 60 seconds total poll time; report `TIMEOUT` if still `RUNNING`
- Never fabricate counts if the API returns an error

---

## Auth Reference

Load `aep-fundamentals` for the token acquisition pattern (`POST /ims/token/v3`).
