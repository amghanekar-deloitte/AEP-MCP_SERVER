---
name: explore-campaigns
description: >
  Explore AJO marketing campaigns — list campaigns, inspect a specific campaign's status,
  schedule, channels, and target audience, and filter by status or channel. Load when the
  user asks "show me our campaigns", "list active campaigns", "find campaign X", "what
  campaigns are scheduled", or "explore campaign Y". Uses mcp__aep__list_campaigns and
  mcp__aep__get_campaign.
---

# Explore Campaigns

## When to Load

- "show me our campaigns", "list all campaigns"
- "find campaign [name]"
- "which campaigns are live / scheduled / completed"
- "explore / inspect campaign X"
- "what campaigns target audience Y"

---

## API Approach

```
mcp__aep__list_campaigns   — list all campaigns in the active sandbox
mcp__aep__get_campaign     — detail for a specific campaign
```

Key response fields:
- `name` — campaign name
- `status` — `DRAFT`, `SCHEDULED`, `LIVE`, `STOPPED`, `COMPLETED`, `FAILED`
- `type` — `SCHEDULED` (one-time or recurring) or `TRIGGERED`
- `audienceId` — target audience
- `channel` — `email`, `sms`, `push`, `inApp`, `directMail`
- `startDate`, `endDate` — scheduling
- `content` — message template reference

---

## Output Format

**List view:**

| Campaign | Status | Channel | Audience | Start | End |
|---|---|---|---|---|---|
| Q3 Gold Loyalty Offer | SCHEDULED | email | Gold Loyalty Members | 2026-09-15 | 2026-09-15 |
| Summer Push Blast | COMPLETED | push | All Mobile Users | 2026-08-01 | 2026-08-01 |
| Abandoned Cart Alert | LIVE | sms | Cart Abandoners | Triggered | — |

Filter by status: show `LIVE` and `SCHEDULED` by default; include `FAILED` and `STOPPED` if requested.

**Detail view:**

```
Campaign: Q3 Gold Loyalty Offer
Status:  SCHEDULED
Type:    Scheduled (one-time)
Channel: email
Surface: email.cvs-aetna.com

Audience: Gold Loyalty Members (ID: abc123 · ~47,400 profiles)
Schedule: 2026-09-15 09:00 UTC

Content: "Your Gold Rewards Are Waiting"
  Subject: Your exclusive Gold benefits inside
  Preview: Hi {firstName}, as a Gold member you've earned...
```

---

## Audience → Campaign Lookup

When the user asks "which campaigns target audience X":
1. Get audience ID from `audience-search`
2. Scan all campaigns' `audienceId` for a match
3. Return matching campaigns with status and schedule
