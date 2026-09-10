---
name: explore-data-schemas
description: >
  Explore the structure and fields of AEP data schemas — browse all schemas, inspect
  a specific schema's field groups and properties, check which schemas are profile-enabled,
  and understand schema composition. Load when the user says "show me the schemas",
  "explore schema X", "what's in this schema", "list our schemas", or "what schemas do we have".
  Uses mcp__aep__list_schemas and mcp__aep__get_schema. More detailed field view than field-discovery.
---

# Explore Data Schemas

## When to Load

- "show me our schemas", "list all schemas"
- "explore / inspect schema X"
- "what field groups are on schema Y"
- "which schemas are profile-enabled"
- "what's the structure of the ExperienceEvent schema"

---

## API Approach

### List all schemas

```
mcp__aep__list_schemas   — returns all schemas in the active sandbox
```

REST: `GET {AEP_BASE_URL}/data/core/schemaregistry/tenant/schemas`

Key response fields per schema:
- `title` — human-readable name
- `$id` — schema URI
- `meta:class` — profile, experienceEvent, or record
- `meta:altId` — short ID usable in follow-up calls
- `unifiedProfile.enabled` — whether Profile is enabled

### Inspect a single schema

```
mcp__aep__get_schema   — full schema with all field group properties expanded
```

REST: `GET {AEP_BASE_URL}/data/core/schemaregistry/tenant/schemas/{altId}`

---

## Output Format

**List view** (all schemas):

| Title | Class | Profile Enabled | Field Groups |
|---|---|---|---|
| Individual Profile | XDM Individual Profile | Yes | 5 |
| Experience Events | XDM ExperienceEvent | Yes | 3 |

**Detail view** (single schema):

```
Schema: Individual Profile
Class:  XDM Individual Profile
Profile Enabled: Yes
Tenant: _deloitte_digitalengage

Field Groups:
  - Profile Person Details (standard)
  - Profile Personal Details (standard)
  - Consent and Preference Details (standard)
  - [Tenant Name] Custom Attributes (custom)
    Fields: accountBalance, membershipTier, proxyId

Identities:
  - email (Primary)
  - phone
  - _deloitte_digitalengage.proxyId (custom)
```

---

## Notes

- Schema Registry uses `meta:altId` (URL-encoded) for retrieval by ID
- `_{tenantId}` fields are in the custom field group; expose the tenant slug explicitly
- Load `schema-browser` skill for a richer HTML artifact rendering of a schema
