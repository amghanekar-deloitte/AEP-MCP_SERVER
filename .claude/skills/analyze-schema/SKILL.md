---
name: analyze-schema
description: Deep analysis of an XDM schema — per-field sample values, distinct value enumerations, inferred enums, cross-schema lookups/relationships via descriptors, and cross-dataset value validation. Use when the user asks to analyze a schema, profile a schema, get distinct values, find schema relationships, or validate schema values.
---

# Analyze Schema Skill

## When to Load
- User asks "analyze schema", "profile schema", "get distinct values", "find schema relationships", "validate schema values"
- User wants field-level statistics (cardinality, null rate, enums) or cross-schema relationship discovery, not just a structural view

## When NOT to Load
- Just want the field tree with types/samples, no statistics → use `view-schema`
- Browsing multiple schemas at once → use `schema-browser`
- Designing a new schema → use `xdm-schema-design`

---

## Workflow

### Step 1 — Determine Sandbox + Target Schema
Resolve sandbox and schema the same way as `view-schema` Steps 1–2 (`get_current_org`, `mcp__aep__list_schemas`). Confirm the match with the user if ambiguous.

### Step 2 — Locate Backing Dataset(s)
Find **every** dataset matching `schemaRef.id` via `mcp__aep__list_datasets` — check the full result set (paginate if the sandbox has more than one page of datasets), don't stop at the first hit. Skip auto-generated/system dataset names (adhoc, `JOJourneyVersionsDs_*`, summaries_ds — see `schema-browser`'s classification rules). If no real backing dataset exists, skip to the structure-only fallback (see Guardrails).

For each dataset found, resolve and carry forward into Step 6:
- **Profile enabled** — `tags.unifiedProfile` on the dataset record (`enabled:true`/`enabled:false`), read directly, not inferred
- **Last ingestion date** — `mcp__aep__list_batches(dataset_id=..., status="success", limit=1)`, the most recent batch's `completed` timestamp

Use the most active dataset (most recent ingestion) as the source for Steps 3–5's SQL analysis. **Dataset name caveat:** the display `name` is not the Query Service table name — read `tags["adobe/pqs/table"][0]` for the actual queryable name before writing SQL (see `aep_api_quirks` memory).

### Step 3 — Enumerate Leaf Fields
Walk the `get_schema` JSON recursively. Split fields into two scopes:
- **Scalar scope** — top-level and nested object leaf fields, addressed by dot path
- **Array-item scope** — fields inside array items, addressed with `[]` in the path (matches `schema-browser`'s path convention, e.g. `personalizedVisits[].customAttributes.service_type`)

Load `sandbox-schema-context` first — resolve actual field names per sandbox before building SQL paths.

### Step 4 — Per-Field SQL Analysis
**Batch, don't iterate — never one SQL query per field.** Group 20–30 fields per query.

- **4a. Cardinality + NULL rate** — `COUNT(DISTINCT field)`, `COUNT(*) FILTER (WHERE field IS NULL)` per field, batched across the field group.
- **4b. Distinct-value enumeration** — for any field whose distinct count from 4a is ≤10, run a `GROUP BY field` to pull the full value list → render as an **inferred enum**.
- **4c. Sample values** — for high-cardinality fields (>10 distinct), pull 3–5 sample values instead of a full enumeration.

### Step 5 — Relationships & Lookups
- **5a. Explicit descriptors** — `mcp__aep__list_descriptors` for the schema; surface any relationship/lookup descriptors.
- **5b. Inferred FKs by naming pattern** — fields matching `*Id`, `*Code`, `*Namespace` are candidate foreign keys even without a descriptor. List them as "inferred, unconfirmed."
- **5c. Cross-dataset coverage check** — for each inferred/explicit relationship, check what fraction of values in this dataset resolve against the target dataset/schema. Color-code: green ≥95%, amber 80–95%, red <80%.

### Step 6 — Build Artifact
New components beyond `view-schema`'s field tree:
- **Datasets using this schema** — one row per dataset from Step 2: name, Profile-enabled (yes/no), last ingestion date. State explicitly if none were found.
- **Summary stat cards** — row count, field count, relationship count, data-quality flag count
- **Field-detail rows** — cardinality bar (visual proportion of distinct/total), enum chips (from 4b), sample-value codes (from 4c)
- **Relationship cards** — source field → target schema/field, with a coverage bar colored per the 5c thresholds
- **Data-quality flags table** — high null rate, unexpectedly low cardinality, typos (reuse `view-schema`'s typo detection), values outside inferred enum
- **Inferred-enums appendix** — full distribution (value, count, percentage) for every field flagged in 4b

### Step 7 — Save + Summarize
Write to `scratchpad/artifacts/aep-analysis-<slug>.html` (project convention) and publish with the `Artifact` tool. Print a chat summary of 20 lines or fewer: field count analyzed, relationships found, data-quality flags, PII handling note if prod, link to artifact.

---

## Guardrails

- **Cost control** — before running full cardinality analysis, check row count. If >100M rows, ask the user for confirmation and suggest `TABLESAMPLE` to bound the scan instead of a full-table pass.
- **PII by sandbox**:
  - **Dev** (`aetna-hipaa-dev`, `cvs-aetna`) — synthetic data, safe to publish as an artifact normally.
  - **Prod** (`aetna-hipaa-prod`) — real PII. Save the artifact to `scratchpad/` only — **do not publish** via the `Artifact` tool without explicit user confirmation. Add a visible PII warning banner inside the artifact itself and state it plainly in the chat summary.
- **Batch, don't iterate** — never issue one SQL statement per field; group into 20–30-field batches per Step 4.
- **Skip when impossible** — no backing dataset found → fall back to a structure-only artifact (same as `view-schema` with sampling skipped) and say so explicitly in the summary; do not fabricate statistics.

---

## Design System

Same tokens as `view-schema` (IBM Plex Mono/Sans, `#1852A3` accent, three-way theme resolution — see that skill for the full CSS block). Do not introduce a second palette.

Additional semantic tokens for this skill's coverage bars and quality flags (kept separate from the accent hue, per `artifact-design`'s rule that semantic color is not the accent):

```css
:root {
  --cov-good-bg:#E3F3E6; --cov-good-fg:#1F6B34;   /* >=95% */
  --cov-warn-bg:#FCEBD4; --cov-warn-fg:#A15C0A;   /* 80-95% */
  --cov-bad-bg: #FDE8E8; --cov-bad-fg: #9B1C1C;   /* <80% */
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --cov-good-bg:#163823; --cov-good-fg:#7FD99A;
    --cov-warn-bg:#3A250A; --cov-warn-fg:#F2B96B;
    --cov-bad-bg: #3A1414; --cov-bad-fg: #F5A3A3;
  }
}
:root[data-theme="dark"] {
  --cov-good-bg:#163823; --cov-good-fg:#7FD99A;
  --cov-warn-bg:#3A250A; --cov-warn-fg:#F2B96B;
  --cov-bad-bg: #3A1414; --cov-bad-fg: #F5A3A3;
}
```

---

## Related Skills

- `view-schema` — structural field tree this skill builds statistics on top of; reuse its typo/deprecation detection for the data-quality flags table
- `schema-browser` — registry-wide view; use for browsing rather than deep analysis
- `sandbox-schema-context` — **load before writing any analysis SQL** — resolve real field names per sandbox first
- `query-service` — batched SQL patterns, `run_query_sync`/`view_query_results`, and the cost/row-limit gotchas referenced in the guardrails above
