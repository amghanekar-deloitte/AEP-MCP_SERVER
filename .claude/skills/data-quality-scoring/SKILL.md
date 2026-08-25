---
name: data-quality-scoring
description: Data quality profiling methodology, scoring rubric (0-100), report generation patterns, threshold definitions, and AEP-specific data quality checks. Load this skill when performing data quality analysis (Stage 5) or when evaluating CSV/JSON data completeness and fitness for AEP ingestion.
---

# Data Quality Scoring

Load this skill when:
- Running Stage 5 (Quality Analysis) of the AEP pipeline
- Evaluating data fitness before schema generation or ingestion
- Generating quality reports (CSV format)
- Defining or adjusting quality thresholds
- Reviewing data profiling results

Do NOT load this skill for:
- Schema design or deployment (use xdm-schema-design)
- AEP API interaction patterns (use aep-fundamentals)
- ERD generation methodology (use xdm-schema-design)

---

## Quality Dimensions

Data quality is assessed across six dimensions. Each dimension produces a score from 0 to 100. The overall quality score is a weighted average.

### 1. Completeness (Weight: 25%)

Measures the proportion of non-null, non-empty values across all fields.

**Scoring**:
- Field completeness = (non-null count / total records) * 100
- Dimension score = average of all field completeness scores

**Severity levels**:
- 95-100%: Excellent — minimal missing data
- 80-94%: Good — acceptable for most use cases
- 60-79%: Fair — review required fields, may block ingestion
- Below 60%: Poor — significant data gaps, remediation needed

**AEP-specific checks**:
- Identity fields (email, ECID, CRM ID) MUST be 100% complete for profile-enabled datasets
- Required XDM fields must meet minimum completeness thresholds
- Timestamp fields must be present for ExperienceEvent schemas

### 2. Uniqueness (Weight: 15%)

Measures the proportion of distinct values where uniqueness is expected.

**Scoring**:
- Field uniqueness = (distinct count / total records) * 100 for identity/key fields
- For non-key fields, uniqueness is informational only (not penalized)
- Dimension score = average uniqueness of identified key/identity fields

**Key checks**:
- Primary identity fields should have high uniqueness (>99%)
- Duplicate identity records will cause merge conflicts in Real-Time Customer Profile
- Low uniqueness on expected-unique fields signals data quality issues upstream

### 3. Consistency (Weight: 20%)

Measures format and pattern consistency within each field.

**Scoring**:
- Detect the dominant pattern per field (e.g., email format, date format, phone format)
- Consistency = (records matching dominant pattern / total non-null records) * 100
- Dimension score = average consistency across all fields with detectable patterns

**Pattern checks**:
- Date/timestamp fields: consistent format (ISO 8601 preferred for AEP)
- Email fields: valid email pattern
- Phone fields: consistent format (E.164 preferred)
- Enum/category fields: values within expected set
- Numeric fields: consistent scale and unit

### 4. Validity (Weight: 20%)

Measures whether values conform to expected data types and business rules.

**Scoring**:
- Type validity = (records with correct data type / total records) * 100
- Range validity = (records within expected range / total records) * 100
- Dimension score = average of type and range validity across all fields

**Validation rules**:
- Numeric fields: within expected min/max range
- Date fields: parseable and within reasonable date range
- Boolean fields: only true/false/0/1 values
- Enum fields: values in the defined value set
- String length: within expected min/max character count
- Nested objects: structural validity (required sub-fields present)

### 5. Accuracy (Weight: 10%)

Measures correctness relative to known reference data or business logic.

**Scoring**:
- Cross-field validation: logically related fields are consistent (e.g., city matches postal code region)
- Reference data validation: values exist in reference datasets (e.g., country codes in ISO 3166)
- Dimension score = pass rate of accuracy checks

**Note**: Accuracy scoring requires reference data or business rules. When neither is available, score this dimension as N/A and redistribute its weight to Completeness and Validity (12.5% each).

### 6. Timeliness (Weight: 10%)

Measures data freshness and temporal validity.

**Scoring**:
- Record age = time since the most recent timestamp field
- Freshness = percentage of records within the acceptable age window
- Dimension score = freshness percentage

**AEP-specific checks**:
- ExperienceEvent data should have timestamps within the expected lookback window
- Profile data should have recent update timestamps
- Stale data (>90 days with no updates) may indicate sync issues

**Note**: When timestamp fields are absent, score this dimension as N/A and redistribute its weight to Completeness and Consistency (5% each).

---

## Overall Score Calculation

```
overall_score = (
    completeness_score * completeness_weight +
    uniqueness_score * uniqueness_weight +
    consistency_score * consistency_weight +
    validity_score * validity_weight +
    accuracy_score * accuracy_weight +
    timeliness_score * timeliness_weight
)
```

Default weights:
| Dimension | Weight |
|-----------|--------|
| Completeness | 0.25 |
| Uniqueness | 0.15 |
| Consistency | 0.20 |
| Validity | 0.20 |
| Accuracy | 0.10 |
| Timeliness | 0.10 |

When a dimension is N/A, redistribute its weight proportionally to the remaining dimensions.

Weights SHOULD be configurable per pipeline run — define them in a quality configuration, not hardcoded in scoring logic.

### Score Thresholds

| Score Range | Rating | Action |
|-------------|--------|--------|
| 90-100 | Excellent | Proceed to ingestion |
| 75-89 | Good | Proceed with minor remediation notes |
| 60-74 | Fair | Review recommended before ingestion |
| 40-59 | Poor | Remediation required before ingestion |
| 0-39 | Critical | Data unsuitable — block ingestion |

---

## Quality Report Format

Quality reports are generated as CSV files with the following structure:

### Summary Report (quality_summary.csv)

```csv
dimension,score,weight,weighted_score,rating,notes
completeness,92.5,0.25,23.13,Excellent,2 fields below 90% threshold
uniqueness,98.1,0.15,14.72,Excellent,Primary key 100% unique
consistency,85.3,0.20,17.06,Good,Date format inconsistency in 3 fields
validity,88.7,0.20,17.74,Good,12 records with invalid email format
accuracy,N/A,0.10,0.00,N/A,No reference data available - weight redistributed
timeliness,91.2,0.10,9.12,Excellent,95% of records within 30-day window
OVERALL,88.7,1.00,88.7,Good,Proceed with minor remediation
```

### Field-Level Report (quality_fields.csv)

```csv
field_name,data_type,total_records,non_null_count,completeness,unique_count,uniqueness,dominant_pattern,consistency,valid_count,validity,notes
email,string,10000,9850,98.5,9820,98.2,email_pattern,96.1,9800,98.0,12 invalid emails
created_at,datetime,10000,10000,100.0,9500,95.0,ISO8601,89.3,10000,100.0,Some non-ISO dates
customer_id,string,10000,10000,100.0,10000,100.0,alphanumeric,100.0,10000,100.0,Primary identity
age,integer,10000,9200,92.0,85,0.9,numeric,100.0,9180,91.8,20 values out of range
```

### Issue Report (quality_issues.csv)

```csv
severity,field_name,dimension,issue_description,affected_records,recommendation
HIGH,email,completeness,150 records missing email (identity field),150,Required for profile - must remediate
MEDIUM,created_at,consistency,1070 records use non-ISO date format,1070,Convert to ISO 8601 before ingestion
LOW,age,validity,20 records have age > 150 or < 0,20,Review and correct or null out invalid values
INFO,phone,uniqueness,Phone field has 45% uniqueness,N/A,Expected for shared household numbers
```

---

## AEP-Specific Quality Checks

These checks are specific to data destined for Adobe Experience Platform:

### Identity Field Validation
- At least one identity field must be present and complete
- Primary identity field must have 100% completeness
- Identity values must be non-empty strings after trimming
- Email identities must pass format validation
- ECID values must be valid format (numeric string)

### XDM Mapping Coverage
- Every field in the source data should map to an XDM field
- Unmapped fields should be flagged as INFO-level issues
- Required XDM fields with no source mapping should be flagged as HIGH severity

### Schema Compatibility
- Data types in source must be compatible with target XDM field types
- String-to-number conversions should be flagged if the source contains non-numeric values
- Array fields must have consistent element types
- Nested object fields must have consistent structure across records

### Ingestion Readiness
- File size within AEP batch ingestion limits
- Record count within single-batch limits (or plan for multi-batch)
- JSON structure is valid NDJSON or JSON array format
- CSV encoding is UTF-8

---

## Data Profiling Methodology

### Step 1: Statistical Profiling

For each field in the dataset:
- Count: total records, non-null records, distinct values
- Distribution: min, max, mean, median, mode (for numeric fields)
- Pattern detection: dominant format patterns (for string fields)
- Type inference: detected data type vs declared data type

### Step 2: Quality Dimension Scoring

Apply each quality dimension's scoring formula to the profiling results.

### Step 3: Cross-Field Analysis

- Identify logically related field pairs (e.g., country + postal code)
- Validate cross-field consistency
- Detect orphaned references (foreign keys pointing to non-existent records)

### Step 4: AEP Readiness Assessment

Apply AEP-specific checks from the section above.

### Step 5: Report Generation

Generate all three report files (summary, field-level, issues) in the output directory.

---

## Integration With Pipeline Stages

### Input (from earlier stages)
- Stage 0 output: CSV file profiles (column names, types, row counts, sample values)
- Stage 1 output: Generated XDM schema definitions (for mapping coverage checks)

### Output (to later stages)
- Quality summary with overall score and go/no-go recommendation
- Field-level quality metrics for schema refinement feedback
- Issue list for remediation before re-running the pipeline
- Quality score feeds into ERD annotations (Stage 6)
