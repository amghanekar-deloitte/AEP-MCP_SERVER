---
name: find-duplicate-audiences
description: >
  Find AEP audience definitions that are duplicates of or very similar to each other —
  identical PQL, near-identical names, or overlapping criteria. Load when the user asks
  "find duplicate audiences", "do we have duplicate segments", "are there similar audiences",
  "audience hygiene check", or "consolidate our audiences". Helps reduce audience sprawl
  and identify redundant definitions.
---

# Find Duplicate Audiences

## When to Load

- "find duplicate audiences / segments"
- "do we have any duplicate definitions"
- "are there similar audiences"
- "audience hygiene / cleanup"
- "consolidate our audiences"

---

## Detection Approach

### Step 1: Fetch all audience definitions

```
mcp__aep__list_segments   — retrieve all definitions with name, PQL, evaluationType
```

### Step 2: Detect duplicates across three signals

**Signal 1 — Identical PQL (exact duplicates)**
Normalize PQL: lowercase, strip extra whitespace, sort top-level `and` clauses alphabetically.
Group by normalized PQL. Any group with 2+ definitions = exact duplicate.

**Signal 2 — Near-identical names**
Use fuzzy string match: Levenshtein distance ≤ 3, or one is a substring of the other.
Flag pairs like "Gold Members" / "Gold Members v2" / "Gold Members (copy)".

**Signal 3 — Overlapping profile attribute predicates**
Extract top-level profile predicates (non-xEvent clauses).
Two definitions with identical profile predicates but different event sub-queries are likely redundant variants.

---

## Output Format

```
Audience Duplicate Report (sandbox: cvs-aetna)
Total audiences: 42

EXACT DUPLICATES (same PQL, different name)
  Group A:
    - Gold Loyalty Members        (ID: abc123 · created 2026-01-15)
    - Gold Members - Email        (ID: def456 · created 2026-03-02)
    PQL: loyalty.tier = "Gold" and consents.marketing.email.val = "y"
    Recommendation: Keep abc123 (older, likely authoritative); delete or merge def456

NEAR-IDENTICAL NAMES (possible copies)
    - High Value Customers        (ID: ghi789)
    - High Value Customers v2     (ID: jkl012)
    - High Value Customers FINAL  (ID: mno345)
    Recommendation: Review PQLs; consolidate to one authoritative definition

OVERLAPPING PROFILE PREDICATES
    - Gold Email Members (ID: pqr678) — loyalty.tier="Gold", consents.email="y" + purchase event
    - Gold SMS Members   (ID: stu901) — loyalty.tier="Gold", consents.sms="y" + purchase event
    Note: These intentionally differ by channel consent — not true duplicates

No duplicates: 34 audiences
```

---

## Notes

- Never delete an audience — only flag and recommend; deletion requires explicit user action
- An audience used in an active journey or campaign should NEVER be consolidated without checking `trace-audience-lineage` first
