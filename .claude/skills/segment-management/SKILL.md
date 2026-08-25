---
name: segment-management
description: AEP audience segment design and creation patterns — segment design JSON format, PQL (Profile Query Language) guide with operators and examples, consent/preference attribute requirements, segment API patterns, evaluation types, and QA test criteria. Load when designing or creating AEP segments.
---

# Segment Management

Load this skill when:

- Designing AEP audience segments
- Writing PQL expressions
- Creating segments via AEP Segment Definitions API
- Validating segment logic for consent and business rules
- Generating segment design JSON files

Do NOT load this skill for:

- AEP authentication (use aep-fundamentals)
- Schema design (use xdm-schema-design)

---

## Segment Design JSON Format

Every segment design MUST produce a `segment-design-{name}.json` with this structure:

```json
{
  "segmentDesign": {
    "segmentName": "string — business-friendly name",
    "segmentDescription": "string — one-line audience description",
    "segmentDefinition": "string — full business definition: who qualifies and why",
    "targetAudience": "string — size estimate and business value",
    "evaluationType": "batch | streaming | edge",
    "requiredAttributes": {
      "profileAttributes": [
        {
          "xdmPath": "XDM path to the attribute",
          "condition": "operator and value",
          "description": "business rationale for this condition"
        }
      ],
      "eventAttributes": [
        {
          "eventType": "standard XDM eventType value",
          "timeWindow": "last X days | within X hours",
          "condition": "at least N | exactly N | at most N",
          "description": "what behavior this captures"
        }
      ],
      "consentAndPreferences": [
        {
          "xdmPath": "consent XDM path",
          "condition": "= \"y\" or != \"n\"",
          "description": "regulatory/privacy rationale"
        }
      ]
    },
    "segmentLogicPQL": "full PQL expression as string",
    "segmentCreationAPIBody": {
      "name": "segment name",
      "description": "segment description",
      "expression": {
        "type": "PQL",
        "format": "pql/text",
        "value": "PQL expression"
      },
      "evaluationInfo": {
        "batch": {"enabled": true},
        "continuous": {"enabled": false},
        "synchronous": {"enabled": false}
      },
      "schema": {
        "name": "_xdm.context.profile"
      },
      "payloadSchema": ""
    },
    "qaTestCriteria": {
      "positiveCase": "profile that MUST qualify",
      "negativeCase": "profile that MUST NOT qualify",
      "edgeCase": "boundary condition to verify"
    }
  }
}
```

---

## PQL Guide

PQL (Profile Query Language) is SQL-like but operates on XDM schema paths.

### Operators

| Operator | Usage |
|---|---|
| `=` | Equals |
| `!=` | Not equals |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater than or equal |
| `<=` | Less than or equal |
| `in` | Value in list: `field in ["a", "b", "c"]` |
| `not in` | Value not in list |
| `and` | Logical AND |
| `or` | Logical OR |
| `not` | Logical NOT |
| `exists` | Field exists and is not null |
| `!exists` | Field is null or missing |

### Profile Attribute Paths

```
person.name.firstName
person.name.lastName
person.birthDate
homeAddress.countryCode
homeAddress.city
personalEmail.address
mobilePhone.number
loyalty.tier                              (standard field group)
loyalty.points                            (standard field group)
consents.marketing.email.val              (standard field group)
consents.marketing.sms.val               (standard field group)
consents.collect.val                      (standard field group)
_{TENANT_ID}.customAttribute              (custom field group)
```

### Event Paths

```
eventType
timestamp
commerce.purchases.value
commerce.order.priceTotal
commerce.productListItems.SKU
commerce.productListItems.name
web.webPageDetails.URL
web.webPageDetails.name
web.webInteraction.URL
```

### Time Window Syntax

```
event.timestamp occurs <= X days before now
event.timestamp occurs > 24 hours before now
event.timestamp occurs between [date1] and [date2]
```

### Event Query Pattern

```
select event from xEvent
where event.eventType = "commerce.purchases"
and event.timestamp occurs <= 90 days before now
```

### RULE — events go to Event (`xEvent`), NOT profile attributes

Any criterion based on an ExperienceEvent (a purchase, shipment, page view, email open, etc.) MUST be
expressed as an `xEvent` timeline sub-query — NEVER flattened into a top-level profile-attribute predicate.
Profile attributes (`consents.*`, `person.*`, `homeAddress.*`, `_{TENANT_ID}.*` on the profile schema) go at
the profile level; event fields (`eventType`, `timestamp`, `commerce.*`, and the event schema's own
`_{TENANT_ID}.*`) go INSIDE `select event from xEvent where …`. Mixing an event field into a profile
predicate is invalid — the field does not exist on the profile union.

Custom event fields use the event schema's tenant path inside the sub-query, e.g. an ExperienceEvent
with tenant-custom fields:

```
consents.marketing.email.val = "y"
and (select event from xEvent
     where event.eventType = "commerce.purchases"
     and event._{tenantId}.serviceBaseCode = "PRIORITY_OVERNIGHT"
     and event._{tenantId}.destinationCountryCode = "US"
     and event.commerce.purchases.value >= 1
     and event.timestamp occurs <= 90 days before now)
```

Replace `{tenantId}` with the project's actual IMS tenant (found in the deployment manifest or schema `$id`).


**Identity caveat (must-know for B2B).** An `xEvent` sub-query only matches events that are in the SEGMENTED
entity's timeline — i.e. the event must share an identity with the segment's union. FX Shipping Transaction
events are **account-keyed** (`identityMap.b2b_account`), so they are in the ACCOUNT timeline, NOT the person
timeline. A `_xdm.context.profile` (person) segment with a shipping-event sub-query is structurally correct
but matches **zero people** until the events are also stitched to persons (add a `b2b_person`/`Email`
identity to the event) OR the segment is built on the account audience. Do not "fix" a 0-match by moving the
event field into a profile attribute — that is the wrong pattern this rule forbids.

---

## PQL Examples

### Profile Attribute-Only Segment

```
loyalty.tier = "Gold" and loyalty.points >= 5000
```

### Profile + Event Segment

```
loyalty.tier = "Gold"
and (select event from xEvent
     where event.eventType = "commerce.purchases"
     and event.timestamp occurs <= 90 days before now)
```

### Multi-Event Segment (AND)

```
(select event from xEvent where event.eventType = "web.webpagedetails.pageViews" and event.timestamp occurs <= 30 days before now)
and (select event from xEvent where event.eventType = "commerce.productViews" and event.timestamp occurs <= 30 days before now)
```

### Segment with Consent (REQUIRED for marketing segments)

```
loyalty.tier = "Gold"
and consents.marketing.email.val = "y"
and consents.collect.val != "n"
and (select event from xEvent
     where event.eventType = "commerce.purchases"
     and event.timestamp occurs <= 90 days before now)
```

### Segment Exclusion Pattern

```
loyalty.tier in ["Gold", "Platinum"]
and not (select event from xEvent
         where event.eventType = "directMarketing.emailUnsubscribed"
         and event.timestamp occurs <= 30 days before now)
```

### Null Check

```
personalEmail.address exists
and _{TENANT_ID}.accountBalance > 0
```

---

## Consent Attributes (MANDATORY in all marketing segments)

Every segment intended for marketing activation MUST include consent checks:

| Consent Attribute | XDM Path | Required Condition | Regulation |
|---|---|---|---|
| Email marketing consent | `consents.marketing.email.val` | `= "y"` | GDPR, CCPA, CAN-SPAM |
| Data collection consent | `consents.collect.val` | `!= "n"` | GDPR |
| SMS marketing consent | `consents.marketing.sms.val` | `= "y"` | TCPA, GDPR |
| Personalization consent | `consents.personalize.content.val` | `!= "n"` | GDPR |

Consent values:

- `"y"` = explicitly opted in
- `"n"` = explicitly opted out — EXCLUDE
- `"p"` = pending — treat as not consented unless otherwise configured
- `"u"` = unknown — check business rules

---

## Evaluation Types

| Type | When to Use | Latency |
|---|---|---|
| Batch | Large segments, nightly refresh OK, scheduled campaigns | Updated nightly |
| Streaming (Continuous) | Near-real-time segments for triggered journeys | Updated within minutes |
| Edge | Sub-second personalization, onsite targeting | Milliseconds |

Batch is the default. Enable streaming only when the journey or campaign requires near-real-time profile entry.

---

## Segment Creation — Direct REST API (PRIMARY)

Create segment/audience DEFINITIONS via the Segmentation Service REST API using `.env` credentials — the
SAME auth pattern as every other pipeline stage (schema-processor, dataset-creator, profile-operator,
data-ingestion). Do NOT depend on an MCP UI widget for creation: it is not programmatic and is unavailable
in headless/terminal runs (see "Optional MCP path" below).

### Create a segment definition (REST)

```
POST {AEP_BASE_URL}/data/core/ups/segment/definitions
Headers: Authorization: Bearer {token}, x-api-key, x-gw-ims-org-id, x-sandbox-name,
         Content-Type: application/json, Accept: application/json
```
```json
{
  "name": "<segmentName>",
  "description": "<description>",
  "expression": { "type": "PQL", "format": "pql/text", "value": "<PQL expression>" },
  "schema": { "name": "_xdm.context.profile" },
  "ttlInDays": 30
}
```

Returns the created definition with its `id`. Use `"schema": { "name": "_xdm.context.account" }` for a B2B
account audience. Check existence first: `GET /segment/definitions?limit=100` and match on `name`.

### Segment Definitions / jobs / preview endpoints

```
GET    /data/core/ups/segment/definitions?limit=100        list
GET    /data/core/ups/segment/definitions/{segmentId}      retrieve
PATCH  /data/core/ups/segment/definitions/{segmentId}      update
DELETE /data/core/ups/segment/definitions/{segmentId}      delete
POST   /data/core/ups/preview                              preview / estimate audience size (no definition)
POST   /data/core/ups/segment/jobs                         batch evaluation job (see B2B note below)
```

### Evaluation — batch jobs are SCHEDULE-managed on B2B-simplification orgs

`POST /segment/jobs` triggers on-demand batch evaluation, BUT orgs enabled for **B2B simplification** reject
non-scheduled jobs: `UPAPI-054554-400 "Non-scheduled segment jobs are not allowed for orgs enabled for B2B
simplification."` On those orgs, definitions evaluate on the managed **daily** schedule — do NOT try to kick
a manual job; create the definition and let the schedule run (`GET /data/core/ups/config/schedules`). This is
the same daily-batch mechanism that governs B2B account materialization.

### B2B account audiences & evaluation constraints (hard limits — verified live)

- **Creating B2B-entity audiences via the Segmentation API is DEPRECATED by Adobe — it is not possible.**
  Per Adobe (Segmentation FAQ): *"Creation of audiences using B2B entities using the Segmentation Service
  API is deprecated. You can no longer create audiences using the following B2B entities: Account,
  Account-Person Relation, Campaign, Campaign Member, Marketing List, Marketing List Member, Opportunity,
  and Opportunity-Person Relation."* `POST /segment/definitions` with `schema.name=_xdm.context.account`
  fails with `NEBULA-100116-400 "SDD expression is expected for account audiences."` — that is the API
  rejecting the removed path; NO expression format will make it work. **Account audiences MUST be built in
  the AEP UI Segment Builder (or Journey Optimizer B2B), not via API.** Only PERSON audiences
  (`_xdm.context.profile`) can be created programmatically via `POST /segment/definitions`.
  Source: https://experienceleague.adobe.com/en/docs/experience-platform/segmentation/faq
- **Event look-back is capped at 30 days.** An `xEvent` predicate with a longer window fails:
  `NEBULA-100115-400 "Constraint violated: EVENT_LOOK_BACK_WINDOW_MAX_DAYS, Value: 30"`. Events older than 30
  days cannot be matched at all — so an event predicate over stale/synthetic data (older than 30 days)
  returns 0 regardless of union.
- **Counts are schedule-driven on B2B-simplification orgs.** On-demand `POST /segment/jobs` is blocked
  (`UPAPI-054554-400`) and preview/estimate is constrained, so a synchronous non-zero member count is
  generally NOT obtainable via API on these orgs — membership populates on the managed daily evaluation.
  The account union itself is also empty until the daily entity-resolution job runs (see aep-fundamentals).
- **Net:** to get a non-zero ACCOUNT audience you need (1) the account union materialized (daily job / batch
  segmentation enabled) AND (2) the account-audience SDD expression (UI builder). Neither is forceable
  headlessly on a B2B-simplification sandbox.

### Optional MCP path (VS Code Copilot convenience only)

`mcp_stage_adobe-marketing-agent-mcp-widget` is a VS Code UI widget: it renders to the AEP sidebar panel,
returns empty text to the agent, and requires the USER to complete creation manually. It is NOT programmatic
and is absent in headless/terminal/CI runs. Treat it as an OPTIONAL convenience for interactive VS Code use —
NEVER the sole or default creation path. If used, set sandbox first via `mcp_stage_core-set_sandbox`.

### Common Creation Errors (REST)

| Error | Cause | Fix |
|---|---|---|
| `400` invalid expression | Bad PQL syntax / wrong operator or field path | Validate operators + XDM paths against the deployed schema |
| Unknown field | Field path not in the deployed schema | Check XDM path via Schema Registry; custom fields use `_{TENANT_ID}.field` |
| `400` on `schema.name` | Wrong union name | `_xdm.context.profile` (person) or `_xdm.context.account` (B2B account) |
| `UPAPI-054554-400` | Manual `/segment/jobs` on a B2B-simplification org | Don't run manual jobs — create the definition; it evaluates on the daily schedule |

---

## Segment Design Output Format

Every segment design produces **two files**:

### segment-design-{name}.json

`output/<ProjectName>/segments/segment-design-{name}.json`

Machine-readable segment specification (see Segment Design JSON Format section above).

### segment-design-{name}.html

`output/<ProjectName>/segments/segment-design-{name}.html`

Styled HTML rendering of the segment design — same information as the JSON, formatted for human review. Sections:

1. **Overview** — segment name, description, evaluation type badge (Streaming/Batch/Edge), journey mapping, date
2. **Business Definition** — full segmentDefinition text, target audience, governance notes
3. **Required Attributes** — three sub-tables: Profile Attributes, Event Attributes, Consent & Preferences
4. **PQL Expression** — code block with full PQL + plain-English clause breakdown
5. **API Creation Body** — segmentCreationAPIBody JSON (pretty-printed code block)
6. **QA Test Criteria** — table: Positive Case, Negative Case, Edge Case
7. **Governance & Compliance** — governanceNotes text; PHI callout if RHD fields referenced in PQL

Written alongside the JSON file every time. Used for design review and client sharing.

---

## Segment Design Anti-Patterns

- MUST NOT create a marketing segment without consent attributes in PQL
- MUST NOT use non-standard eventType values (use standard XDM eventType values only)
- MUST NOT use source field names instead of XDM paths (e.g., use `personalEmail.address` not `email`)
- MUST NOT mix profile attributes from different schemas in one segment
- MUST NOT skip qaTestCriteria — positive, negative, and edge cases are required for QA phase
- MUST NOT assume custom fields exist — verify schema is deployed before referencing custom paths
- MUST NOT complete a segment design without writing both files: .json + .html — both are required outputs
