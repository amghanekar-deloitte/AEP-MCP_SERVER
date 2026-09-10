---
name: find-audience-fields
description: >
  Find the specific data fields that can be used to build or target a described audience
  in AEP — given a business description of who to target, discover which XDM fields and
  paths to use in PQL. Load when the user says "what fields do I need to target people
  who X", "which fields support this audience idea", "I want to target customers who did Y
  — what fields do I need", or "find the right fields for this audience". Bridges business
  language to XDM paths.
---

# Find Audience Fields

## When to Load

- "what fields do I need to target [business description]"
- "I want to target customers who did X — what XDM fields"
- "which fields support this audience idea"
- "find me the right fields to build an audience for [use case]"

---

## Approach

This skill bridges a business description → XDM field discovery.

### Step 1: Parse the business description

Extract the key criteria the user described:
- Profile traits: age, location, tier, balance, plan type, demographics
- Behavioral events: purchases, logins, page views, email opens, specific actions
- Consent requirements: marketing channel, data collection
- Time windows: "in the last 30 days", "since January"

### Step 2: Map to XDM field categories

| Business Concept | XDM Field Category | Example Paths |
|---|---|---|
| Name / identity | `person.*` | `person.name.firstName`, `personalEmail.address` |
| Demographics | `person.*` | `person.birthDate`, `homeAddress.countryCode` |
| Loyalty / tier | `loyalty.*` or tenant | `loyalty.tier`, `loyalty.points`, `_{t}.membershipTier` |
| Consent / opt-in | `consents.*` | `consents.marketing.email.val`, `consents.collect.val` |
| Purchase behavior | xEvent: `commerce.*` | `event.commerce.purchases.value`, `event.eventType="commerce.purchases"` |
| Page views | xEvent: `web.*` | `event.web.webPageDetails.URL`, `event.eventType="web.webpagedetails.pageViews"` |
| Custom fields | `_{tenantId}.*` | Must discover at runtime |

### Step 3: Discover actual field paths

Load `field-discovery` skill to search deployed schemas for each concept:
- Search by concept keyword (e.g., "tier", "balance", "purchase")
- Return actual XDM path + schema + standard/custom flag

---

## Output Format

```
Fields for: "Gold loyalty members who purchased in the last 30 days and opted in to email"

  Concept              XDM Path                         Schema               Type
  ─────────────────────────────────────────────────────────────────────────────────
  Loyalty tier         loyalty.tier                     Individual Profile   string
  Email consent        consents.marketing.email.val     Individual Profile   string
  Data collection      consents.collect.val             Individual Profile   string
  Purchase event       event.eventType (="commerce.purchases")  ExperienceEvent  string (xEvent)
  Purchase timestamp   event.timestamp                  ExperienceEvent      datetime (xEvent)

PQL template using these fields:
  loyalty.tier = "Gold"
  and consents.marketing.email.val = "y"
  and consents.collect.val != "n"
  and (select event from xEvent
       where event.eventType = "commerce.purchases"
       and event.timestamp occurs <= 30 days before now)
```

Hand off to `audience-creation-flow` if the user wants to proceed to build the audience.
