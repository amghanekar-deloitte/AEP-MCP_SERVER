"""
schema_context — runtime field-name discovery utilities

Field names for nested struct fields (e.g. _cvs.personalizedVisit) vary between
sandboxes and schema versions. Never hardcode them. Import these helpers to
discover the correct name at runtime from either a Python dict (profile API
responses) or a PostgreSQL/QS connection (Query Service).
"""

from __future__ import annotations
import json
import re
from typing import Any


# ── Dict-level discovery (profile API responses) ─────────────────────────────

def find_field(obj: dict, patterns: list[str]) -> Any:
    """Return the value of the first key in obj whose name matches any pattern.

    Patterns are checked in order:
      - Exact string match (case-sensitive)
      - Case-insensitive match via str.lower()
      - Substring match (pattern in key.lower())

    Returns None if no key matches.
    """
    if not obj or not isinstance(obj, dict):
        return None
    # Pass 1: exact match on known candidates (fastest, most common)
    for p in patterns:
        if p in obj:
            return obj[p]
    # Pass 2: case-insensitive exact
    lower_patterns = [p.lower() for p in patterns]
    for key, val in obj.items():
        if key.lower() in lower_patterns:
            return val
    # Pass 3: substring — any pattern is a substring of a key
    for key, val in obj.items():
        if any(p.lower() in key.lower() for p in patterns):
            return val
    return None


def find_visits(cvs: dict) -> list:
    """Locate the personalized-visits list inside a _cvs entity dict.

    Tries known field names first (ordered by most common), then falls back
    to scanning all list-valued keys whose name contains 'visit', 'prompt',
    or 'personal'. Returns [] if nothing is found.
    """
    val = find_field(cvs, [
        "personalizedVisit",
        "personlizedVisits",   # dev typo
        "personalizedVisits",
        "personalisedVisit",
        "personalisedVisits",
    ])
    if isinstance(val, list):
        return val
    # Broad scan fallback
    for key, v in (cvs or {}).items():
        if isinstance(v, list) and v and any(
            s in key.lower() for s in ("visit", "prompt", "personal")
        ):
            return v
    return []


def parse_visits_from_json_text(raw: str) -> list:
    """Parse a JSON text representation of a _cvs struct and extract visits.

    Used when Query Service returns _cvs as a TEXT/JSON column rather than
    selecting a specific nested field.
    """
    if not raw:
        return []
    try:
        obj = json.loads(raw)
        return find_visits(obj if isinstance(obj, dict) else {})
    except (json.JSONDecodeError, TypeError):
        return []


# ── SQL-level discovery (Query Service / psycopg2) ────────────────────────────

_VISIT_CANDIDATES = [
    "personalizedVisit",
    "personlizedVisits",   # dev typo
    "personalizedVisits",
    "personalisedVisit",
    "personalisedVisits",
]


def probe_qs_struct_field(conn, table: str, struct_col: str,
                           candidates: list[str]) -> str | None:
    """Probe a Query Service table to find which nested struct field name exists.

    Executes lightweight LIMIT 1 queries trying each candidate field name in
    order. Returns the first name that succeeds, or None if all fail.

    Args:
        conn: psycopg2 connection (must be open).
        table: Fully-qualified table name (e.g. 'aetna_dataset_profile_...').
        struct_col: Top-level struct column (e.g. '_cvs').
        candidates: Ordered list of nested field name candidates to try.
    """
    for name in candidates:
        try:
            cur = conn.cursor()
            cur.execute(
                f"SELECT CAST({struct_col}.{name} AS TEXT) FROM {table} LIMIT 1"
            )
            cur.fetchone()
            cur.close()
            return name
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
    return None


def probe_visits_field(conn, table: str, struct_col: str = "_cvs") -> str | None:
    """Return the correct personalized-visits field name for the given QS table.

    Wraps probe_qs_struct_field with the standard visit candidate list.
    """
    return probe_qs_struct_field(conn, table, struct_col, _VISIT_CANDIDATES)


# ── Offer characteristics discovery ──────────────────────────────────────────

def find_characteristic(characteristics: dict, *preferred_keys: str) -> str:
    """Return the value of the first matching key in characteristics.

    Checks preferred_keys in order (exact then case-insensitive), then returns
    the first non-empty string value found in the dict if nothing matches.
    """
    if not characteristics:
        return ""
    for key in preferred_keys:
        val = characteristics.get(key, "")
        if val:
            return str(val)
    # Case-insensitive fallback on preferred keys
    lower = {k.lower(): v for k, v in characteristics.items()}
    for key in preferred_keys:
        val = lower.get(key.lower(), "")
        if val:
            return str(val)
    # Last resort: first non-empty string value
    for val in characteristics.values():
        if val and isinstance(val, str):
            return val
    return ""


def extract_prompt_text(characteristics: dict) -> str:
    """Extract the prompt/offer text from characteristics regardless of key casing."""
    return find_characteristic(
        characteristics,
        "PromptText", "promptText", "prompt_text",
        "offerText", "OfferText", "offer_text",
        "text", "Text", "content", "Content",
    )
