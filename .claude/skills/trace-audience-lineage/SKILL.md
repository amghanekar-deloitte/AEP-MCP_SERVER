---
name: trace-audience-lineage
description: >
  Show how an AEP audience was built and everywhere it is used downstream — which schemas
  and fields the PQL references, which journeys use it as entry/exit criteria, which
  campaigns target it, and which destinations it is activated to. Load when the user asks
  "trace audience X", "where is audience Y used", "what does this audience depend on",
  "show me the lineage of segment Z", or "downstream impact of audience X".
---

# Trace Audience Lineage

## When to Load

- "trace audience [name or ID]"
- "where is audience X used"
- "what does this audience depend on"
- "show me the full lineage of segment Y"
- "downstream impact of audience X"

---

## Lineage Graph

```
Schema Fields → PQL Expression → Audience Definition
                                        ↓
                    ┌───────────────────┼──────────────────────┐
                 Journeys            Campaigns            Destinations
                 (entry/exit)        (target audience)    (activation)
```

---

## Step 1: Get the audience definition

```
mcp__aep__get_segment   — retrieve PQL expression, evaluationType, profileCount
```

Or search by name: `audience-search` skill.

## Step 2: Trace upstream — what schemas/fields does the PQL reference

Parse the PQL expression:
- Extract field paths from top-level profile predicates → these reference the Profile schema
- Extract field paths inside `xEvent` sub-queries → these reference the ExperienceEvent schema
- Replace `_{tenantId}` with the actual tenant slug from `.env`

Cross-reference against `mcp__aep__list_schemas` to identify which schema/field group each path belongs to.

## Step 3: Trace downstream — where is this audience used

**Journeys:**
```
mcp__aep__list_journeys   — scan journey definitions for audience ID references
```
Look for the audience ID in journey entry conditions (`audienceId`) and exit conditions.

**Campaigns:**
```
mcp__aep__list_campaigns   — scan campaign audience references
```

**Destinations (activations):**
```
mcp__aep__list_dataflows   — filter for dataflows with sourceType=audience, check audienceIds
```

---

## Output Format

```
Audience Lineage: Gold Loyalty Members
ID: 7f3e...
PQL: loyalty.tier = "Gold" and consents.marketing.email.val = "y"
     and (select event from xEvent where event.eventType = "commerce.purchases"
          and event.timestamp occurs <= 30 days before now)
Estimated Size: 47,382 profiles

UPSTREAM DEPENDENCIES
  Schema: Individual Profile
    Fields: loyalty.tier, consents.marketing.email.val
  Schema: ExperienceEvent
    Fields: eventType, timestamp

DOWNSTREAM USAGE
  Journeys (2):
    - Loyalty Upgrade Journey   (entry criteria)
    - Gold Welcome Series       (entry criteria)

  Campaigns (1):
    - Q3 Gold Loyalty Offer     (target audience)

  Destinations (1):
    - Adobe Campaign v8         (batch activation · weekly)
```
