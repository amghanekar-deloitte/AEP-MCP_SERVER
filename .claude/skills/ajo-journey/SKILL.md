---
name: ajo-journey
description: Adobe Journey Optimizer email journey design patterns — journey types, entry conditions, email action node configuration, wait logic (time-based and event-based), condition/decision nodes, personalization token syntax, channel surface configuration, and AJO UI navigation guide. Load when designing email journeys.
---

# AJO Journey Design

Load this skill when:

- Designing AJO email journeys
- Generating AJO UI developer guides
- Configuring wait logic or decision nodes
- Writing personalization expressions for journey emails
- Understanding channel surface requirements

Do NOT load this skill for:

- Campaign creation (use ajo-campaign skill)
- Email template content creation (use ajo-email-template skill)
- AEP segment creation (use segment-management skill)

Note: AJO journey canvas building is UI-only — no public REST API exists for creating journeys. Journey design produces step-by-step AJO UI guides for developers to follow.

---

## Journey Types

| Journey Type | Entry Trigger | Use Case |
|---|---|---|
| **Read Audience** | AEP segment evaluation (batch or streaming) | Scheduled outreach, lifecycle campaigns |
| **API-Triggered** | REST API call | Real-time event-triggered, transactional |
| **Event-Triggered (Unitary)** | AEP streaming event | Behavioral triggers (purchase, login, abandon) |

---

## Journey Node Types

### Entry Nodes

| Node | Purpose |
|---|---|
| Read Audience | Segment-triggered entry — reads AEP segment |
| Event | Event-triggered entry — streaming event from AEP |
| API Trigger | API call triggers individual profile entry |

### Action Nodes

| Node | Purpose |
|---|---|
| Email | Send an email using a content template + surface |
| Custom Action | Call external API/webhook |

### Orchestration Nodes

| Node | Purpose |
|---|---|
| Wait | Pause journey for time period or until event |
| Condition | Branch based on profile attribute or event |
| End | Journey exit point |

---

## Entry Configuration: Read Audience

In AJO UI → Journeys → Create Journey → Drag "Read Audience":

| Setting | Description | Where to Set |
|---|---|---|
| Audience | AEP segment to use as entry population | Click "Select Audience" → search segment |
| Identity Namespace | Primary identity for delivery | Select "Email" or matching namespace |
| Scheduling — Once | Run one time on specified date/time | Toggle "Once" → set start date + time |
| Scheduling — Recurring | Repeating run | Toggle "Recurring" → Frequency + Start + End |
| Force re-entrance | Allow profiles to re-enter after completing | Toggle ON + set cooldown period |

---

## Email Action Node Configuration

In AJO UI → Drag "Action" → "Email":

| Setting | Where | Notes |
|---|---|---|
| Label | Node properties panel → Label field | Descriptive name (e.g., "Welcome Email D0") |
| Surface | Node properties → Surface dropdown | Must exist in Administration → Channels |
| Edit Content | Node → "Edit Content" button | Opens Email Designer |
| Select Template | Email Designer → "Select a template" | Choose from Content Templates by name |
| Personalization | Inside Email Designer → </> icon | Profile/contextual attribute tokens |
| Tracking | Node properties → Tracking section | Enable Open + Click tracking |

### Subject Line Personalization

In Email Designer → Subject field → click </> (personalization icon):

```
Hi {{profile.person.name.firstName}}, your {{profile._{TENANT_ID}.loyaltyTier}} benefits await
```

With fallback:

```
Hi {{profile.person.name.firstName default "Valued Customer"}}, your benefits await
```

---

## Wait Node Configuration

### Time-Based Wait (Duration)

In AJO UI → Drag "Wait" → click node:

- Type: **Duration**
- Unit: Hours | Days | Weeks
- Value: Enter numeric value
- Use case: Fixed delay between touchpoints

Examples:

- 1 hour after journey entry (initial processing delay)
- 3 days after email 1 (time for customer to engage)
- 7 days for re-engagement check

### Event-Based Wait

- Type: **Custom** (event-based condition)
- Use case: Wait until customer performs an action OR time limit expires

In AJO UI:

- Type: **Custom**
- Condition: Select event-based condition from expression editor
  - Journey events → Email → Opened / Clicked
  - AEP events → profile attribute change
- Max wait time: Set a timeout (e.g., max 7 days) — profiles take the "timeout path" if event doesn't occur

### Wait Best Practices

| Scenario | Recommended Wait |
|---|---|
| After Read Audience entry | 1 hour (processing buffer) |
| Between marketing emails | 3-7 days minimum |
| Engagement check window | 7 days (wait for open/click) |
| Re-engagement timeout | 14-30 days |
| Transactional email | No wait — immediate send |

---

## Condition Node Configuration

In AJO UI → Drag "Condition" → click node:

1. **Path 1 (True/Yes path)**:
   - Click "Add condition"
   - Use Expression Editor to define condition
   - Examples:
     - Profile: `profile._{TENANT_ID}.loyaltyTier = "Gold"`
     - Event (open): Journey events → Email → Opened = true
     - Segment membership: `inAudience("SEGMENT_ID")`
   - Label the path (e.g., "Opened Email")

2. **Path 2 (Otherwise/No path)**: Auto-created — catches everyone who doesn't match Path 1

3. Connect each path to next action node

### Common Condition Patterns

```
# Email engagement check
journey.email.opened = true

# Loyalty tier branch
profile.loyalty.tier = "Gold" OR profile.loyalty.tier = "Platinum"

# Profile attribute check
profile._{TENANT_ID}.accountBalance > 50000

# Segment membership
inAudience("SEGMENT_UUID")
```

---

## Personalization Token Reference

### Standard Profile Tokens

| Display | AJO Token | XDM Path |
|---|---|---|
| First Name | `{{profile.person.name.firstName}}` | person.name.firstName |
| Last Name | `{{profile.person.name.lastName}}` | person.name.lastName |
| Email | `{{profile.personalEmail.address}}` | personalEmail.address |
| City | `{{profile.homeAddress.city}}` | homeAddress.city |
| Country | `{{profile.homeAddress.countryCode}}` | homeAddress.countryCode |

### Custom Attribute Tokens

| Display | AJO Token | XDM Path |
|---|---|---|
| Loyalty Tier | `{{profile._{TENANT_ID}.loyaltyTier}}` | _{TENANT_ID}.loyaltyTier |
| Account Balance | `{{profile._{TENANT_ID}.accountBalance}}` | _{TENANT_ID}.accountBalance |
| Advisor Name | `{{profile._{TENANT_ID}.advisorName}}` | _{TENANT_ID}.advisorName |

### Conditional Content Block (show/hide based on profile)

In Email Designer → Select component → Personalization:

```jinja2
{% if profile._{TENANT_ID}.loyaltyTier = "Gold" %}
  <div>Gold exclusive offer: ...</div>
{% elsif profile._{TENANT_ID}.loyaltyTier = "Platinum" %}
  <div>Platinum VIP offer: ...</div>
{% else %}
  <div>Member exclusive offer: ...</div>
{% endif %}
```

---

## Channel Surface Configuration

A Channel Surface defines: sender email, sender name, reply-to, header parameters.

### Verify Surface Exists

AJO UI: Administration → Channels → Channel surfaces

| Setting | Typical Value |
|---|---|
| Name | e.g., "Email - Marketing US", "Email - Transactional" |
| Type | Email |
| Subdomain | Must be configured and validated in AJO |
| From email | <noreply@brand.com> |
| From name | Brand Name |
| Reply-to | <reply@brand.com> |
| Header parameters | List-Unsubscribe (required for deliverability) |

Create surface if missing: Administration → Channels → Channel surfaces → Create channel surface

---

## Journey Properties (Global Settings)

In AJO UI → Journey canvas → Journey Properties icon (gear, top right):

| Setting | Description | Recommended Value |
|---|---|---|
| Journey timeout | Max time a profile stays in journey | 30-90 days |
| Profile timeout | Auto-exit after X days of no progress | Enable with 30 days |
| Re-entrance | Allow profiles to re-enter after completing | Configure per business rule |
| Timezone | Journey schedule timezone | Client's primary timezone |

---

## Journey Limits (AJO Platform)

| Limit | Value |
|---|---|
| Max nodes per journey | 50 |
| Max journeys live simultaneously | 100 |
| Max profiles per Read Audience journey | Unlimited (batched internally) |
| Journey hold for profile processing | 1 hour (first entry delay recommended) |

---

## Journey Design Output Format

Journey design docs saved to `output/<ProjectName>/journeys/` include **three files per journey**:

### journey-design-{name}.md

Human-readable AJO UI step-by-step guide:

1. Overview table (name, type, segment, schedule, templates used, surface)
2. Numbered AJO UI steps for each node (exact navigation path + settings)
3. Journey flow Mermaid diagram
4. Email action configuration table
5. Wait logic reference table
6. Personalization token reference
7. Channel surface configuration check
8. Testing checklist

### journey-design-{name}.html

Styled HTML rendering of the .md content — same sections as above, formatted as static HTML using the standard framework style (Segoe UI, #1F4E79 headings, table styles). Written alongside the .md file every time. Used for client sharing and browser-based review without a Markdown renderer.

### journey-design-{name}.json

Machine-readable journey specification:

```json
{
  "journeyBuildSpec": {
    "journeyName": "string",
    "description": "string",
    "entryType": "read | api | event",
    "segmentName": "string — segment name from design",
    "segmentId": "",
    "scheduler": "Once | Daily | Weekly",
    "reEntryWindowDays": 30,
    "steps": [
      {"stepId": "step-1", "type": "wait", "duration": 1, "unit": "Hours"},
      {"stepId": "step-2", "type": "email", "emailTemplateName": "string", "surface": "string"},
      {"stepId": "step-3", "type": "condition", "yesBranch": "step-4", "noBranch": "step-5"},
      {"stepId": "step-4", "type": "email", "emailTemplateName": "string", "surface": "string"},
      {"stepId": "step-5", "type": "end"}
    ],
    "journeyTimeoutDays": 30,
    "publishOnBuild": false
  }
}
```

Rules:

- `segmentId` left blank — resolved from DevPlan at build time
- `publishOnBuild` ALWAYS false in design — never set to true
- `emailTemplateName` MUST be specified for every email step — never leave as TBD

### journey-event-design-{name}.json (event-triggered journeys only)

```json
{
  "journeyEventDesign": {
    "eventName": "string",
    "description": "string",
    "eventType": "unitaryEvent",
    "schema": {"name": "string", "id": "string"},
    "identityNamespace": "string",
    "eventIdCondition": {"expression": "PQL condition", "type": "PQL", "format": "pql/text"},
    "uiCreationSteps": {
      "path": "Journey Optimizer → Administration → Events → Create Event",
      "note": "Journey events are UI-only — no public REST API exists for this resource."
    }
  }
}
```

---

## Journey Design Anti-Patterns

- MUST NOT design a journey without specifying the email template name for every email action node
- MUST NOT design a journey without specifying the channel surface name
- MUST NOT use custom PQL in journey conditions without verifying the field path exists in deployed schema
- MUST NOT set re-entry rules without a cooldown period (duplicate sends risk)
- MUST NOT set journey timeout shorter than the total journey duration (profiles ejected mid-journey)
- MUST NOT leave wait time as "0" for the first email in a Read Audience journey (processing buffer required)
- MUST NOT complete a journey design without writing all three files: .md + .json + .html — all three are required outputs
