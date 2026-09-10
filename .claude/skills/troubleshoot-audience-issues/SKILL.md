---
name: troubleshoot-audience-issues
description: >
  Find out why an AEP audience's size or qualification unexpectedly changed — audience
  dropped to zero, audience count spiked, profiles stopped qualifying, or evaluation
  results are unexpected. Load when the user says "why is my audience empty", "audience
  size dropped to 0", "why did this segment shrink", "profiles not qualifying",
  "audience count wrong", or "troubleshoot audience X". Diagnoses schema changes,
  data ingestion gaps, PQL issues, merge policy effects, and evaluation type mismatches.
---

# Troubleshoot Audience Issues

## When to Load

- "my audience is empty / dropped to zero"
- "why did this segment shrink or spike"
- "profiles not qualifying for audience X"
- "audience count looks wrong"
- "troubleshoot audience [name]"

---

## Diagnostic Checklist

Work through these in order — stop when the root cause is found.

### 1. Confirm the audience definition is valid

```
mcp__aep__get_segment   — retrieve PQL and evaluationInfo
```

- Is the PQL syntactically valid? Look for common errors: wrong field path, bad operator, unbalanced parentheses
- Is evaluation type correct? (batch won't update until nightly run; streaming requires enabled connector)
- Is the schema correct? `_xdm.context.profile` for person audiences

### 2. Check event look-back window

If the PQL has an `xEvent` sub-query: is the look-back > 30 days? AEP hard cap is 30 days — PQL with longer windows returns 0 without an error message.

### 3. Check data freshness

```
mcp__aep__list_datasets + mcp__aep__list_batches
```

When was the profile dataset last successfully ingested? A stalled pipeline = stale profiles = audience size doesn't reflect current data.

### 4. Check if referenced fields exist

Load `field-discovery`: do all fields in the PQL exist in the deployed schema? A field removed or renamed after the audience was created causes silent 0-match.

### 5. Check merge policy

```
mcp__aep__list_merge_policies
```

The audience's merge policy determines which profile fragments are included. A wrong merge policy (e.g., one excluding your main dataset) shrinks the audience.

### 6. Run a preview estimate

Load `audience-size-estimate`: run the Preview API now and compare to the stored `profileCount`. If Preview returns 0 but count was non-zero: the PQL is evaluating against a currently empty union.

### 7. Check identity graph

If this is a B2B account audience: the account union materializes on a daily batch job. Until it runs, the count is 0.

---

## Output Format

```
Audience Troubleshoot: Gold Loyalty Members (ID: abc123)
Current profileCount: 0  (was 47,382 last week)

Diagnostic Results:
  [OK] PQL syntax is valid
  [OK] Evaluation type: batch (nightly)
  [WARN] Event look-back: 30 days (at limit — OK)
  [FAIL] Profile dataset last batch: FAILED on 2026-09-10 (342 records, INGEST-1210)
  [WARN] No successful batch ingestion since 2026-09-08 → profiles are 2 days stale

Root Cause:
  Profile dataset ingestion failed on 2026-09-10 (identity field null).
  Batch evaluation ran against a dataset with 2-day-old data, dropping qualifying count.

Fix:
  1. Resolve ingestion failure (see analyze-data-import-failures)
  2. Re-ingest profile data
  3. Trigger a new batch evaluation or wait for nightly run
```
