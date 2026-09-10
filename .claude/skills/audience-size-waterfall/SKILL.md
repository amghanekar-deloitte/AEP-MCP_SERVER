---
name: audience-size-waterfall
description: >
  Decompose a compound PQL expression into sub-predicates and estimate audience size
  at each layer using the AEP Preview API, producing a waterfall breakdown. Load when
  the user asks which condition filters most profiles, wants to see a waterfall of
  audience attrition, wants to decompose a PQL clause by clause, or wants to understand
  how each condition progressively narrows the audience. Requires audience-size-estimate
  for individual Preview API calls.
---

# Audience Size Waterfall

## When to Load

- "show me a waterfall of this PQL"
- "which condition filters out the most profiles"
- "decompose this audience clause by clause"
- "audience attrition / funnel breakdown"

---

## Decomposition Strategy

Given a compound PQL:
```
loyalty.tier = "Gold"
and consents.marketing.email.val = "y"
and (select event from xEvent where event.eventType = "commerce.purchases" and event.timestamp occurs <= 30 days before now)
```

Build cumulative sub-predicates from broadest to narrowest:

| Step | Predicate Added | PQL Evaluated |
|---|---|---|
| 1 | Base (all profiles) | _(no filter — use global total)_ |
| 2 | `loyalty.tier = "Gold"` | `loyalty.tier = "Gold"` |
| 3 | + email consent | `loyalty.tier = "Gold" and consents.marketing.email.val = "y"` |
| 4 | + purchase event | full compound PQL |

---

## Execution

For each row in the waterfall:
1. Build the cumulative PQL by AND-ing clauses left to right
2. Call the Preview API (see `audience-size-estimate` skill for exact API pattern)
3. Record `totalFilteredRows` for that step

For the "Base" row, use the sandbox global profile count from:
```
GET {AEP_BASE_URL}/data/core/ups/preview
```
— this returns `{ "totalRows": N }` with no filtering.

---

## Output Format

```
Audience Size Waterfall
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step  Condition                          Count      Drop       Retained
────  ─────────────────────────────────  ─────────  ─────────  ────────
  0   All profiles (sandbox total)       1,000,000             100.0%
  1   loyalty.tier = "Gold"                200,000   -800,000   20.0%
  2   + email consent = "y"               160,000    -40,000   80.0%
  3   + purchased in last 30 days          47,382   -112,618   29.6%

Final audience: 47,382 profiles (4.7% of sandbox total)
```

- **Drop**: absolute count lost at each step
- **Retained**: % of previous step that passed the filter
- Render as a plain-text table (not markdown table) for readability

---

## PQL Parsing Rules

Split compound PQL at top-level `and` keywords only — do NOT split inside `(select event from xEvent ...)` sub-queries. A sub-query is one atomic predicate.

Simple split heuristic:
1. Tokenize at `and` only when parenthesis depth = 0
2. Each token is one clause

---

## Constraints

- Run Preview API calls sequentially (not in parallel) to avoid rate limits
- Cap at 10 steps; if PQL has more clauses, group the remainder into a final compound step
- If any Preview call returns ERROR or times out, mark that row as `ERROR` and continue
- Mention 30-day event look-back limit if any event sub-query appears in the PQL
