---
name: analyze-data-fields
description: >
  Find a data field across AEP datasets and show everywhere it is used, with sample values
  from Query Service. Load when the user says "show me sample values for field X",
  "what values does field Y have", "analyze field distribution", "what's in this field",
  or "show me field X across all datasets". Combines schema lookup with Query Service
  sampling to show actual data values alongside field metadata.
---

# Analyze Data Fields

## When to Load

- "show me sample values for field X"
- "what values does [field] have in our data"
- "analyze / profile field Y"
- "what's actually in the [field] field"
- "distribution of values for [field]"

---

## Approach

### Step 1: Locate the field

Use `look-up-schema-fields` skill to find the XDM path and which dataset(s) contain it.

### Step 2: Query for sample values

Use Query Service to retrieve actual values:

```sql
SELECT {field_path}, COUNT(*) as frequency
FROM {dataset_name}
WHERE {field_path} IS NOT NULL
GROUP BY {field_path}
ORDER BY frequency DESC
LIMIT 20
```

For nested/struct fields, cast to text first:
```sql
SELECT CAST({struct_field} AS TEXT) as val, COUNT(*) as n
FROM {dataset_name}
GROUP BY val ORDER BY n DESC LIMIT 20
```

Run via:
```
mcp__aep__run_query_sync   — synchronous Query Service execution
```

Or: `POST {AEP_BASE_URL}/data/core/query/queries` then poll for results.

### Step 3: Compute field stats

From the query result:
- **Distinct values**: count of unique values
- **Null rate**: rows where field IS NULL / total rows
- **Top values**: top 10 by frequency
- **Type distribution**: for mixed-type fields

---

## Output Format

```
Field Analysis: loyalty.tier
Dataset: Profile Dataset (dev) · 142,000 rows

Top Values:
  Tier         Count    %
  Bronze       58,000   40.8%
  Silver       42,000   29.6%
  Gold         28,000   19.7%
  Platinum     12,000    8.5%
  [null]        2,000    1.4%

Stats:
  Distinct values: 4
  Null rate: 1.4%
  Most common: Bronze (40.8%)
```

---

## Notes

- QS field paths use dot notation for nested structs; struct sub-fields must be cast to TEXT for GROUP BY
- For arrays: use EXPLODE or lateral view pattern
- Load `sandbox-schema-context` to discover the actual field name if the column name varies by sandbox
