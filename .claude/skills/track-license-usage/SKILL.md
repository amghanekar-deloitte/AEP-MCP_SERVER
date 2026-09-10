---
name: track-license-usage
description: >
  Show how much of AEP licensed capacity is consumed across products — addressable profiles,
  richness, compute hours, and other entitlements. Load when the user asks "show license usage",
  "how much of our license are we using", "license consumption", "are we over-provisioned",
  "profile count vs license limit", or "license utilization report". Uses AEP License Usage
  dashboard data and mcp__aep__get_hygiene_quota.
---

# Track License Usage

## When to Load

- "show license usage"
- "how much of our license are we using"
- "license consumption / utilization"
- "are we at or near our profile limit"
- "license report"

---

## License Metrics

AEP licenses are scoped to:
1. **Addressable Audience** — total unique profiles in the Profile store
2. **Profile Richness** — average data payload size per profile (bytes)
3. **Data Lake Storage** — GB stored in the data lake
4. **Compute Hours** — Query Service / Data Distiller hours
5. **Sandboxes** — number of production vs. development sandboxes

---

## API Approach

### Profile count (vs license limit)

```
mcp__aep__get_metrics
```

Metric: `timeseries.profile.profileCount` — total profiles in production sandbox.

Compare against the contracted addressable audience limit (from the order form / Admin Console > License).

### Data Hygiene quota

```
mcp__aep__get_hygiene_quota   — shows dataset TTL and record delete entitlements
```

### Sandbox count

```
mcp__aep__list_sandboxes   — count production vs. development sandboxes
```

---

## Output Format

```
License Usage Report (org: deloitte-digitalengage · 2026-09-10)

  Entitlement               Used            Licensed         Utilization  Status
  ────────────────────────────────────────────────────────────────────────────────
  Addressable Audience      142,000         5,000,000        2.8%         OK
  Production Sandboxes      2               3                66.7%        OK
  Dev Sandboxes             5               5                100%         WARN (at limit)
  Data Hygiene Quota        2 orders        10/month         20%          OK
  Query Service Hours       48h             100h/mo          48%          OK

  Profile Richness: ~12 KB/profile (estimate based on dataset size / profileCount)

  Note: License limits sourced from AEP Admin Console. Verify against your order form
  as contracted limits vary by package (Prime vs Ultimate).
```

---

## Notes

- Addressable audience counts profiles in the **production** sandbox only
- Dev sandbox profiles do not count toward the license limit
- Load `rtcdp` skill for exact guardrail values by package tier (Prime vs Ultimate)
