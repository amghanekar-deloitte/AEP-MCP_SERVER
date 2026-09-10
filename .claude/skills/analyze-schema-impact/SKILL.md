---
name: analyze-schema-impact
description: >
  Analyze what would break or be affected downstream if a schema or field is changed,
  deprecated, or removed in AEP. Load when the user asks "what happens if I remove field X",
  "what breaks if I change schema Y", "impact analysis for this schema change",
  "is it safe to deprecate field Z", or "what depends on this schema". Traces downstream
  dependencies: datasets, audiences (segments), journeys, dataflows, and identity descriptors.
---

# Analyze Schema Impact

## When to Load

- "what breaks if I change / remove / deprecate [field or schema]"
- "impact analysis for schema change"
- "is it safe to remove field X"
- "what depends on schema Y"

---

## Impact Surface — What to Check

For a schema change, check each layer:

### 1. Datasets

```
mcp__aep__list_datasets   — filter by schemaRef.$id matching the target schema
```

Any dataset using this schema is affected by structural changes. Removing a required field breaks ingestion.

### 2. Audience Segments (PQL references)

```
mcp__aep__list_segments   — retrieve all segment definitions
```

Scan each segment's `expression.value` (PQL) for references to the changed field path. A segment referencing a removed field evaluates to 0 or errors at next evaluation.

### 3. Journeys (AJO)

```
mcp__aep__list_journeys   — list all journeys
```

Check journey conditions and personalization blocks for field references. Field removal can break journey entry criteria or conditional splits.

### 4. Dataflows / Mapping Sets

```
mcp__aep__list_mapping_sets   — list data prep mappings
mcp__aep__list_dataflows
```

Source-to-XDM mappings reference target field paths. A changed path breaks the mapping and silently drops the field from ingested records.

### 5. Identity Descriptors

```
mcp__aep__list_descriptors   — filter type=xdm:descriptorIdentity
```

If the changed field is an identity descriptor, removal affects profile stitching and identity graph.

### 6. Computed Attributes

```
mcp__aep__list_computed_attributes
```

Computed attributes referencing the field will produce null values or errors after removal.

---

## Output Format

```
Impact Analysis: Removing field `loyalty.tier`
Schema: Individual Profile

AFFECTED                                  RISK
────────────────────────────────────────  ──────────
Datasets (2)
  - Profile Dataset (dev)                 Ingestion drops field silently
  - Profile Dataset (prod)                Ingestion drops field silently

Segments (3)
  - Gold Loyalty Members                  PQL breaks — evaluates to 0
  - High Value Customers                  PQL broken — references loyalty.tier
  - Email Reengagement                    Indirect — check full PQL

Journeys (1)
  - Loyalty Upgrade Journey               Entry condition broken

Mapping Sets (2)
  - CSV to Profile Mapping                Target path invalidated

Computed Attributes (0)
  - None affected

Identity Descriptors: No impact
```

- Color-code by risk: HIGH (direct reference), MEDIUM (indirect), LOW (no current reference)
- Recommend: deprecate the field first (`meta:status: deprecated`) rather than deleting
