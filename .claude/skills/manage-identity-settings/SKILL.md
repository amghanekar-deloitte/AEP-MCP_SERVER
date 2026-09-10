---
name: manage-identity-settings
description: >
  Show how customer identifiers are configured in AEP — list identity namespaces, check
  which fields are marked as identity descriptors, inspect the identity graph for a profile,
  and review merge policies. Load when the user asks "show me our identity namespaces",
  "how is identity set up", "what identities does profile X have", "check identity resolution",
  "manage identity settings", or "show identity graph". Uses mcp__aep__list_identity_namespaces,
  get_identity_namespace, list_descriptors, and get_identity_cluster.
---

# Manage Identity Settings

## When to Load

- "show me our identity namespaces"
- "how is identity configured"
- "what identities does profile X have"
- "check identity resolution / graph"
- "manage identity settings"
- "show identity graph for [value]"

---

## Identity Concepts

| Concept | Description |
|---|---|
| **Namespace** | The type of identifier: ECID, email, phone, CRM ID, custom |
| **Identity Descriptor** | A schema field marked as an identity with a namespace |
| **Identity Cluster** | All identity values linked to one person in the graph |
| **Merge Policy** | Rules for how profile fragments from different sources are merged |
| **Primary Identity** | The single strongest identifier used for profile stitching |

---

## API Approach

### List namespaces

```
mcp__aep__list_identity_namespaces   — all custom + standard namespaces in the org
mcp__aep__get_identity_namespace     — detail for a specific namespace by code
```

Key fields: `code` (the namespace code used in PQL/API), `namespaceType` (Standard vs Custom), `idType` (COOKIE, CROSS_DEVICE, EMAIL, PHONE, etc.)

### List identity descriptors on schemas

```
mcp__aep__list_descriptors   — filter type=xdm:descriptorIdentity
```

Shows which schema fields are configured as identity fields.

### Look up a profile's identity cluster

```
mcp__aep__get_identity_cluster   — all identity values linked to a given ID
```

Input: `{ "xid": "<namespace>:<value>" }` or `{ "namespace": { "code": "email" }, "id": "user@example.com" }`

---

## Output Format

**Namespaces:**

| Code | Name | Type | ID Type | Custom |
|---|---|---|---|---|
| ECID | Experience Cloud ID | Standard | COOKIE | No |
| Email | Email | Standard | Email | No |
| ProxyID | ProxyID | Custom | Cross-device | Yes |
| _deloitte_digitalengage.proxyId | Deloitte ProxyId | Custom | Cross-device | Yes |

**Identity Cluster for a profile:**

```
Identity Cluster for email: john.doe@example.com

  Namespace   Value                     Linked Since
  ─────────────────────────────────────────────────────
  email       john.doe@example.com      2026-01-15
  ECID        38498273648293746         2026-01-15
  ProxyID     PRX-00012345              2026-03-01
  phone       +15551234567              2026-06-10

  Total linked identities: 4
  Profile merged across: 3 datasets
```
