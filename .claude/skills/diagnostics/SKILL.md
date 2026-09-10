---
name: diagnostics
description: >
  Primary entry point for troubleshooting an unexplained AEP problem — data not showing up,
  a pipeline behaving unexpectedly, a number that looks wrong, anything without an obvious
  cause. Load when the user says "something is broken", "why isn't this working", "help me
  debug X", "investigate this issue", or describes a symptom without naming the root cause.
  Orchestrates diagnostics-research, diagnostics-investigator, and diagnostics-evaluator in a
  hypothesis-driven loop; falls back to diagnostics-knowledge when no hypothesis fits.
---

# Diagnostics

## When to Load

- "something is broken / not working"
- "why isn't [X] happening"
- "help me debug / investigate [symptom]"
- "this number looks wrong and I don't know why"
- Any vague symptom report with no known root cause yet

Do NOT load this for problems with a known, named cause and an existing skill —
route directly instead: audience issues → `troubleshoot-audience-issues`,
campaign issues → `troubleshoot-campaign-issues`, ingestion failures →
`analyze-data-import-failures`, dataflow health → `check-dataflow-health`.
Load `diagnostics` only when the symptom doesn't already point at one of those.

---

## Method: Hypothesis-Driven Investigation Loop

This skill does not itself contain domain checklists — it coordinates the loop and keeps
state. Each sub-skill has one job:

```
1. Capture the symptom precisely (what, since when, expected vs actual)
        |
        v
2. diagnostics-research   — map the AEP topology touching this symptom
        |                    (which schemas, datasets, flows, segments, journeys are involved)
        v
3. Generate a ranked list of falsifiable hypotheses from the topology + symptom
        |
        v
4. diagnostics-investigator — test the top hypothesis with a falsifiable probe
        |
        +-- hypothesis CONFIRMED --> go to step 5
        |
        +-- hypothesis REJECTED --> pull next hypothesis, repeat step 4
        |                            (if hypothesis list exhausted, go to diagnostics-knowledge)
        v
5. diagnostics-evaluator  — review the investigation artifact: is the evidence
        |                    actually sufficient to call this root cause, or just correlated?
        |
        +-- evidence WEAK --> back to step 4, dig deeper on the same hypothesis
        |
        +-- evidence SUFFICIENT --> done
        v
6. Report root cause + fix, citing the probe(s) that confirmed it
```

If no hypothesis from `diagnostics-research` survives investigation, load
`diagnostics-knowledge` to search AEP documentation for failure modes matching the symptom
pattern, then generate new hypotheses from what comes back and re-enter step 4.

---

## Step 1: Capture the Symptom

Never start investigating from a vague symptom. Pin down, asking the user directly if needed:

| Field | Example |
|---|---|
| **What** is wrong | "Segment X has 0 members" / "Dataset Y stopped receiving data" |
| **Since when** | "since this morning" / "always been this way" / "just noticed" |
| **Expected** vs **actual** | "expected ~40K profiles, seeing 0" |
| **Scope** | one sandbox / one dataset / org-wide |
| **Recent changes** | any schema edits, dataflow changes, credential rotations around the onset time |

A vague symptom ("audiences seem off") produces a vague, unfalsifiable hypothesis list.
Push back and ask for specifics before calling `diagnostics-research`.

---

## Hypothesis Discipline

Every hypothesis fed to `diagnostics-investigator` MUST be falsifiable — phrased so a single
probe can return CONFIRMED or REJECTED, not "maybe" or "possibly." Reject hypotheses like
"something with the schema might be wrong" — reframe as "the field `_tenant.visitCount`
referenced in the PQL was removed from the schema after the audience was last edited."

Rank hypotheses by:
1. **Recency** — anything that changed near the symptom's onset time
2. **Blast radius match** — a hypothesis whose scope matches the symptom's scope (org-wide
   symptom → rule out namespace/sandbox-wide causes before single-object causes)
3. **Cheapest to test first** — prefer a probe that's one API call over one requiring a new
   query or waiting on a batch job

---

## Output Format

```
Diagnostic Session: Segment "Gold Loyalty Members" returning 0 members (since 2026-09-10)

Topology (diagnostics-research):
  Schema: Loyalty Profile (profile-enabled)
  Datasets: Loyalty Profile Dataset (dev), CRM Sync Dataset
  Referenced in PQL: _tenant.loyaltyTier, _tenant.visitCount

Hypotheses tested:
  [REJECTED]  PQL syntax invalid — probe: get_segment, PQL parses cleanly
  [REJECTED]  Event look-back > 30 days — probe: no xEvent clause present
  [CONFIRMED] Field _tenant.visitCount removed from schema on 2026-09-09
              probe: get_schema shows field absent; get_segment shows PQL still references it

Evidence review (diagnostics-evaluator): SUFFICIENT
  — schema diff timestamp (09-09) precedes symptom onset (09-10) by one evaluation cycle
  — field absence is a direct, not correlated, cause of a PQL 0-match

Root Cause:
  Field _tenant.visitCount was removed from the Loyalty Profile schema on 2026-09-09.
  The segment's PQL still references it, causing silent 0-match on the next evaluation.

Fix:
  1. Restore the field, or update the PQL to use the replacement field
  2. Re-run segment evaluation
  3. Add a schema-impact check (see analyze-schema-impact) before future field removals
```

---

## Notes

- Never report a root cause without a confirming probe — a plausible story is not evidence
- If two hypotheses both show CONFIRMED evidence, investigate whether they're the same root
  cause described two ways before reporting either
- Time-box: after 3 rejected hypotheses with no new information, load `diagnostics-knowledge`
  rather than continuing to guess
