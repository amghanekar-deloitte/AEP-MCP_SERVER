---
name: look-up-schema-fields
description: >
  Look up a specific field in AEP schemas and show everywhere that field is used —
  which schemas reference it, which field groups define it, and its XDM path.
  Load when the user says "find field X", "where is field Y used", "what schema has
  field Z", "show me everywhere email is used", or "look up field path for X".
  Returns XDM paths, field groups, and usage across schemas.
---

# Look Up Schema Fields

## When to Load

- "find field [name]"
- "where is [fieldName] used across our schemas"
- "what's the XDM path for [field]"
- "which schema has [field]"
- "show me all uses of email / phone / proxyId"

---

## Lookup Strategy

### Step 1: Get all schemas

```
mcp__aep__list_schemas
```

### Step 2: Retrieve and flatten each schema

For each schema, call `mcp__aep__get_schema` and flatten all properties to dot-notation paths (same as `field-discovery` skill).

### Step 3: Search

Match the user's term against:
- Last path segment (field name): e.g., `address` matches `homeAddress.address`
- Full path substring: e.g., `email` matches `personalEmail.address` and `workEmail.address`
- `meta:description` of the field if available

---

## Output Format

For each match, show:

| Field Path | Schema | Field Group | Type | Identity? |
|---|---|---|---|---|
| `personalEmail.address` | Individual Profile | Profile Personal Details | string | Yes (email) |
| `workEmail.address` | Individual Profile | Profile Work Details | string | No |
| `_deloitte_digitalengage.proxyId` | Individual Profile | Custom Attributes | string | Yes (ProxyID) |

- If a field is an identity descriptor, show the namespace
- If a field appears in multiple schemas, show one row per schema occurrence
- If no match: state clearly — do NOT invent paths
