# Generate Schema

Run Stage 1 (Schema Design) and Stage 2 (Schema Deployment) from Stage 0 data analysis results.

## When to Use
- Designing XDM schemas from data analysis reports (output of `/analyze-data` or Stage 0)
- Deploying generated schemas to AEP Schema Registry
- Iterating on schema design after quality feedback
- Running schema stages independently of the full pipeline

## Usage
```
/generate-schema
/generate-schema deploy
/generate-schema design-only
/generate-schema <description of target schema requirements>
```

## Mandatory Protocols
- **Source Data Gate**: Only process entities that have matching CSV files in `Sampledata/` — never create schemas for phantom entities
- **User Confirmation Gate**: Save schema design mapping to `Matched_SchemaClass & Group/` and confirm with user BEFORE any deployment
- **No Auto-Profile**: NEVER enable Profile during schema design or deployment — that is Stage 5 (profile-operator)

## Workflow

### 1. Load Prerequisites
- Verify Stage 0 outputs exist in `Result_DataAnalysis/profiles/`
- If missing, advise running `/analyze-data` first
- Confirm source CSV files in `Sampledata/` — only process entities with matching files

### 2. Invoke `schema-processor` (Stages 1 + 2)
Route to `schema-processor` agent:
- Load `xdm-schema-design` skill — composition rules, field type mappings, identity configuration
- Load `aep-fundamentals` skill — Schema Registry API patterns, authentication

**Stage 1 (Schema Design)**:
- Review data profiles from `Result_DataAnalysis/profiles/`
- Determine schema class: query Schema Registry for standard classes, match entities
- Identify matching standard field groups: query Schema Registry, check coverage
- Design custom field groups for unmapped fields
- **B2C vs B2B gate**: default is B2C / standard Individual-Profile (identity via identityMap — unchanged). Apply the B2B model ONLY for genuine B2B use cases (Business Account / Opportunity / Account-Person Relation entities, or RT-CDP B2B Edition): B2B entities are keyed on `<entityKey>.sourceKey` (e.g. `accountKey.sourceKey`) under a type-matched namespace (`B2B_ACCOUNT`, …), NOT identityMap. See `xdm-schema-design` → "B2B Edition Schema Architecture".
- Map source types to XDM field types
- Configure identity fields — include identityMap for email and FK/CRMID fields
- Save design mapping to `Matched_SchemaClass & Group/` per entity + combined summary
- Present mapping to user and WAIT for confirmation before deploying

**Stage 2 (Schema Deployment)** — only after user confirms:
- Deploy custom field groups to Schema Registry
- Deploy schema referencing field groups
- Apply identity descriptors (xdm:namespace as string, xdm:property: "xdm:code")
- DO NOT enable Profile — hand off to `dataset-creator` next
- Validate post-deployment state

### 3. Outputs
- `Matched_SchemaClass & Group/` — schema design mapping files (Stage 1)
- Deployed schema IDs, field group IDs, identity descriptor details in deployment manifest (Stage 2)
- Schema composition validation report

Use `/aep-pipeline` for the full end-to-end flow.

Context: $ARGUMENTS
