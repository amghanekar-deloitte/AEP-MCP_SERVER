---
name: synthetic
description: Synthetic XDM record generation from schema design JSONs — generates valid records (N=5, XDM-compliant NDJSON with identityMap + authenticatedState) and invalid records (missing required field, wrong datatype, invalid timestamp) for ingestion QA testing. Handles both XDM Individual Profile (batch) and XDM ExperienceEvent (streaming) record structures. Pure Python standard library — no AEP API calls. Load when generating synthetic test data for /qa read ingestion.
---

# Synthetic Data Generation Skill

Load this skill before any `/qa read ingestion` or synthetic data generation operation.

---

## 1. Input Contract

**Source file:** `output/<ProjectName>/schemas/schema-design-{kebab-name}.json`

Extract these fields from the design JSON (defensive access — handle both wrapped and flat formats):

```python
import json

def load_schema_design(project_name, schema_name):
    kebab = schema_name.lower().replace(" ", "-")
    path = f"output/{project_name}/schemas/schema-design-{kebab}.json"
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return raw.get("schemaDesign", raw.get("design", raw))

design = load_schema_design(project_name, schema_name)

schema_name     = design.get("schemaName", "")
xdm_class       = design.get("schemaClass") or design.get("xdmClass", "")
profile_enabled = design.get("profileEnabled", False)
attributes      = design.get("attributes", [])
identity_config = design.get("identityConfig", {})
schema_id       = design.get("schemaAPIPayload", {}).get("$id", "")
tenant_id       = design.get("tenantId", "")
```

---

## 2. Output Files

Files are written to the DESIGN_DIR (sandbox-agnostic) synthetic subfolder:

```
output/<ProjectName>/synthetic/valid-{kebab-schema-name}.ndjson   ← 5 valid XDM records
output/<ProjectName>/synthetic/invalid-{kebab-schema-name}.ndjson ← 3 invalid records
```

Plus a metadata sidecar (ephemeral, used at run time only):

```
/tmp/synthetic_meta_{kebab-schema-name}.json
```

The metadata sidecar is the contract between `/qa read ingestion` (which generates) and `/qa run ingestion` (which executes).

---

## 3. Method Determination

```python
def determine_method(xdm_class, override=None):
    if override in ("batch", "stream"):
        return override
    return "stream" if "ExperienceEvent" in xdm_class else "batch"
```

- `XDM ExperienceEvent` → `stream` (HTTPS Streaming via AEP_INLET_URL)
- `XDM Individual Profile` → `batch` (Batch Ingestion API)

---

## 4. Python Helpers

```python
import json, uuid, random, string
from datetime import datetime, timedelta

def make_uuid():
    return str(uuid.uuid4())

def make_email():
    domains = ["test.com", "qa.example.com", "synthetic.io"]
    name = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"{name}@{random.choice(domains)}"

def make_timestamp():
    base = datetime(2024, 1, 1)
    offset = timedelta(days=random.randint(0, 365), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return (base + offset).strftime("%Y-%m-%dT%H:%M:%SZ")

def make_date():
    base = datetime(1960, 1, 1)
    offset = timedelta(days=random.randint(0, 20000))
    return (base + offset).strftime("%Y-%m-%d")

def make_identity_map(primary_ns, primary_id, secondary_ns=None, secondary_id=None):
    identity_map = {
        primary_ns: [{
            "id": primary_id,
            "authenticatedState": "ambiguous",
            "primary": True
        }]
    }
    if secondary_ns and secondary_id:
        identity_map[secondary_ns] = [{
            "id": secondary_id,
            "authenticatedState": "ambiguous",
            "primary": False
        }]
    return identity_map

def set_nested(obj, dot_path, value):
    keys = dot_path.split(".")
    for key in keys[:-1]:
        obj = obj.setdefault(key, {})
    obj[keys[-1]] = value

def del_nested(obj, dot_path):
    keys = dot_path.split(".")
    for key in keys[:-1]:
        if key not in obj:
            return False
        obj = obj[key]
    return obj.pop(keys[-1], None) is not None

def get_nested(obj, dot_path):
    keys = dot_path.split(".")
    for key in keys:
        if not isinstance(obj, dict) or key not in obj:
            return None
        obj = obj[key]
    return obj

def type_value_for_attribute(attr):
    data_type = attr.get("dataType", attr.get("type", "string"))
    fmt = attr.get("format", attr.get("xdmFormat", ""))
    enum_values = attr.get("enumValues", attr.get("enum", []))

    if enum_values:
        return random.choice(enum_values)
    if data_type == "string":
        if fmt == "email":
            return make_email()
        if fmt == "date-time":
            return make_timestamp()
        if fmt == "date":
            return make_date()
        if fmt == "uri":
            return f"https://example.com/path/{make_uuid()[:8]}"
        return f"synthetic-{''.join(random.choices(string.ascii_lowercase, k=6))}"
    if data_type in ("integer", "int"):
        return random.randint(1, 9999)
    if data_type in ("number", "float", "double"):
        return round(random.uniform(1.0, 9999.99), 2)
    if data_type == "boolean":
        return random.choice([True, False])
    if data_type == "array":
        return []
    if data_type == "object":
        return {}
    return f"synthetic-{make_uuid()[:8]}"
```

---

## 5. Valid Record Generation

Generate N=5 valid records per schema.

```python
def generate_valid_record(design, record_index):
    xdm_class = design.get("schemaClass") or design.get("xdmClass", "")
    attributes = design.get("attributes", [])
    identity_config = design.get("identityConfig", {})
    tenant_id = design.get("tenantId", "")

    is_event = "ExperienceEvent" in xdm_class

    record = {"_id": make_uuid()}
    if is_event:
        record["timestamp"] = make_timestamp()

    for attr in attributes:
        xdm_path = attr.get("xdmPath", "")
        if not xdm_path:
            continue
        if attr.get("isIdentity") or attr.get("isPrimaryIdentity"):
            continue
        value = type_value_for_attribute(attr)
        actual_path = xdm_path.replace("_tenant", f"_{tenant_id}") if tenant_id else xdm_path
        set_nested(record, actual_path, value)

    primary = identity_config.get("primaryIdentity", {})
    primary_ns = primary.get("namespaceCode", "Email")

    if primary_ns == "Email":
        primary_id = make_email()
    elif primary_ns == "ECID":
        primary_id = "".join([str(random.randint(0, 9)) for _ in range(19)])
    else:
        primary_id = f"SYN-{make_uuid()[:12].upper()}"

    secondary_ns = None
    secondary_id = None
    secondaries = identity_config.get("secondaryIdentities", [])
    if secondaries:
        sec = secondaries[0]
        secondary_ns = sec.get("namespaceCode", "")
        if secondary_ns == "Email":
            secondary_id = make_email()
        else:
            secondary_id = f"SYN-{make_uuid()[:12].upper()}"

    record["identityMap"] = make_identity_map(primary_ns, primary_id, secondary_ns, secondary_id)

    return record, primary_ns, primary_id
```

---

## 6. Invalid Record Generation (3 per schema)

Each invalid record is a clone of valid record 0 with ONE deliberate mutation.

```python
import copy

def generate_invalid_records(valid_records, design):
    attributes = design.get("attributes", [])
    xdm_class = design.get("schemaClass") or design.get("xdmClass", "")
    is_event = "ExperienceEvent" in xdm_class
    invalid_records = []
    metadata = []

    # Invalid Record 0: missing_required_field
    rec0 = copy.deepcopy(valid_records[0])
    omitted_field = None
    for attr in attributes:
        if attr.get("isRequired") and not attr.get("isIdentity") and not attr.get("isPrimaryIdentity"):
            path = attr.get("xdmPath", "")
            if path and del_nested(rec0, path):
                omitted_field = path
                break
    if not omitted_field:
        omitted_field = "_id"
        rec0.pop("_id", None)

    invalid_records.append(rec0)
    metadata.append({
        "index": 0,
        "type": "missing_required_field",
        "omitted_field": omitted_field,
        "description": f"Required field '{omitted_field}' removed"
    })

    # Invalid Record 1: wrong_datatype
    rec1 = copy.deepcopy(valid_records[0])
    wrong_field = None
    for attr in attributes:
        dtype = attr.get("dataType", attr.get("type", ""))
        path = attr.get("xdmPath", "")
        if dtype in ("integer", "number", "float") and path and not attr.get("isIdentity"):
            set_nested(rec1, path, "not-a-number")
            wrong_field = path
            break
    if not wrong_field:
        for attr in attributes:
            dtype = attr.get("dataType", attr.get("type", "string"))
            path = attr.get("xdmPath", "")
            if dtype == "string" and path and not attr.get("isIdentity"):
                set_nested(rec1, path, 99999)
                wrong_field = path
                break
    if not wrong_field:
        wrong_field = "_id"
        rec1["_id"] = 12345

    invalid_records.append(rec1)
    metadata.append({
        "index": 1,
        "type": "wrong_datatype",
        "field": wrong_field,
        "invalid_value": "not-a-number (or integer where string expected)",
        "description": f"Field '{wrong_field}' set to wrong datatype"
    })

    # Invalid Record 2: invalid_timestamp
    rec2 = copy.deepcopy(valid_records[0])
    ts_field = None
    if is_event:
        rec2["timestamp"] = "not-a-timestamp-value"
        ts_field = "timestamp"
    else:
        for attr in attributes:
            fmt = attr.get("format", attr.get("xdmFormat", ""))
            path = attr.get("xdmPath", "")
            if fmt == "date-time" and path and not attr.get("isIdentity"):
                set_nested(rec2, path, "32-13-2099T99:99:99Z")
                ts_field = path
                break
        if not ts_field:
            rec2["_id"] = ""
            ts_field = "_id"

    invalid_records.append(rec2)
    metadata.append({
        "index": 2,
        "type": "invalid_timestamp",
        "field": ts_field,
        "invalid_value": "not-a-timestamp-value or 32-13-2099T99:99:99Z",
        "description": f"Field '{ts_field}' set to malformed timestamp"
    })

    return invalid_records, metadata
```

---

## 7. File Writing Patterns

**Write NDJSON:**

```python
def write_ndjson(records, filepath):
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

**Write metadata sidecar:**

```python
def write_meta_sidecar(schema_name, kebab, method, profile_enabled, schema_id,
                        primary_ns, valid_count, invalid_metadata, tmp_path):
    meta = {
        "schema_name": schema_name,
        "kebab_name": kebab,
        "method": method,
        "profile_enabled": profile_enabled,
        "schema_id": schema_id,
        "primary_identity_ns": primary_ns,
        "valid_count": valid_count,
        "invalid_records": invalid_metadata
    }
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
```

---

## 8. Streaming Envelope Format

For ExperienceEvent schemas, wrap each record in this envelope at execution time (store bare records in NDJSON, wrap at ingest time):

```json
{
  "header": {
    "schemaRef": {
      "id": "<schema_$id>",
      "contentType": "application/vnd.adobe.xed-full+json;version=1"
    },
    "imsOrgId": "${AEP_ORG_ID}",
    "datasetId": "<dataset_id>",
    "source": { "name": "QA Synthetic Ingestion" }
  },
  "body": {
    "xdmMeta": {
      "schemaRef": {
        "id": "<schema_$id>",
        "contentType": "application/vnd.adobe.xed-full+json;version=1"
      }
    },
    "xdmEntity": "<record_object>"
  }
}
```

```python
def wrap_streaming_envelope(record, schema_id, org_id, dataset_id):
    schema_ref = {
        "id": schema_id,
        "contentType": "application/vnd.adobe.xed-full+json;version=1"
    }
    return {
        "header": {
            "schemaRef": schema_ref,
            "imsOrgId": org_id,
            "datasetId": dataset_id,
            "source": {"name": "QA Synthetic Ingestion"}
        },
        "body": {
            "xdmMeta": {"schemaRef": schema_ref},
            "xdmEntity": record
        }
    }
```

---

## 9. Full Generation Script (inline execution pattern)

```python
# Write to /tmp/generate_synthetic_{kebab}.py and execute:
# python3 /tmp/generate_synthetic_{kebab}.py

import json, uuid, random, string, copy, os
from datetime import datetime, timedelta

PROJECT = "<ProjectName>"
SCHEMA_NAME = "<schemaName>"
KEBAB = "<kebab-name>"
N_VALID = 5

# [Include all helper functions from Sections 4-7 above]

design = load_schema_design(PROJECT, SCHEMA_NAME)
xdm_class = design.get("schemaClass") or design.get("xdmClass", "")
method = "stream" if "ExperienceEvent" in xdm_class else "batch"
profile_enabled = design.get("profileEnabled", False)
schema_id = design.get("schemaAPIPayload", {}).get("$id", "")

valid_records = []
primary_ns_used = "Email"
for i in range(N_VALID):
    rec, primary_ns, primary_id = generate_valid_record(design, i)
    valid_records.append(rec)
    primary_ns_used = primary_ns

invalid_records, invalid_metadata = generate_invalid_records(valid_records, design)

os.makedirs(f"output/{PROJECT}/synthetic", exist_ok=True)
write_ndjson(valid_records,   f"output/{PROJECT}/synthetic/valid-{KEBAB}.ndjson")
write_ndjson(invalid_records, f"output/{PROJECT}/synthetic/invalid-{KEBAB}.ndjson")

write_meta_sidecar(
    schema_name=SCHEMA_NAME, kebab=KEBAB, method=method,
    profile_enabled=profile_enabled, schema_id=schema_id,
    primary_ns=primary_ns_used, valid_count=N_VALID,
    invalid_metadata=invalid_metadata,
    tmp_path=f"/tmp/synthetic_meta_{KEBAB}.json"
)

print(f"Synthetic data generated for: {SCHEMA_NAME}")
print(f"  Method: {method}")
print(f"  Valid records:   {N_VALID}  → output/{PROJECT}/synthetic/valid-{KEBAB}.ndjson")
print(f"  Invalid records: 3   → output/{PROJECT}/synthetic/invalid-{KEBAB}.ndjson")
for m in invalid_metadata:
    print(f"    [{m['index']}] {m['type']}: {m['description']}")
```

---

## 10. Rules

- identityMap MUST always include `authenticatedState: "ambiguous"` — omitting it causes UIS INVALID errors on profile-enabled datasets
- NEVER generate records without `_id` (for valid records) — `_id` must be a non-empty UUID string
- Tenant-prefixed fields use `_{tenantId}.fieldName` — replace `_tenant` placeholder with actual tenant ID from design JSON
- For Profile schemas: `_id` is NOT the primary identity — identity is in `identityMap`; `_id` is the record's unique row ID
- For ExperienceEvent schemas: `timestamp` is REQUIRED and must be ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)
- Invalid records are clones of valid record 0 — individually valid except for the one deliberate mutation
- The metadata sidecar at `/tmp/synthetic_meta_{kebab}.json` is the contract between `/qa read ingestion` and `/qa run ingestion`
- Output path for synthetic files: `output/<ProjectName>/synthetic/` — this is DESIGN_DIR (sandbox-agnostic) because synthetic data is schema-specific, not sandbox-specific
