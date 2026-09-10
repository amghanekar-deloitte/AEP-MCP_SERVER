---
name: diagnostics-research
description: >
  Map the AEP topology relevant to a reported symptom — which schemas, datasets, dataflows,
  segments, journeys, and identity namespaces are connected to the object at the center of
  the problem. Load as part of the diagnostics loop (called from the diagnostics skill) or
  directly when the user asks "what touches this dataset", "map the dependencies of X", or
  "what's connected to this segment/schema/dataset before I change it".
---

# Diagnostics: Research

## When to Load

- Called from `diagnostics` step 2, after the symptom is captured
- Directly: "what touches / depends on [object]"
- Directly: "map dependencies of [dataset/schema/segment] before I change it"

---

## Purpose

Before generating hypotheses, build a topology map of everything connected to the symptom's
object. Hypotheses generated without this map tend to guess at causes outside the object's
actual blast radius — this step keeps the hypothesis list grounded in what can actually
reach the symptom.

---

## API Approach

Start from the symptom's named object and walk outward one hop at a time. Which calls apply
depends on the object type:

### From a dataset

```
mcp__aep__get_dataset            — schema ref, enabled flags (profile, streaming)
mcp__aep__list_batches           — recent ingestion activity into this dataset
mcp__aep__list_dataflows         — dataflows targeting this dataset
mcp__aep__list_descriptors       — identity descriptors on the dataset's schema
```

### From a schema

```
mcp__aep__get_schema             — field groups, class, profile-enabled status
mcp__aep__list_datasets          — datasets using this schema
mcp__aep__list_segments          — segments with PQL referencing this schema's fields
                                    (filter client-side by field path substring)
```

### From a segment/audience

```
mcp__aep__get_segment            — PQL, evaluation type, schema
Load field-discovery             — resolve every field path in the PQL to its schema + dataset
mcp__aep__list_merge_policies    — merge policy applied at evaluation
```

### From a journey or campaign

```
mcp__aep__get_journey / get_campaign   — entry audience, actions, channels
mcp__aep__list_segments                 — resolve entry audience ID to its definition
```

### From a dataflow

```
mcp__aep__get_dataflow           — source connection, target dataset, mapping set
mcp__aep__list_flow_runs         — recent run history and status
mcp__aep__get_mapping_set        — field-level source-to-XDM mapping
```

---

## Output Format

```
Topology Map: Segment "Gold Loyalty Members"

  Segment
   └── Schema: Loyalty Profile (profile-enabled: yes)
        └── Datasets:
             - Loyalty Profile Dataset (dev)   [last batch: 2026-09-10, SUCCESS]
             - CRM Sync Dataset                [last batch: 2026-09-08, FAILED]
        └── Fields referenced in PQL:
             - _tenant.loyaltyTier   -> present in schema
             - _tenant.visitCount    -> NOT FOUND in current schema  <-- flag
   └── Merge Policy: Default (23803271)
   └── Downstream: Loyalty Upgrade Journey (entry audience)

Flags for hypothesis generation:
  - _tenant.visitCount referenced in PQL but absent from schema
  - CRM Sync Dataset has a failed batch as of 2026-09-08
```

Always surface anomalies inline (missing fields, failed batches, disabled flags) as flags —
these become the seed hypotheses for `diagnostics-investigator`.

---

## Notes

- Stop at one hop beyond the object unless a flag found at that hop warrants going further
- This step produces a map, not a verdict — do not declare root cause here, that's what
  `diagnostics-investigator` and `diagnostics-evaluator` are for
- If the object can't be found at all (deleted, wrong ID, wrong sandbox), report that
  immediately — a missing object is often the root cause, not a research dead-end
