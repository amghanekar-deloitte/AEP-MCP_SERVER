---
name: explore-connected-databases
description: >
  Explore external databases and data warehouses connected to AEP without moving data —
  Query Service federated access, Data Distiller connections, and external source connectors.
  Load when the user asks "what databases are connected", "show me external data connections",
  "can I query Snowflake from AEP", "what can I access via Query Service", or "external
  database access". Covers Query Service connections, Data Distiller, and source connectors.
---

# Explore Connected Databases

## When to Load

- "what external databases are connected to AEP"
- "can I query Snowflake / Redshift / BigQuery from here"
- "show me external data connections"
- "what can I access via Query Service"

---

## Connection Types in AEP

### 1. Query Service — Inline Data Lake Access

AEP Query Service natively accesses the AEP data lake (datasets stored as Parquet).
No external connection needed — datasets are directly queryable by their dataset name.

```
mcp__aep__list_datasets   — shows all queryable datasets
mcp__aep__run_query_sync  — executes SQL against the data lake
```

### 2. Data Distiller — External DB Export

Data Distiller allows exporting Query Service results to external destinations:
- Snowflake, Azure Synapse, Amazon Redshift, BigQuery, SFTP

Check via Flow Service for `connectionSpec.id` matching Data Distiller connectors.

### 3. Source Connectors — External Databases as Sources

AEP can ingest FROM external databases into datasets:

```
mcp__aep__list_connections        — all configured connections
mcp__aep__list_connection_specs   — available connector types
mcp__aep__get_connection          — detail for a specific connection
```

Common external DB connectors: PostgreSQL, MySQL, Microsoft SQL Server, Oracle, Snowflake (as source), IBM Db2, Azure SQL.

---

## Output Format

```
External Data Connections (sandbox: cvs-aetna)

Query Service Data Lake (always available):
  - Direct SQL access to all 12 datasets in this sandbox
  - Connect via psycopg2: host=crq.platform.adobe.io port=80 db=all

Source Connectors (ingesting FROM external):
  Name                Type            Status    Schedule
  ──────────────────────────────────────────────────────
  CRM PostgreSQL      PostgreSQL      active    daily
  Data Warehouse      Snowflake       active    weekly

Data Distiller Exports (sending TO external):
  Destination         Type            Status
  ──────────────────────────────────────────
  Analytics DW        Azure Synapse   active
```

---

## Query Service Connection String

```
Host:     crq.platform.adobe.io
Port:     80
Database: all
Username: {AEP_QS_USERNAME}  (from .env or Adobe Admin Console)
Password: {AEP_ACCESS_TOKEN}  (refreshed IMS token)
SSL:      required
```

The `AEP_QS_USERNAME` is org-specific — found in AEP UI under Query > Credentials.
