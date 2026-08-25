---
name: dataset-automation
description: AEP dataset creation patterns for Stage 3 — parquet format enforcement, duplicate-dataset prevention gate, safe tag PATCH protocol (GET-merge-PATCH), and deployment manifest updates. Load when creating or managing AEP datasets via the Catalog API.
---

# Dataset Automation Skill

Load this skill before any dataset creation operation in Stage 3.

---

## 1. Mandatory Protocol: No Duplicate Datasets

**BEFORE creating any dataset, always check for existing ones.**

```python
import json, subprocess, os

def list_existing_datasets(base, token, client_id, org_id, sandbox):
    """Return list of {id, name, schemaRef} for all datasets in the sandbox."""
    result = subprocess.run([
        "curl", "-s",
        f"{base}/data/foundation/catalog/dataSets?properties=name,schemaRef&limit=100",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}"
    ], capture_output=True, text=True)
    raw = json.loads(result.stdout)
    return [{"id": ds_id, **ds_data} for ds_id, ds_data in raw.items()]

def find_existing_dataset(datasets, schema_id=None, name=None):
    """Return existing dataset if name or schemaRef matches, else None."""
    for ds in datasets:
        if name and ds.get("name") == name:
            return ds
        if schema_id and ds.get("schemaRef", {}).get("id") == schema_id:
            return ds
    return None
```

Decision rule:
- If a dataset with the **same name** exists → REUSE it, report "Reusing existing dataset {name} ({id})"
- If a dataset with the **same schemaRef** exists → REUSE it, even if the name differs
- Only CREATE if no match found on either name or schemaRef
- Present findings to user: "Found existing dataset X for schema Y — will reuse"

---

## 2. Mandatory Protocol: Parquet Format

Every dataset MUST be created with `"format": "parquet"`. JSON format causes `ERR-BI-106: Batch ingestion format not compatible with storage format`.

```python
def create_dataset(base, token, client_id, org_id, sandbox, name, schema_id):
    payload = json.dumps({
        "name": name,
        "schemaRef": {
            "id": schema_id,
            "contentType": "application/vnd.adobe.xed-full+json;version=1"
        },
        "fileDescription": {
            "format": "parquet"
        }
    })
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"{base}/data/foundation/catalog/dataSets",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}",
        "-H", "Content-Type: application/json",
        "-d", payload
    ], capture_output=True, text=True)
    response = json.loads(result.stdout)
    # Response is a list with one element: the new dataset ID
    if isinstance(response, list) and len(response) > 0:
        return response[0]
    raise ValueError(f"Unexpected dataset creation response: {response}")
```

**NEVER include** `unifiedProfile`, `unifiedIdentity`, or `acp_granular_plugin_validation_flags` at creation time.
Profile enablement is exclusively Stage 5 (profile-operator) after explicit user approval.

---

## 3. Mandatory Protocol: Safe Tag PATCH (GET → Merge → PATCH)

When updating dataset tags (e.g., during Profile enablement in Stage 5), **always GET existing tags first** and merge before PATCHing. Sending only new tags will blank existing ones like `adobe/siphon/table/format`, causing 422 errors on future tag updates.

```python
def get_dataset_tags(base, dataset_id, token, client_id, org_id, sandbox):
    result = subprocess.run([
        "curl", "-s",
        f"{base}/data/foundation/catalog/dataSets/{dataset_id}?properties=tags",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}"
    ], capture_output=True, text=True)
    raw = json.loads(result.stdout)
    # Response is {dataset_id: {tags: {...}}}
    ds_data = list(raw.values())[0]
    return ds_data.get("tags", {})

def safe_patch_tags(base, dataset_id, new_tags, token, client_id, org_id, sandbox):
    """Merge new_tags into existing tags then PATCH — never overwrite existing tags."""
    existing = get_dataset_tags(base, dataset_id, token, client_id, org_id, sandbox)
    merged = {**existing, **new_tags}
    result = subprocess.run([
        "curl", "-s", "-X", "PATCH",
        f"{base}/data/foundation/catalog/dataSets/{dataset_id}",
        "-H", f"Authorization: Bearer {token}",
        "-H", f"x-api-key: {client_id}",
        "-H", f"x-gw-ims-org-id: {org_id}",
        "-H", f"x-sandbox-name: {sandbox}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"tags": merged})
    ], capture_output=True, text=True)
    return json.loads(result.stdout)
```

---

## 4. Deployment Manifest Update

After creating or reusing datasets, update `Result_DataAnalysis/deployment_manifest.json`:

```python
import json

def update_manifest_datasets(manifest_path, entity_name, dataset_id, dataset_name, schema_id):
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    if "datasets" not in manifest:
        manifest["datasets"] = {}
    manifest["datasets"][entity_name] = {
        "datasetId": dataset_id,
        "name": dataset_name,
        "schemaId": schema_id,
        "format": "parquet",
        "profileEnabled": False
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
```

---

## 5. Error Reference

| Error | Cause | Fix |
|---|---|---|
| `ERR-BI-106` | Dataset created with `format: json` | Delete and recreate with `format: parquet` |
| `422 Unprocessable Entity` on PATCH | Existing tag `adobe/siphon/table/format` was blanked | Use safe_patch_tags — always GET and merge first |
| `409 Conflict` on dataset create | Dataset name already exists | REUSE the existing dataset — do not create |
| `400` on schema reference | Schema $id not URL-encoded in query params | Use `urllib.parse.quote(schema_id, safe="")` |

---

## 6. Verify Dataset Creation

```bash
# Confirm dataset exists and has correct format
curl -s "${AEP_BASE_URL}/data/foundation/catalog/dataSets/${DATASET_ID}?properties=name,schemaRef,fileDescription,tags" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "x-api-key: ${AEP_CLIENT_ID}" \
  -H "x-gw-ims-org-id: ${AEP_ORG_ID}" \
  -H "x-sandbox-name: ${AEP_SANDBOX_NAME}" | python3 -m json.tool
```

Expected: `fileDescription.format = "parquet"`, no `unifiedProfile` tags at this stage.
