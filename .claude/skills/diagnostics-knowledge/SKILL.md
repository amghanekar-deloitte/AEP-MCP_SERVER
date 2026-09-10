---
name: diagnostics-knowledge
description: >
  Search AEP/AJO documentation and known failure-mode patterns for a symptom that has
  exhausted the current hypothesis list with no confirmed root cause. Called from the
  diagnostics loop when diagnostics-investigator has rejected every generated hypothesis.
  Also usable directly when the user asks "is this a known AEP issue/limitation" or "what
  does this AEP error mean".
---

# Diagnostics: Knowledge

## When to Load

- Called from `diagnostics` when 3+ hypotheses have been REJECTED with no new lead
- Directly: "is this a known AEP limitation / issue"
- Directly: "what does this AEP/AJO error code mean"

---

## Purpose

When topology-driven hypotheses run out, the cause is often a platform-level constraint or
known behavior rather than something specific to this org's configuration — a hard limit,
an undocumented edge case, or a known bug. This step searches outward instead of inward.

---

## Search Approach

1. **Extract the signature** — the exact error code, error message, or precise symptom
   phrasing (e.g., `UPAPI-054554-400`, "segment evaluation stuck IN_PROGRESS").
2. **Search Adobe Experience League documentation** for the signature and the feature area
   (Segmentation, RTCDP, AJO, Query Service, Flow Service) via WebSearch/WebFetch.
3. **Check known AEP platform constraints** already captured in project memory before
   searching externally — many hard limits are already documented from prior sessions
   (event look-back caps, B2B-simplification API restrictions, etc.).
4. **Cross-reference the symptom against this framework's own skill notes** — several
   skills (`troubleshoot-audience-issues`, `analyze-data-import-failures`,
   `troubleshoot-campaign-issues`) already encode known gotchas; check those before an
   external search.

---

## Known Constraint Reference (check first, before searching externally)

| Symptom pattern | Known cause |
|---|---|
| PQL with `xEvent` returns 0 unexpectedly | Event look-back window exceeds 30-day hard cap — fails silently, no error |
| `POST /segment/jobs` returns `UPAPI-054554-400` | Org is on B2B-simplification — on-demand evaluation blocked, batch/nightly only |
| B2B account audience creation fails via API | Account audiences cannot be created via API on B2B-simplification orgs — UI Segment Builder required |
| Preview API count differs from published segment count by a few % | Preview is an estimate (±5%), not authoritative — expected variance, not a bug |
| Schema PATCH fails with wrong content-type error | Schema Registry PATCH requires `application/json-patch+json`, not `application/json` |
| Batch upload silently rejected or malformed | Batch ingestion body must be `application/octet-stream`, not multipart |
| Row read from a dataset returns nothing via Data Access API | Use Query Service (Postgres interface) to read rows instead — Data Access API path is not reliable for this |
| Offer-decisioning rule/collection changes not reflected | UI-published offer changes have a propagation delay — re-check after a short wait before treating as broken |

---

## Output Format

```
Knowledge Search: "segment evaluation stuck IN_PROGRESS for 6+ hours"

Checked against known constraint reference: no exact match

External search results:
  - Adobe Experience League: "Segment evaluation job monitoring" — documents expected
    evaluation duration scales with profile store size; jobs over ~50M profiles can run
    2-4 hours during a full batch evaluation, not necessarily stuck
  - No documented bug matching "stuck indefinitely" for this AEP version

Recommendation:
  Not a known failure mode — this looks like an actual stuck job rather than expected
  behavior. Escalate: check mcp__aep__get_segment_job status and timestamps directly;
  if truly stalled past 2x normal duration, this needs an Adobe support case, not a
  configuration fix.
```

---

## Notes

- If a documentation search confirms the symptom is expected platform behavior (not a bug),
  report that clearly — "this is not a defect" is a valid diagnostic conclusion
- If nothing matches internally or externally, say so explicitly and recommend escalation
  (Adobe support) rather than inventing a plausible-sounding but unverified explanation
- Feed anything found back into `diagnostics` as a new hypothesis to test with
  `diagnostics-investigator` — a documentation match is a lead, not itself a confirmed root
  cause for this specific instance
