# AEP Pipeline

Run the full end-to-end AEP automation pipeline (Stage 0 through Stage 8).

## When to Use
- Running the complete data-to-AEP pipeline on a set of CSV input files
- Orchestrating all stages: CSV analysis, schema design and deployment, dataset creation, identity configuration, profile enablement, data ingestion, and post-ingestion validation
- First-time pipeline run on a new dataset

## Usage
```
/aep-pipeline Sampledata/
/aep-pipeline path/to/csv-files
/aep-pipeline <description of the data and target schemas>
```

## Pipeline Stage Sequence

```
Stage 0 (CSV Analysis + Quality + ERD) — data-analyst
        ↓
Stage 1 (Schema Design) — schema-processor
        ↓
Stage 2 (Schema Deployment) — schema-processor
        ↓
Stage 3 (Dataset Creation) — dataset-creator
        ↓
Stage 4 (Identity Inspection) — identity-inspector
        ↓
Stage 5 (Profile Enablement) — profile-operator
        ↓
Stage 6 (Data Ingestion) — data-ingestion
        ↓
Stage 7 (Data Validation) — data-validator
        ↓
Stage 8 (QA Gate) — qa-master
```

All stages are sequential — each stage depends on the output of the prior stage.

## Workflow

### Step 0: Source Data Gate (MANDATORY — FIRST)
Before any pipeline stage, the `data-analyst` agent MUST:
1. List all CSV files in `Sampledata/` (or the provided path)
2. Map each file to an entity name (e.g., `customers.csv` → customers)
3. Present the file→entity mapping to the user and CONFIRM before proceeding
4. Entities without a matching source file are EXCLUDED — no schemas, datasets, or namespaces created for them

### Step 1: Invoke `data-analyst` (Stage 0)
Route to `data-analyst` agent. It will:
- Profile each CSV file (field types, completeness, uniqueness, patterns)
- Score quality across 6 dimensions (completeness, uniqueness, consistency, validity, accuracy, timeliness)
- Generate a Mermaid ERD from field relationships
- Output to `Result_DataAnalysis/`: JSON profiles, quality CSVs, ERD markdown
- Hand off to `schema-processor`

### Step 2: Invoke `schema-processor` (Stages 1 + 2)
- Stage 1: Design XDM schemas from Stage 0 profiles
  - Match each entity to a standard XDM class
  - Select standard field groups, design custom field groups for unmapped fields
  - **B2C vs B2B gate**: default is B2C / standard (identity via identityMap — unchanged). Apply the B2B model ONLY for genuine B2B use cases — B2B entities keyed on `<entityKey>.sourceKey` under a type-matched namespace (`B2B_ACCOUNT`, …), never identityMap. See `xdm-schema-design` → "B2B Edition Schema Architecture".
  - Save mapping to `Matched_SchemaClass & Group/` and present to user for approval
- Stage 2: Deploy schemas after user confirms
  - Deploy field groups, schemas, apply identity descriptors
  - DO NOT enable Profile — that is Stage 5
- Hand off to `dataset-creator`

### Step 3: Invoke `dataset-creator` (Stage 3)
- Check for existing datasets before creating (no duplicates)
- Create one parquet-format dataset per deployed schema
- Update deployment manifest with dataset IDs
- Hand off to `identity-inspector`

### Step 4: Invoke `identity-inspector` (Stage 4)
- Query schema fields and present identity options per schema to user
- Apply identity descriptors ONLY after explicit user selection
- Hand off to `profile-operator`

### Step 5: Invoke `profile-operator` (Stage 5)
- Present schema/dataset list and ask which to Profile-enable
- Apply all THREE flags after user approval: `unifiedProfile`, `unifiedIdentity`, `acp_granular_plugin_validation_flags`
- Verify all flags post-PATCH
- Hand off to `data-ingestion`

### Step 6: Pre-Ingestion Namespace Gate (MANDATORY — before Stage 6)
The `data-ingestion` agent MUST verify ALL identity namespaces referenced in transforms exist BEFORE ingesting any entity:
- Query `GET /data/core/idnamespace/identities`
- Create any missing namespaces (e.g., CRMID, OrderID)
- Create ALL namespaces before ingesting ANY entity

### Step 7: Invoke `data-ingestion` (Stage 6)
- Transform CSV rows to XDM-mapped NDJSON
- Create batches, upload, complete, monitor to success/failure
- Hand off to `data-validator`

### Step 8: Invoke `data-validator` (Stage 7)
- Query ingested data from AEP datasets
- Compare record counts against source CSVs
- Verify identity resolution and event stitching
- Hand off to `qa-master` on PASS or WARN

### Step 9: Invoke `qa-master` (Stage 8 — Final)
- Run all 13 post-ingestion checks
- Report PASS/FAIL/WARN per check with root cause and remediation
- Update skill file with any new failure patterns learned

## Outputs
- `Result_DataAnalysis/`: data profiles, quality CSVs, ERD markdown, deployment manifest
- `Matched_SchemaClass & Group/`: schema design mapping per entity
- `Identitynamespace/`: identity inspection PNG
- AEP resources: schemas, datasets, identity descriptors, Profile-enabled datasets, ingested batches
- QA report with PASS/FAIL per check

Context: $ARGUMENTS
