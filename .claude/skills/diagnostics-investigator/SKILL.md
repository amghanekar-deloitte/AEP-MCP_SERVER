---
name: diagnostics-investigator
description: >
  Test one specific, falsifiable hypothesis about the cause of an AEP problem using a
  concrete probe (an API call whose result can only mean CONFIRMED or REJECTED). Called
  from the diagnostics loop after diagnostics-research produces a topology map and a
  hypothesis list. Not loaded directly by users — invoked by the diagnostics skill once
  per hypothesis under test.
---

# Diagnostics: Investigator

## When to Load

- Called from `diagnostics` step 4, once per hypothesis in the ranked list
- Never invoked directly by a user — it has no standalone entry point because it requires
  a hypothesis and topology map from the earlier steps

---

## Purpose

Take exactly one hypothesis and design a probe that can only resolve to CONFIRMED or
REJECTED — never "inconclusive" or "probably." If a probe can't be designed to be
falsifiable, the hypothesis is too vague; send it back to be reframed before testing.

---

## Probe Design Rules

1. **One hypothesis per probe.** Do not bundle two hypotheses into one investigation —
   if the probe result is ambiguous, you won't know which hypothesis it addressed.
2. **Prefer direct evidence over correlation.** "The batch failed at the same time the
   symptom started" is correlation. "The batch failed because field X was null, and X is
   a required identity field" is direct evidence — trace the actual causal link.
3. **Pick the cheapest probe that's still conclusive.** An API read beats a new Query
   Service job; a Query Service job beats waiting for a scheduled batch to re-run.
4. **State the falsification condition before running the probe.** Write down "this
   hypothesis is REJECTED if the field IS present in the schema" before calling
   `get_schema` — this prevents post-hoc rationalizing an ambiguous result as confirming.

---

## Common Probe Patterns

| Hypothesis type | Probe |
|---|---|
| Field missing/renamed | `mcp__aep__get_schema` — check field path exists at current version |
| Ingestion failure | `mcp__aep__get_batch` — check `status`, `errors[]` on the specific batch |
| PQL referencing stale field | `mcp__aep__get_segment` + diff against current schema fields |
| Event look-back exceeds cap | Inspect PQL `xEvent` clause window value against 30-day cap |
| Merge policy excludes dataset | `mcp__aep__list_merge_policies` — check `mergePolicyGroup` includes dataset's schema |
| Dataflow stopped running | `mcp__aep__list_flow_runs` — check most recent run status and timestamp |
| Identity not resolving | `mcp__aep__get_identity_cluster` — check expected namespace values are linked |
| Credential/connection broken | `mcp__aep__get_source_connection` / `get_target_connection` — check `connectionSpec` status |
| Segment evaluation stale | Compare `get_segment` evaluationInfo timestamp against dataset's last successful batch |

---

## Output Format

```
Hypothesis: Field _tenant.visitCount was removed from the schema, causing PQL 0-match

Falsification condition: REJECTED if get_schema shows the field present at current version

Probe: mcp__aep__get_schema (Loyalty Profile, version: current)
Result: Field _tenant.visitCount is NOT present. Field group last modified 2026-09-09.

Verdict: CONFIRMED
Direct evidence: get_segment shows the PQL still contains "_tenant.visitCount != null" —
the field it depends on no longer exists in the schema the audience evaluates against.
```

For a rejected hypothesis:

```
Hypothesis: Event look-back window exceeds the 30-day cap

Falsification condition: REJECTED if PQL contains no xEvent clause, or window <= 30 days

Probe: mcp__aep__get_segment — inspect PQL body
Result: PQL contains no xEvent sub-query at all — this is a profile-attribute-only audience

Verdict: REJECTED — hypothesis does not apply to this audience's PQL structure
```

---

## Notes

- Always report both CONFIRMED and REJECTED outcomes back to the calling `diagnostics` loop
  with the probe and result shown — a rejected hypothesis with evidence is progress, not a
  dead end
- If a probe requires a capability that failed to connect (MCP server down), report that as
  a blocked probe, not a REJECTED hypothesis — those are different outcomes
