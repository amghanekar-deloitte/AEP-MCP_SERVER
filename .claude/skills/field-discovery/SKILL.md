---
name: field-discovery
description: >
  Discover XDM fields available for audience building in AEP — search deployed schemas
  and field groups by field name, description, or data type. Load when the user asks
  "what fields can I use to build an audience", "find the XDM path for field X",
  "what custom fields does schema Y have", "which fields are available for segmentation",
  or "show me the fields in the profile schema". Uses mcp__aep__list_schemas,
  mcp__aep__get_schema, and Schema Registry API. Returns XDM paths ready for PQL use.
---

# Field Discovery

## When to Load

- "what fields can I use to build an audience"
- "find the XDM path for [field name]"
- "what custom fields does [schema name] have"
- "which fields are indexable / available for segmentation"
- "show me the tenant fields on the profile schema"

---

## Discovery Steps

### Step 1: List profile-enabled schemas

```
mcp__aep__list_schemas   — lists all schemas in the active sandbox
```

Filter for schemas where `meta:class = "https://ns.adobe.com/xdm/context/profile"` and
`unifiedProfile.enabled = true`. These are the schemas whose fields are available for
audience building.

REST fallback:
```
GET {AEP_BASE_URL}/data/core/schemaregistry/tenant/schemas?property=meta:extends==https://ns.adobe.com/xdm/context/experienceevent,https://ns.adobe.com/xdm/context/profile
```

### Step 2: Retrieve schema details

```
mcp__aep__get_schema   — retrieves the full schema with all field groups expanded
```

The response includes `properties` with all fields, including tenant fields under `_{tenantId}`.

### Step 3: Flatten fields to XDM paths

Walk the schema `properties` tree recursively. For each leaf field, build its full dot-notation path:
- Standard fields: `person.name.firstName`, `personalEmail.address`, `loyalty.tier`
- Tenant fields: `_{tenantId}.customFieldName` (replace `_{tenantId}` with the actual tenant ID slug)
- Event fields (inside xEvent sub-queries): `event.eventType`, `event._{tenantId}.serviceCode`

---

## Search / Filter

After flattening, apply the user's search term:
- Match on field name (last path segment)
- Match on full path (substring)
- Match on `meta:description` if available
- Match on `type` (string, integer, array, object, boolean)

---

## Output Format

Return a table sorted by XDM path:

| XDM Path | Type | Schema | Standard / Custom | Segmentable |
|---|---|---|---|---|
| `consents.marketing.email.val` | string | Individual Profile | Standard | Yes |
| `loyalty.tier` | string | Individual Profile | Standard | Yes |
| `_{tenantId}.accountBalance` | number | Individual Profile | Custom | Yes |
| `event._{tenantId}.serviceBaseCode` | string | ExperienceEvent | Custom | xEvent only |

- **Segmentable**: `Yes` for profile attributes; `xEvent only` for event schema fields (must go in `select event from xEvent where ...` sub-query)
- Include the full PQL-ready path in the table — user should be able to copy it directly
- Highlight consent fields (`consents.*`) as required for any marketing segment

---

## Tenant ID Resolution

Tenant ID is the slug for the org's namespace, e.g., `_deloitte_digitalengage`, `_cvs`, `_aetna`.
Find it from the schema `$id`:
```
https://ns.adobe.com/{tenantId}/schemas/...
```
The segment after `https://ns.adobe.com/` is the tenant ID — use it to build tenant field paths.

---

## Notes

- Only profile-enabled schemas contribute to audience criteria
- ExperienceEvent fields are available but must be wrapped in `xEvent` sub-queries in PQL
- Relationship fields (B2B: accounts, opportunities) may appear but require B2B audience builder
- Never invent field paths — only return paths actually present in the retrieved schema
