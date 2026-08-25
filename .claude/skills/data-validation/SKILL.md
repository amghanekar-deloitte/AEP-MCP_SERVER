---
name: data-validation
description: AEP post-ingestion data validation patterns for Stage 7 — Data Access API queries, source-vs-AEP record count comparison, identity resolution verification, event stitching checks, field-level comparison on samples, and validation report format. Load when validating ingested data against source files.
---

# Data Validation Skill

Load this skill before any post-ingestion validation operation in Stage 7.

---

## 1. Verify Batch Completion

```python
import json, subprocess

def get_batch_details(base, token, client_id, org_id, sandbox, batch_id):
    result = subprocess.run([
        "curl", "-s",
        f"{base}/data/foundation/import/batches/{batch_id}",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}"
    ], capture_output=True, text=True)
    return json.loads(result.stdout)
```

Check:
- `status == "success"` — batch was accepted by AEP
- `metrics.inputRecordCount` — records sent
- `metrics.outputRecordCount` — records accepted (should equal input minus invalid)
- `errors` array — any per-record errors

---

## 2. Query Ingested Data via Data Access API

```python
def list_batch_files(base, token, client_id, org_id, sandbox, batch_id):
    """List files in an ingested batch for download."""
    result = subprocess.run([
        "curl", "-s",
        f"{base}/data/foundation/export/batches/{batch_id}/files",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}"
    ], capture_output=True, text=True)
    return json.loads(result.stdout).get("data", [])

def download_batch_file(base, token, client_id, org_id, sandbox, file_href):
    """Download a file from an ingested batch (returns raw content)."""
    result = subprocess.run([
        "curl", "-s", f"{base}{file_href}",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}"
    ], capture_output=True, text=True)
    return result.stdout
```

---

## 3. Query via AEP Query Service (Alternative for Large Datasets)

```python
def run_query(base, token, client_id, org_id, sandbox, sql, name="validation_query"):
    """Submit a Query Service SQL query and return the query ID."""
    payload = json.dumps({
        "dbName": f"{sandbox}:all",
        "sql": sql,
        "name": name
    })
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"{base}/data/foundation/query/queries",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}",
        "-H", "Content-Type: application/json",
        "-d", payload
    ], capture_output=True, text=True)
    return json.loads(result.stdout).get("id")

def poll_query(base, token, client_id, org_id, sandbox, query_id,
               max_attempts=20, interval_sec=10):
    import time
    for _ in range(max_attempts):
        result = subprocess.run([
            "curl", "-s",
            f"{base}/data/foundation/query/queries/{query_id}",
            "-H", f"Authorization: Bearer {token}",
            "-H", f"x-api-key: {client_id}",
            "-H", f"x-gw-ims-org-id: {org_id}",
            "-H", f"x-sandbox-name: {sandbox}"
        ], capture_output=True, text=True)
        q = json.loads(result.stdout)
        state = q.get("state")
        if state == "SUCCESS":
            return q.get("_links", {}).get("results", {}).get("href")
        if state == "FAILED":
            raise RuntimeError(f"Query failed: {q.get('errors')}")
        time.sleep(interval_sec)
    raise TimeoutError("Query did not complete in time")
```

---

## 4. Record Count Comparison

```python
import csv

def count_csv_rows(csv_path):
    """Count data rows in a CSV (excluding header)."""
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        return sum(1 for _ in reader)

def compare_record_counts(source_count, ingested_count, tolerance_pct=1.0):
    """
    Returns (status, message).
    PASS: counts match exactly.
    WARN: within tolerance (e.g., 1% of records rejected as invalid).
    FAIL: mismatch exceeds tolerance.
    """
    if source_count == ingested_count:
        return "PASS", f"Counts match: {source_count} records"
    diff = abs(source_count - ingested_count)
    diff_pct = (diff / source_count) * 100 if source_count > 0 else 0
    if diff_pct <= tolerance_pct:
        return "WARN", f"Within tolerance: source={source_count}, ingested={ingested_count} ({diff_pct:.1f}% diff)"
    return "FAIL", f"Count mismatch: source={source_count}, ingested={ingested_count} ({diff_pct:.1f}% diff)"
```

---

## 5. Identity Resolution Verification (Profile-Enabled Datasets)

**CRITICAL — Profile Access API response structure**: The `/data/core/ups/access/entities` API returns a dict keyed by AEP entity ID, NOT a flat `{entity, sources}` object. Always unwrap before accessing fields:

```python
def _unwrap_entity_response(resp: dict) -> dict:
    """
    The Profile Access API returns {<aep_entity_id>: {entity, sources, ...}}.
    This helper unwraps the outer key so callers can access .entity and .sources directly.
    Handles both the keyed format and the rare direct format gracefully.
    """
    if "entity" in resp or "sources" in resp:
        return resp
    first_key = next(iter(resp), None)
    if first_key and isinstance(resp.get(first_key), dict):
        return resp[first_key]
    return {}
```

```python
def lookup_profile_by_email(base, token, client_id, org_id, sandbox, email):
    """Query Real-Time Customer Profile for a profile by email address."""
    result = subprocess.run([
        "curl", "-s",
        (f"{base}/data/core/ups/access/entities"
         f"?schema.name=_xdm.context.profile"
         f"&entityId={email}&entityIdNS=Email"),
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}"
    ], capture_output=True, text=True)
    raw = json.loads(result.stdout)
    return _unwrap_entity_response(raw)   # always unwrap

def lookup_events_by_email(base, token, client_id, org_id, sandbox, email):
    """Query ExperienceEvents stitched to a profile identified by email."""
    result = subprocess.run([
        "curl", "-s",
        (f"{base}/data/core/ups/access/entities"
         f"?schema.name=_xdm.context.experienceevent"
         f"&relatedSchema.name=_xdm.context.profile"
         f"&relatedEntityId={email}&relatedEntityIdNS=Email"),
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}"
    ], capture_output=True, text=True)
    return json.loads(result.stdout)
```

What to check:
- Profile lookup returns 200 with `sources` array including the customers dataset ID
- `identityGraph` has more than 1 XID if CRMID is configured
- Events lookup returns `_page.count > 0` (events are stitched)
- If events 404 but batch succeeded: check `authenticatedState` in ingested identityMap, or wait 30-60 min for processing on dev sandboxes

---

## 5b. B2B entity verification (B2B USE CASES ONLY)

**Gate**: applies ONLY to genuine B2B projects (`XDM Business Account` / Opportunity / Account-Person
Relation entities, or RT-CDP B2B Edition). For B2C / standard Individual-Profile projects this does NOT
apply — section 5 (identityMap profile validation) is sufficient. Authoritative model:
`xdm-schema-design` → "B2B Edition Schema Architecture".

A B2B Business Account is keyed on **`accountKey.sourceKey`** under a `B2B_ACCOUNT` namespace — NOT
identityMap. Two rules when querying the account union:

- `entityId` = the `accountKey.sourceKey` composite value; `entityIdNS` = the `b2b_account` namespace code.
- The account/relation union queries **REQUIRE `mergePolicyId`** — omit it and you get
  `422 — merge policy doesn't exist`. Fetch it from `GET /data/core/ups/config/mergePolicies`.

```python
def _merge_policy_id(base, headers, schema_name):
    r = subprocess.run(["curl", "-s", f"{base}/data/core/ups/config/mergePolicies"] + headers,
                        capture_output=True, text=True)
    for p in (json.loads(r.stdout) or {}).get("children", []):
        if p.get("schema", {}).get("name") == schema_name:
            return p.get("id")
    return None

def verify_b2b_account(base, token, client_id, org_id, sandbox, account_source_key):
    """Verify a Business Account resolves in the account union by accountKey.sourceKey.
    account_source_key = composite [sourceID]@[sourceInstanceID].[sourceType]."""
    import subprocess, json
    headers = [
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}",
        "-H", "Accept: application/json",
    ]
    mp = _merge_policy_id(base, headers, "_xdm.context.account")
    r = subprocess.run(["curl", "-s",
        f"{base}/data/core/ups/access/entities"
        f"?schema.name=_xdm.context.account"
        f"&entityId={account_source_key}&entityIdNS=b2b_account"
        f"&mergePolicyId={mp}"] + headers, capture_output=True, text=True)
    resp = _unwrap_entity_response(json.loads(r.stdout) if r.stdout.strip() else {})
    return {"account_found": bool(resp.get("entity")), "merge_policy_id": mp}
```

**B2B association timing**: the B2B graph is async — allow **15–60 min** after ingestion before checking.

**If the account is NOT found**:
1. Namespace idType is `B2B_ACCOUNT` (NOT `CROSS_DEVICE`) — `GET /data/core/idnamespace/identities`
2. A PRIMARY identity descriptor exists on `/accountKey/sourceKey` → `b2b_account`
3. `accountKey.sourceKey` is populated (non-null) in every account record
4. The query included `mergePolicyId` (else 422)
5. Batch `metrics.outputRecordCount > 0` and `failedRecordCount == 0`; dataset flags `["identity:enabled","profile:enabled"]`
6. Account and Person resolve to SEPARATE identity graphs — that is expected; they are linked by a relationship descriptor, not a merged identity node

---

## 6. Field-Level Data Comparison

Sample 10 records (first 5, last 5) from source CSV and compare against AEP:

```python
def read_csv_sample(csv_path, n_head=5, n_tail=5):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    return reader[:n_head] + reader[max(0, len(reader)-n_tail):]

def compare_field_values(source_val, aep_val, field_type="string"):
    """
    Compare a source CSV value to its AEP-ingested equivalent.
    Returns (match: bool, reason: str)
    """
    if source_val is None and aep_val is None:
        return True, "both null"
    if source_val is None or aep_val is None:
        return False, f"null mismatch: source={source_val}, aep={aep_val}"

    if field_type == "string":
        match = str(source_val).strip() == str(aep_val).strip()
    elif field_type == "number":
        try:
            match = abs(float(source_val) - float(aep_val)) < 1e-6
        except ValueError:
            match = str(source_val) == str(aep_val)
    elif field_type == "date":
        # Normalize both to ISO 8601 before comparing
        s = str(source_val).strip().replace(" ", "T")
        if not s.endswith("Z"):
            s += "Z" if "T" in s else "T00:00:00Z"
        a = str(aep_val).strip()
        match = s == a
    else:
        match = str(source_val) == str(aep_val)

    return match, f"source={source_val}, aep={aep_val}"
```

---

## 7. Validation Report Format

```
=== DATA VALIDATION REPORT — Stage 7 ===

| Dataset    | Source Records | Ingested | Count Match | Identity | Sample Match | Status |
|------------|----------------|----------|-------------|----------|--------------|--------|
| Customers  | 5000           | 5000     | PASS        | PASS     | PASS         | PASS   |
| Events     | 25000          | 25000    | PASS        | PASS     | PASS         | PASS   |
| Orders     | 10000          | 10000    | PASS        | N/A      | PASS         | PASS   |
| Products   | 200            | 200      | PASS        | N/A      | PASS         | PASS   |

OVERALL: PASS — proceed to qa-master (Stage 8)

=== DETAILS ===
[Per-dataset section with record count, identity check results, field mismatches]
```

Verdict routing:
- ALL PASS → hand off to `qa-master` (Stage 8) via "Hand off to QA Master" button
- ANY WARN → hand off to `qa-master` with warnings noted
- ANY FAIL → hand off to `data-ingestion` for re-ingestion with specific error details

---

## 8. Timing Notes

After batch completion, allow processing time before checking:
- Record count in batch metadata: immediate (from batch status)
- Profile lookup via `/access/entities`: 15-60 min on dev sandboxes
- Event stitching: 30-60 min on dev sandboxes
- If profile 404 immediately after batch: mark as WARN/PENDING, recheck later

---

## 9. Error Reference

| Error | Cause | Fix |
|---|---|---|
| Profile 404 after successful batch | `acp_granular_plugin_validation_flags` is `profile:disabled` | Check Stage 5 (profile-operator) output; fix granular flag |
| Events 404 but batch succeeded | Missing `authenticatedState` in identityMap, or events use CRMID but Profile lacks CRMID | Check identityMap format in Stage 6 transforms |
| Record count FAIL | Batch partial failure (some records rejected) | Check `errors` in batch details; fix source data and re-ingest |
| Field value mismatch on dates | Timestamp not converted to ISO 8601 | Check Stage 6 `to_iso8601()` transform |
