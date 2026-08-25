---
name: query-service
description: AEP Query Service patterns — ad-hoc async queries, synchronous row retrieval via QS PostgreSQL, query templates, scheduled queries, and the view_query_results HTML artifact tool. Load when querying AEP datasets with SQL, reading row data out of AEP, or rendering query results as an artifact. Key tools: mcp__aep__run_query, mcp__aep__run_query_sync, mcp__aep__view_query_results, mcp__aep__list_queries, mcp__aep__get_query, mcp__aep__cancel_query, mcp__aep__create_query_template, mcp__aep__list_query_templates, mcp__aep__list_scheduled_queries.
---

# Query Service

## Two Execution Modes

| Mode | Tool | Returns | Use When |
|---|---|---|---|
| Async (REST) | `mcp__aep__run_query` | Query ID — poll for completion | Long-running queries, CTAS to output dataset |
| Sync (Postgres) | `mcp__aep__run_query_sync` | Rows inline, immediately | SELECT queries, inspection, up to 5 000 rows |
| Sync + HTML | `mcp__aep__view_query_results` | HTML artifact path + text summary | Presenting results to the user in a formatted table |

**Critical rule:** The Data Access API (`GET /export/files/{id}`) times out reliably (504/ReadTimeout) — never use it to read row data. Use `run_query_sync` or `view_query_results` instead. Both connect directly to the QS PostgreSQL interface.

---

## Async Queries (`run_query`)

```
POST /data/foundation/query/queries
body: { dbName: "{sandbox}:all", sql: "...", name: "optional" }
```

- Returns `{ id: "...", state: "SUBMITTED" }` — rows are NOT included.
- Poll with `mcp__aep__get_query` until `state` is `SUCCESS` or `FAILED`.
- Pass `output_dataset_id` for CTAS (Create Table As Select) — writes results to a dataset.
- `cancel_query` requires `confirm=True` (guard against accidental cancellation).

Status values: `SUBMITTED`, `IN_PROGRESS`, `SUCCESS`, `FAILED`, `CANCELLED`

---

## Synchronous Queries (`run_query_sync`)

Connects to QS via psycopg2 using connection parameters from `/query/connection_parameters`:
- `host`, `port`, `dbName` — org-scoped
- `username` = org IMS org ID
- `password` = short-lived token from the connection_parameters response (NOT the static auth token)
- `sslmode=require`

Row limit: default 500, max 5 000. Returns `{ rowCount, columns, rows }`.

---

## HTML Artifact Tool (`view_query_results`)

Use whenever the user wants to see query results. The tool:
1. Runs the SQL synchronously via QS Postgres
2. Generates a self-contained HTML page (Formatted table + Raw JSON toggle)
3. Writes to `/tmp/aep-query-{slug}-{ts}.html`
4. Returns `{ text_summary, html_file, instruction }`

Follow the `instruction` field: display `text_summary` in your response, then read the `html_file` and publish it as an artifact. Save the artifact HTML to `scratchpad/artifacts/` per project convention.

---

## SQL Patterns

Table names in QS match dataset names exactly (case-sensitive). Use double-quotes for names with special characters:

```sql
-- Profile dataset
SELECT * FROM "aetna_dataset_profile_personalized_prompts" LIMIT 10;

-- Access tenant-specific fields
SELECT to_json(_cvs) FROM "aetna_dataset_profile_personalized_prompts" LIMIT 5;

-- ExperienceEvent dataset
SELECT _id, timestamp, eventType FROM "aetna-dataset-event-personalized-prompts" LIMIT 20;

-- identityMap access
SELECT identityMap['ProxyId'][0].id AS proxy_id FROM "dataset_name" LIMIT 10;

-- Cast complex types
SELECT _cvs."aetnaProxyId" AS proxy_id,
       CAST(_cvs."personlizedVisits" AS TEXT) AS visits
FROM "aetna_dataset_profile_personalized_prompts" LIMIT 20;
```

---

## Query Templates

Save reusable queries as templates:

```
mcp__aep__create_query_template(name, sql, description)
mcp__aep__list_query_templates()
mcp__aep__get_query_template(template_id)
```

Templates are sandbox-scoped. Use them for repeated inspection queries or standard validation queries.

---

## Scheduled Queries

```
mcp__aep__list_scheduled_queries()          — list all scheduled (recurring) queries
mcp__aep__list_query_runs(schedule_id)      — list individual runs for a schedule
```

Scheduled queries run on a cron-like cadence defined at creation. Use `list_query_runs` to check if the last run succeeded or failed.

---

## Gotchas

- **Dataset name case-sensitivity**: QS table names match the dataset name exactly. `personalized` finds nothing; the full exact name is required.
- **Async REST returns no rows**: `run_query` submits a job — call `get_query` to poll. Never assume the submit response contains data.
- **Token in connection params**: The `password` for psycopg2 is the `token` field from `/query/connection_parameters`, not the Authorization header token. Both are short-lived; always fetch fresh connection parameters.
- **`view_personalized_prompts`**: Aetna-specific tool for the `aetna_dataset_profile_personalized_prompts` dataset — parses composite `personlizedVisits` tuples with category badges. Use it instead of a generic `view_query_results` for that dataset.

---

## Related Skills

- `aep-fundamentals` — authentication, environment variables, org profile setup
- `data-ingestion` — batch upload and monitoring (Stage 6)
- `data-validation` — post-ingestion validation queries (Stage 7)
