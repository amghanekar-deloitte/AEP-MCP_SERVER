---
name: diagnostics-evaluator
description: >
  Review a completed diagnostics-investigator probe result and judge whether the evidence
  actually supports the claimed root cause, or is only correlated with the symptom. Called
  from the diagnostics loop after a hypothesis is marked CONFIRMED, before it is reported
  to the user as root cause. Not loaded directly by users.
---

# Diagnostics: Evaluator

## When to Load

- Called from `diagnostics` step 5, immediately after `diagnostics-investigator` returns a
  CONFIRMED verdict
- Never invoked directly by a user

---

## Purpose

A CONFIRMED probe result is not automatically root cause — it may just be the first thing
that happened to be true near the symptom. This step is a skeptical second pass before
committing to a root-cause report: does the evidence causally explain the symptom, or does
it merely co-occur with it?

---

## Evaluation Checklist

Run through all of these before accepting a CONFIRMED hypothesis as final root cause:

### 1. Causal mechanism, not just correlation

Can you state, in one sentence, the mechanism by which the confirmed fact produces the
observed symptom? "Field removed from schema" + "PQL references that field" + "AEP PQL
evaluation returns 0 rows on missing field reference" is a mechanism. "Field was removed
around the same time" alone is not.

### 2. Timing consistency

Does the confirmed cause predate the symptom's onset, by an amount consistent with how the
affected system evaluates (e.g., a schema change followed by the next scheduled batch
evaluation, not before it)? A cause that postdates the symptom cannot be the cause.

### 3. Magnitude consistency

Does the size of the cause match the size of the symptom? A single null field on one record
does not explain an entire dataset going to 0 rows; a full ingestion failure does.

### 4. Alternative explanation check

Is there a second confirmed or plausible hypothesis that could independently explain the
same symptom? If so, don't report either as sole root cause until this is resolved — check
whether they're actually the same underlying event, or investigate which one actually fired
first.

### 5. Reproducibility of the probe

Would re-running the same probe produce the same result right now? If the underlying state
might have already changed (e.g., someone fixed it mid-investigation), re-run the probe
before finalizing the report.

---

## Verdict

- **SUFFICIENT** — mechanism, timing, and magnitude all line up; no competing explanation.
  Return to `diagnostics` to report as root cause.
- **WEAK** — mechanism plausible but timing or magnitude don't fully line up, or a competing
  hypothesis exists. Return to `diagnostics` step 4 with a note on what's missing (usually:
  a probe that resolves the competing hypothesis, or a check on evaluation timing).

---

## Output Format

```
Evidence Review: "Field _tenant.visitCount removed from schema" as root cause of
segment 0-match

  [PASS] Causal mechanism: PQL references a field; AEP returns 0-match when a referenced
         field doesn't exist in the currently deployed schema version
  [PASS] Timing: field removed 2026-09-09, symptom observed 2026-09-10 — consistent with
         the segment's nightly batch evaluation cycle
  [PASS] Magnitude: field is used in a required (non-optional) PQL predicate — removal
         alone is sufficient to zero out matches, no partial-match evidence contradicts this
  [PASS] No competing hypothesis remains CONFIRMED
  [PASS] Probe is reproducible — re-ran get_schema, same result

Verdict: SUFFICIENT
```

```
Evidence Review: "CRM Sync Dataset batch failure" as root cause of segment 0-match

  [PASS] Causal mechanism: failed batch means no new CRM records land in the dataset
  [FAIL] Magnitude: CRM Sync Dataset supplies ~8% of records to this segment based on
         merge policy fan-in; a 100% drop to 0 is not explained by an 8% source failing
  [WARN] Competing hypothesis "_tenant.visitCount field removed" is also CONFIRMED and
         explains 100% of the drop

Verdict: WEAK — magnitude mismatch and an unresolved competing hypothesis.
Next: report the field-removal hypothesis as primary; note the CRM batch failure as a
secondary, real but insufficient-alone issue to fix regardless.
```

---

## Notes

- It is acceptable, and often correct, to report more than one confirmed issue in the final
  diagnostics output as long as each is evaluated on its own magnitude and not conflated
  with the primary root cause
- Never let a WEAK verdict get reported as root cause to the user — send it back for another
  investigation pass or explicitly label it as a contributing factor, not the cause
