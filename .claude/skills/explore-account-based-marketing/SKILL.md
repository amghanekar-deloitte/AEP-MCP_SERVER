---
name: explore-account-based-marketing
description: >
  Explore business accounts in AEP B2B Edition — their journeys, buying groups, product
  interests, and related people. Load when the user asks "show me account X", "explore
  account-based marketing", "find buying groups for account Y", "what journeys is account Z in",
  "account profile details", or "B2B account exploration". For Real-Time CDP B2B Edition only.
  Uses mcp__aep__get_profile_by_identity (account schema), list_journeys, and AJO B2B tools.
---

# Explore Account-Based Marketing

## When to Load

- "show me account [name or ID]"
- "explore account-based marketing"
- "find buying groups for account X"
- "what journeys is account Y in"
- "account profile details"
- "B2B account view"

**Prerequisite**: Org must be provisioned for Real-Time CDP B2B Edition.

---

## B2B Data Model in AEP

```
Account Profile (XDM Business Account)
    ├── Related People (Account-Person Relationship)
    ├── Opportunities (XDM Business Opportunity)
    ├── Campaigns (XDM Business Campaign Member)
    └── Buying Groups (Journey Optimizer B2B)
```

---

## API Approach

### Look up an account profile

```
mcp__aep__get_profile_by_identity
  schema: _xdm.context.account  (NOT _xdm.context.profile)
  namespace: b2b.account, AccountID, or custom account namespace
  id: the account ID value
```

### Find related people (leads/contacts)

```
mcp__aep__get_profile_by_identity
  Look up persons linked via Account-Person Relationship records
  Filter by accountKey.sourceId matching the account ID
```

### Find opportunities

```
Query Service or Profile API against XDM Business Opportunity dataset
  Filter: opportunityKey.sourceId related to the account
```

### Find buying groups (AJO B2B)

```
mcp__aep__get_member_active_journeys   — journeys the account is enrolled in
mcp__aep__get_member_journey_history   — historical journey memberships
```

---

## Output Format

```
Account: Aetna Health Plans (ID: ACC-00001)
Industry: Healthcare
Revenue: $80B
Status: Active

Related People (5):
  Name                  Role              Email                   Journey Status
  ───────────────────────────────────────────────────────────────────────────────
  Jane Smith            VP Marketing      j.smith@aetna.com       In journey
  John Doe              Director, Digital j.doe@aetna.com         Completed
  ...

Open Opportunities (2):
  - Enterprise CDP Renewal · $2.4M · Close: 2026-12-31 · Stage: Negotiation
  - AJO B2B Add-on · $400K · Close: 2026-11-15 · Stage: Proposal

Active Journeys (1):
  - Enterprise Renewal Journey (entry: 2026-09-01 · stage: Negotiation nurture)
```

---

## Notes

- Account audiences CANNOT be created via API on B2B-simplification orgs — must use AEP UI Segment Builder
- Buying group data is managed in AJO B2B Edition, not standard AEP segmentation
- Account profile lookup requires the account identity namespace — check `manage-identity-settings` for the configured namespace code
