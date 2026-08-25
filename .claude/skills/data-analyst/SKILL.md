---
name: data-analyst
description: "Data profiling, quality scoring (0-100), and Mermaid ERD generation for CSV files. Use when analyzing local CSV data (Stage 0 of AEP pipeline), generating data quality reports, or creating entity-relationship diagrams from CSV file structures. Handles: CSV field profiling, 6-dimension quality scoring (completeness, uniqueness, consistency, validity, accuracy, timeliness), FK/PK detection, and Mermaid erDiagram output. No open-source dependencies — Python standard library only."
---

# Data Analyst Skill

## When to Load
- Stage 0 of the AEP pipeline (CSV data analysis)
- CSV data quality assessment or profiling tasks
- Mermaid ERD generation from CSV file structures
- Any task requiring field-level profiling, type inference, or PK/FK detection on CSV files

## When NOT to Load
- XDM schema design or deployment (use xdm-schema-design)
- AEP API calls or dataset creation (use aep-fundamentals)
- Post-schema quality analysis (Stage 5 — use data-quality-scoring)

## Default Output Directory
- **Default**: `Output/{ProjectName}/Result_DataAnalysis/`
- Read `project_config.json` at project root to get `project_name` and `output_dir`; if it is missing, run the Project Init Gate before analysis
- Set `analysis_output_dir = {output_dir}/Result_DataAnalysis/`
- If the user does not specify an output directory, ALWAYS use `analysis_output_dir`
- This applies to all 3 steps below

## Workflow

### Step 0 — Clean Previous Output
```bash
rm -rf "{analysis_output_dir}" && mkdir -p "{analysis_output_dir}"
```
- ALWAYS run this BEFORE any analysis step to remove stale/duplicate files
- Ensures a fresh output directory on every run

### Step 1 — Profile CSV Files
```bash
python3 .claude/skills/data-analyst/scripts/profile_csv.py <input_dir> "{analysis_output_dir}"
```
- Default `analysis_output_dir`: `{output_dir}/Result_DataAnalysis/` (for example, `Output/{ProjectName}/Result_DataAnalysis/`)
- Reads every CSV in `<input_dir>`
- Produces per-file JSON profiles + combined `all_profiles.json` in `{analysis_output_dir}/profiles/`
- Profiles include: record counts, null rates, distinct counts, type inference, pattern detection, PK/FK candidates, numeric stats, sample values

### Step 2 — Score Quality
```bash
python3 .claude/skills/data-analyst/scripts/score_quality.py "{analysis_output_dir}/profiles" "{analysis_output_dir}"
```
- Reads JSON profiles from `<profile_dir>` (output of Step 1)
- Scores 6 dimensions: completeness, uniqueness, consistency, validity, accuracy, timeliness
- Produces 3 CSV reports in `{analysis_output_dir}/`: `quality_summary.csv`, `quality_fields.csv`, `quality_issues.csv`
- Accuracy and timeliness marked N/A when not applicable; weights redistributed per scoring methodology

### Step 3 — Generate ERD (Mermaid + HTML)
```bash
python3 .claude/skills/data-analyst/scripts/generate_erd.py <input_dir> "{analysis_output_dir}" "{project_name}"
```
- Reads CSV headers + profile data (from `{analysis_output_dir}/profiles/all_profiles.json`)
- Detects PK/FK relationships and cardinality
- Produces **two** outputs:
  1. `{analysis_output_dir}/erd_data_model.md` — Mermaid `erDiagram` (embedded in markdown code block)
  2. `{analysis_output_dir}/erd_data_model.html` — Rich self-contained HTML with tabbed ERD overview, relationships table, field-level data mapping table, and interactive reviewer comment section at the bottom
- Pass `project_name` as the third argument (read from `project_config.json`) so it appears in the HTML report header

## Script Reference

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `profile_csv.py` | Field-level CSV profiling with type inference and PK/FK detection | Directory of CSV files | JSON profiles in `profiles/` |
| `score_quality.py` | 6-dimension quality scoring with weighted overall score | JSON profile directory | 3 CSV reports |
| `generate_erd.py` | Mermaid ERD generation with relationship detection | CSV directory + profiles | `erd_data_model.md` |

## Output Structure
```
{analysis_output_dir}/
  profiles/
    {filename}_profile.json    # per-file profile
    all_profiles.json           # combined profiles
  quality_summary.csv           # dimension scores per file
  quality_fields.csv            # field-level quality stats
  quality_issues.csv            # detected issues with severity
  erd_data_model.md             # Mermaid erDiagram (for rendering in GitHub/VS Code)
  erd_data_model.html           # Rich HTML ERD + Data Mapping + Reviewer Comments (open in browser)
```

## Project Config
- Before running, read `project_config.json` at project root to get `project_name` and `output_dir`
- If `project_config.json` does not exist, stop and run the Project Init Gate (ask for project name and Sampledata)
- Pass `project_name` as the third argument to `generate_erd.py` so it appears in the HTML report header
- All output goes under `{output_dir}/Result_DataAnalysis/` (for example, `Output/{ProjectName}/Result_DataAnalysis/`) — never directly to `Result_DataAnalysis/` at project root

## Quality Scoring Weights
| Dimension | Default Weight | When N/A |
|-----------|---------------|----------|
| Completeness | 0.25 | +0.05 from Accuracy, +0.05 from Timeliness (if both N/A) |
| Uniqueness | 0.15 | — |
| Consistency | 0.20 | +0.05 from Timeliness (if N/A) |
| Validity | 0.20 | +0.05 from Accuracy (if N/A) |
| Accuracy | 0.10 | N/A when no reference data → redistribute to Completeness +0.05, Validity +0.05 |
| Timeliness | 0.10 | N/A when no datetime fields → redistribute to Completeness +0.05, Consistency +0.05 |

## Related Skills
- **data-quality-scoring**: Detailed scoring methodology, threshold definitions, AEP-specific checks
- **xdm-schema-design**: Mermaid ERD syntax reference, XDM type mappings, schema composition patterns
