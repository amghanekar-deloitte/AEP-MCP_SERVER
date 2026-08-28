---
name: sandbox-schema-context
description: >
  Runtime schema introspection before hardcoding any field name. Load this skill
  whenever a tool reads, renders, or queries profile data, offer content, or any
  XDM entity whose field structure may differ between sandboxes (dev vs. prod,
  client A vs. client B). Teaches the `find_field` / `find_visits` /
  `probe_visits_field` / `extract_prompt_text` helpers from tools/schema_context.py
  and the SQL column-probing pattern for Query Service.
---

# Sandbox Schema Context

## Why This Skill Exists

Field names inside XDM structs (especially under `_cvs`, `_tenantId`, or custom
field groups) are **not guaranteed to be consistent between sandboxes** or schema
versions. Examples seen in production:

| Sandbox | Field in `_cvs` |
|---------|-----------------|
| dev     | `personlizedVisits` (typo retained in schema) |
| prod    | `personalizedVisit` |

Hardcoding either name causes silent failures — the field is just missing from
the response, often manifesting as "0 records" or empty sections with no error.

**Rule**: Never hardcode a nested field name from a custom field group. Always
discover it at runtime using the helpers below.

---

## Shared Module — `tools/schema_context.py`

All discovery logic lives in `tools/schema_context.py`. Import from there; do
not duplicate logic inline.

### Dict-level helpers (profile API, entity responses)

```python
from tools.schema_context import find_field, find_visits, extract_prompt_text

# Generic: find the first matching key in a dict
val = find_field(cvs, ["personalizedVisit", "personlizedVisits", "personalizedVisits"])

# Visits-specific: discovers the visits list in _cvs automatically
visits = find_visits(cvs)           # returns [] if nothing found

# Offer characteristics: extracts prompt/offer text regardless of key casing
text = extract_prompt_text(offer_characteristics)
```

`find_field` resolution order:
1. Exact match on each candidate (case-sensitive)
2. Case-insensitive exact match
3. Substring: any candidate is contained in the key name

### SQL-level helpers (Query Service / psycopg2)

When querying via Query Service (psycopg2), nested struct sub-fields must be
named in the SQL. Use `probe_visits_field` to discover the correct name before
building the query:

```python
from tools.schema_context import probe_visits_field, parse_visits_from_json_text

# Probe: tries each candidate field name with LIMIT 1; returns first that works
tbl = "aetna_dataset_profile_personalized_prompts"
visits_col = probe_visits_field(conn, tbl)   # e.g. "personalizedVisit"

if visits_col:
    cur.execute(
        f"SELECT _cvs.aetnaProxyId, CAST(_cvs.{visits_col} AS TEXT) "
        f"FROM {tbl} LIMIT {n}"
    )
    # parse result with existing _pp_parse_visits()
else:
    # Fallback: fetch whole struct, discover in Python
    cur.execute(
        f"SELECT _cvs.aetnaProxyId, CAST(_cvs AS TEXT) FROM {tbl} LIMIT {n}"
    )
    # then: visits = parse_visits_from_json_text(row[1])
```

`probe_visits_field` tries: `personalizedVisit`, `personlizedVisits`,
`personalizedVisits`, `personalisedVisit`, `personalisedVisits` — in that order.
It issues `ROLLBACK` after each failed attempt so the connection stays clean.

---

## When to Load This Skill

Load **before** any of these actions:

| Action | Reason |
|--------|--------|
| Rendering profile data from `/data/core/ups/access/entities` | `_cvs` fields vary by sandbox |
| Querying `_cvs.*` columns via Query Service | SQL field names must match schema |
| Reading offer characteristics (`xdm:characteristics`) | Characteristic key names vary |
| Ingesting data that maps to custom field group fields | Source→XDM mapping must match actual schema |
| Building a data dictionary or schema browser view | Field paths must be discovered, not assumed |

---

## Adding Support for a New Sandbox

When onboarding a new client sandbox, check what names their custom field group
uses for any structured list fields (visits, events, interactions):

1. Fetch one profile via `view_profile` and inspect Raw JSON
2. Or run via QS: `SELECT _cvs FROM <dataset> LIMIT 1`
3. Identify the list field(s) and add their names to `_VISIT_CANDIDATES` in
   `tools/schema_context.py` if not already present

Do **not** add sandbox-specific conditionals to `profile_viewer.py`,
`query_viewer.py`, or `offer_viewer.py`. The discovery logic belongs only in
`schema_context.py`.

---

## Pattern for New Tools

Any new tool that reads from a custom XDM field group must follow this pattern:

```python
# 1. Get the raw entity dict
entity = response.get("entity", {})
tenant = entity.get("_cvs", {})          # or _tenantId, etc.

# 2. Discover field name at runtime
from tools.schema_context import find_field
events = find_field(tenant, ["myEventList", "eventList", "events"])

# 3. Render / process — never assume the list exists
for evt in (events or []):
    ...
```

For SQL tools, use `probe_qs_struct_field` with your own candidate list:

```python
from tools.schema_context import probe_qs_struct_field
col = probe_qs_struct_field(conn, "my_table", "_cvs",
                             ["myEventList", "eventList", "events"])
```
