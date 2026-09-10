---
name: explore-customer-journeys
description: >
  Find and explore AJO customer journeys — list journeys, inspect a specific journey's
  configuration, find which audiences a journey uses, check journey status, and browse
  recent journey activity. Load when the user asks "show me our journeys", "find journey X",
  "what journeys use audience Y", "list active journeys", or "explore journey Z". Uses
  mcp__aep__list_journeys and mcp__aep__get_journey for journey navigation and inspection.
---

# Explore Customer Journeys

## When to Load

- "show me our journeys", "list all journeys"
- "find journey [name]"
- "what journeys use audience X"
- "which journeys are active / live"
- "explore / inspect journey Y"

---

## API Approach

```
mcp__aep__list_journeys        — list all journey versions in the sandbox
mcp__aep__list_journey_versions — get all versions of a specific journey
mcp__aep__get_journey          — detail for a specific journey version
```

Note: `list_journeys` may require the AJO Journey Viewer role in Admin Console. If it returns a permissions error, surface that message and suggest the admin grants the role.

Key response fields:
- `name` — journey name
- `status` — `DRAFT`, `LIVE`, `STOPPED`, `CLOSED`, `FINISHED`
- `version` — version number
- `entryConditions` — audience or event that triggers entry
- `actions` — channels used (email, SMS, push, wait, condition nodes)

---

## Output Format

**List view:**

| Journey | Status | Version | Entry Type | Audience / Event | Last Modified |
|---|---|---|---|---|---|
| Loyalty Upgrade Journey | LIVE | 3 | Audience | Gold Loyalty Members | 2026-09-01 |
| Welcome Series | LIVE | 1 | Audience | New Signups | 2026-08-15 |
| Abandoned Cart | DRAFT | 2 | Event | commerce.checkouts | 2026-09-08 |

**Detail view (single journey):**

```
Journey: Loyalty Upgrade Journey (v3)
Status:  LIVE
Entry:   Audience — Gold Loyalty Members (batch · nightly)

Nodes:
  Entry → Wait 1h → Email: "Welcome to Gold" → Condition: opened?
    Yes → SMS: "Your Gold benefits" → Exit
    No  → Wait 3d → Email: "Gold reminder" → Exit

Channels used: email, SMS
Est. daily entries: ~500 profiles
```

---

## Audience → Journey Lookup

When the user asks "what journeys use audience X":
1. Get the audience ID from `audience-search`
2. Scan all journeys' entry conditions for that audience ID
3. Return matching journey names and statuses
