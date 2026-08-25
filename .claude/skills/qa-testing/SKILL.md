---
name: qa-testing
description: AEP/AJO QA test case generation and execution patterns — consolidated test_cases.csv format (13 columns including Artifact_Type, Story_ID, Sandbox, Run_Timestamp), TC_ID prefixes (NS-/SCH-/DST-/IDN-/PRF-/SEG-/CAM-/ING-/JRN-), namespace/schema/dataset/identity/profile/segment/campaign/ingestion/journey test types, AEP Schema Registry + Catalog + Namespace + Segment + Profile + Campaign API curl patterns, field navigation rules, XDM class URL map, failure categories, gate definitions (advisory only), and HTML report formats. Load when running /qa read or /qa run for any artifact category.
---

# QA Testing Skill

**Purpose**: Test execution patterns for all QA consolidated agents (how to generate and execute tests)

**Relationship to qa-master skill**:

- **qa-testing skill** (this file) = Execution: test case generation, CSV format, API patterns, test type definitions
- **qa-master skill** = Orchestration: dispatch table, gate logic, consolidated reporting, agent coordination
- **No duplication** - complementary skills for different purposes

Load this skill before any `/qa read` or `/qa run` operation.

**Who loads this skill**:

- qa-platform.md (namespace, schema, dataset, identity, profile, mapping, ingestion tests)
- qa-journey-activation-orchestrator.md (segment, campaign, journey tests)
- qa-governance.md (governance tests)
- NOT loaded by qa-master.md (orchestrator only dispatches, doesn't execute tests)

---

## 1. Consolidated test_cases.csv Format

Single file for ALL QA categories: `output/<ProjectName>/<sandbox>/QA/test_cases.csv`

```
TC_ID,Category,Artifact_Type,Artifact_Name,Story_ID,Test_Type,Expected_Value,Actual_Value,Status,Failure_Reason,Evidence,Sandbox,Run_Timestamp
```

| Column | Description | Example |
|---|---|---|
| `TC_ID` | Unique ID — prefix by category + 3-digit sequence | `NS-001`, `SCH-001`, `DST-001` |
| `Category` | QA domain (human-readable) | `Namespace` / `Schema` / `Dataset` / `Identity` / `Profile` / `Segment` / `Campaign` / `Ingestion` / `Journey` |
| `Artifact_Type` | Component type matching DevPlan Component column | `Namespace` / `Schema` / `Dataset` / `Identity` / `Profile` / `Segment` / `Campaign` / `Journey` |
| `Artifact_Name` | Name of the artifact being tested | `Customer Profile` |
| `Story_ID` | Matching DevPlan.csv story ID — looked up by artifact name | `AEP-001` |
| `Test_Type` | Validation type code (see per-category tables below) | `type`, `identity_primary`, `existence` |
| `Expected_Value` | Value from design document | `string`, `email`, `exists` |
| `Actual_Value` | Value retrieved from AEP API — filled on `/qa run` | `string` |
| `Status` | `Pending` → `PASS` / `FAIL` / `WARN` / `ERROR` after run | `PASS` |
| `Failure_Reason` | Failure category code — filled on FAIL | `TYPE_MISMATCH` |
| `Evidence` | API response snippet or field value — filled on run | `"type": "integer"` |
| `Sandbox` | AEP_SANDBOX_NAME at time of write | `training` |
| `Run_Timestamp` | ISO 8601 timestamp set during `/qa run` — empty at read time | `2026-05-16T10:22:00Z` |

**TC_ID prefixes:**

| Prefix | Category | Artifact_Type |
|---|---|---|
| `NS-` | Namespace | Namespace |
| `SCH-` | Schema | Schema |
| `DST-` | Dataset | Dataset |
| `IDN-` | Identity | Identity |
| `PRF-` | Profile | Profile |
| `SEG-` | Segment | Segment |
| `CAM-` | Campaign | Campaign |
| `ING-` | Ingestion | Ingestion |
| `JRN-` | Journey | Journey |

**TC_ID assignment rule**: Before generating new test cases for a category+artifact, read the existing CSV, find the highest sequence number for that category prefix, and start from `max+1`. If no rows exist for that prefix, start from `001`.

**Re-read rule**: When `/qa read <category> <name>` is called for an artifact that already has rows in the CSV, delete all rows where `Category=<category>` AND `Artifact_Name=<name>`, then append freshly generated rows.

**Story_ID resolution**: Read `output/<ProjectName>/DevPlan/DevPlan.csv`. Find row where `Component` matches `Artifact_Type` AND `Story_Title` contains `Artifact_Name`. Use `ID` column value. If not found, leave blank.

**Sandbox column**: Set to `AEP_SANDBOX_NAME` at time the row is written (both read and run phases).

**Run_Timestamp column**: Set to `$(date -u +%Y-%m-%dT%H:%M:%SZ)` during `/qa run` execution. Left empty during `/qa read`.

---

## 2. Namespace QA — Test Types (TC_ID prefix: NS-)

Applied when `Category = Namespace`. Source of truth: design JSONs and DevPlan.csv.

| Test_Type | Condition | Field_Path | Expected_Value |
|---|---|---|---|
| `existence` | Always | `namespace-level` | `exists` |
| `code_match` | Always | `code` | `<namespace_code>` |
| `idType_match` | Always | `idType` | `<idType>` e.g. `CROSS_DEVICE` |
| `no_duplicate` | Always | `namespace-level` | `unique` |

---

## 3. Schema QA — Test Types (TC_ID prefix: SCH-)

Applied when `Category = Schema`. Source of truth: `output/<ProjectName>/schemas/schema-design-{name}.json`

### Per-Attribute Tests

| Test_Type | Condition to generate | Field_Path | Expected_Value |
|---|---|---|---|
| `type` | Always | `attribute.xdmPath` | `attribute.xdmType` |
| `format` | Only if `attribute.xdmFormat` set | `attribute.xdmPath` | `attribute.xdmFormat` |
| `required` | Only if `attribute.isRequired = true` | `attribute.xdmPath` | `true` |
| `enum` | Only if `attribute.enumValues` non-empty | `attribute.xdmPath` | Pipe-separated e.g. `bronze\|silver\|gold` |
| `path` | Always | `attribute.xdmPath` | `exists` |
| `identity_primary` | Only if `attribute.isPrimaryIdentity = true` | `attribute.xdmPath` | `primary\|<namespace>` |
| `identity_secondary` | Only if `attribute.isIdentity = true` AND `isPrimaryIdentity = false` | `attribute.xdmPath` | `secondary\|<namespace>` |

### Schema-Level Tests

| Test_Type | Field_Path | Expected_Value |
|---|---|---|
| `class` | `schema-level` | `design.xdmClass` e.g. `XDM Individual Profile` |
| `profile` | `schema-level` | `enabled` if `design.profileEnabled = true`, else `disabled` |

---

## 4. Dataset QA — Test Types (TC_ID prefix: DST-)

Always 8 test cases per dataset. `profileEnabled` only affects `Expected_Value`, never whether the test is generated.

| Test_Type | Field_Path | Expected_Value (profile=true) | Expected_Value (profile=false) |
|---|---|---|---|
| `existence` | `dataset-level` | `exists` | `exists` |
| `name_check` | `dataset-level` | `{schemaName} Dataset` | `{schemaName} Dataset` |
| `schema_association` | `schemaRef.id` | `{schema $id}` | `{schema $id}` |
| `profile_tag_unified` | `tags.unifiedProfile` | `enabled` | `not-enabled` |
| `profile_tag_identity` | `tags.unifiedIdentity` | `enabled` | `not-enabled` |
| `profile_tag_granular` | `tags.acp_granular_plugin_validation_flags` | `enabled` | `not-enabled` |
| `profile_consistent` | `tags (all 3)` | `all-enabled` | `all-disabled` |
| `format_tag` | `tags.adobe/siphon/table/format` | `exists` | `exists` |

`format_tag` is always WARN (never FAIL) — it is an informational check.

---

## 5. Identity QA — Test Types (TC_ID prefix: IDN-)

Applied when `Category = Identity`. Only profile-enabled schemas generate test cases.

| Test_Type | Field_Path | Expected_Value | Phase |
|---|---|---|---|
| `namespace_exists` | `<namespace_code>` (one row per ns) | `exists` | Config |
| `merge_policy_exists` | `merge-policy-level` | `exists` | Config |
| `merge_policy_default` | `merge-policy-level` | `isDefault=true` | Config |
| `identity_field_not_null` | Identity field paths joined with `\|` | `null_count=0` | Runtime |
| `identity_stitching` | `identityMap` | `all_namespaces_present` | Runtime |
| `merge_policy_profile_view` | `mergePolicy.name` | `matches_default_policy` | Runtime |

Runtime rows pre-set to `Status=WARN`, `Failure_Reason=PENDING_POST_INGEST` at read time.

---

## 6. Profile QA — Test Types (TC_ID prefix: PRF-)

Applied when `Category = Profile`. Source of truth: schema design JSON + Catalog API + Schema Registry.

| Test_Type | Field_Path | Expected_Value |
|---|---|---|
| `schema_union_tag` | `meta:immutableTags` | `union` |
| `dataset_unified_profile` | `tags.unifiedProfile` | `enabled:true` |
| `dataset_unified_identity` | `tags.unifiedIdentity` | `enabled:true` |
| `dataset_granular_flag` | `tags.acp_granular_plugin_validation_flags` | `profile:enabled` |

---

## 7. Segment QA — Test Types (TC_ID prefix: SEG-)

Source of truth: `output/<ProjectName>/segments/segment-design-{name}.json`

| Test_Type | Field_Path | Expected_Value | Phase |
|---|---|---|---|
| `segment_exists` | `segment-level` | `exists` | Config |
| `name_match` | `name` | `<segment_name>` | Config |
| `description_match` | `description` | `<first 80 chars>` | Config |
| `pql_match` | `expression.value` | `<normalised pql>` | Config |
| `consent_in_pql` | `expression.value` | `consent_field_present` | Config |
| `evaluation_type` | `evaluationInfo` | `batch\|streaming\|edge` | Config |
| `profile_count` | `metrics.data.totalProfiles` | `totalProfiles>0` | Runtime |
| `segment_membership_positive` | `segmentMembership.ups` | `status=realized\|existing` | Runtime |
| `segment_membership_negative` | `segmentMembership.ups` | `status=absent\|exited` | Runtime |

`consent_in_pql` is evaluated at READ time — FAIL is set immediately if consent field absent from PQL.
TC+8 (`segment_membership_negative`) only generated if `qaTestCriteria.negativeCase` is non-empty.
Runtime rows pre-set to `Status=WARN`, `Failure_Reason=PENDING_SEGMENT_EVAL`.

---

## 8. Campaign QA — Test Types (TC_ID prefix: CAM-)

Source of truth: DevPlan.csv + Campaign Service API.

| Test_Type | Field_Path | Expected_Value |
|---|---|---|
| `existence` | `campaign-level` | `exists` |
| `status_check` | `status` | `DRAFT` |
| `surface_valid` | `content.channel` | `<surface_name>` |
| `segment_linked` | `audience.definition.id` | `<segment_id>` |

---

## 9. Ingestion QA — Test Types (TC_ID prefix: ING-)

Source of truth: schema design JSON + synthetic NDJSON files.

| TC | Test_Type | Field_Path | Expected_Value (batch) | Expected_Value (stream) |
|---|---|---|---|---|
| +0 | `valid_payload` | `ingestion-level` | `status=success` | `http_200` |
| +1 | `dataset_preview` | `ingestion-level` | `records_visible` | N/A (WARN) |
| +2 | `incremental_load` | `ingestion-level` | `updated_no_duplicate` | N/A (WARN) |
| +3 | `missing_required_field` | `<omitted_field>` | `status=failed\|quarantined` | `http_400\|http_200_warn` |
| +4 | `wrong_datatype` | `<wrong_field>` | `validation_error` | `http_400\|http_200_warn` |
| +5 | `invalid_timestamp` | `<ts_field>` | `validation_error\|quarantined` | `http_400\|http_200_warn` |
| +6 | `record_count` | `ingestion-level` | `count_within_1pct` | N/A (WARN) |
| +7 | `profile_resolution` | `ingestion-level` | `profile_exists` | `profile_exists\|N/A` |

Pre-set WARN rows at read time:

- Streaming schema: rows +1, +2, +6 → `Status=WARN`, `Failure_Reason=NOT_APPLICABLE_STREAMING`
- Profile disabled: row +7 → `Status=WARN`, `Failure_Reason=NOT_APPLICABLE_PROFILE_DISABLED`

---

## 10. Journey QA — Test Types (TC_ID prefix: JRN-)

Source of truth: DevPlan.csv.

| Test_Type | Field_Path | Expected_Value |
|---|---|---|
| `id_recorded` | `devplan-level` | `AEP_Resource_ID_present` |
| `publish_status` | `journey-level` | `LIVE\|DRAFT` |

---

## 11. AEP API Patterns

### Get IMS Token (use cached token helper — never inline curl/python3)

```bash
source .env
source scripts/get_or_refresh_token.sh
# ACCESS_TOKEN is now exported — reused from cache if < 23h old, fetched fresh otherwise
# NEVER use the inline ACCESS_TOKEN=$(curl ... | python3 ...) pattern:
#   - starts with ACCESS_TOKEN= which is not in the bash allow list → prompts for approval every time
#   - fetches a fresh IMS token on every agent run — slow and wasteful
#   - uses python3 inline — appears as a Python availability check on every invocation
```

### Standard Headers (all API calls)

```bash
-H "Authorization: Bearer ${ACCESS_TOKEN}" \
-H "x-api-key: ${AEP_CLIENT_ID}" \
-H "x-gw-ims-org-id: ${AEP_ORG_ID}" \
-H "x-sandbox-name: ${AEP_SANDBOX_NAME}"
```

### Fetch Full Schema

```bash
ENCODED_ID=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${SCHEMA_ID}', safe=''))")
curl -s "${AEP_BASE_URL}/data/foundation/schemaregistry/tenant/schemas/${ENCODED_ID}" \
  -H "Accept: application/vnd.adobe.xed-full+json; version=1" \
  [standard headers]
```

### Fetch Identity Descriptors

```bash
curl -s "${AEP_BASE_URL}/data/foundation/schemaregistry/tenant/descriptors?property=sourceSchema==${ENCODED_ID}" \
  [standard headers]
```

### List Namespaces

```bash
curl -s "${AEP_BASE_URL}/data/core/idnamespace/identities" [standard headers]
```

### Catalog Dataset

```bash
curl -s "${AEP_BASE_URL}/data/foundation/catalog/datasets/${DATASET_ID}?properties=name,schemaRef,tags" \
  [standard headers]
```

### Segment Definition

```bash
curl -s "${AEP_BASE_URL}/data/core/ups/segment/definitions/${SEGMENT_ID}" [standard headers]
```

### Campaign (Campaign Service)

```bash
curl -s "${AEP_BASE_URL}/journey/campaigns/service/campaigns/${CAMPAIGN_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "x-api-key: ${AEP_CLIENT_ID}" \
  -H "x-gw-ims-org-id: ${AEP_ORG_ID}" \
  -H "x-sandbox-name: ${AEP_SANDBOX_NAME}"
```

### Profile Entity Lookup

```bash
curl -s "${AEP_BASE_URL}/data/core/ups/access/entities?schema.name=_xdm.context.profile&entityId=${VALUE}&entityIdNS=${NS}" \
  [standard headers]
```

### Merge Policies

```bash
curl -s "${AEP_BASE_URL}/data/core/ups/config/mergePolicies?schema.name=_xdm.context.profile&limit=50" \
  [standard headers]
```

---

## 12. Field Path Navigation Rules

The full schema JSON response has a deeply nested `properties` structure. To find a field at XDM path `a.b.c`:

1. Split path by `.` → segments = `["a", "b", "c"]`
2. Start at `schema.properties`
3. For each segment except the last: navigate to `current[segment].properties`
4. At the last segment: read `current[segment]` — this is the field node

**For tenant-namespaced fields** (path starts with `_{TENANT_ID}`, e.g., `_deloitte.loyaltyInfo.tier`):

- Navigate: `schema.properties._deloitte.properties.loyaltyInfo.properties.tier`

**Checking `required`**:

- For path `a.b.c` where `c` is required: check `schema.properties.a.properties.b.required` contains `"c"`

**Descriptor path conversion**: `xdm:sourceProperty` uses `/` separator (`/personalEmail/address`). Design JSON uses `.` (`personalEmail.address`). Convert: `"." → "/"` with leading `/` prepended.

---

## 13. XDM Class URL → Display Name Map

| API URL | Display Name |
|---|---|
| `https://ns.adobe.com/xdm/context/profile` | XDM Individual Profile |
| `https://ns.adobe.com/xdm/context/experienceevent` | XDM ExperienceEvent |
| `https://ns.adobe.com/xdm/context/segmentdefinition` | XDM Segment Definition |
| `https://ns.adobe.com/xdm/classes/account` | XDM Business Account |
| `https://ns.adobe.com/xdm/classes/campaign` | XDM Business Campaign |
| `https://ns.adobe.com/xdm/classes/product` | XDM Business Product |

**Fallback**: Extract last URL segment, replace hyphens with spaces, title-case.

---

## 14. Failure Categories

### Namespace

| Code | Meaning |
|---|---|
| `NAMESPACE_NOT_FOUND` | Namespace code absent from AEP idnamespace list |
| `CODE_MISMATCH` | Registered code differs from design |
| `IDTYPE_MISMATCH` | idType differs from design |
| `NAMESPACE_DUPLICATE` | Same code registered more than once |

### Schema

| Code | Meaning |
|---|---|
| `TYPE_MISMATCH` | Field type differs from design |
| `FORMAT_MISMATCH` | Field format differs from design |
| `REQUIRED_MISMATCH` | Field missing from required array |
| `ENUM_MISMATCH` | Enum values differ from design |
| `MISSING_FIELD` | Field path not found in schema |
| `IDENTITY_MISMATCH` | Descriptor missing, wrong namespace, or wrong isPrimary |
| `CLASS_MISMATCH` | Schema class differs from design |
| `PROFILE_MISMATCH` | Schema profile-enabled status differs from design |
| `SCHEMA_NOT_FOUND` | Schema not deployed in AEP |

### Dataset

| Code | Meaning |
|---|---|
| `DATASET_NOT_FOUND` | Dataset name not found via Catalog |
| `NAME_MISMATCH` | Dataset name differs from expected |
| `SCHEMA_ASSOCIATION_MISMATCH` | schemaRef.id differs from design |
| `PROFILE_TAG_MISMATCH` | Profile tag enabled/disabled state differs from expected |
| `PROFILE_TAG_GRANULAR_INCOMPLETE` | Both identity:enabled and profile:enabled not present |
| `PROFILE_TAGS_INCONSISTENT` | Tags are in inconsistent state across the 3 flags |
| `FORMAT_TAG_MISSING` | adobe/siphon/table/format tag absent (WARN) |

### Identity / Profile

| Code | Meaning |
|---|---|
| `NAMESPACE_NOT_FOUND` | Identity namespace not registered |
| `MERGE_POLICY_NOT_FOUND` | No merge policies found |
| `NO_DEFAULT_MERGE_POLICY` | No merge policy with isDefault=true |
| `IDENTITY_NULL_FOUND` | Null identity field values in dataset |
| `IDENTITY_STITCHING_INCOMPLETE` | Profile missing expected namespaces |
| `PROFILE_NOT_FOUND` | No profile found for lookup identity |
| `NON_DEFAULT_MERGE_POLICY` | Profile uses non-default merge policy (WARN) |
| `SCHEMA_UNION_TAG_MISSING` | Schema missing meta:immutableTags union |
| `PROFILE_PROCESSING_BLOCKED` | Dataset granular flag has profile:disabled |

### Segment

| Code | Meaning |
|---|---|
| `SEGMENT_NOT_FOUND` | Segment not found in AEP |
| `NAME_MISMATCH` | Segment name differs |
| `DESCRIPTION_MISMATCH` | Description differs |
| `PQL_MISMATCH` | PQL expression differs from design |
| `CONSENT_MISSING_FROM_PQL` | PQL has no consent field |
| `EVALUATION_TYPE_MISMATCH` | Evaluation mode differs |
| `NO_PROFILES_IN_SEGMENT` | No profiles qualify (after evaluation) |
| `SEGMENT_NOT_EVALUATED` | No evaluation run yet (WARN) |
| `COUNT_VARIANCE_HIGH` | >10% diff between metrics and SQL count (WARN) |
| `QUERY_RETURNS_ZERO` | segmentValidationSQL returns 0 |
| `MEMBERSHIP_NOT_QUALIFIED` | Positive profile not in segment |
| `MEMBERSHIP_EXITED` | Profile qualified before but now exited |
| `MEMBERSHIP_INCORRECTLY_QUALIFIED` | Negative profile unexpectedly in segment |

### Campaign

| Code | Meaning |
|---|---|
| `CAMPAIGN_NOT_FOUND` | Campaign not found via Campaign Service API |
| `STATUS_NOT_DRAFT` | Campaign is not in DRAFT status |
| `SURFACE_MISMATCH` | Channel surface name differs from design |
| `SEGMENT_NOT_LINKED` | Audience segment ID does not match |

### Ingestion

| Code | Meaning |
|---|---|
| `BATCH_FAILED` | Batch ingestion failed |
| `BATCH_QUARANTINED` | Batch quarantined |
| `STREAM_NON_200` | Streaming endpoint returned non-200 |
| `DATASET_PREVIEW_EMPTY` | No records visible after ingestion |
| `INCREMENTAL_DUPLICATE` | Incremental load created duplicate |
| `RECORD_COUNT_MISMATCH` | Ingested count > 1% diff from source |
| `PROFILE_RESOLUTION_FAILED` | Profile not found after ingestion (FAIL) |
| `PROFILE_RESOLUTION_DELAYED` | Profile not yet available — retry later (WARN) |
| `NEGATIVE_BATCH_SUCCEEDED` | AEP accepted an invalid record (Phase B) |
| `DATASET_NOT_FOUND` | Target dataset not found |

### Journey

| Code | Meaning |
|---|---|
| `ID_NOT_RECORDED` | Journey ID absent from DevPlan.csv |
| `STATUS_UNEXPECTED` | Journey is neither LIVE nor DRAFT |

---

## 15. Gates (Advisory Only)

Gates query `test_cases.csv` and return a status — they do NOT block or enforce any build command.

```
PASS     — all test cases for this phase are PASS
BLOCKED  — one or more FAIL rows exist for this phase
INCOMPLETE — one or more Pending or WARN rows exist, no FAILs
```

Gate phase mapping:

| Gate | Categories checked |
|---|---|
| `pre-build` | Namespace, Schema |
| `pre-ingest` | Namespace, Schema, Dataset, Identity, Profile |
| `post-ingest` | Ingestion |
| `post-activation` | Segment, Campaign, Journey |

Invoke: `/qa gate <phase>` — reads OUTPUT_DIR/QA/test_cases.csv, prints gate result.

---

## 16. QA Report Format

### Per-Artifact HTML Report

Filename: `output/<ProjectName>/<sandbox>/QA/<prefix>_report-{kebab-artifact-name}.html`

Structure:

```html
<h1>{Artifact_Type} QA Report: {Artifact_Name}</h1>
<p>Sandbox: {sandbox} | Run: {timestamp} | Story: {Story_ID}</p>
<table>
  <tr><th>TC_ID</th><th>Test_Type</th><th>Field_Path</th><th>Expected</th><th>Actual</th><th>Status</th><th>Failure_Reason</th><th>Evidence</th></tr>
  <!-- only FAIL and ERROR rows -->
</table>
<h2>Remediation</h2>
<!-- per failure_reason code, from failure categories above -->
```

### Consolidated QA_Report.html

Filename: `output/<ProjectName>/<sandbox>/QA/QA_Report.html`

Sections:

1. Dashboard — count by status per category (table)
2. Gate summary — pre-build / pre-ingest / post-ingest / post-activation
3. Per-category FAIL details (collapsed by artifact)
