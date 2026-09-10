---
name: audit-account-activity
description: >
  Show who created, changed, or deleted AEP resources — datasets, schemas, audiences,
  and other objects. Load when the user asks "who created dataset X", "who deleted schema Y",
  "show audit log", "what changed recently", "who modified audience Z", or "audit trail for
  this resource". Uses the AEP Audit Query API to retrieve user activity logs with timestamps,
  actors, and action types.
---

# Audit Account Activity

## When to Load

- "who created / changed / deleted [resource]"
- "show audit log / audit trail"
- "what changed in the last [time period]"
- "who modified audience / schema / dataset X"
- "recent activity in this sandbox"

---

## API Approach

AEP provides an Audit Query API (part of Audit Service):

```
GET {AEP_BASE_URL}/data/foundation/audit/events
Headers: Authorization, x-api-key, x-gw-ims-org-id, x-sandbox-name
Params:  limit, start (ISO timestamp), end (ISO timestamp),
         entityType (dataset, schema, segment, etc.), entityId, action
```

Key response fields per event:
- `timestamp` — when the action occurred (ISO 8601)
- `user.id` — user or service account that performed the action
- `user.email` — user's email
- `action` — `CREATE`, `UPDATE`, `DELETE`, `ACTIVATE`, `DEACTIVATE`, `PUBLISH`
- `entityType` — type of resource affected (dataset, schema, segment, journey, campaign, etc.)
- `entityId` — ID of the resource
- `entityName` — display name of the resource
- `requestBody` — (when available) what changed

---

## Filtering Options

| Filter | API Param | Example |
|---|---|---|
| By resource type | `entityType` | `dataset`, `schema`, `segment`, `dataflow` |
| By resource ID | `entityId` | specific dataset/schema/segment UUID |
| By time range | `start` + `end` | last 7 days |
| By action | `action` | `DELETE`, `CREATE` |
| By user | (filter in-memory on `user.email`) | |

---

## Output Format

```
Audit Log (sandbox: cvs-aetna · last 7 days)

  Timestamp (UTC)      User                    Action    Resource Type  Resource Name
  ──────────────────────────────────────────────────────────────────────────────────────
  2026-09-10 14:32     amghanekar@deloitte.com  CREATE    segment        Gold Loyalty Members
  2026-09-10 09:15     amghanekar@deloitte.com  UPDATE    dataset        Profile Dataset (dev)
  2026-09-09 16:44     system@adobe.com         CREATE    batch          (ingestion batch)
  2026-09-08 11:02     amghanekar@deloitte.com  DELETE    segment        Old Test Segment
  2026-09-07 09:00     amghanekar@deloitte.com  ACTIVATE  journey        Loyalty Upgrade Journey
```

For a specific resource: show only events for that entity, reverse-chronological.
