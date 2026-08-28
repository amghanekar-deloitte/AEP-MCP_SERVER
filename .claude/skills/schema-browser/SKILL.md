---
name: schema-browser
description: "Fetch all schemas from AEP Schema Registry and render an interactive HTML artifact — expandable cards per schema showing field paths, data types, identity, required, deprecated, and enum tags. Use when the user asks to browse schemas, inspect schema details, or wants a field-level view of the registry for any sandbox."
---

# Schema Browser Skill

## When to Load
- User asks to "show schemas", "list schema details", "browse schemas", or "what fields does schema X have"
- User wants a visual or structured view of the AEP Schema Registry
- User wants to compare schemas or identify field overlaps across schemas
- User wants to know identity fields, required fields, or deprecated fields in deployed schemas

## When NOT to Load
- Designing or deploying new schemas (use xdm-schema-design)
- Creating datasets (use dataset-automation)
- Post-ingestion data validation (use data-validation)

---

## Workflow

### Step 1 — Fetch Schema List

Call `mcp__aep__list_schemas` twice to get the full registry (API returns max 100 per page):

```
list_schemas(limit=100, start=0, sandbox=<active_sandbox>)
list_schemas(limit=100, start=100, sandbox=<active_sandbox>)
```

Combine results. Filter into two buckets:

**Custom schemas** — keep schemas whose `$id` or `title` does NOT match any of these patterns:
- `JOJourneyVersionsDs_` prefix in title
- `meta:schemaType: "Adhoc"` in properties (auto-generated adhoc dataset schemas)
- `_experience` only schemas with no tenant field groups (pure AJO provisioning)

AJO provisioning schemas to treat as "system/AJO" (show card but skip field detail):
- AJO Channel Tracking Event Schema
- AJO Secondary Recipient Feedback Event Schema
- Journey Step Event schema for Journey Orchestration
- Initial Profile schema for Orchestrated Campaigns
- Recipients (adhoc-v2 type)

**AJO adhoc** — everything else (JOJourneyVersionsDs_*, summaries_ds, test schemas). Collect these into a collapsed "System / AJO Adhoc" section at the bottom.

### Step 2 — Fetch Schema Field Details

For each **custom schema**, call `mcp__aep__get_schema` to retrieve its full JSON payload. Run all calls in parallel (one batch).

Extract from each schema:
- `meta:class` → determines Profile / ExperienceEvent / Lookup classification
- `meta:version` → version chip (amber/hot if ≥ 1.5)
- `$id` → use last 8 chars as display ID chip
- Custom field groups under the tenant namespace (`_<tenantId>.*`)
- Identity fields: look for `meta:descriptors` with `@type: "xdm:descriptorIdentity"` and `xdm:isPrimary: true`
- Required fields: `required: []` array at any object level
- Deprecated fields: `meta:status: "deprecated"` on individual properties

### Step 3 — Parse Fields Into Flat Display List

For each custom schema, build a flat field list for the expand panel:

```
{ path, type, tags[] }
```

- **path**: Use dot-notation for nested objects, `[]` suffix for array items
  - Example: `personalizedVisits[].customAttributes.service_type`
  - Group separator row for top-level objects/arrays (use `.fgroup-row` class)
- **type**: Map XDM `type` + `format` to display type using the table below
- **tags**: Collect from schema inspection (see tag rules below)

#### XDM → Display Type Mapping

| XDM type + format | Display | CSS class |
|---|---|---|
| `string` (no format) | string | `tc-str` |
| `string` + `date` | date | `tc-date` |
| `string` + `date-time` | date-time | `tc-dt` |
| `integer` or `number` | int / number | `tc-int` |
| `boolean` | boolean | `tc-bool` |
| `array` | array&lt;itemType&gt; | `tc-arr` |
| `object` | object | `tc-obj` |
| `object` + `additionalProperties` | map&lt;string&gt; | `tc-map` |
| identityMap | identityMap | `tc-map` |

#### Tag Rules

| Condition | Tag label | CSS class |
|---|---|---|
| Field has primary identity descriptor | Primary Identity | `tg-id` |
| Field appears in schema's `required[]` | Required | `tg-req` |
| Property has `meta:status: "deprecated"` | Deprecated | `tg-dep` |
| Property has `enum: [...]` | Enum: val1/val2 | `tg-enum` |
| Field is from XDM standard field group | XDM Standard | `tg-sys` |

### Step 4 — Classify Schemas

| XDM meta:class | Display badge | CSS |
|---|---|---|
| `xdm/context/profile` | Profile | `.bp` (green) |
| `xdm/context/experienceevent` | Event | `.be` (blue) |
| `xdm/context/record` or used as lookup | Lookup | `.bl` (purple) |

Note: Some schemas use Profile class but function as event/trigger sources — note the discrepancy in the field panel.

### Step 5 — Render HTML Artifact

Write the artifact to the scratchpad directory and deploy using the `Artifact` tool.

Use the design system below verbatim — do not change palette, component structure, or CSS class names. The user has confirmed this design.

If the user has previously deployed a schema-browser artifact for this sandbox (URL stored in conversation), redeploy to that same URL by passing `url=<existing_url>` to the Artifact tool. Otherwise create a new artifact.

---

## HTML Design System

### Palette (CSS variables)

```css
:root {
  --ground:    #EFF2F7;
  --surface:   #FFFFFF;
  --surface2:  #F7F9FC;
  --border:    #D6DCE8;
  --text-pri:  #0A1628;
  --text-sec:  #4A5878;
  --text-dim:  #8A94A8;
  --accent:    #005FCC;
  --accent-bg: #E5EFFA;
  --tp-bg: #E6F4EA; --tp-fg: #1B6B2A;   /* Profile — green */
  --te-bg: #E3EEF9; --te-fg: #0A4A8C;   /* Event — blue */
  --tl-bg: #F3ECF9; --tl-fg: #5A2D8C;   /* Lookup — purple */
}
```

### Type Chips (`.tc`)

```css
.tc-str  { background:#F0F4FF; color:#3B5BDB; }
.tc-int  { background:#FFF4E6; color:#C2410C; }
.tc-bool { background:#F3ECF9; color:#5A2D8C; }
.tc-date { background:#E6F4EA; color:#1B6B2A; }
.tc-dt   { background:#E3F9F5; color:#0D7B6A; }
.tc-arr  { background:#FFF9E6; color:#A16207; }
.tc-obj  { background:#F5F5F5; color:#555;    }
.tc-map  { background:#FDE8E8; color:#9B1C1C; }
```

### Tag Pills (`.tg`)

```css
.tg-id   { background:#FEF3C7; color:#92400E; }   /* amber — Primary Identity */
.tg-req  { background:#E6F4EA; color:#1B6B2A; }   /* green — Required */
.tg-dep  { background:#FEE2E2; color:#991B1B; text-decoration:line-through; } /* red — Deprecated */
.tg-enum { background:#EEF2FF; color:#3730A3; }   /* indigo — Enum */
.tg-sys  { background:var(--surface2); color:var(--text-dim); } /* grey — XDM Standard */
```

### Version Chip

```css
.ver     { background:var(--surface2); color:var(--text-sec); border:1px solid var(--border); border-radius:4px; font-variant-numeric:tabular-nums; padding:1px 7px; font-size:11px; }
.ver.hot { background:#FEF3C7; color:#B45309; border-color:#FDE68A; } /* v1.5+ */
```

### Card Structure

```html
<div class="card">
  <div class="card-head" onclick="toggleCard(this)">
    <div class="card-top">
      <span class="card-name">{Schema Title}</span>
      <span class="badge bp|be|bl">{Profile|Event|Lookup}</span>
    </div>
    <div class="card-meta">
      <span class="ver [hot]">v{version}</span>
      <span style="font-size:11px;color:var(--text-dim)">Identity: {identityField} ({namespace})</span>
    </div>
    <div class="card-meta">
      <span class="id-chip">{short $id}</span>
      <button class="expand-btn"><span class="arr">▼</span> Fields</button>
    </div>
  </div>
  <div class="field-panel">
    <div class="field-panel-inner">
      <table class="ftable">
        <thead><tr><th>Field</th><th>Type</th><th>Tags</th></tr></thead>
        <tbody>
          <!-- identity row gets class "identity-row" -->
          <tr class="identity-row">
            <td class="td-path">{fieldName}</td>
            <td><span class="tc tc-str">string</span></td>
            <td class="td-tags">
              <span class="tg tg-id">Primary Identity</span>
              <span class="tg tg-req">Required</span>
            </td>
          </tr>
          <!-- group separator -->
          <tr class="fgroup-row"><td colspan="3">{Group Label}</td></tr>
          <!-- nested field with path prefix -->
          <tr>
            <td class="td-path"><span class="obj-pfx">{parent}.</span>{field}</td>
            <td><span class="tc tc-date">date</span></td>
            <td></td>
          </tr>
          <!-- note row -->
          <tr class="note-row"><td colspan="3">{observation text}</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
```

### Toggle JavaScript

```js
function toggleCard(head) {
  const panel = head.nextElementSibling;
  const btn = head.querySelector('.expand-btn');
  const isOpen = panel.classList.toggle('open');
  if (btn) btn.classList.toggle('open', isOpen);
}
```

Field panel is hidden by default (`display:none`) and shown when `.open` is added.

### Stats Bar

Show four stat cells at the top: Total schemas, Custom schemas, Profile count, Event count, Lookup count, AJO Adhoc count.

### Observations Block

After the stats bar, render a bordered observations block (`border-left: 3px solid var(--accent)`) with 3–5 non-obvious design issues discovered during field inspection (typos, class mismatches, deprecated fields in use, serialised JSON string fields, duplicate schemas, etc.).

---

## System / AJO Schema Handling

For AJO system schemas (provisioning schemas, Recipients adhoc-v2, Journey Step Event, etc.):
- Render a card with the badge and version chip
- In the field panel, show a single `<tr class="note-row">` explaining it is an AJO system schema and directing the user to the Schema Registry UI for full detail
- Do NOT attempt to render all fields — the payload is too large and the schema is not editable

For JOJourneyVersionsDs_* and other auto-generated adhoc schemas:
- Collect into a collapsed "System / AJO Adhoc" section at the bottom of the page
- Render as a simple table (title, short ID, version) inside a toggle

---

## Sandbox Awareness

Always check the active sandbox before calling `list_schemas`. Use `get_current_org` or read from the active profile. Include the sandbox name and org ID in the artifact header.

If the user asks to show schemas for a different sandbox, call `switch_sandbox` first, then re-run this skill from Step 1.

---

## Field Detail Depth

For custom schemas with fewer than 30 top-level custom fields: render all fields inline in the panel.

For custom schemas with 30+ top-level custom fields (e.g. large Member Universe schemas): render top-level fields and one level of nesting. For deeply nested arrays, use a group row showing the array name and render its child fields indented.

For schemas where `get_schema` returns a payload exceeding the tool's display limit: render only the fields visible in the truncated response, add a `<tr class="note-row">` noting the schema is too large to display fully, and direct the user to the Schema Registry UI.

## Related Skills

- `sandbox-schema-context` — **load alongside schema-browser when building tools that read or render data** from a schema; use `find_field` to locate the correct field key at runtime before hardcoding any custom field group path discovered from this browser
