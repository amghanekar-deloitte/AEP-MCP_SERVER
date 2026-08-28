---
name: offer-decisioning
description: AJO Offer Decisioning (classic Decision Management / DPS) — offer library, eligibility rules, collections, activities, placements, PQL for offers, offer decisioning API flow (draft to publish to propagation), get_member_offers, view_offers HTML artifact, and known gotchas (customAttributes JSON-string, propagation delay, placement matching, colons in IDs). Load when working with AJO offer decisioning, listing or creating offers, evaluating offers for a profile, or debugging offer eligibility.
---

# Offer Decisioning

## API Bases

| Domain | Base Path |
|---|---|
| Offer Library (authoring) | `/data/core/dps` |
| Offer Decisioning Service (runtime/delivery) | `/data/core/ods` |

All DPS tools require a valid `x-sandbox-name` header. Wrong sandbox → 400 "sandbox not found"; missing → 500.

---

## Core Objects

```
Placements       — channels/surfaces where an offer can appear (e.g. email, web)
Offers           — personalized or fallback content with eligibility rules + representations
Collections      — curated groups of offers (filterType: anyTags / allTags / offers)
Eligibility Rules — PQL expressions that gate offer delivery per profile
Activities       — decisions: link collections + placements + ranking → select best offer
```

---

## Tool Reference

### Read Operations

```
mcp__aep__list_offers(offer_type="personalized")   — list offers (also "fallback")
mcp__aep__get_offer(offer_id)                      — get single offer
mcp__aep__list_placements()                        — list placement surfaces
mcp__aep__list_collections()                       — list offer collections
mcp__aep__list_offer_activities()                  — list offer activities (decisions)
mcp__aep__get_offer_activity(activity_id)          — get single activity
mcp__aep__list_ranking_formulas()                  — list AI ranking formulas
```

### Write Operations

```
mcp__aep__create_eligibility_rule(name, pql)       — create PQL-based eligibility rule
```

### Delivery / Evaluation

```
mcp__aep__get_member_offers(
    identity_id, identity_namespace,
    activity_ids="",           # comma-separated activity IDs (auto-resolves placements)
    decision_scopes="",        # Base64-encoded scopes (takes priority over activity_ids)
    context_language="en",     # shorthand for xdm:language context
    context_data="{}",         # JSON object of additional context key-value pairs
    merge_policy_id=""         # if omitted, tries all sandbox merge policies
)
```

### HTML Artifact

```
mcp__aep__view_offers(identity_id, identity_namespace, ...)
```

Evaluates offers and renders a self-contained HTML artifact with offer cards, eligibility status, content preview, and Raw JSON toggle. Follow the `instruction` field in the response: display `text_summary`, then read `html_file` and publish as artifact. Save to `scratchpad/artifacts/`.

---

## Offer Lifecycle: Draft → Publish → Propagation

```
Create offer / activity via API  →  Status: DRAFT
Publish in AJO UI               →  Status: LIVE (content indexed for runtime)
Runtime serving                  →  Propagation delay: 15–45 min for NEW objects
```

**No publish API exists.** Only the AJO UI "Publish" button forces the runtime re-index. Programmatic creation sets status to DRAFT — the offer/activity will not be returned by the decisioning engine until UI-published.

**Propagation delay gotcha:** A brand-new decision activity returned 404 "scope not found" for 45+ minutes after UI publish. Edits to existing offers can take 15+ minutes to appear in runtime responses. Days-old decisions serve instantly. Factor this into testing — if offers are not appearing, wait before assuming a bug.

---

## PQL for Eligibility Rules

Use `mcp__aep__create_eligibility_rule(name, pql)` to create rules. PQL syntax for offer rules:

```pql
-- Profile attribute check
person.age >= 18 and homeAddress.countryCode = "US"

-- Array membership (NOT lambda syntax)
"RADIOLOGY" in _tenant.cohortList

-- Context data (language injected by get_member_offers context_language param)
-- NOTE: xdm: prefix is STRIPPED in PQL — use bare key name
select cd from @{_xdm.context.additionalParameters;version=1} where cd.language = "en"

-- Combined profile + context
homeAddress.stateProvince = "CA"
and (select cd from @{_xdm.context.additionalParameters;version=1} where cd.language = "en")
```

**PQL anti-pattern:** Do NOT use lambda syntax (`.exists(v -> ...)`) — it is not valid offer PQL. Use `in` or `select v from ... where v.field.equals("x", false)` instead.

---

## Eligibility: Placement Matching Rule

An offer is only eligible for an activity if it has a **representation matching the activity's placement**. Placement mismatch = offer is silently ineligible, no error returned. Always verify that each offer has a representation for the placement used in the activity.

---

## `customAttributes` / `offerContexts` Location

`offerContexts` and `customAttributes` are embedded **inside the JSON content string** of `representations[].components[].content` — they are NOT top-level offer fields or `characteristics`. Access pattern:

```python
content_str = offer["representations"][0]["components"][0]["content"]
offer_data = json.loads(content_str)   # content is a JSON string, not an object
contexts = offer_data.get("offerContexts", [])
```

Some offers (Radiology, Low Acuity in Aetna) have invalid JSON requiring regex extraction. Always wrap `json.loads(content_str)` in a try/except.

---

## ID Handling Quirks

- `get_offer` requires `?offer-type=personalized` query param (or `fallback`) — omitting it returns 400/404.
- Offer and activity IDs contain literal colons (e.g. `dps:offer-activity:abc123`). Do NOT URL-encode them — literal colons in path segments work; `urllib.parse.quote(id)` breaks the request.
- Direct `GET /offer-decisions/{id}` may fail for colon-containing IDs on some DPS versions. Workaround: fetch all activities with `list_offer_activities()` and filter by ID in Python.

---

## Context Data for Offer Evaluation

```python
# Language context (most common — use the shorthand)
mcp__aep__get_member_offers(
    identity_id="17P41BBBB",
    identity_namespace="ProxyId",
    context_language="en"    # injected as xdm:language
)

# Additional context
mcp__aep__get_member_offers(
    identity_id="17P41BBBB",
    identity_namespace="ProxyId",
    context_data='{"xdm:channel":"web","xdm:device":"mobile"}'
)
```

In eligibility rules, context data keys have the `xdm:` prefix stripped — reference as `cd.language`, not `cd["xdm:language"]`.

---

## Merge Policy Behavior

If `merge_policy_id` is omitted, `get_member_offers` tries all merge policies in the sandbox and returns results keyed by policy name. For Aetna, use:
- Dev: Edge merge policy `7dc5b130...` first; fallback to `23803271...`
- Prod: Always `23803271...`

See `aetna_merge_policies.md` memory for full IDs.

---

## Related Skills

- `ajo` — fetches AJO documentation from Experience League; use for guardrails and limits
- `ajo-journey` — journey-specific patterns
- `segment-management` — PQL for audience segments (different endpoint but same syntax family)
- `sandbox-schema-context` — **load when reading offer characteristics or rendering offer content**; use `extract_prompt_text(characteristics)` to find the prompt text key dynamically instead of hardcoding `"PromptText"` or `"promptText"`
