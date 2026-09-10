---
name: audience-creation-flow
description: >
  Primary entry point for end-to-end AEP audience creation — orchestrates field discovery,
  PQL assembly, size estimation, and publishing. Load when the user says "create an audience",
  "build a segment", "I want to define an audience for X", "help me create an AEP audience
  from scratch", or "new audience". Runs a structured pipeline: gather requirements, discover
  relevant XDM fields, compose PQL, estimate size, confirm, then publish. Delegates to
  field-discovery, audience-size-estimate, segment-management, and audience-search skills.
---

# Audience Creation Flow

## Pipeline

```
1. Gather Requirements
2. Field Discovery
3. PQL Assembly
4. Size Estimation
5. Design Review (user confirm)
6. Publish
```

---

## Step 1 — Gather Requirements

Ask the user for:
- **Business purpose**: what customer group and why (e.g., "Gold loyalty members who purchased in the last 30 days")
- **Profile attributes**: static traits (tier, balance, demographics)
- **Behavioral events**: actions with time windows (purchased, viewed, clicked)
- **Consent requirements**: email/SMS marketing, data collection (REQUIRED for any marketing activation)
- **Evaluation type**: batch (nightly), streaming (near-real-time), or edge (sub-second)

Do not ask all at once — collect in 2-3 turns if the user's initial description is sparse.

---

## Step 2 — Field Discovery

Load `field-discovery` skill.

Search the deployed profile-enabled schemas for fields matching the user's criteria:
- Profile attributes → flatten schema `properties`
- Event fields → discover from ExperienceEvent schema, flag as `xEvent-only`

Surface the XDM path for each identified field so the user can confirm before PQL is written.

---

## Step 3 — PQL Assembly

Load `segment-management` skill for PQL syntax rules.

**RULES (non-negotiable):**
- Event criteria → `select event from xEvent where event.eventType = "..." and event.timestamp occurs <= N days before now` sub-query
- Marketing segments → MUST include consent: `consents.marketing.email.val = "y"` and `consents.collect.val != "n"`
- Custom tenant fields → use actual tenant ID slug (from field-discovery, not a placeholder)
- Event look-back → max 30 days (AEP hard limit)

Produce the full PQL expression and show it to the user in a code block.

---

## Step 4 — Size Estimation

Load `audience-size-estimate` skill.

Run the Preview API against the assembled PQL. Report:
- Estimated qualifying profiles
- % of sandbox total

If the estimate is 0: diagnose before proceeding — check look-back window, identity stitching, and whether profile union is materialized.

---

## Step 5 — Design Review Gate (MANDATORY — do not skip)

Present a confirmation summary:

```
Audience Name:   [name]
Description:     [description]
Evaluation Type: [batch | streaming | edge]
Estimated Size:  [N profiles | N%]

PQL:
[full expression]

Consent clauses: [list]
QA criteria:
  + Positive:  [who qualifies]
  - Negative:  [who is excluded]
  ± Edge case: [boundary condition]
```

Ask: "Ready to create this audience in AEP, or would you like to adjust the criteria?"

Wait for explicit confirmation before Step 6.

---

## Step 6 — Publish

Load `segment-management` skill for the REST creation pattern.

Create via:
```
POST {AEP_BASE_URL}/data/core/ups/segment/definitions
```

Save the returned `id` as the audience ID. Report success with the ID and name.

Save design JSON to `output/<ProjectName>/segments/segment-design-{name}.json`.

---

## Handoff Points

- User wants to activate this audience in a journey → hand off to `journey-flow-designer`
- User wants to check an existing audience → hand off to `audience-search`
- User wants to check size only → hand off to `audience-size-estimate`
