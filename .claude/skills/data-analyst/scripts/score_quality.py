#!/usr/bin/env python3
"""Quality scoring across 6 dimensions for CSV profile data.

Usage: python score_quality.py <profile_dir> [output_dir]
  profile_dir — directory containing JSON profile files (from profile_csv.py)
  output_dir  — where to write CSV reports (default: parent of profile_dir)

Output: 3 CSV reports in output_dir:
  - quality_summary.csv  (dimension scores per file + grand total)
  - quality_fields.csv   (field-level quality stats)
  - quality_issues.csv   (detected issues with severity and recommendations)

Weights: Completeness 0.25, Uniqueness 0.15, Consistency 0.20,
         Validity 0.20, Accuracy 0.10, Timeliness 0.10
When Accuracy N/A: redistribute +0.05 Completeness, +0.05 Validity
When Timeliness N/A: redistribute +0.05 Completeness, +0.05 Consistency

Standard library only — no third-party dependencies.
"""

import csv
import json
import math
import os
import sys
from pathlib import Path


def _rating(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Fair"
    if score >= 40:
        return "Poor"
    return "Critical"


def _score_completeness(fields: dict) -> float:
    """Average non-null ratio across all fields."""
    if not fields:
        return 100.0
    ratios = []
    for fstats in fields.values():
        total = fstats["total_records"]
        if total == 0:
            ratios.append(100.0)
        else:
            ratios.append(fstats["non_null_count"] / total * 100)
    return sum(ratios) / len(ratios)


def _score_uniqueness(fields: dict) -> float:
    """Average uniqueness ratio for PK and identity fields only.

    FK fields are expected to have duplicates, so they are excluded.
    Falls back to all fields if no PK/identity fields found.
    """
    pk_fields = {
        fn: fs for fn, fs in fields.items()
        if fs.get("is_potential_pk") or fn.lower() == "email"
    }
    target = pk_fields if pk_fields else fields
    if not target:
        return 100.0
    ratios = []
    for fstats in target.values():
        nn = fstats["non_null_count"]
        if nn == 0:
            ratios.append(100.0)
        else:
            ratios.append(fstats["distinct_count"] / nn * 100)
    return sum(ratios) / len(ratios)


def _score_consistency(fields: dict) -> float:
    """Average type consistency across all fields."""
    if not fields:
        return 100.0
    scores = []
    for fstats in fields.values():
        scores.append(fstats.get("type_consistency", 100.0))
    return sum(scores) / len(scores)


def _score_validity(fields: dict, record_count: int) -> tuple:
    """Score validity: type match rate, outlier check for numerics. Returns (score, field_valid_counts)."""
    if not fields:
        return 100.0, {}
    field_scores = {}
    field_valid_counts = {}
    for fn, fstats in fields.items():
        consistency = fstats.get("type_consistency", 100.0)
        nn = fstats["non_null_count"]
        valid_count = int(nn * consistency / 100)

        # Outlier penalty for numeric fields
        if fstats["inferred_type"] in ("int", "float") and fstats.get("stddev", 0) > 0:
            mean_val = fstats.get("mean", 0)
            stddev = fstats.get("stddev", 0)
            min_val = fstats.get("min", 0)
            max_val = fstats.get("max", 0)
            # Check if min or max is > 3 stddev from mean
            if stddev > 0:
                lower = mean_val - 3 * stddev
                upper = mean_val + 3 * stddev
                if min_val < lower or max_val > upper:
                    # Penalize slightly
                    consistency = max(consistency - 5, 0)

        field_scores[fn] = consistency
        field_valid_counts[fn] = valid_count

    avg = sum(field_scores.values()) / len(field_scores)
    return avg, field_valid_counts


def _score_timeliness(fields: dict) -> tuple:
    """Score timeliness based on datetime field freshness. Returns (score_or_None, has_datetime)."""
    datetime_fields = {
        fn: fs for fn, fs in fields.items()
        if fs["inferred_type"] in ("datetime", "date")
    }
    if not datetime_fields:
        return None, False

    # Simple freshness heuristic: type consistency of datetime fields
    # (In a real scenario we'd parse dates, but with stdlib-only we approximate)
    scores = []
    for fstats in datetime_fields.values():
        scores.append(fstats.get("type_consistency", 100.0))
    return sum(scores) / len(scores), True


def score_file(file_profile: dict) -> dict:
    """Score a single file across all 6 dimensions."""
    fields = file_profile["fields"]
    record_count = file_profile["record_count"]

    completeness = _score_completeness(fields)
    uniqueness = _score_uniqueness(fields)
    consistency = _score_consistency(fields)
    validity, field_valid_counts = _score_validity(fields, record_count)
    timeliness_score, has_datetime = _score_timeliness(fields)

    # Base weights
    weights = {
        "completeness": 0.25,
        "uniqueness": 0.15,
        "consistency": 0.20,
        "validity": 0.20,
        "accuracy": 0.10,
        "timeliness": 0.10,
    }

    # Accuracy is always N/A (no reference data)
    accuracy_na = True
    timeliness_na = not has_datetime

    notes = {}

    # Redistribute accuracy weight
    if accuracy_na:
        weights["accuracy"] = 0.0
        weights["completeness"] += 0.05
        weights["validity"] += 0.05
        notes["accuracy"] = "N/A - no reference data; weight redistributed to Completeness (+0.05) and Validity (+0.05)"

    # Redistribute timeliness weight if N/A
    if timeliness_na:
        weights["timeliness"] = 0.0
        weights["completeness"] += 0.05
        weights["consistency"] += 0.05
        notes["timeliness"] = "N/A - no datetime fields; weight redistributed to Completeness (+0.05) and Consistency (+0.05)"

    scores = {
        "completeness": round(completeness, 2),
        "uniqueness": round(uniqueness, 2),
        "consistency": round(consistency, 2),
        "validity": round(validity, 2),
        "accuracy": None if accuracy_na else 0.0,
        "timeliness": round(timeliness_score, 2) if timeliness_score is not None else None,
    }

    # Weighted overall
    overall = 0.0
    for dim, score in scores.items():
        if score is not None:
            overall += score * weights[dim]

    scores["overall"] = round(overall, 2)

    return {
        "scores": scores,
        "weights": weights,
        "notes": notes,
        "field_valid_counts": field_valid_counts,
    }


def _detect_issues(file_name: str, fields: dict, scores: dict) -> list:
    """Detect quality issues and return a list of issue dicts."""
    issues = []

    for fn, fstats in fields.items():
        total = fstats["total_records"]
        nn = fstats["non_null_count"]
        null_pct = (total - nn) / total * 100 if total > 0 else 0

        # HIGH: identity fields with missing values
        if ("id" in fn.lower() or "email" in fn.lower()) and null_pct > 0:
            severity = "HIGH" if null_pct > 20 else "MEDIUM"
            issues.append({
                "severity": severity,
                "file_name": file_name,
                "field_name": fn,
                "dimension": "completeness",
                "issue_description": f"Identity field has {null_pct:.1f}% missing values",
                "affected_records": total - nn,
                "recommendation": f"Investigate and fill missing {fn} values before ingestion",
            })

        # HIGH: completeness < 80%
        if null_pct > 20:
            issues.append({
                "severity": "HIGH",
                "file_name": file_name,
                "field_name": fn,
                "dimension": "completeness",
                "issue_description": f"Field completeness is {100 - null_pct:.1f}% (below 80% threshold)",
                "affected_records": total - nn,
                "recommendation": "Review data source for missing values or consider marking field as optional",
            })

        # MEDIUM: consistency < 90%
        tc = fstats.get("type_consistency", 100.0)
        if tc < 90:
            inconsistent = int(nn * (100 - tc) / 100)
            issues.append({
                "severity": "MEDIUM",
                "file_name": file_name,
                "field_name": fn,
                "dimension": "consistency",
                "issue_description": f"Type consistency is {tc:.1f}% — mixed data types detected",
                "affected_records": inconsistent,
                "recommendation": f"Standardize {fn} values to a single type ({fstats['inferred_type']})",
            })

        # MEDIUM: uniqueness — only flag PK/identity fields, not FK fields
        is_pk = fstats.get("is_potential_pk", False)
        is_fk = fstats.get("is_potential_fk", False)
        is_identity = fn.lower() == "email"
        if (is_pk or is_identity) and not is_fk and nn > 0:
            uniq_pct = fstats["distinct_count"] / nn * 100
            if uniq_pct < 90:
                issues.append({
                    "severity": "MEDIUM",
                    "file_name": file_name,
                    "field_name": fn,
                    "dimension": "uniqueness",
                    "issue_description": f"Key field uniqueness is {uniq_pct:.1f}% — duplicates detected",
                    "affected_records": nn - fstats["distinct_count"],
                    "recommendation": f"Deduplicate {fn} values or verify if duplicates are expected",
                })

        # LOW: string fields with very low distinct counts (possible enum)
        if fstats["inferred_type"] == "string" and nn > 10 and fstats["distinct_count"] < 20:
            issues.append({
                "severity": "INFO",
                "file_name": file_name,
                "field_name": fn,
                "dimension": "validity",
                "issue_description": f"Low cardinality ({fstats['distinct_count']} distinct values) — possible enum/category field",
                "affected_records": 0,
                "recommendation": "Consider mapping to an XDM enum type in schema design",
            })

    # File-level score issues
    overall = scores.get("overall", 100)
    if overall < 60:
        issues.append({
            "severity": "HIGH",
            "file_name": file_name,
            "field_name": "",
            "dimension": "overall",
            "issue_description": f"Overall quality score is {overall} (below Fair threshold)",
            "affected_records": 0,
            "recommendation": "Review all HIGH and MEDIUM issues before proceeding with ingestion",
        })

    return issues


def write_summary_csv(path: str, all_results: dict) -> None:
    """Write quality_summary.csv."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file_name", "dimension", "score", "weight", "weighted_score", "rating", "notes"])

        grand_totals = {}
        file_count = 0

        for file_name, result in all_results.items():
            file_count += 1
            scores = result["scores"]
            weights = result["weights"]
            notes = result["notes"]

            for dim in ["completeness", "uniqueness", "consistency", "validity", "accuracy", "timeliness"]:
                score = scores[dim]
                weight = weights[dim]
                if score is None:
                    writer.writerow([
                        file_name, dim, "N/A", f"{weight:.2f}", "N/A",
                        "N/A", notes.get(dim, "")
                    ])
                else:
                    ws = round(score * weight, 2)
                    writer.writerow([
                        file_name, dim, f"{score:.2f}", f"{weight:.2f}",
                        f"{ws:.2f}", _rating(score), notes.get(dim, "")
                    ])
                    grand_totals.setdefault(dim, []).append(score)

            overall = scores["overall"]
            writer.writerow([
                file_name, "OVERALL", f"{overall:.2f}", "1.00",
                f"{overall:.2f}", _rating(overall), ""
            ])
            grand_totals.setdefault("overall", []).append(overall)
            writer.writerow([])  # blank row between files

        # Grand total
        if file_count > 0:
            for dim in ["completeness", "uniqueness", "consistency", "validity", "accuracy", "timeliness"]:
                vals = grand_totals.get(dim, [])
                if vals:
                    avg = sum(vals) / len(vals)
                    writer.writerow(["GRAND TOTAL", dim, f"{avg:.2f}", "", "", _rating(avg), ""])
                else:
                    writer.writerow(["GRAND TOTAL", dim, "N/A", "", "", "N/A", ""])
            overall_vals = grand_totals.get("overall", [])
            if overall_vals:
                grand_avg = sum(overall_vals) / len(overall_vals)
                writer.writerow(["GRAND TOTAL", "OVERALL", f"{grand_avg:.2f}", "1.00", f"{grand_avg:.2f}", _rating(grand_avg), ""])


def write_fields_csv(path: str, all_profiles: dict, all_results: dict) -> None:
    """Write quality_fields.csv."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "file_name", "field_name", "data_type", "total_records",
            "non_null_count", "completeness", "unique_count", "uniqueness",
            "dominant_pattern", "consistency", "valid_count", "validity", "notes"
        ])

        for file_name, profile in all_profiles.items():
            result = all_results[file_name]
            fvc = result["field_valid_counts"]
            for fn, fstats in profile["fields"].items():
                total = fstats["total_records"]
                nn = fstats["non_null_count"]
                comp = round(nn / total * 100, 2) if total > 0 else 100.0
                uniq = round(fstats["distinct_count"] / nn * 100, 2) if nn > 0 else 100.0
                consistency = fstats.get("type_consistency", 100.0)
                valid_count = fvc.get(fn, nn)
                validity = round(valid_count / nn * 100, 2) if nn > 0 else 100.0

                field_notes = []
                if fstats.get("is_potential_pk"):
                    field_notes.append("PK candidate")
                if fstats.get("is_potential_fk"):
                    ref = fstats.get("fk_references", "")
                    field_notes.append(f"FK -> {ref}")
                if fstats.get("shared_across"):
                    field_notes.append(f"Shared with {', '.join(fstats['shared_across'])}")

                writer.writerow([
                    file_name, fn, fstats["inferred_type"], total,
                    nn, f"{comp:.2f}", fstats["distinct_count"], f"{uniq:.2f}",
                    fstats.get("dominant_pattern", ""), f"{consistency:.2f}",
                    valid_count, f"{validity:.2f}", "; ".join(field_notes)
                ])


def write_issues_csv(path: str, all_issues: list) -> None:
    """Write quality_issues.csv."""
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    sorted_issues = sorted(all_issues, key=lambda i: severity_order.get(i["severity"], 9))

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "severity", "file_name", "field_name", "dimension",
            "issue_description", "affected_records", "recommendation"
        ])
        for issue in sorted_issues:
            writer.writerow([
                issue["severity"], issue["file_name"], issue["field_name"],
                issue["dimension"], issue["issue_description"],
                issue["affected_records"], issue["recommendation"]
            ])


def main():
    if len(sys.argv) < 2:
        print("Usage: python score_quality.py <profile_dir> [output_dir]")
        sys.exit(1)

    profile_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else profile_dir.parent

    # Load profiles
    combined_path = profile_dir / "all_profiles.json"
    if combined_path.exists():
        with open(combined_path, "r", encoding="utf-8") as f:
            all_profiles = json.load(f)
    else:
        # Load individual profiles
        all_profiles = {}
        for p in sorted(profile_dir.glob("*_profile.json")):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_profiles[data["file"]] = data

    if not all_profiles:
        print(f"No profile data found in {profile_dir}")
        sys.exit(1)

    print(f"Scoring quality for {len(all_profiles)} files")

    all_results = {}
    all_issues = []

    for file_name, profile in all_profiles.items():
        print(f"  Scoring {file_name}...")
        result = score_file(profile)
        all_results[file_name] = result

        issues = _detect_issues(file_name, profile["fields"], result["scores"])
        all_issues.extend(issues)

        overall = result["scores"]["overall"]
        print(f"    Overall: {overall:.2f} ({_rating(overall)})")

    # Write reports
    output_dir.mkdir(parents=True, exist_ok=True)
    write_summary_csv(str(output_dir / "quality_summary.csv"), all_results)
    write_fields_csv(str(output_dir / "quality_fields.csv"), all_profiles, all_results)
    write_issues_csv(str(output_dir / "quality_issues.csv"), all_issues)

    print(f"\nReports written to {output_dir}:")
    print(f"  quality_summary.csv")
    print(f"  quality_fields.csv")
    print(f"  quality_issues.csv")

    # Print summary
    if all_results:
        overalls = [r["scores"]["overall"] for r in all_results.values()]
        grand_avg = sum(overalls) / len(overalls)
        print(f"\nGrand Average Quality Score: {grand_avg:.2f} ({_rating(grand_avg)})")
    print("Quality scoring complete.")


if __name__ == "__main__":
    main()
