---
name: explain-audience
description: >
  Explain in plain language what an AEP audience targets and how it was built — translate
  PQL into business English, describe who qualifies and why, and summarize the audience
  for non-technical stakeholders. Load when the user asks "explain audience X in plain English",
  "what does this audience mean", "translate this PQL", "describe this segment to my client",
  or "what customers does audience Y target". Does NOT create or modify audiences.
---

# Explain Audience

## When to Load

- "explain audience [name] in plain English"
- "what does this audience target / mean"
- "translate this PQL for me"
- "describe this segment to my client"
- "what customers qualify for audience X"

---

## Approach

### Step 1: Retrieve the audience

```
mcp__aep__get_segment   — by ID
```

Or search by name via `audience-search` skill.

### Step 2: Parse and translate the PQL

Break the PQL into clauses and translate each to plain English:

| PQL Clause | Plain English |
|---|---|
| `loyalty.tier = "Gold"` | "Is a Gold loyalty member" |
| `consents.marketing.email.val = "y"` | "Has opted in to email marketing" |
| `select event from xEvent where event.eventType = "commerce.purchases" and event.timestamp occurs <= 30 days before now` | "Made at least one purchase in the last 30 days" |
| `not (select event from xEvent where event.eventType = "directMarketing.emailUnsubscribed")` | "Has NOT unsubscribed from email" |
| `personalEmail.address exists` | "Has a valid email address on file" |

Combine with natural conjunctions: "AND" → "and also", "OR" → "or alternatively", "NOT" → "excluding anyone who".

### Step 3: Compose plain-language summary

Structure the explanation as:

**Who qualifies:** one sentence describing the target person
**How they qualify:** bullet list of criteria in plain language
**Who is excluded:** any NOT clauses
**Consent requirements:** which consent flags are checked
**Evaluation type:** when this audience updates (nightly / near-real-time / at the edge)
**Estimated size:** profile count if available

---

## Output Format

```
Audience: Gold Loyalty Members

Who qualifies:
  Gold-tier loyalty program members who opted in to email marketing
  and made at least one purchase in the last 30 days.

Criteria:
  ✓ Is a Gold loyalty tier member
  ✓ Has opted in to email marketing (GDPR/CCPA compliant)
  ✓ Has opted in to data collection
  ✓ Made at least 1 purchase in the last 30 days

Exclusions:
  ✗ None specified

Updates: Batch (refreshed nightly)
Size:    ~47,400 profiles

For client presentation:
  "This audience targets our most engaged Gold members — people
  who actively shop and have said yes to hearing from us by email.
  It refreshes nightly so campaigns always reach the freshest list."
```
