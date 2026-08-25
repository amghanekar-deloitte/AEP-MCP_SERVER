---
name: aep-fundamentals
description: Core Adobe Experience Platform concepts, API patterns, authentication, schema registry, dataset catalog, data ingestion, and sandbox management. Load this skill when working on any AEP integration task, API call, or pipeline stage that interacts with AEP services.
---

# AEP Fundamentals

Load this skill when:
- Implementing any pipeline stage that calls AEP APIs
- Designing or reviewing AEP client code
- Troubleshooting AEP API errors
- Configuring authentication or sandbox context
- Working with the AEP MCP servers

Do NOT load this skill for:
- Pure data analysis tasks with no AEP interaction
- Mermaid ERD generation (use xdm-schema-design instead)
- Quality scoring methodology (use data-quality-scoring instead)

---

## AEP Core Concepts

### Experience Data Model (XDM)

XDM is the standardized data model for Adobe Experience Platform. All data ingested into AEP must conform to an XDM schema.

Key primitives:
- **Class**: The base behavior of a schema (XDM Individual Profile, XDM ExperienceEvent, XDM Record)
- **Field Group**: A reusable set of fields that can be added to schemas. Standard field groups are provided by Adobe; custom field groups are tenant-defined.
- **Data Type**: A reusable structure used as a field type within field groups (e.g., Address, Phone Number, Geo Coordinates)
- **Schema**: A composition of one class + one or more field groups. Schemas define the structure of datasets.
- **Identity Descriptor**: Marks a field as an identity field (e.g., email, ECID, CRM ID) with a namespace
- **Relationship Descriptor**: Defines a relationship between two schemas

### Sandboxes

AEP uses sandboxes to isolate datasets, schemas, and other resources:
- Each API call must include an `x-sandbox-name` header
- Sandbox name is always read from configuration, never hardcoded
- Production and development sandboxes have different lifecycle rules

### Organizations

- Each API call must include an `x-gw-ims-org-id` header with the IMS Organization ID
- Organization ID is always read from configuration

---

## Authentication

AEP uses IMS (Identity Management Service) OAuth for API authentication.

### Token Flow

1. Client sends credentials to `{IMS_URL}/ims/token/v3`
2. Required parameters: `client_id`, `client_secret`, `grant_type=client_credentials`, `scope=openid,session,AdobeID,read_organizations,additional_info.projectedProductContext`
3. Response includes `access_token` with expiry
4. All subsequent API calls include `Authorization: Bearer {access_token}`

### Required Headers (every AEP API call)

```
Authorization: Bearer {access_token}
x-api-key: {client_id}
x-gw-ims-org-id: {org_id}
x-sandbox-name: {sandbox_name}
Content-Type: application/json
Accept: application/json
```

### Configuration Requirements

All authentication values MUST come from the `.env` file at the project root:
- `AEP_IMS_URL` — IMS token endpoint base URL
- `AEP_CLIENT_ID` — API client ID
- `AEP_CLIENT_SECRET` — API client secret
- `AEP_ORG_ID` — IMS organization ID
- `AEP_SANDBOX_NAME` — target sandbox name
- `AEP_BASE_URL` — AEP API base URL (e.g., platform endpoint)

**MANDATORY**: ALWAYS source `.env` before any AEP API call:
```bash
source .env
ACCESS_TOKEN=$(curl -s -X POST "${AEP_IMS_URL}/ims/token/v3" \
  -d "client_id=${AEP_CLIENT_ID}&client_secret=${AEP_CLIENT_SECRET}&grant_type=client_credentials&scope=openid,session,AdobeID,read_organizations,additional_info.projectedProductContext" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

**NEVER** use MCP server authentication for AEP API calls — always use `.env` credentials directly.
**NEVER** hardcode any of these values in source code, agent prompts, skills, or configuration files committed to version control.

---

## Schema Registry API

Base path: `{AEP_BASE_URL}/data/foundation/schemaregistry`

### Key Endpoints

**List schemas**
```
GET /tenant/schemas
Accept: application/vnd.adobe.xed-id+json
```

**Create schema**
```
POST /tenant/schemas
Content-Type: application/json
```

Request body structure:
```json
{
  "type": "object",
  "title": "Schema Title",
  "description": "Schema description",
  "allOf": [
    { "$ref": "https://ns.adobe.com/xdm/context/profile" },
    { "$ref": "https://ns.adobe.com/{TENANT_ID}/mixins/{field_group_id}" }
  ],
  "meta:extends": [
    "https://ns.adobe.com/xdm/context/profile",
    "https://ns.adobe.com/{TENANT_ID}/mixins/{field_group_id}"
  ]
}
```

**Create field group**
```
POST /tenant/fieldgroups
Content-Type: application/json
```

**Create data type**
```
POST /tenant/datatypes
Content-Type: application/json
```

**Get schema by ID**
```
GET /tenant/schemas/{SCHEMA_ID}
Accept: application/vnd.adobe.xed-full+json; version=1
```

### Accept Header Variants

- `application/vnd.adobe.xed-id+json` — returns only `$id` and `meta:altId`
- `application/vnd.adobe.xed+json` — returns schema with `$ref` preserved
- `application/vnd.adobe.xed-full+json` — returns fully resolved schema
- `application/vnd.adobe.xed-notext+json` — returns without title/description
- Append `; version=1` to get the latest minor version of a major version

### Schema Composition Rules

- A schema MUST have exactly one class
- A schema CAN have multiple field groups
- Field groups are scoped to a class — a profile field group cannot be added to an ExperienceEvent schema
- Custom field groups use the tenant namespace: `https://ns.adobe.com/{TENANT_ID}/mixins/`
- Custom schemas use the tenant namespace: `https://ns.adobe.com/{TENANT_ID}/schemas/`
- Once a schema is used by a dataset, breaking changes are restricted

---

## Dataset Catalog API

Base path: `{AEP_BASE_URL}/data/foundation/catalog`

### Key Endpoints

**Create dataset**
```
POST /dataSets
Content-Type: application/json
```

Request body:
```json
{
  "name": "Dataset Name",
  "description": "Dataset description",
  "schemaRef": {
    "id": "https://ns.adobe.com/{TENANT_ID}/schemas/{SCHEMA_ID}",
    "contentType": "application/vnd.adobe.xed-full+json; version=1"
  },
  "fileDescription": {
    "persisted": true,
    "containerFormat": "parquet",
    "format": "parquet"
  },
  "tags": {
    "unifiedProfile": ["enabled:true"],
    "unifiedIdentity": ["enabled:true"]
  }
}
```

**List datasets**
```
GET /dataSets?limit=10&properties=name,schemaRef
```

**Get dataset by ID**
```
GET /dataSets/{DATASET_ID}
```

### Profile-Enabling a Dataset (NEVER AUTO-ENABLE)

**NEVER auto-enable Profile on any schema or dataset.** Deploy all schemas and create all datasets with Profile DISABLED. After ALL deployment is complete, ASK the user if they want to enable Profile. Only proceed after explicit confirmation naming exact schemas/datasets. This is a MANDATORY protocol — no exceptions.

When the user approves Profile enablement, BOTH the schema and dataset must be enabled:

**Step 1 — Enable schema for Profile union:**
```
PUT /tenant/schemas/{SCHEMA_ID}
```
With `"meta:immutableTags": ["union"]` in the request body.

**Step 2 — Enable dataset with Profile tags:**
```json
{
  "tags": {
    "unifiedProfile": ["enabled:true"],
    "unifiedIdentity": ["enabled:true"]
  }
}
```

Include these tags at dataset creation time OR patch them via:
```
PATCH /dataSets/{DATASET_ID}
Content-Type: application/json

{
  "tags": {
    "unifiedProfile": ["enabled:true"],
    "unifiedIdentity": ["enabled:true"]
  }
}
```

**IMPORTANT:** One without the other is incomplete — always enable BOTH schema and dataset.

**Step 3 — Enable granular profile processing flag (CRITICAL):**

After setting `unifiedProfile` and `unifiedIdentity` tags, you MUST also flip the internal granular processing flag. By default, datasets are created with `acp_granular_plugin_validation_flags: ["identity:enabled", "profile:disabled"]`. The `profile:disabled` flag prevents the Profile pipeline from processing ingested batches — data lands in the data lake but is NEVER sent to the Real-Time Customer Profile store.

Patch the granular flag to enable profile processing:
```
PATCH /dataSets/{DATASET_ID}
Content-Type: application/json

{
  "tags": {
    ... (preserve all existing tags) ...
    "acp_granular_plugin_validation_flags": ["identity:enabled", "profile:enabled"]
  }
}
```

**WARNING:** The AEP UI sets this flag automatically, but the API does NOT. If you enable Profile via API only (setting `unifiedProfile`/`unifiedIdentity`) without flipping this granular flag, identity processing runs but profile store ingestion is silently skipped. Always verify this flag after enabling Profile via API.

### Dataset Creation Protocol (MANDATORY)

Before creating any dataset:
1. **CHECK FOR DUPLICATES FIRST**: Query `GET /dataSets?properties=name,schemaRef&limit=100` and check if a dataset with the same name OR same schemaRef already exists. If it does, REUSE it — NEVER create a duplicate. ASK the user if ambiguous.
2. Verify the schema exists and is valid
3. **DO NOT enable Profile** — create ALL datasets with Profile DISABLED (no unifiedProfile/unifiedIdentity tags). Profile enablement is a separate step requiring explicit user approval.
4. Verify dataset creation includes `fileDescription` with parquet format
5. After creation, verify by querying back — confirm exactly ONE dataset per schema

---

## Data Ingestion API

Base path: `{AEP_BASE_URL}/data/foundation/import`

### Batch Ingestion Flow

1. **Create batch**
```
POST /batches
Content-Type: application/json
```
```json
{
  "datasetId": "{DATASET_ID}",
  "inputFormat": { "format": "json" }
}
```

2. **Upload file to batch**
```
PUT /batches/{BATCH_ID}/datasets/{DATASET_ID}/files/{FILE_NAME}
Content-Type: application/octet-stream
```

3. **Signal batch completion**
```
POST /batches/{BATCH_ID}?action=COMPLETE
```

4. **Monitor batch status**
```
GET /batches/{BATCH_ID}
```

Batch statuses: `loading` > `staging` > `success` / `failed`

### Data Format Requirements

- JSON ingestion expects newline-delimited JSON (NDJSON) or JSON arrays
- Each record must conform to the dataset's XDM schema
- Identity fields must be populated for profile-enabled datasets
- Timestamps should be ISO 8601 format
- **identityMap entries MUST include `authenticatedState`** for Profile Service to process records:
  ```json
  {
    "identityMap": {
      "Email": [{
        "id": "user@example.com",
        "authenticatedState": "ambiguous",
        "primary": true
      }]
    }
  }
  ```
  Without `authenticatedState`, batch-ingested data may land in the data lake but NOT be processed into Real-Time Customer Profile. Valid values: `"ambiguous"`, `"authenticated"`, `"loggedOut"`.

### ExperienceEvent eventType Mapping (MANDATORY)

The `eventType` field on ExperienceEvent schemas is a free-form string, but **AEP UI only recognizes standard XDM event type values**. Using non-standard values (e.g., `pageViews`, `emailBounce`) causes events to display as "Unknown Event" in the AEP UI.

**ALWAYS map source event types to standard XDM eventType values AND set the corresponding XDM metric field:**

| Common Source Value | XDM eventType | XDM Metric Field (set `value: 1`) |
|---|---|---|
| pageViews, pageView | `web.webpagedetails.pageViews` | `web.webPageDetails.pageViews` |
| productViews, productView | `commerce.productViews` | `commerce.productViews` |
| checkouts, checkout | `commerce.checkouts` | `commerce.checkouts` |
| purchases, purchase | `commerce.purchases` | `commerce.purchases` |
| linkClicks, linkClick | `web.webinteraction.linkClicks` | `web.webInteraction.linkClicks` |
| webVisits, webVisit | `web.webpagedetails.pageViews` | `web.webPageDetails.pageViews` |
| emailOpened, emailOpen | `directMarketing.emailOpened` | `directMarketing.emailOpened` |
| emailClicked, emailClick | `directMarketing.emailClicked` | `directMarketing.emailClicked` |
| emailBounce, emailBounced | `directMarketing.emailBounced` | `directMarketing.emailBounced` |
| emailUnsubscribed | `directMarketing.emailUnsubscribed` | `directMarketing.emailUnsubscribed` |
| emailSent, emailDelivered | `directMarketing.emailSent` | `directMarketing.emailSent` |
| addToCart, cartAdd | `commerce.productListAdds` | `commerce.productListAdds` |
| removeFromCart | `commerce.productListRemovals` | `commerce.productListRemovals` |
| saveForLater | `commerce.productListSaves` | `commerce.productListSaves` |
| impressions | `advertising.impressions` | `advertising.impressions` |

**Example — correct event transform:**
```json
{
  "eventType": "commerce.purchases",
  "commerce": {
    "purchases": { "value": 1 },
    "order": { "purchaseID": "ORD-123", "priceTotal": 99.99 }
  }
}
```

If a source event type does not map to any standard value, use a custom dotted string (e.g., `custom.loyaltyPointsEarned`) — but it will still show as "Other" in the AEP UI timeline.

---

## Identity Namespace API

Base path: `{AEP_BASE_URL}/data/core/idnamespace`

**CRITICAL**: The correct endpoint for listing and creating namespaces is `/identities`, NOT `/namespaces`. The `/namespaces` path returns HTML 404 from openresty. Agents, skills, and scripts MUST use `/identities`.

### Key Endpoints

**List all namespaces (GET)**
```
GET /data/core/idnamespace/identities
```
Returns array of all namespaces (standard + custom) for the org/sandbox.

**Create custom namespace (POST)**
```
POST /data/core/idnamespace/identities
Content-Type: application/json
```
```json
{
  "name": "Display Name",
  "code": "UniqueCode",
  "idType": "Cross_device"
}
```
Valid `idType` values: `Cross_device`, `Cookie`, `Device`, `Non-people`.

**Response includes**: `id` (numeric), `code`, `status` (ACTIVE), `namespaceType` (Custom), `idType` (CROSS_DEVICE).

### B2B Namespaces (apply ONLY for B2B use cases)

Create these ONLY when the use case is genuinely B2B (models business Accounts / Opportunities /
Campaigns / Marketing Lists / Account-Person relations, or targets RT-CDP B2B Edition). For standard
B2C / Individual-Profile projects, do NOT create B2B namespaces — use standard namespaces (Email,
Phone, ECID) or a single custom `CROSS_DEVICE` namespace. See the B2B detection gate in
`xdm-schema-design`.

**The idType MUST match the entity type.** A B2B Account keyed by a `CROSS_DEVICE` namespace will NOT
materialize in the Business Account union. `idType` is immutable after creation — you cannot convert a
`CROSS_DEVICE` namespace into a `B2B_ACCOUNT` one; you must create a new namespace (or reset the sandbox).

Standard B2B namespaces (codes/idTypes from Adobe's B2B auto-generation utility):

| name                            | code                              | idType                   |
| ------------------------------- | --------------------------------- | ------------------------ |
| B2B Account                     | `b2b_account`                     | `B2B_ACCOUNT`            |
| B2B Person                      | `b2b_person`                      | `CROSS_DEVICE`           |
| B2B Account Person Relation     | `b2b_account_person_relation`     | `B2B_ACCOUNT_PERSON`     |
| B2B Opportunity                 | `b2b_opportunity`                 | `B2B_OPPORTUNITY`        |
| B2B Opportunity Person Relation | `b2b_opportunity_person_relation` | `B2B_OPPORTUNITY_PERSON` |
| B2B Campaign                    | `b2b_campaign`                    | `B2B_CAMPAIGN`           |
| B2B Campaign Member             | `b2b_campaign_member`             | `B2B_CAMPAIGN_MEMBER`    |
| B2B Marketing List              | `b2b_marketing_list`              | `B2B_MARKETING_LIST`     |
| B2B Marketing List Member       | `b2b_marketing_list_member`       | `B2B_MARKETING_LIST_MEMBER` |

Create via the SAME endpoint as any namespace (`POST /data/core/idnamespace/identities`). Example B2B
Account namespace body:

```json
{
  "name": "B2B Account",
  "code": "b2b_account",
  "idType": "B2B_ACCOUNT",
  "description": "Namespace B2B Account created for B2B ingestion purpose"
}
```

The B2B identity fields these namespaces attach to (`accountKey.sourceKey`, `b2b.personKey.sourceKey`,
`accountPersonKey.sourceKey`) and their identity/relationship descriptors are documented in
`xdm-schema-design` → "B2B Edition Schema Architecture".

### Namespace Pre-ingestion Gate (MANDATORY)

Before ingesting any entity, all identity namespaces referenced in identityMap fields MUST exist in AEP. A missing namespace causes `adobe_uis_export_status: INVALID` on ALL profile-enabled batches — not just the entity using that namespace.

Check and auto-create pattern:
```python
existing = {n['code'] for n in list_namespaces(base_url, token, client_id, org_id, sandbox)}
for ns in required_namespaces:
    if ns['code'] not in existing:
        create_namespace(base_url, token, client_id, org_id, sandbox, ns)
```

### Important Notes
- DELETE namespace: `DELETE /data/core/idnamespace/identities/{id}` — may return 401 if client not allowlisted for delete
- Namespace codes are case-sensitive in identityMap keys — `"Email"` not `"email"`, `"ClientAccountID"` not `"clientaccountid"`
- Standard namespaces (Email, Phone, ECID, etc.) do not require creation — they are pre-provisioned org-wide

---

## Real-Time Customer Profile Access API

Base path: `{AEP_BASE_URL}/data/core/ups`

**Look up an entity (profile / account / relation union):**
```
GET /data/core/ups/access/entities?schema.name={UNION}&entityId={ID}&entityIdNS={NS}&mergePolicyId={MP}
```

- `schema.name` is the UNION schema: `_xdm.context.profile` (persons), `_xdm.context.account` (B2B accounts),
  `_xdm.classes.account-person` (relations), `_xdm.context.experienceevent` (events).
- **`mergePolicyId` is REQUIRED.** Omitting it returns `422 UPAPI-001025-422 "The merge policy doesn't exist."`
  Fetch the right one first:
  ```
  GET /data/core/ups/config/mergePolicies
  ```
  and pick the policy whose `schema.name` matches the union you are querying (each union has a default
  Timebased policy). Merge-policy IDs are sandbox-specific and are regenerated after a sandbox reset — never
  hardcode them.
- **Unwrap the response** — it is keyed by the AEP entity ID: `{"<xid>": {entity, sources, identityGraph, ...}}`.
  Do `resp[next(iter(resp))]` before reading `.entity` / `.sources`.
- For **event stitching**, query with `relatedSchema.name` + `relatedEntityId` + `relatedEntityIdNS`
  (+ `mergePolicyId`) to fetch events related to a profile/account.

**Transient after Profile enablement:** immediately after a schema is first Profile-enabled and its first
batch is ingested, an entity lookup can return `500 UPLIB-101601-500 "unexpected response while listing
schemas from XDM registry."` This is the Profile Store's schema cache catching up — it is NOT a 404 and NOT
a data error. Retry with backoff for up to ~15 min; it resolves once the union schema is registered in the
Profile Store. Only treat a clean `404` (after propagation) as "entity not materialized."

**Two 404 shapes — they mean different things:**
- `UPAPI-038022-404` with NO `debugInfo`/xid → no identity was created for that namespace+id (the identity
  descriptor is missing, OR the entity hasn't been processed into an identity yet).
- `UPLIB-201001-404` WITH `debugInfo.xid` → the identity resolved to an xid but no entity/profile fragment
  is attached to it (data not yet merged, or the record didn't carry that field).

**B2B account union (`_xdm.context.account`) is populated by a DAILY BATCH job, not in real time — this is
the single most important B2B gotcha.** Person profiles resolve in minutes via the near-real-time profile
store (there is an hourly `batch_change_stream_job` for `_xdm.context.profile`). **Business Accounts and
Opportunities are entity-resolved by a separate job that runs once daily during batch segmentation**
(Adobe: *"Account profiles require daily batch segmentation evaluation enabled to show data"*; *"Entity
resolution job runs daily during batch segmentation… based on deterministic ID matching"*). So a
correctly-built account returns a clean `UPAPI-038022-404` (query accepted, no entity yet) until that daily
job runs — expect up to ~24h, NOT minutes. This is expected behavior, not a bug.

Key operational facts:
- **The account identity is created at ingestion** (the `b2b_account` XID exists immediately — verify with
  `GET /data/core/identity/identity?namespace=b2b_account&id=<sourceKey>`), but the account **entity** only
  appears in the union after the daily entity-resolution job. Identity present + entity absent = waiting on
  the daily job, not a config error.
- **You usually cannot force it on demand.** Orgs on "B2B simplification" reject manual segment jobs:
  `POST /data/core/ups/segment/jobs` → `UPAPI-054554-400 "Non-scheduled segment jobs are not allowed for
  orgs enabled for B2B simplification."` Account resolution runs only on the managed daily schedule. Confirm
  batch segmentation is enabled/scheduled for the sandbox; check `GET /data/core/ups/config/schedules`.
- **Account-Person / Opportunity-Person Relations, Campaigns, and Marketing Lists are NOT queryable via
  `/access/entities`** — Adobe de-supported relation lookups (a query returns HTTP 400). Relations are
  consumed via relationship descriptors / multi-entity segmentation, not entity lookups.
- **B2B multi-entity uses the single default merge policy** (do not create a custom account merge policy).

Before concluding an account "failed", verify the six config layers — (1) primary identity descriptor on
`/accountKey/sourceKey` → `b2b_account` with `xdm:isPrimary: true`, `xdm:property: "xdm:code"` (GET the
descriptor directly; the global `/tenant/descriptors` list can return 0 even when descriptors exist — query
`?xdm:sourceSchema=<id>` or GET `/descriptors/{id}`), (2) `accountKey.sourceKey` populated non-empty,
(3) namespace `b2b_account` idType `B2B_ACCOUNT`, (4) dataset `unifiedProfile`/`unifiedIdentity`/`profile:enabled`,
(5) schema `union` tag, (6) batch `success`, plus the account `b2b_account` XID exists in the Identity
Service. If all hold, the account IS correctly built — it will appear after the next daily
batch-segmentation/entity-resolution cycle. Do NOT "fix" it by adding a `CROSS_DEVICE` identityMap namespace
(that is the classic wrong-model bug).

---

## Sandbox Management API

Base path: `{AEP_BASE_URL}/data/foundation/sandbox-management`

- **Get sandbox:** `GET /sandboxes/{name}` → returns `state`, `type` (development/production), `region`.
- **Reset a DEVELOPMENT sandbox** (wipes ALL schemas, field groups, datasets, namespaces, profiles, batches —
  irreversible): `PUT /sandboxes/{name}` with body `{"action":"reset"}`. Returns HTTP 200 and runs
  asynchronously (completes in minutes). Only development sandboxes can be reset. This is the cleanest way to
  shed artifacts that cannot be individually deleted — e.g. a namespace created with the wrong `idType`
  (idType is immutable; a `CROSS_DEVICE` namespace can never become `B2B_ACCOUNT`, so reset is the only way to
  replace it). ALWAYS get explicit user confirmation before resetting — it is destructive and org-visible.

---

## Common Error Patterns

| Error Code | Meaning | Resolution |
|------------|---------|------------|
| 400 | Invalid request body or schema composition error | Check JSON structure and schema references |
| 401 | Authentication failed or token expired | Refresh IMS token |
| 403 | Insufficient permissions or wrong sandbox | Verify org ID, sandbox name, and API permissions |
| 404 | Resource not found | Check schema/dataset ID, verify sandbox context |
| 409 | Conflict — resource already exists | Use GET to check existence before POST |
| 422 | Schema validation error | Check field types, required fields, and composition rules |
| 429 | Rate limited | Implement exponential backoff retry |
| 500/503 | AEP service error | Retry with backoff, check AEP status page |

### Troubleshooting Checklist

1. Verify all required headers are present (Authorization, x-api-key, x-gw-ims-org-id, x-sandbox-name)
2. Verify the access token is not expired
3. Verify the sandbox name matches the target environment
4. Verify schema/dataset IDs include the full namespace URI
5. Verify field group class compatibility with the target schema class
6. Check AEP status page for service outages

---

## MCP Server Integration

When the AEP Stage MCP server is available (configured in `.vscode/mcp.json`):
- Prefer Stage MCP server calls over direct REST API calls
- The Stage MCP server handles authentication and header management
- Fall back to direct REST via `aep_client.py` when the Stage MCP server is unavailable
- MCP server configuration should reference environment variables for any sensitive values

---

## Environment Configuration Pattern

```python
# config/settings.py pattern
import os

class AEPConfig:
    base_url: str = os.environ.get("AEP_BASE_URL", "")
    ims_url: str = os.environ.get("AEP_IMS_URL", "")
    client_id: str = os.environ.get("AEP_CLIENT_ID", "")
    client_secret: str = os.environ.get("AEP_CLIENT_SECRET", "")
    org_id: str = os.environ.get("AEP_ORG_ID", "")
    sandbox_name: str = os.environ.get("AEP_SANDBOX_NAME", "")
```

All pipeline modules receive configuration through dependency injection or by importing from `config.settings` — never by reading environment variables directly.
