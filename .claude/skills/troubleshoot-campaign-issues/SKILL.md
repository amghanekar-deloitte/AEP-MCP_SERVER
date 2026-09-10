---
name: troubleshoot-campaign-issues
description: >
  Find out why an AJO campaign failed to publish, stop, or deliver correctly. Load when
  the user says "why did my campaign fail", "campaign not publishing", "campaign didn't send",
  "campaign stopped unexpectedly", "campaign delivery issues", or "troubleshoot campaign X".
  Diagnoses surface configuration, audience issues, content approval, channel surface errors,
  and scheduling problems using mcp__aep__list_campaigns and mcp__aep__get_campaign.
---

# Troubleshoot Campaign Issues

## When to Load

- "why did my campaign fail to publish"
- "campaign didn't send / not delivering"
- "campaign stopped unexpectedly"
- "troubleshoot campaign [name]"

---

## Diagnostic Checklist

### Step 1: Get campaign state

```
mcp__aep__get_campaign   — full campaign config and current status
```

Key status values: `DRAFT`, `SCHEDULED`, `LIVE`, `STOPPED`, `COMPLETED`, `FAILED`

### Step 2: Check common failure modes

| Issue | Signal | Check |
|---|---|---|
| Audience empty | `audienceId` → get_segment → profileCount = 0 | Run `troubleshoot-audience-issues` |
| Channel surface misconfigured | `surfaceId` invalid or not approved | Verify in AJO > Administration > Channels |
| Content not approved | Content status pending review | Governance/brand approval workflow |
| Scheduled in the past | `startDate` < now with status DRAFT | Update schedule |
| Consent policy blocking | Data governance policy applied | Check `mcp__aep__get_effective_policies` |
| Frequency cap hit | Profile has received too many messages | Check frequency capping rules |
| Journey conflict | Profile already in a conflicting journey | Check for priority conflicts |

### Step 3: Check the target audience

```
mcp__aep__get_segment   — retrieve profileCount and PQL
```

If `profileCount = 0`: surface this as the likely root cause and hand off to `troubleshoot-audience-issues`.

### Step 4: Validate channel surface

The campaign's `surface` (email subdomain, SMS number, push app) must be active and approved in AJO.
```
mcp__aep__list_campaigns   — surface reference visible in campaign config
```
If the surface is inactive, the campaign cannot send.

---

## Output Format

```
Campaign Troubleshoot: Q3 Gold Loyalty Offer
Status: FAILED (never delivered)

Diagnostic Results:
  [OK] Campaign config is valid
  [OK] Schedule: 2026-09-15 09:00 UTC (future)
  [FAIL] Audience: Gold Loyalty Members → profileCount = 0
         → Root cause: audience empty due to ingestion failure (see troubleshoot-audience-issues)
  [OK] Channel surface: email.cvs-aetna.com (active)
  [OK] Content: approved

Root Cause:
  Campaign audience has 0 qualifying profiles. Ingestion failure on 2026-09-10 left
  the profile dataset stale — no profiles qualify for the Gold tier audience.

Fix:
  1. Resolve profile dataset ingestion failure
  2. Wait for or trigger nightly audience evaluation
  3. Verify profileCount > 0 before campaign send date
```
