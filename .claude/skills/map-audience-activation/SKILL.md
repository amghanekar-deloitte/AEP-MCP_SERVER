---
name: map-audience-activation
description: >
  Show where each AEP audience is activated — which destinations, journeys, and campaigns
  use it, who activated it, and when. Load when the user asks "where is audience X activated",
  "which destinations receive audience Y", "show me audience activation map", "what's using
  this segment", or "audience activation report". Traces all downstream activations for one
  or all audiences. More activation-focused than trace-audience-lineage (which also covers
  schema dependencies).
---

# Map Audience Activation

## When to Load

- "where is audience [name] activated"
- "which destinations receive this audience"
- "show me the audience activation map"
- "what is using segment X"
- "audience activation report for all segments"

---

## Activation Surfaces to Check

### 1. Destinations (direct activation via dataflows)

```
mcp__aep__list_dataflows   — filter sourceType or check audience IDs in flow spec
```

For each dataflow targeting an audience, retrieve:
- `destinationId` → resolve to destination name via `mcp__aep__list_connections`
- `audienceIds` — list of segments activated to this destination
- `scheduleParams` — batch schedule or streaming

### 2. Journeys (AJO)

```
mcp__aep__list_journeys   — scan for audience references in entry/exit criteria
```

### 3. Campaigns (AJO)

```
mcp__aep__list_campaigns   — scan for audience references
```

---

## Output Format

**Single audience:**

```
Activation Map: Gold Loyalty Members (ID: abc123)

Destinations (2):
  Destination               Type         Schedule       Records Sent  Last Activation
  ─────────────────────────────────────────────────────────────────────────────────────
  Adobe Campaign v8         Batch        Weekly Mon     47,200        2026-09-08
  Google Customer Match     Streaming    Real-time      47,382        Live

Journeys (2):
  - Loyalty Upgrade Journey   (entry: audience membership)
  - Gold Welcome Series       (entry: audience membership)

Campaigns (1):
  - Q3 Gold Loyalty Offer     (target audience · status: scheduled)
```

**All audiences (activation summary):**

| Audience | Destinations | Journeys | Campaigns | Total Uses |
|---|---|---|---|---|
| Gold Loyalty Members | 2 | 2 | 1 | 5 |
| Email Re-engagement | 1 | 1 | 0 | 2 |
| Uncontacted Prospects | 0 | 0 | 0 | 0 (UNUSED) |

Flag unused audiences (0 activations) — candidates for cleanup.
