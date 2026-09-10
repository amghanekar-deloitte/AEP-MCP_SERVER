---
name: journey-analyze-conflict
description: >
  Find conflicts between AJO journeys and campaigns competing for the same profiles —
  audience overlap across concurrently live journeys, frequency-capping collisions, and
  re-entry/priority conflicts causing profiles to be excluded or double-messaged. Load when
  the user asks "are these journeys conflicting", "audience overlap between journeys",
  "why did this profile get two messages", "frequency cap issues", or "journey priority
  conflicts". Uses mcp__aep__list_journeys, list_campaigns, and mcp__aep__get_segment.
---

# Journey Analyze Conflict

## When to Load

- "are these journeys conflicting with each other"
- "audience overlap between journey X and Y"
- "why did this profile get messaged twice"
- "frequency cap issues"
- "journey / campaign priority conflicts"

---

## Conflict Types

| Type | Symptom |
|---|---|
| **Audience overlap** | Two live journeys/campaigns share entry audiences — same profile qualifies for both simultaneously |
| **Frequency cap collision** | A profile hits an org- or channel-level send limit because multiple journeys/campaigns are messaging it in the same window |
| **Priority conflict** | Two journeys both want to act on the same profile at the same time with no defined precedence |
| **Re-entry collision** | A profile exits and re-enters the same journey faster than intended due to a short/no cooldown, compounding with another journey's messaging |

---

## API Approach

### Step 1: Enumerate live journeys and campaigns

```
mcp__aep__list_journeys     — filter status = LIVE
mcp__aep__list_campaigns    — filter status = LIVE
```

### Step 2: Resolve each entry audience

```
mcp__aep__get_segment   — for each journey/campaign's entry audienceId, get the PQL
```

### Step 3: Detect audience overlap

Compare PQL definitions pairwise for structural overlap (same base predicates, one being a
superset/subset of another, or shared demographic/behavioral clauses). For a precise
overlap count rather than a structural guess:

```
mcp__aep__run_query_sync

SELECT COUNT(DISTINCT a.profileId) AS overlap_count
FROM segment_membership a
JOIN segment_membership b ON a.profileId = b.profileId
WHERE a.segmentId = '<segment_A_id>' AND b.segmentId = '<segment_B_id>'
```

Adjust to the actual profile-to-segment membership table/dataset name deployed in this org.

### Step 4: Check channel-level frequency caps

```
mcp__aep__get_effective_policies   — data governance / capping policies in effect
```

Frequency capping in AJO is typically configured per-channel or per-campaign-category
(Marketing vs. Transactional) — check whether overlapping journeys share a capping group
or bypass it entirely (e.g., one is Transactional and therefore uncapped).

### Step 5: Check journey priority settings

```
mcp__aep__get_journey   — journey properties may define priority/precedence rules
                           relative to other journeys targeting the same profile
```

If no priority rule exists between two overlapping journeys, flag this explicitly — AJO
does not automatically arbitrate; profiles simply proceed through both independently.

---

## Output Format

```
Journey/Campaign Conflict Analysis (sandbox: cvs-aetna)

Live journeys/campaigns checked: 6 journeys, 3 campaigns

Overlap Detected:
  Journey "Loyalty Upgrade Journey" (audience: Gold Loyalty Members, ~12,400 profiles)
  Journey "Re-engagement Series" (audience: Inactive 30+ Days, ~8,100 profiles)
    -> Overlap: 1,240 profiles in BOTH audiences
    -> Both are Marketing category, both use Email channel
    -> No priority rule defined between these two journeys

Frequency Cap Status:
  Marketing email cap: 3 sends / 7 days (org-wide policy)
  Overlapping profiles (1,240) are eligible to receive up to 2 emails from each journey
  in the same week — combined volume can exceed the 3-send cap, causing AJO to silently
  suppress later sends rather than erroring

Root Cause (for "profile got two messages" reports):
  Profiles in the 1,240-member overlap are legitimately eligible for both journeys with no
  precedence set — this is not a bug, it's an undefined priority configuration.

Recommendation:
  1. Add an exclusion clause to one journey's entry audience (exclude profiles in the
     other journey's active population), or
  2. Define explicit priority in Journey Properties if AJO's precedence feature is
     available in this org, or
  3. Accept the overlap if intentional, but confirm the frequency cap covers combined
     volume across both journeys, not per-journey independently
```

---

## Notes

- Audience overlap alone is not inherently a bug — many programs intentionally allow it;
  only flag it as a problem when paired with a reported symptom (duplicate sends, cap
  breaches, conflicting content) or an explicit "is this designed correctly" question
- Frequency cap enforcement scope (per-campaign vs. org-wide vs. per-channel) varies by org
  configuration — always confirm the actual capping scope via `get_effective_policies`
  rather than assuming
- For a single affected profile's exact message history, use `mcp__aep__get_member_active_journeys`
  and `get_member_journey_history` to see precisely what fired and when, rather than
  inferring from aggregate overlap alone
