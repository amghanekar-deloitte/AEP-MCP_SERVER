---
name: data-prep
description: AEP Data Prep — mapping sets, individual field mappings, expression validation, built-in function catalog, and mapping preview. Use when creating or inspecting XDM field mappings for source-to-XDM transformation in the ingestion pipeline (Stage 6), validating Data Prep expressions, or checking available built-in transform functions. Key tools: mcp__aep__create_mapping_set, mcp__aep__get_mapping_set, mcp__aep__list_mapping_sets, mcp__aep__create_mapping, mcp__aep__list_mappings, mcp__aep__get_mapping, mcp__aep__preview_mapping_set, mcp__aep__validate_mapping_expression, mcp__aep__list_data_prep_functions.
---

# Data Prep

Data Prep maps source fields (CSV, JSON) to XDM paths via a mapping set. The AEP Flow Service uses the mapping set during streaming ingestion; batch ingestion can also reference a mapping set for server-side transformation.

API base: `/data/foundation/conversion`

---

## Core Objects

```
Mapping Set   — container: input schema + output schema + list of field mappings
Mapping       — individual field rule: sourceType + source (JSONPath) + destination (XDM dot-path)
```

---

## Mapping Set Workflow

```
1. Validate expressions (optional)    mcp__aep__validate_mapping_expression
2. Create mapping set                  mcp__aep__create_mapping_set
3. Preview against sample data         mcp__aep__preview_mapping_set
4. List / inspect                      mcp__aep__list_mapping_sets, mcp__aep__get_mapping_set
5. Inspect individual mappings         mcp__aep__list_mappings, mcp__aep__get_mapping
```

---

## Creating a Mapping Set

```python
mcp__aep__create_mapping_set(
    name="Customer Profile Mapping",
    input_schema={          # JSON Schema for source record
        "type": "object",
        "properties": {
            "firstName": {"type": "string"},
            "email":     {"type": "string"},
            "age":       {"type": "integer"}
        }
    },
    output_schema={         # JSON Schema for target XDM record (usually derived from the deployed schema)
        "type": "object",
        "$schema": "http://json-schema.org/draft-07/schema#"
    },
    mappings=[
        {"sourceType": "ATTRIBUTE", "source": "$.firstName",  "destination": "person.name.firstName"},
        {"sourceType": "ATTRIBUTE", "source": "$.email",      "destination": "personalEmail.address"},
        {"sourceType": "EXPRESSION","source": "toUpperCase($.email)", "destination": "_{tenant}.emailUpper"},
    ]
)
```

### Mapping `sourceType` Values

| sourceType | Description | Example source |
|---|---|---|
| `ATTRIBUTE` | Direct field copy | `$.fieldName` |
| `EXPRESSION` | Built-in function applied to field | `toUpperCase($.field)` |
| `STATIC` | Hardcoded constant | `"AEP_BATCH"` |

### Source Notation

Sources use JSONPath with `$` as root:
- `$.field` — top-level field
- `$.nested.field` — nested field
- `$.array[0].field` — first array element
- `$.array[*].field` — all array elements (maps to XDM array)

### Destination Notation

Destinations use dot-notation XDM paths (no `$` prefix):
- `person.name.firstName`
- `personalEmail.address`
- `_{tenantId}.customField` — tenant-prefixed custom fields

---

## Expression Validation

Before saving a complex expression, validate it:

```python
mcp__aep__validate_mapping_expression(
    expression="toUpperCase($.email)",
    input_schema={"type": "object", "properties": {"email": {"type": "string"}}}
)
```

Returns `{ valid: true }` or an error message. Use this for any non-trivial expression before creating the mapping set.

---

## Built-in Functions

```python
mcp__aep__list_data_prep_functions()   # returns all functions with name, category, signature, description
```

Common function categories and examples:

| Category | Examples |
|---|---|
| String | `toUpperCase`, `toLowerCase`, `trim`, `concat`, `substring`, `replace`, `length` |
| Math | `add`, `subtract`, `multiply`, `divide`, `mod`, `abs`, `ceil`, `floor` |
| Date/Time | `toDate`, `formatDate`, `now`, `timestamp_to_date` |
| Conditional | `iif`, `nullif`, `coalesce` |
| Array | `array_to_string`, `size_of`, `get` |
| Type conversion | `toString`, `toInteger`, `toDouble`, `toBoolean` |

For the full list with signatures, call `list_data_prep_functions` — the catalog is large and changes with AEP releases.

---

## Mapping Preview

Test a mapping set against a real source record before ingestion:

```python
mcp__aep__preview_mapping_set(
    mapping_set_id="abc123",
    sample_data={"firstName": "Jane", "email": "jane@example.com", "age": 35}
)
```

Returns the transformed XDM output. Use this to catch path mismatches or expression errors before running a full ingestion batch.

---

## Inspecting Existing Mappings

```python
mcp__aep__list_mapping_sets(name="Customer")        # substring filter on name
mcp__aep__get_mapping_set("abc123")                  # full mapping set details
mcp__aep__list_mappings("abc123")                    # all field rules in the set
mcp__aep__get_mapping("abc123", "mapping456")        # single field rule
```

---

## Common Patterns in the Ingestion Pipeline

### identityMap Mapping

AEP cannot map to `identityMap` via a standard ATTRIBUTE mapping — identityMap has a special structure. Either:
1. Pre-build `identityMap` in the source transform (Python) before ingestion (preferred for batch), or
2. Use an EXPRESSION mapping with the `createMap` / `toObject` function if available in your AEP version.

### Tenant Field Mapping

Custom fields under the tenant namespace use the format: `_{tenantId}.fieldName`

Find the tenant ID from the schema `$id` or from the CLAUDE.md deployment manifest. Example:
```
destination: "_deloitte_digitalengage.proxyId"
```

---

## Related Skills

- `data-ingestion` — CSV-to-XDM transform, batch upload (Stage 6)
- `xdm-schema-design` — schema structure, field paths, tenant namespacing
- `aep-fundamentals` — authentication and environment variables
