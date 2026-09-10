---
name: explore-organization-tags
description: >
  Find AEP organization tags and show which campaigns, audiences, or other objects use them.
  Load when the user asks "show me our tags", "find tag X", "what objects use tag Y",
  "list organization tags", or "tag management". Tags in AEP are used to group and organize
  objects across campaigns and audiences. Uses mcp__aep__list_campaigns filtered by tags
  and the Unified Tags API.
---

# Explore Organization Tags

## When to Load

- "show me our tags"
- "find tag [name]"
- "what campaigns / objects use tag X"
- "list organization tags"
- "tag management / audit"

---

## Tags in AEP

AEP Unified Tags allow grouping objects (campaigns, journeys, audiences) under custom labels
for organization and filtering. Tags are org-wide (not sandbox-scoped).

---

## API Approach

### List all tags in the org

```
GET {AEP_BASE_URL}/tagregistry/tags
Headers: Authorization, x-api-key, x-gw-ims-org-id
```

Key response fields:
- `id` — tag UUID
- `name` — tag name
- `category` — optional grouping category
- `createdAt`, `createdBy`

### Find objects using a tag

```
mcp__aep__list_campaigns   — filter by tagIds
mcp__aep__list_journeys    — filter by tagIds (if supported)
mcp__aep__list_segments    — filter by tagIds (if supported)
```

Campaign filter: `GET /campaign/executions?tagIds=<tagId>`

---

## Output Format

**All tags:**

| Tag Name | Category | Created | Used In |
|---|---|---|---|
| Q3-2026 | Campaign Season | 2026-07-01 | 3 campaigns |
| Loyalty Program | Program | 2026-01-15 | 5 campaigns, 2 journeys |
| CVS Aetna | Client | 2026-01-01 | 12 campaigns |
| TEST | Testing | 2026-05-10 | 2 campaigns |

**Single tag detail:**

```
Tag: Loyalty Program (ID: abc123)
Category: Program
Created: 2026-01-15 by amghanekar@deloitte.com

Used in:
  Campaigns (5):
    - Q3 Gold Loyalty Offer (SCHEDULED)
    - Loyalty Tier Upgrade (LIVE)
    - Gold Welcome Series (COMPLETED)
    - Silver to Gold Nudge (DRAFT)
    - Platinum Retention (COMPLETED)

  Journeys (2):
    - Loyalty Upgrade Journey (LIVE)
    - Gold Welcome Journey (LIVE)
```
