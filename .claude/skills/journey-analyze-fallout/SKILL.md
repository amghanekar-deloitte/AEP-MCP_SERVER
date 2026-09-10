---
name: journey-analyze-fallout
description: >
  Analyze where profiles drop off inside an AJO journey — entry count vs. exit count at
  each node, fallout percentage per step, and which branch or wait node loses the most
  profiles. Load when the user asks "where are people dropping off in this journey",
  "journey fallout analysis", "why is completion rate low", "show me the funnel for journey
  X", or "which step loses the most profiles". Queries the journey step events dataset via
  mcp__aep__run_query_sync.
---

# Journey Analyze Fallout

## When to Load

- "where are people dropping off in journey [name]"
- "journey fallout / funnel analysis"
- "why is completion rate low for this journey"
- "which step loses the most profiles"
- "show the drop-off funnel for journey X"

---

## Concept

Every journey step (node entry/exit) is logged as an event to the journey step events
dataset. Fallout analysis aggregates entry counts per node against exit/next-node counts to
build a step-by-step funnel, and flags nodes with abnormally high loss.

---

## API Approach

### Step 1: Resolve journey structure

```
mcp__aep__get_journey   — node graph: node IDs, types, labels, sequence
```

Build the expected node sequence (entry → wait → email → condition → ... → end) so counts
can be mapped to labeled steps, not raw node IDs.

### Step 2: Query journey step events

```
mcp__aep__run_query_sync

SELECT
  nodeId,
  nodeType,
  COUNT(DISTINCT profileId) AS profiles_at_step
FROM journey_step_events
WHERE journeyId = '<journey_id>'
  AND timestamp >= now() - interval '<lookback>' day
GROUP BY nodeId, nodeType
ORDER BY profiles_at_step DESC
```

Adjust the dataset/table name to the org's actual journey step events dataset — confirm via
`explore-datasets` if `journey_step_events` isn't the deployed name.

### Step 3: Compute fallout per step

For each consecutive pair of nodes in the journey graph:

```
fallout_pct = (profiles_at_step[N] - profiles_at_step[N+1]) / profiles_at_step[N] * 100
```

Flag any step with fallout well above the journey's average step-to-step fallout — that's
the node losing disproportionately many profiles.

### Step 4: Branch-specific fallout (condition nodes)

For a condition node, compute the split between the Yes/No paths and compare against
expected distribution (if the condition is based on a known audience trait, cross-check
against that trait's known population split).

---

## Output Format

```
Journey Fallout: Loyalty Upgrade Journey (v3) — last 30 days

  Step                          Entered    Exited    Fallout %
  ──────────────────────────────────────────────────────────────
  Entry (Read Audience)         12,400     12,400    0%
  Wait 1h                       12,400     12,180    1.8%
  Email: Welcome to Gold        12,180     11,950    1.9%
  Condition: opened email?
    -> Yes (SMS: Gold benefits)  4,780      4,690    1.9%
    -> No  (Wait 3d)             7,170      3,020    57.9%   <-- FLAG
  Email: Gold reminder           3,020      2,940    2.6%
  End                            2,940         —        —

Flag: 57.9% fallout on the "No" branch's Wait 3d node — well above the ~2% baseline
seen elsewhere in this journey.

Likely cause: journey timeout or profile exit rule may be triggering before the 3-day
wait completes — check journey timeout setting (ajo-journey: Journey Properties) against
the wait duration. If timeout < step wait + upstream steps, profiles are being ejected
before reaching the next node.

Recommendation: extend journey timeout, or investigate via diagnostics if timeout
setting appears correct but fallout persists.
```

---

## Notes

- A 100% fallout at the very last node before "End" is often correct (that's if you're not
  also counting End as a step) — always exclude terminal nodes from fallout math unless
  fallout is being measured against total journey entrants
- Distinguish fallout from expected branch splits: a condition node splitting 60/40 is not
  fallout, it's routing — only flag loss within a single path, not across branches
- For unusually low volumes, note that with small entry counts, fallout percentages are
  noisy — recommend caution below ~200 profiles per step
- Route to `diagnostics` for root-cause investigation if the flagged node's cause isn't
  obvious from journey config alone (e.g., suspected but unconfirmed timeout issue)
