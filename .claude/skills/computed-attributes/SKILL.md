---
name: computed-attributes
description: AEP Computed Attributes — profile-level scalar aggregations derived from ExperienceEvent data (e.g. total purchase amount last 30 days, number of ER visits in last year). Covers creation, the draft-to-published lifecycle, update and deprecation via JSON Patch, status monitoring, and when to use computed attributes vs segment membership. Load when creating, listing, or debugging computed attributes. Key tools: mcp__aep__create_computed_attribute, mcp__aep__get_computed_attribute, mcp__aep__list_computed_attributes, mcp__aep__update_computed_attribute.
---

# Computed Attributes

Computed attributes are profile-level scalar values derived by aggregating ExperienceEvent data over a time window. They are recalculated continuously as new events arrive and stored on the unified profile — available in segmentation, personalization, and decisioning without re-querying event data.

API base: `/data/core/ups/config/computedAttributes`

---

## Lifecycle

```
Create (POST)  →  NEW  →  PROCESSING  →  PROCESSED
                                       →  FAILED
                                       →  DISABLED (deprecated)
```

- `NEW` — definition saved, not yet published.
- `PROCESSING` — the system is building/rebuilding the attribute across all profiles.
- `PROCESSED` — attribute is live and available on profiles.
- `FAILED` — expression error or infrastructure issue; check the error details on the definition.
- `DISABLED` — manually deprecated via PATCH.

---

## Tool Reference

```
mcp__aep__list_computed_attributes(status="")      # filter by status: NEW, PROCESSING, PROCESSED, FAILED, DISABLED
mcp__aep__get_computed_attribute(attribute_id)
mcp__aep__create_computed_attribute(name, display_name, description, expression, duration_unit, duration_value)
mcp__aep__update_computed_attribute(attribute_id, patches)
```

---

## Creating a Computed Attribute

```python
mcp__aep__create_computed_attribute(
    name="totalPurchaseAmount30d",          # internal name — alphanumeric, no spaces
    display_name="Total Purchase Amount (30 Days)",
    description="Sum of all purchase order totals in the last 30 days",
    expression="sum(commerce.order.priceTotal)",  # PQL aggregation over ExperienceEvent
    duration_unit="DAYS",                   # DAYS, WEEKS, or MONTHS
    duration_value=30
)
```

`name` must be unique per sandbox. The same name in a different sandbox is a new attribute.

---

## PQL Expressions for Computed Attributes

Expressions aggregate ExperienceEvent fields over the lookback window. All PQL here operates on the event stream — no `xEvent` wrapper needed (the service scopes to events automatically).

| Pattern | Expression |
|---|---|
| Sum a numeric field | `sum(commerce.order.priceTotal)` |
| Count events | `count()` |
| Count matching events | `count(eventType = "commerce.purchases")` |
| Maximum value | `max(commerce.order.priceTotal)` |
| Minimum value | `min(commerce.order.priceTotal)` |
| Most recent value | `mostRecentValue(_{tenant}.customField)` |
| Boolean — any event matched | `any(eventType = "commerce.purchases")` |

Use standard XDM event paths. For custom fields: `_{tenantId}.fieldName`. Find the tenant ID from the deployed schema `$id`.

---

## Updating a Computed Attribute

Use JSON Patch operations:

```python
mcp__aep__update_computed_attribute(
    attribute_id="ca-abc123",
    patches=[
        {"op": "replace", "path": "/description", "value": "Updated description"},
        {"op": "replace", "path": "/duration/value", "value": 60}
    ]
)
```

Changing `expression` or `duration` on a `PROCESSED` attribute triggers re-processing (returns to `PROCESSING`). Changing only `description` or `displayName` does not.

---

## Deprecating (Disabling) a Computed Attribute

```python
mcp__aep__update_computed_attribute(
    attribute_id="ca-abc123",
    patches=[{"op": "replace", "path": "/status", "value": "DISABLED"}]
)
```

A `DISABLED` attribute stops updating and is removed from profile union views. It cannot be re-enabled — create a new attribute if needed.

---

## Computed Attributes vs Segment Membership

| Need | Use |
|---|---|
| Binary in/out membership | Segment definition |
| Actual scalar value (sum, count, max) | Computed attribute |
| Reuse the same aggregation across many segments | Computed attribute + reference the CA field in segment PQL |
| Value available in personalization templates | Computed attribute (available on profile) |
| Event look-back beyond 30 days in segmentation | Not possible in segmentation (30-day B2B cap); use CA with MONTHS duration instead |

Computed attributes appear on the profile under `_{tenantId}.{name}` once in `PROCESSED` status. Reference them in segment PQL as profile attributes:

```pql
_{tenantId}.totalPurchaseAmount30d >= 500
and consents.marketing.email.val = "y"
```

---

## Monitoring

```python
# Check status of all attributes
mcp__aep__list_computed_attributes(status="PROCESSING")   # find ones still computing
mcp__aep__list_computed_attributes(status="FAILED")       # find failed ones

# Get error details on a failed attribute
mcp__aep__get_computed_attribute("ca-abc123")             # check errorDetails field
```

Processing time depends on profile volume — expect minutes for small sandboxes, up to hours for production orgs with millions of profiles.

---

## Related Skills

- `segment-management` — PQL for audience segments; computed attributes can be referenced in PQL
- `profile-enablement` — enabling profile on schemas/datasets (prerequisite for computed attributes)
- `xdm-schema-design` — finding the correct XDM event field paths for expressions
