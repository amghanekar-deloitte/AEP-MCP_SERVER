---
name: profile-enablement
description: AEP Real-Time Customer Profile enablement patterns for Stage 5 — three-flag protocol, PATCH-not-PUT for schema union tag, safe tag merge, granular flag requirement, and never-auto-enable rule. Load when enabling Profile on schemas or datasets.
---

# Profile Enablement Skill

Load this skill before any Profile enablement operation in Stage 5.

---

## 1. Never-Auto-Enable Rule (MANDATORY)

**NEVER enable Profile without explicit user approval.**
- Present the full list of schemas and datasets
- Ask: "Which schemas/datasets should be Profile-enabled? Please name them explicitly."
- Wait for the user to name exact entities
- Only proceed after confirmation

This applies at every pipeline run — no exceptions, even for re-runs.

---

## 2. Three-Flag Protocol (ALL THREE ARE REQUIRED)

Profile enablement requires three distinct actions. Missing any one causes silent failures.

| Flag | Where | Effect if Missing |
|---|---|---|
| `meta:immutableTags: ["union"]` | Schema | Schema not included in Profile union — Profile Service ignores it entirely |
| `tags.unifiedProfile: ["enabled:true"]` | Dataset | Dataset not flagged for Profile processing |
| `tags.acp_granular_plugin_validation_flags: ["identity:enabled", "profile:enabled"]` | Dataset | Data lands in data lake but is NEVER processed into Real-Time Customer Profile |

The granular flag is the most common failure cause: the API defaults it to `profile:disabled`. The AEP UI sets it automatically; the API does NOT. Without it, the dataset appears enabled in the UI but data never reaches Profile Service.

---

## 3. Schema: PATCH with JSON Patch (PATCH-not-PUT)

**NEVER use PUT to add `meta:immutableTags`.** PUT with the full schema body fails with `XDM-1500-400` because server-generated read-only fields (like `meta:extends`) cannot be included.

Use JSON Patch:

```python
import json, subprocess, urllib.parse

def enable_schema_for_profile(base, token, client_id, org_id, sandbox, schema_id):
    """Add union tag to schema using JSON Patch. Never use PUT."""
    encoded_id = urllib.parse.quote(schema_id, safe="")
    patch = json.dumps([{"op": "add", "path": "/meta:immutableTags", "value": ["union"]}])
    result = subprocess.run([
        "curl", "-s", "-X", "PATCH",
        f"{base}/data/foundation/schemaregistry/tenant/schemas/{encoded_id}",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/vnd.adobe.xed+json",
        "-d", patch
    ], capture_output=True, text=True)
    return json.loads(result.stdout)

def verify_schema_union_tag(base, token, client_id, org_id, sandbox, schema_id):
    encoded_id = urllib.parse.quote(schema_id, safe="")
    result = subprocess.run([
        "curl", "-s",
        f"{base}/data/foundation/schemaregistry/tenant/schemas/{encoded_id}",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}",
        "-H", "Accept: application/vnd.adobe.xed-full+json; version=1"
    ], capture_output=True, text=True)
    schema = json.loads(result.stdout)
    return "union" in schema.get("meta:immutableTags", [])
```

---

## 4. Dataset: Safe Tag PATCH (GET → Merge → PATCH)

Always GET existing tags first before PATCHing. Sending only new tags blanks existing ones (e.g., `adobe/siphon/table/format`), causing 422 errors on future tag updates.

Set all three dataset-level flags in a single PATCH:

```python
def enable_dataset_for_profile(base, token, client_id, org_id, sandbox, dataset_id):
    """
    Enable Profile on a dataset. Sets all three required flags in one PATCH.
    Merges with existing tags to preserve adobe/siphon/table/format and others.
    """
    # Step 1: GET existing tags
    get_result = subprocess.run([
        "curl", "-s",
        f"{base}/data/foundation/catalog/dataSets/{dataset_id}?properties=tags",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}"
    ], capture_output=True, text=True)
    raw = json.loads(get_result.stdout)
    existing_tags = list(raw.values())[0].get("tags", {})

    # Step 2: Merge new flags into existing tags
    existing_tags["unifiedProfile"] = ["enabled:true"]
    existing_tags["unifiedIdentity"] = ["enabled:true"]
    existing_tags["acp_granular_plugin_validation_flags"] = ["identity:enabled", "profile:enabled"]

    # Step 3: PATCH with merged tags
    patch_result = subprocess.run([
        "curl", "-s", "-X", "PATCH",
        f"{base}/data/foundation/catalog/dataSets/{dataset_id}",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"tags": existing_tags})
    ], capture_output=True, text=True)
    return json.loads(patch_result.stdout)
```

---

## 5. Verification After Enablement (MANDATORY)

After every Profile enablement, verify all three flags are set correctly:

```python
def verify_dataset_profile_flags(base, token, client_id, org_id, sandbox, dataset_id):
    result = subprocess.run([
        "curl", "-s",
        f"{base}/data/foundation/catalog/dataSets/{dataset_id}?properties=tags",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}"
    ], capture_output=True, text=True)
    raw = json.loads(result.stdout)
    tags = list(raw.values())[0].get("tags", {})

    checks = {
        "unifiedProfile": "enabled:true" in tags.get("unifiedProfile", []),
        "unifiedIdentity": "enabled:true" in tags.get("unifiedIdentity", []),
        "granular_profile": "profile:enabled" in tags.get("acp_granular_plugin_validation_flags", []),
        "granular_identity": "identity:enabled" in tags.get("acp_granular_plugin_validation_flags", [])
    }
    all_pass = all(checks.values())
    return all_pass, checks
```

If `granular_profile` is False: data will ingest but NEVER reach Real-Time Customer Profile.

---

## 6. Scope: What Needs Profile Enablement

Typical enablement targets:
- **Customers** (XDM Individual Profile) — YES, enable Profile
- **Events** (XDM ExperienceEvent) — YES, enable Profile for event stitching
- **Orders** (XDM ExperienceEvent) — YES if orders need to appear on profile timeline
- **Products** (Product class) — NO, data-lake only
- **Accounts** (XDM Business Account) — only if B2B profile merge is needed

When enabling Profile schemas, the schema MUST have at least one primary identity configured — check identity descriptors before enabling.

---

## 7. Error Reference

| Error | Cause | Fix |
|---|---|---|
| `XDM-1500-400` on schema update | Used PUT with full schema body | Switch to PATCH with JSON Patch op |
| `422` on dataset PATCH | Blanked `adobe/siphon/table/format` by sending partial tags | GET tags first, merge, then PATCH |
| Data ingests but not in Profile | `acp_granular_plugin_validation_flags` is `profile:disabled` | PATCH granular flag to `profile:enabled` |
| Profile sub-batch `recordsSkipped = total` | Schema not in union (missing `meta:immutableTags: ["union"]`) | PATCH schema with JSON Patch to add union tag |
