# Analyze Data

Run Stage 0 (CSV Analysis, Quality Scoring, and ERD Generation) on local CSV files.

## When to Use
- Profiling a new set of CSV files before schema design
- Running data analysis independently of the full pipeline
- Generating data profiles to review before proceeding to schema generation
- Re-analyzing data after source file updates

## Usage
```
/analyze-data Sampledata/
/analyze-data path/to/csv-files
/analyze-data <description of files to analyze>
```

## Workflow

### 1. Source Data Gate (MANDATORY — First)
Before profiling, `data-analyst` MUST:
1. List all CSV files in the provided path
2. Map each file to an entity name
3. Present the file→entity mapping to the user and confirm before proceeding

### 2. Invoke `data-analyst` (Stage 0)
Route to `data-analyst` agent. It will:
- Profile each CSV file: column inventory, inferred types, completeness stats, pattern distributions
- Score quality across 6 dimensions: completeness, uniqueness, consistency, validity, accuracy, timeliness
- Generate a Mermaid ERD from field relationships and FK/PK detection
- Output to `Result_DataAnalysis/`:
  - `profiles/` — per-entity JSON profiles
  - `quality_summary.csv`, `quality_fields.csv`, `quality_issues.csv`
  - `erd_data_model.md` — Mermaid ERD
  - `deployment_manifest.json` — initialized for downstream stages

### 3. Review and Proceed
- Review the quality summary and ERD before proceeding
- If quality score < 60 for any entity: data remediation is recommended before ingestion
- Use `/generate-schema` next to design XDM schemas from the analysis results
- Or use `/aep-pipeline` for the full end-to-end flow

Context: $ARGUMENTS
