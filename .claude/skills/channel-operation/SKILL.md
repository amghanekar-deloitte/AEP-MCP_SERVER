---
name: channel-operation
description: >
  Explore AJO channel configurations — channel surfaces, sender identities, presets, and
  which channels (email, SMS, push, in-app, direct mail, custom) are set up and active in
  this sandbox. Load when the user asks "what channels do we have", "show channel surfaces",
  "is the SMS channel configured", "channel setup / configuration", or "list AJO channel
  presets". Uses mcp__aep__list_placements and the AJO Surfaces API; most channel setup is
  UI-only, so this skill reports configuration state rather than creating it.
---

# Channel Operation

## When to Load

- "what channels do we have / are configured"
- "show channel surfaces"
- "is [SMS/push/email/direct mail] set up"
- "channel configuration / setup review"
- "list AJO channel presets"

Do NOT load for campaign-specific surface lookup during a publish flow — that's covered
inline by `ajo-campaign`. Load this skill for a broader "what's configured across all
channels" review.

---

## Channel Types in AJO

| Channel | Surface Concept | Typical Use |
|---|---|---|
| **Email** | Channel surface (sender identity, subdomain, reply-to) | Marketing, transactional |
| **SMS** | Sending number / short code | Alerts, OTP, marketing opt-in |
| **Push** | Mobile app registration (iOS/Android) | App re-engagement |
| **In-App** | App placement | In-session messaging |
| **Direct Mail** | Print vendor connection | Physical mail campaigns |
| **Custom Action** | Webhook / external API | Any external system integration |

---

## API Approach

### List channel surfaces (email)

```
GET {AEP_BASE_URL}/journey/campaigns/service/surfaces?channel=email&count=50
Headers: Authorization, x-api-key, x-gw-ims-org-id, x-sandbox-name
```

Repeat with `channel=sms`, `channel=push`, `channel=directMail` for other channel types.

Key fields per surface:
- `name` — surface display name
- `channelRef` — ID used when referencing this surface in a campaign/journey
- `status` — `ACTIVE`, `INACTIVE`, `PENDING_VALIDATION`
- Email-specific: `fromAddress`, `subdomain`, `replyTo`
- SMS-specific: `phoneNumber` / `shortCode`, `countryCode`

### List placements (in-app / push targets)

```
mcp__aep__list_placements   — configured placements for personalization/in-app surfaces
```

### Custom action / webhook channels

Custom actions are configured per-journey-node, not as a standalone channel surface —
check `journey-analyze-custom-action` to inspect webhook endpoints already wired into
live journeys.

---

## Output Format

```
Channel Configuration (sandbox: cvs-aetna)

  Channel      Surfaces Configured    Active    Notes
  ────────────────────────────────────────────────────────────────────
  Email        3                      3         email.cvs-aetna.com (primary)
  SMS          1                      0         PENDING_VALIDATION — number not yet verified
  Push         0                      0         Not configured
  Direct Mail  1                      1         Print vendor: Vendor X (connected)
  In-App       2 placements           2         Home banner, checkout modal

Detail — Email Surfaces:
  Name                        channelRef    Status    From Address              Subdomain
  ─────────────────────────────────────────────────────────────────────────────────────────
  Email - Marketing US        srf-001       ACTIVE    marketing@cvs-aetna.com   email.cvs-aetna.com
  Email - Transactional       srf-002       ACTIVE    noreply@cvs-aetna.com     email.cvs-aetna.com
  Email - Loyalty Program     srf-003       ACTIVE    loyalty@cvs-aetna.com     email.cvs-aetna.com

Flags:
  - SMS surface exists but is not yet validated — campaigns/journeys targeting SMS will fail
  - No Push channel configured — any journey design assuming push notifications needs a
    channel surface created first (Administration > Channels > Channel surfaces, UI-only)
```

---

## Notes

- Channel surface creation is UI-only (Administration → Channels → Channel surfaces) — this
  skill reports what exists, it does not create surfaces
- A journey or campaign referencing a channel with no active surface will fail at publish
  time — cross-check with `troubleshoot-campaign-issues` when a publish failure is reported
- `channelRef` values found here are exactly what `ajo-campaign` needs for its `channelRef`
  field in campaign creation payloads
