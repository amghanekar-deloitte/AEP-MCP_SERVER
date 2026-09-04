---
name: view-schema
description: Fetch an XDM schema from AEP and render its field structure as a designed HTML artifact with color-coded types, collapsible nested objects, and inline deprecation/typo warnings. Use when the user asks to show a schema, get schema structure, view schema fields, or get the structure of a named schema.
---

# View Schema Skill

## When to Load
- User asks "show schema", "get schema structure", "view schema fields", "get me the structure of X"
- User wants a single schema's field tree with types and sample values, not a registry-wide browse

## When NOT to Load
- Browsing/comparing every schema in the registry at once → use `schema-browser`
- Statistical field analysis (cardinality, distinct values, relationships) → use `analyze-schema`
- Designing or deploying a new schema → use `xdm-schema-design`
- Reading a field name at runtime inside a tool (not for display) → use `sandbox-schema-context`

---

## Workflow

### Step 1 — Determine Sandbox
Resolve prod / dev / explicit sandbox from the user's request or the active org profile (`get_current_org`). If ambiguous, ask.

### Step 2 — Locate Schema
Call `mcp__aep__list_schemas` (paginate in batches of 100 if needed) and match by title or `$id` substring against what the user named. If more than one candidate matches, confirm with the user before proceeding.

### Step 3 — Fetch Full Schema
Call `mcp__aep__get_schema` with the resolved `$id` for the full JSON payload.

### Step 3.5 — Sample Values + Dataset List
Find **every** dataset referencing this schema's `$id` via `mcp__aep__list_datasets` — do not stop at the first match (a schema can back more than one dataset; check the full result set, paginating if the sandbox has more datasets than one page). For each dataset found, resolve:
- **Profile enabled** — read `tags.unifiedProfile` (`enabled:true`/`enabled:false`) directly from the dataset record; don't infer it from anything else
- **Last ingestion date** — `mcp__aep__list_batches(dataset_id=..., status="success", limit=1)`, most recent batch's `completed` timestamp

If no backing dataset exists at all, skip sampling and render structure-only. Otherwise sample 1–3 values per leaf field from the primary/most-active dataset using **batched** SQL via `mcp__aep__run_query_sync` — group multiple leaf fields into a single `SELECT`, never one query per field (see `query-service` skill).

**Dataset name caveat:** the dataset's display `name` is not necessarily its Query Service table name — the real queryable table name lives in `tags["adobe/pqs/table"][0]`. Read that before writing SQL against it (see `aep_api_quirks` memory).

Load `sandbox-schema-context` before writing the SQL — nested field names vary between sandboxes and must be discovered, not assumed.

### Step 4 — Build the Artifact
Render using the design system below. Do not invent a new palette — reuse these tokens so schema artifacts stay visually consistent across sessions.

### Step 5 — Save
Write to `scratchpad/artifacts/aep-schema-<slug>.html` (project convention — see `feedback_artifact_storage` memory) and publish with the `Artifact` tool.

### Step 6 — Chat Summary
Print a summary of 15 lines or fewer: schema name/class, field count, identity field, count of deprecated/typo warnings found, link to the artifact.

---

## Sections Rendered (in order)

1. **Datasets using this schema** — one row per dataset found in Step 3.5: name, Profile-enabled (yes/no), last ingestion date. If none found, state that explicitly rather than omitting the section.
2. **Identity** — primary identity field(s), namespace, descriptor source
3. **Active tenant fields** — current custom field group fields, grouped by nesting level
4. **Deprecated** — fields with `meta:status: "deprecated"`, collapsed by default
5. **Standard XDM** — inherited standard field-group fields (collapsed by default)

## Type Badges

| XDM type + format | Badge label | Hue |
|---|---|---|
| `string` (no format) | string | teal |
| `string` + `date` | date | violet |
| `string` + `date-time` | date-time | violet |
| `string` + `uri-reference` | uri-ref | yellow |
| `object` | object | green |
| `array` | array&lt;itemType&gt; | amber |

## Inline Warnings

- **Typo detection** — flag when a field's `title` and its property key diverge in a way that looks like a misspelling (e.g. `personlizedVisits` key vs "Personalized Visits" title). Render as an amber inline chip next to the field.
- **Deprecation markers** — `meta:status: "deprecated"` renders the field row struck through with a red "Deprecated" chip.
- **Sample-value chips** — under each leaf field, render up to 3 sampled values as small muted chips (from Step 3.5). If sampling was skipped, omit silently — do not render an empty chip row.

---

## Design System

Three-way theme resolution (system/light/dark) — see `artifact-design` skill for the full contract. Tokens:

```css
:root {
  --bg:        #EEF2F8;
  --surface:   #FFFFFF;
  --surface-2: #F5F8FC;
  --border:    #D3DBE8;
  --text:      #101827;
  --muted:     #58637A;
  --accent:    #1852A3;
  --accent-bg: #E4EEFA;
  --mono: 'IBM Plex Mono', 'Menlo', monospace;
  --sans: 'IBM Plex Sans', system-ui, sans-serif;

  --tc-string-bg:#E1F5F3; --tc-string-fg:#0F6B62;   /* teal */
  --tc-date-bg:  #EFE7FB; --tc-date-fg:  #5B2A9E;   /* violet — date & date-time */
  --tc-uriref-bg:#FBF3D6; --tc-uriref-fg:#8A6A0A;   /* yellow */
  --tc-object-bg:#E3F3E6; --tc-object-fg:#1F6B34;   /* green */
  --tc-array-bg: #FCEBD4; --tc-array-fg: #A15C0A;   /* amber */

  --warn-typo-bg:#FCEBD4; --warn-typo-fg:#A15C0A;
  --warn-dep-bg: #FDE8E8; --warn-dep-fg: #9B1C1C;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg:#0A0F1A; --surface:#131B2C; --surface-2:#1B2540; --border:#2B3856;
    --text:#DCE5F5; --muted:#7C8AAC; --accent:#5B9BE0; --accent-bg:#14294A;
    --tc-string-bg:#0F3B37; --tc-string-fg:#5EEAD4;
    --tc-date-bg:  #2D1B4E; --tc-date-fg:  #C4A6F5;
    --tc-uriref-bg:#3A2E0A; --tc-uriref-fg:#F5D97A;
    --tc-object-bg:#163823; --tc-object-fg:#7FD99A;
    --tc-array-bg: #3A250A; --tc-array-fg: #F2B96B;
    --warn-typo-bg:#3A250A; --warn-typo-fg:#F2B96B;
    --warn-dep-bg: #3A1414; --warn-dep-fg: #F5A3A3;
  }
}
:root[data-theme="dark"] {
  --bg:#0A0F1A; --surface:#131B2C; --surface-2:#1B2540; --border:#2B3856;
  --text:#DCE5F5; --muted:#7C8AAC; --accent:#5B9BE0; --accent-bg:#14294A;
  --tc-string-bg:#0F3B37; --tc-string-fg:#5EEAD4;
  --tc-date-bg:  #2D1B4E; --tc-date-fg:  #C4A6F5;
  --tc-uriref-bg:#3A2E0A; --tc-uriref-fg:#F5D97A;
  --tc-object-bg:#163823; --tc-object-fg:#7FD99A;
  --tc-array-bg: #3A250A; --tc-array-fg: #F2B96B;
  --warn-typo-bg:#3A250A; --warn-typo-fg:#F2B96B;
  --warn-dep-bg: #3A1414; --warn-dep-fg: #F5A3A3;
}
```

Field rows use `--mono` for the field path, `--sans` for labels/prose. Nested objects are collapsible (`<button class="nested-toggle">` pattern, same JS mechanism as `schema-browser`'s `toggleCard`).

---

## Related Skills

- `schema-browser` — registry-wide view across all schemas; use when the user wants to browse/compare rather than deep-dive one schema
- `analyze-schema` — statistical field analysis (cardinality, distinct values, relationships) on top of the same schema
- `sandbox-schema-context` — **load before writing sampling SQL** — field names vary by sandbox, never hardcode
- `query-service` — batched SQL sampling patterns and the `view_query_results` / `run_query_sync` tools
- `xdm-schema-design` — for designing/deploying new schemas, not viewing existing ones
