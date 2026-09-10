---
name: audience-search
description: >
  Find, list, and inspect AEP audiences (segment definitions) by name, ID, description,
  or evaluation type. Load when the user asks to search for an audience, find a segment,
  look up an audience by name or ID, list all audiences, check if an audience exists,
  or inspect audience membership count or PQL expression. Uses mcp__aep__list_segments
  and mcp__aep__get_segment when available; falls back to Segmentation REST API.
---

# Audience Search

## When to Load

- "find audience named X", "look up segment Y"
- "list all audiences", "what audiences do we have"
- "does an audience called X exist"
- "show me the PQL for audience X"
- "what is the membership count of audience X"

---

## Search Strategy

### Via MCP (preferred)

```
mcp__aep__list_segments   — list all segment definitions in the active sandbox
mcp__aep__get_segment     — retrieve one definition by segmentId
```

Filter results in-memory on `name` (case-insensitive substring) or `description`.

### Via REST (fallback when MCP unavailable)

```
GET {AEP_BASE_URL}/data/core/ups/segment/definitions?limit=100
Headers: Authorization: Bearer {token}
         x-api-key: {AEP_CLIENT_ID}
         x-gw-ims-org-id: {AEP_ORG_ID}
         x-sandbox-name: {AEP_SANDBOX_NAME}
```

Paginate via `_links.next.href` until all results are collected. Match on `name` field.
Retrieve a single definition: append `/{segmentId}` to the path.

---

## Output Format

Present results as a table:

| Name | ID | Evaluation Type | Estimated Size | Description |
|---|---|---|---|---|

- **Evaluation Type**: `batch`, `streaming`, or `edge` (from `evaluationInfo`)
- **Estimated Size**: show `profileCount` or `memberCount` if available; otherwise `—`
- For a single result: show the full PQL expression in a code block below the table
- If zero results: state clearly — do NOT invent audiences

---

## Key Fields in the API Response

```json
{
  "id": "...",
  "name": "...",
  "description": "...",
  "expression": { "type": "PQL", "format": "pql/text", "value": "..." },
  "evaluationInfo": {
    "batch":      { "enabled": true },
    "continuous": { "enabled": false },
    "synchronous":{ "enabled": false }
  },
  "profileCount": 12345
}
```

---

## Notes

- Always search in the active sandbox (`AEP_SANDBOX_NAME`)
- IDs are UUIDs — exact match only when user provides a full UUID
- `profileCount` is stale on B2B-simplification orgs; report it with a "last evaluated" caveat
- Never fabricate audience IDs or counts
