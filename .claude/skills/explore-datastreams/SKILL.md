---
name: explore-datastreams
description: >
  Show how AEP datastreams connect sources to datasets and schemas — list datastreams,
  inspect a specific datastream's configuration, and trace which datasets receive data
  from each stream. Load when the user asks "show me our datastreams", "what is datastream X",
  "which dataset does this datastream feed", "how is data flowing in", or "show streaming
  ingestion setup". Uses Flow Service (mcp__aep__list_connections, list_dataflows,
  get_dataflow, list_source_connections).
---

# Explore Datastreams

## When to Load

- "show me our datastreams"
- "what is datastream / connection X"
- "which dataset does [datastream] feed"
- "how is data coming into AEP"
- "show streaming ingestion setup"

---

## Key Concepts

In AEP Flow Service, a "datastream" pipeline consists of:

```
Source Connection → Dataflow → Target Connection → Dataset
```

- **Source Connection**: authentication and location of the source system (S3, SFTP, CRM, streaming)
- **Dataflow**: the scheduled or streaming flow linking source to target
- **Target Connection**: the destination dataset in AEP
- **Connection Spec**: the connector type (S3, SFTP, Azure Blob, HTTP API, etc.)

---

## API Approach

### List dataflows

```
mcp__aep__list_dataflows          — all dataflows in the sandbox
mcp__aep__get_dataflow            — single dataflow detail
mcp__aep__list_source_connections — source configs (auth, location)
mcp__aep__list_target_connections — target dataset mappings
```

### Flow Service REST

```
GET {AEP_BASE_URL}/data/foundation/flowservice/flows
GET {AEP_BASE_URL}/data/foundation/flowservice/sourceConnections
GET {AEP_BASE_URL}/data/foundation/flowservice/targetConnections
```

---

## Output Format

```
Datastreams (sandbox: cvs-aetna)

  Name                          Source Type   Schedule        Target Dataset         Status
  ──────────────────────────────────────────────────────────────────────────────────────────
  Profile Daily Load            Amazon S3     Daily 02:00 UTC Profile Dataset (dev)  active
  Events HTTP Streaming         HTTP API      Streaming       Events Dataset          active
  Product Catalog Sync          SFTP          Weekly Mon      Lookup - Products       active

Detail — Profile Daily Load:
  Source: s3://deloitte-cvs-aetna/profile-exports/
  Mapping: Data Prep mapping set abc123
  Last Run: 2026-09-10 02:15 UTC (success · 142,000 rows)
  Next Run: 2026-09-11 02:00 UTC
```

---

## Notes

- Streaming (HTTP API) dataflows show real-time throughput instead of schedule
- A paused dataflow shows `state: disabled`; recommend checking alert subscriptions
