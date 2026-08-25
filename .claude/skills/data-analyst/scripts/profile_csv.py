#!/usr/bin/env python3
"""CSV field profiling with type inference, PK/FK detection, and statistical analysis.

Usage: python profile_csv.py <input_dir> [output_dir]
  input_dir  — directory containing CSV files to profile
  output_dir — where to write profiles (default: {input_dir}/output)

Output: JSON profiles in {output_dir}/profiles/
  - {filename}_profile.json per CSV file
  - all_profiles.json combined

Standard library only — no third-party dependencies.
"""

import csv
import json
import math
import os
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

# -- Type inference patterns --

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
BOOLEAN_RE = re.compile(r"^(true|false|yes|no|0|1)$", re.IGNORECASE)


def _infer_type(value: str) -> str:
    """Return the most specific type for a single non-empty string value."""
    if UUID_RE.match(value):
        return "uuid"
    if EMAIL_RE.match(value):
        return "email"
    if DATETIME_RE.match(value):
        return "datetime"
    if DATE_RE.match(value):
        return "date"
    if BOOLEAN_RE.match(value):
        return "boolean"
    try:
        int(value)
        return "int"
    except ValueError:
        pass
    try:
        float(value)
        return "float"
    except ValueError:
        pass
    return "string"


def _dominant_type(type_counts: Counter) -> str:
    """Pick the dominant (most frequent) inferred type."""
    if not type_counts:
        return "string"
    return type_counts.most_common(1)[0][0]


def _dominant_pattern(inferred_type: str) -> str:
    """Map inferred type to a pattern label."""
    mapping = {
        "uuid": "uuid",
        "email": "email",
        "date": "date",
        "datetime": "datetime",
        "boolean": "boolean",
        "int": "numeric",
        "float": "numeric",
    }
    return mapping.get(inferred_type, "alphanumeric")


def _numeric_stats(values: list) -> dict:
    """Compute numeric stats for a list of float values."""
    if not values:
        return {}
    return {
        "min": min(values),
        "max": max(values),
        "mean": round(statistics.mean(values), 4),
        "median": round(statistics.median(values), 4),
        "stddev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
    }


def profile_field(field_name: str, raw_values: list) -> dict:
    """Profile a single field across all records."""
    total = len(raw_values)
    non_null = [v for v in raw_values if v.strip()]
    non_null_count = len(non_null)
    distinct = set(non_null)
    distinct_count = len(distinct)

    # Type inference
    type_counts = Counter()
    for v in non_null:
        type_counts[_infer_type(v)] += 1
    inferred = _dominant_type(type_counts)

    profile = {
        "total_records": total,
        "non_null_count": non_null_count,
        "distinct_count": distinct_count,
        "inferred_type": inferred,
        "dominant_pattern": _dominant_pattern(inferred),
        "sample_values": list(distinct)[:5],
        "is_potential_pk": distinct_count == total and non_null_count == total,
        "is_potential_fk": False,
    }

    # Numeric stats
    if inferred in ("int", "float"):
        nums = []
        for v in non_null:
            try:
                nums.append(float(v))
            except ValueError:
                pass
        stats = _numeric_stats(nums)
        profile.update(stats)

    # String length stats
    if inferred in ("string", "email", "uuid"):
        lengths = [len(v) for v in non_null]
        if lengths:
            profile["min_length"] = min(lengths)
            profile["max_length"] = max(lengths)

    # Type consistency: percentage of values matching dominant type
    if non_null_count > 0:
        dominant_count = type_counts.get(inferred, 0)
        profile["type_consistency"] = round(dominant_count / non_null_count * 100, 2)
    else:
        profile["type_consistency"] = 100.0

    return profile


def profile_csv_file(filepath: str) -> dict:
    """Profile all fields in a single CSV file."""
    path = Path(filepath)
    columns = {}  # field_name -> list of raw values

    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return {"file": path.name, "record_count": 0, "fields": {}}
        for fn in reader.fieldnames:
            columns[fn] = []
        for row in reader:
            for fn in reader.fieldnames:
                columns[fn].append(row.get(fn, ""))

    record_count = len(next(iter(columns.values()), []))
    fields = {}
    for fn in columns:
        fields[fn] = profile_field(fn, columns[fn])

    return {
        "file": path.name,
        "record_count": record_count,
        "fields": fields,
    }


def _refine_pks(all_profiles: dict) -> None:
    """When a file has an _id PK candidate, demote other PK candidates."""
    for fname, profile in all_profiles.items():
        fields = profile["fields"]
        id_pks = [fn for fn, fs in fields.items() if fs["is_potential_pk"] and fn.endswith("_id")]
        if id_pks:
            # Keep only _id fields as PKs; demote the rest
            for fn, fs in fields.items():
                if fs["is_potential_pk"] and fn not in id_pks:
                    fs["is_potential_pk"] = False


def detect_fk_relationships(all_profiles: dict) -> None:
    """Refine PK candidates then mark FK fields by cross-referencing across files."""
    _refine_pks(all_profiles)

    # Build PK index: field_name -> file_name
    pk_index = {}
    for fname, profile in all_profiles.items():
        for field_name, fstats in profile["fields"].items():
            if fstats["is_potential_pk"]:
                pk_index[field_name] = fname

    # Build table name index (filename stem without extension, pluralized check)
    table_names = {}
    for fname in all_profiles:
        stem = Path(fname).stem.lower()
        table_names[stem] = fname

    # Detect FK: field ends with _id and matches a PK in another table
    for fname, profile in all_profiles.items():
        for field_name, fstats in profile["fields"].items():
            if fstats["is_potential_pk"]:
                continue
            # Check if this field is a PK in another file
            if field_name in pk_index and pk_index[field_name] != fname:
                fstats["is_potential_fk"] = True
                fstats["fk_references"] = pk_index[field_name]
                continue
            # Check pattern: field_name like "account_id" -> table "accounts"
            if field_name.endswith("_id"):
                base = field_name[:-3]  # strip _id
                plural = base + "s"
                for candidate_table in (plural, base):
                    if candidate_table in table_names and table_names[candidate_table] != fname:
                        # Verify the target table has this field as a PK
                        target_file = table_names[candidate_table]
                        target_fields = all_profiles[target_file]["fields"]
                        if field_name in target_fields and target_fields[field_name].get("is_potential_pk"):
                            fstats["is_potential_fk"] = True
                            fstats["fk_references"] = target_file
                            break

    # Shared identity fields (like email) across tables — only fields that
    # act as identity links, not generic columns like name/address
    _IDENTITY_FIELDS = {"email", "phone", "ecid", "crm_id", "loyalty_id"}
    field_files = {}
    for fname, profile in all_profiles.items():
        for field_name in profile["fields"]:
            if field_name.endswith("_id"):
                continue
            if field_name.lower() not in _IDENTITY_FIELDS:
                continue
            field_files.setdefault(field_name, []).append(fname)
    for field_name, files in field_files.items():
        if len(files) > 1:
            for fname in files:
                fstats = all_profiles[fname]["fields"][field_name]
                if not fstats.get("is_potential_fk"):
                    fstats["shared_across"] = [f for f in files if f != fname]


def main():
    if len(sys.argv) < 2:
        print("Usage: python profile_csv.py <input_dir> [output_dir]")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_dir / "output"
    profiles_dir = output_dir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        sys.exit(1)

    print(f"Profiling {len(csv_files)} CSV files in {input_dir}")
    all_profiles = {}

    for csv_path in csv_files:
        print(f"  Profiling {csv_path.name}...")
        profile = profile_csv_file(str(csv_path))
        all_profiles[csv_path.name] = profile

        out_path = profiles_dir / f"{csv_path.stem}_profile.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, default=str)
        print(f"    {profile['record_count']} records, {len(profile['fields'])} fields -> {out_path.name}")

    # Detect FK relationships across all profiles
    detect_fk_relationships(all_profiles)

    # Re-write individual profiles with FK info
    for csv_name, profile in all_profiles.items():
        out_path = profiles_dir / f"{Path(csv_name).stem}_profile.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, default=str)

    # Write combined profiles
    combined_path = profiles_dir / "all_profiles.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_profiles, f, indent=2, default=str)
    print(f"\nCombined profiles written to {combined_path}")
    print("Profiling complete.")


if __name__ == "__main__":
    main()
