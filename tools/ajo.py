"""
Adobe Journey Optimizer (AJO) tools — journeys, campaigns, offers, and offer decisioning.

API base: https://platform.adobe.io
  Journeys & Campaigns : /data/core/ajo/
  Offer Decisioning    : /data/core/dps/      (Decision Platform Service)

Verify exact paths against the AJO REST API reference at:
  https://developer.adobe.com/journey-optimizer/api-reference/
"""

import base64
import json
import time
from datetime import datetime, timezone

from auth import aep_get, aep_post, get_active_sandbox
from tools.usage_logger import track

_AJO = "/data/core/ajo"
_DPS = "/data/core/dps"
_ODS = "/data/core/ods"  # Offer Decisioning Service — decisions/propositions


def _extract_placements(activity: dict) -> list:
    """Return a deduplicated list of placement IDs from an offer activity object.

    Placements live inside criteria[].placements (not at the top level).
    """
    seen: set = set()
    result: list = []
    for criterion in activity.get("criteria", []):
        for pid in criterion.get("placements", []):
            if pid not in seen:
                seen.add(pid)
                result.append(pid)
    return result


def register(mcp) -> None:

    # ── Journeys ─────────────────────────────────────────────────────────────

    @mcp.tool()
    @track("list_journeys")
    def list_journeys(
        sandbox: str = "",
        limit: int = 20,
        start: int = 0,
        status: str = "",
    ) -> dict:
        """List AJO journey definitions.

        Args:
            sandbox: Sandbox name.
            limit: Max records.
            start: Pagination offset.
            status: Filter by status (DRAFT, LIVE, FINISHED, CLOSED).
        """
        try:
            params: dict = {"limit": limit, "start": start}
            if status:
                params["status"] = status
            return aep_get(f"{_AJO}/journeys", sandbox=sandbox or None, params=params)
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("get_journey")
    def get_journey(journey_id: str, sandbox: str = "") -> dict:
        """Get details for a specific AJO journey.

        Args:
            journey_id: Journey ID.
            sandbox: Sandbox name.
        """
        try:
            return aep_get(f"{_AJO}/journeys/{journey_id}", sandbox=sandbox or None)
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("list_journey_versions")
    def list_journey_versions(journey_id: str, sandbox: str = "") -> dict:
        """List all published versions of a journey.

        Args:
            journey_id: Journey ID.
            sandbox: Sandbox name.
        """
        try:
            return aep_get(
                f"{_AJO}/journeys/{journey_id}/versions",
                sandbox=sandbox or None,
            )
        except Exception as exc:
            return {"error": str(exc)}

    # ── Campaigns ────────────────────────────────────────────────────────────

    @mcp.tool()
    @track("list_campaigns")
    def list_campaigns(
        sandbox: str = "",
        limit: int = 20,
        start: int = 0,
        status: str = "",
    ) -> dict:
        """List AJO campaigns.

        Args:
            sandbox: Sandbox name.
            limit: Max records.
            start: Pagination offset.
            status: Filter by status (DRAFT, LIVE, COMPLETED, STOPPED, etc.).
        """
        try:
            params: dict = {"limit": limit, "start": start}
            if status:
                params["status"] = status
            return aep_get(f"{_AJO}/campaigns", sandbox=sandbox or None, params=params)
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("get_campaign")
    def get_campaign(campaign_id: str, sandbox: str = "") -> dict:
        """Get details for a specific AJO campaign.

        Args:
            campaign_id: Campaign ID.
            sandbox: Sandbox name.
        """
        try:
            return aep_get(f"{_AJO}/campaigns/{campaign_id}", sandbox=sandbox or None)
        except Exception as exc:
            return {"error": str(exc)}

    # ── Offer Library (Decision Management) ─────────────────────────────────

    @mcp.tool()
    @track("list_offers")
    def list_offers(
        sandbox: str = "",
        offer_type: str = "personalized",
        limit: int = 20,
        start: int = 0,
    ) -> dict:
        """List offers from the Offer Library.

        Args:
            sandbox: Sandbox name.
            offer_type: 'personalized' or 'fallback'.
            limit: Max records.
            start: Pagination offset.
        """
        try:
            return aep_get(
                f"{_DPS}/offers",
                sandbox=sandbox or None,
                params={"offer-type": offer_type, "limit": limit, "_start": start},
            )
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("get_offer")
    def get_offer(offer_id: str, sandbox: str = "") -> dict:
        """Get details for a specific personalized offer.

        Args:
            offer_id: Offer ID.
            sandbox: Sandbox name.
        """
        try:
            return aep_get(
                f"{_DPS}/offers/{offer_id}",
                sandbox=sandbox or None,
                params={"offer-type": "personalized"},
            )
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("list_placements")
    def list_placements(sandbox: str = "", limit: int = 20) -> dict:
        """List offer placements (channels/surfaces where offers appear).

        Args:
            sandbox: Sandbox name.
            limit: Max records.
        """
        try:
            return aep_get(
                f"{_DPS}/placements",
                sandbox=sandbox or None,
                params={"limit": limit},
            )
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("list_collections")
    def list_collections(sandbox: str = "", limit: int = 20) -> dict:
        """List offer collections (curated groups of offers).

        Args:
            sandbox: Sandbox name.
            limit: Max records.
        """
        try:
            return aep_get(
                f"{_DPS}/offer-collections",
                sandbox=sandbox or None,
                params={"limit": limit},
            )
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("list_offer_activities")
    def list_offer_activities(sandbox: str = "", limit: int = 20) -> dict:
        """List offer activities (decisions) — the logic that selects the best offer.

        Args:
            sandbox: Sandbox name.
            limit: Max records.
        """
        try:
            return aep_get(
                f"{_DPS}/offer-decisions",
                sandbox=sandbox or None,
                params={"limit": limit},
            )
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("get_offer_activity")
    def get_offer_activity(activity_id: str, sandbox: str = "") -> dict:
        """Get details for a specific offer activity (decision).

        Args:
            activity_id: Offer activity ID.
            sandbox: Sandbox name.
        """
        try:
            return aep_get(f"{_DPS}/offer-decisions/{activity_id}", sandbox=sandbox or None)
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("create_eligibility_rule")
    def create_eligibility_rule(
        name: str,
        pql: str,
        description: str = "",
        sandbox: str = "",
    ) -> dict:
        """Create an AJO offer eligibility rule (offer-rule) with a PQL expression.

        Args:
            name: Display name for the rule.
            pql: PQL expression string.
            description: Optional description.
            sandbox: Sandbox name.
        """
        try:
            body: dict = {
                "name": name,
                "condition": {
                    "type": "PQL",
                    "format": "pql/text",
                    "value": pql,
                },
            }
            if description:
                body["description"] = description
            return aep_post(f"{_DPS}/offer-rules", body, sandbox=sandbox or None)
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("list_ranking_formulas")
    def list_ranking_formulas(sandbox: str = "", limit: int = 20) -> dict:
        """List offer ranking formulas used for AI-ranked offer decisioning.

        Args:
            sandbox: Sandbox name.
            limit: Max records.
        """
        try:
            return aep_get(
                f"{_DPS}/ranking-formulas",
                sandbox=sandbox or None,
                params={"limit": limit},
            )
        except Exception as exc:
            return {"error": str(exc)}

    # ── Offer Decisioning — member-level evaluation ───────────────────────────

    @mcp.tool()
    @track("get_member_offers")
    def get_member_offers(
        identity_id: str,
        identity_namespace: str,
        activity_ids: str = "",
        decision_scopes: str = "",
        context_language: str = "",
        context_data: str = "",
        merge_policy_id: str = "",
        allow_duplicates: bool = True,
        include_content: bool = True,
        include_characteristics: bool = False,
        sandbox: str = "",
    ) -> dict:
        """Get personalized offers for a member via the ODS Decisions API.

        Evaluates eligibility rules and ranking formulas and returns the best
        offer per decision scope (one per activity+placement pair).

        Provide activity_ids (comma-separated) to evaluate specific activities;
        omit to evaluate all active offer activities in the sandbox.
        Pass decision_scopes (comma-separated Base64 strings) to use pre-encoded
        scopes directly — this takes priority over activity_ids.

        Args:
            identity_id: Member identity value (e.g. "17P41BBBBPXZ_1").
            identity_namespace: Namespace code (e.g. ProxyId, Email, CRMID).
            activity_ids: Comma-separated offer activity IDs. The tool resolves
                their placements from the activity object automatically.
            decision_scopes: Comma-separated Base64-encoded decision scope strings
                (takes priority over activity_ids when both are supplied).
            context_language: Language code injected as xdm:language context
                variable (e.g. "en", "es"). Shorthand for the most common
                context override; use context_data for other variables.
            context_data: JSON object of additional xdm:data context key-value
                pairs passed to eligibility rules, e.g.
                {"xdm:channel":"web","xdm:device":"mobile"}.
                Merged with context_language when both are supplied.
            merge_policy_id: UUID of the merge policy to use for profile
                resolution (e.g. "1350ede5-f621-4448-9c26-a12d2ab2ce2b").
                Defaults to the sandbox default merge policy when omitted.
            allow_duplicates: Allow the same offer to appear across multiple
                activities or placements (default true).
            include_content: Include offer content/representation in response
                (default true).
            include_characteristics: Include offer characteristics metadata
                (OfferID, OfferName, OfferType, etc.) in response (default false).
            sandbox: Sandbox name.
        """
        _CT = (
            'application/vnd.adobe.xdm+json; schema='
            '"https://ns.adobe.com/experience/offer-management/decision-request;version=1.0"'
        )
        _ACCEPT = (
            'application/vnd.adobe.xdm+json; schema='
            '"https://ns.adobe.com/experience/offer-management/decision-response;version=1.0"'
        )

        try:
            # Build xdm:propositionRequests ───────────────────────────────────
            prop_requests: list = []

            if decision_scopes:
                for scope in [s.strip() for s in decision_scopes.split(",") if s.strip()]:
                    try:
                        decoded = json.loads(base64.b64decode(scope).decode())
                        entry: dict = {"xdm:activityId": decoded.get("activityId", scope)}
                        if decoded.get("placementId"):
                            entry["xdm:placementId"] = decoded["placementId"]
                        prop_requests.append(entry)
                    except Exception:
                        prop_requests.append({"xdm:activityId": scope})

            elif activity_ids:
                # Fetch full list once and filter — direct GET by ID fails for
                # IDs containing colons (e.g. dps:offer-activity:...) on DPS.
                acts_resp = aep_get(
                    f"{_DPS}/offer-decisions",
                    sandbox=sandbox or None,
                    params={"limit": 100},
                )
                all_acts = (
                    acts_resp.get("results")
                    or acts_resp.get("items")
                    or acts_resp.get("_embedded", {}).get("decisions", [])
                    or []
                )
                act_map = {
                    a.get("id") or a.get("@id") or a.get("xdm:id", ""): a
                    for a in all_acts
                }
                for act_id in [a.strip() for a in activity_ids.split(",") if a.strip()]:
                    act = act_map.get(act_id, {})
                    placements = _extract_placements(act)
                    if placements:
                        for pid in placements:
                            prop_requests.append(
                                {"xdm:activityId": act_id, "xdm:placementId": pid}
                            )
                    else:
                        prop_requests.append({"xdm:activityId": act_id})

            else:
                resp = aep_get(
                    f"{_DPS}/offer-decisions",
                    sandbox=sandbox or None,
                    params={"limit": 100},
                )
                activities = (
                    resp.get("items")
                    or resp.get("results")
                    or resp.get("_embedded", {}).get("decisions", [])
                    or []
                )
                now = datetime.now(timezone.utc)
                for act in activities:
                    act_id = act.get("id") or act.get("@id") or act.get("xdm:id", "")
                    if not act_id:
                        continue
                    # Skip non-live or expired activities
                    if act.get("status") != "live":
                        continue
                    end = act.get("endDate")
                    if end:
                        try:
                            if datetime.fromisoformat(end.replace("Z", "+00:00")) < now:
                                continue
                        except Exception:
                            pass
                    placements = _extract_placements(act)
                    if placements:
                        for pid in placements:
                            prop_requests.append(
                                {"xdm:activityId": act_id, "xdm:placementId": pid}
                            )
                    else:
                        prop_requests.append({"xdm:activityId": act_id})

            if not prop_requests:
                return {
                    "error": (
                        "No offer activities resolved. Provide activity_ids or decision_scopes, "
                        "or ensure active offer activities exist in this sandbox."
                    )
                }

            # Build profile context data ──────────────────────────────────────
            ctx_data: dict = {}
            if context_language:
                ctx_data["xdm:language"] = context_language
            if context_data:
                try:
                    ctx_data.update(json.loads(context_data))
                except json.JSONDecodeError as exc:
                    return {"error": f"Invalid context_data JSON: {exc}"}

            profile: dict = {
                "xdm:identityMap": {
                    identity_namespace: [{"xdm:id": identity_id, "primary": True}]
                }
            }
            if ctx_data:
                profile["xdm:contextData"] = [
                    {
                        "@type": "_xdm.context.additionalParameters;version=1",
                        "xdm:data": ctx_data,
                    }
                ]

            # Assemble base ODS request body ─────────────────────────────────
            base_body: dict = {
                "xdm:propositionRequests": prop_requests,
                "xdm:profiles": [profile],
                "xdm:allowDuplicatePropositions": {
                    "xdm:acrossActivities": allow_duplicates,
                    "xdm:acrossPlacements": allow_duplicates,
                },
                "xdm:responseFormat": {
                    "xdm:includeContent": include_content,
                    **({"xdm:includeMetadata": {"xdm:option": ["characteristics"]}} if include_characteristics else {}),
                },
            }

            def _run(policy_id: str = "") -> dict:
                body = dict(base_body)
                if policy_id:
                    body["xdm:mergePolicy"] = {"xdm:id": policy_id}
                return aep_post(
                    f"{_ODS}/decisions",
                    body,
                    sandbox=sandbox or None,
                    content_type=_CT,
                    accept=_ACCEPT,
                )

            # Single merge policy — return result directly
            if merge_policy_id:
                return _run(merge_policy_id)

            # No merge policy specified — run against every policy in the sandbox
            mp_resp = aep_get(
                "/data/core/ups/config/mergePolicies",
                sandbox=sandbox or None,
                params={"limit": 50},
            )
            policies = (
                mp_resp.get("children")
                or mp_resp.get("results")
                or mp_resp.get("items")
                or []
            )

            if not policies:
                # No policies discoverable — run once with sandbox default
                return _run()

            results: dict = {}
            for mp in policies:
                pid = mp.get("id", "")
                pname = mp.get("name", pid)
                label = f"{pname} ({pid})"
                try:
                    results[label] = _run(pid)
                except Exception as exc:
                    results[label] = {"error": str(exc)}

            return {
                "merge_policy_count": len(policies),
                "results_by_merge_policy": results,
            }

        except Exception as exc:
            return {"error": str(exc)}

    # ── Journey profile participation ─────────────────────────────────────────

    @mcp.tool()
    @track("get_member_active_journeys")
    def get_member_active_journeys(
        identity_id: str,
        identity_namespace: str = "ProxyID",
        lookback_days: int = 30,
        sandbox: str = "",
    ) -> dict:
        """List AJO journeys a member is currently active in, with their current step.

        Queries the journey step events dataset via Query Service to find journey
        instances where the member entered but has not yet reached an end node
        within the lookback window. Polls up to ~15 s for results.

        Args:
            identity_id: Member identity value (e.g. "C7P41BBBBPXZ").
            identity_namespace: Namespace code (default ProxyID).
            lookback_days: Days back to search for journey entry events (default 30).
            sandbox: Sandbox name.
        """
        try:
            effective_sandbox = sandbox or get_active_sandbox()

            # Discover the journey step events dataset
            ds_resp = aep_get(
                "/catalog/dataSets",
                sandbox=sandbox or None,
                params={"limit": 100, "orderBy": "-created"},
            )
            ds_map = ds_resp if isinstance(ds_resp, dict) else {}
            jse_name: str = ""
            for _ds_id, ds in ds_map.items():
                name = (ds.get("name") or "").lower()
                if "journey" in name and "step" in name:
                    jse_name = ds.get("name", "")
                    break

            if not jse_name:
                return {
                    "error": (
                        "No journey step events dataset found in this sandbox. "
                        "Ensure AJO is active and at least one journey has been published."
                    )
                }

            sql = f"""
WITH events AS (
    SELECT
        timestamp,
        _experience.journeyOrchestration.stepEvents.journeyVersionID   AS journey_version_id,
        _experience.journeyOrchestration.stepEvents.journeyVersionName AS journey_name,
        _experience.journeyOrchestration.stepEvents.instanceID         AS instance_id,
        _experience.journeyOrchestration.stepEvents.nodeName           AS node_name,
        _experience.journeyOrchestration.stepEvents.nodeType           AS node_type,
        _experience.journeyOrchestration.stepEvents.stepStatus         AS step_status,
        ROW_NUMBER() OVER (
            PARTITION BY _experience.journeyOrchestration.stepEvents.instanceID
            ORDER BY timestamp DESC
        ) AS rn
    FROM "{jse_name}"
    WHERE identityMap['{identity_namespace}'][0].id = '{identity_id}'
      AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{lookback_days}' DAY
)
SELECT
    latest.journey_version_id,
    latest.journey_name,
    latest.instance_id,
    latest.node_name     AS current_node,
    latest.node_type     AS current_node_type,
    latest.step_status   AS current_step_status,
    latest.timestamp     AS last_event_time,
    entry.min_ts         AS entry_time
FROM events latest
JOIN (
    SELECT instance_id, MIN(timestamp) AS min_ts FROM events GROUP BY instance_id
) entry ON latest.instance_id = entry.instance_id
WHERE latest.rn = 1
  AND LOWER(latest.node_type) NOT IN ('end', 'endevent', 'exit')
ORDER BY latest.timestamp DESC
""".strip()

            body = {
                "dbName": f"{effective_sandbox}:all",
                "sql": sql,
                "name": f"active_journeys_{identity_id[:12]}",
            }
            query = aep_post("/data/foundation/query/queries", body, sandbox=sandbox or None)
            query_id = query.get("id", "")

            # Poll up to ~15 s for results
            for _ in range(5):
                time.sleep(3)
                status = aep_get(
                    f"/data/foundation/query/queries/{query_id}",
                    sandbox=sandbox or None,
                )
                state = status.get("state", "")
                if state == "SUCCESS":
                    return {
                        "query_id": query_id,
                        "state": state,
                        "dataset": jse_name,
                        "rowCount": status.get("rowCount", 0),
                        "data": status.get("data") or status.get("result"),
                    }
                if state in ("FAILED", "CANCELLED"):
                    return {
                        "query_id": query_id,
                        "state": state,
                        "errors": status.get("errors"),
                    }

            return {
                "query_id": query_id,
                "state": "PENDING",
                "message": "Query submitted. Use get_query to check status.",
                "dataset": jse_name,
            }

        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("get_member_journey_history")
    def get_member_journey_history(
        identity_id: str,
        identity_namespace: str = "ProxyID",
        lookback_days: int = 90,
        include_active: bool = True,
        sandbox: str = "",
    ) -> dict:
        """Get a member's full journey participation history.

        Queries the journey step events dataset via Query Service and returns every
        journey instance the member has been part of — completed, exited, and
        (optionally) still-active — within the lookback window. Polls up to ~15 s.

        Args:
            identity_id: Member identity value (e.g. "C7P41BBBBPXZ").
            identity_namespace: Namespace code (default ProxyID).
            lookback_days: Days back to search (default 90).
            include_active: Include journeys still in progress (default True).
            sandbox: Sandbox name.
        """
        try:
            effective_sandbox = sandbox or get_active_sandbox()

            # Discover the journey step events dataset
            ds_resp = aep_get(
                "/catalog/dataSets",
                sandbox=sandbox or None,
                params={"limit": 100, "orderBy": "-created"},
            )
            ds_map = ds_resp if isinstance(ds_resp, dict) else {}
            jse_name: str = ""
            for _ds_id, ds in ds_map.items():
                name = (ds.get("name") or "").lower()
                if "journey" in name and "step" in name:
                    jse_name = ds.get("name", "")
                    break

            if not jse_name:
                return {
                    "error": (
                        "No journey step events dataset found in this sandbox. "
                        "Ensure AJO is active and at least one journey has been published."
                    )
                }

            active_filter = (
                ""
                if include_active
                else "AND LOWER(latest.node_type) IN ('end', 'endevent', 'exit')"
            )

            sql = f"""
WITH events AS (
    SELECT
        timestamp,
        _experience.journeyOrchestration.stepEvents.journeyVersionID   AS journey_version_id,
        _experience.journeyOrchestration.stepEvents.journeyVersionName AS journey_name,
        _experience.journeyOrchestration.stepEvents.instanceID         AS instance_id,
        _experience.journeyOrchestration.stepEvents.nodeName           AS node_name,
        _experience.journeyOrchestration.stepEvents.nodeType           AS node_type,
        _experience.journeyOrchestration.stepEvents.stepStatus         AS step_status,
        ROW_NUMBER() OVER (
            PARTITION BY _experience.journeyOrchestration.stepEvents.instanceID
            ORDER BY timestamp DESC
        ) AS rn
    FROM "{jse_name}"
    WHERE identityMap['{identity_namespace}'][0].id = '{identity_id}'
      AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{lookback_days}' DAY
)
SELECT
    latest.journey_version_id,
    latest.journey_name,
    latest.instance_id,
    latest.node_name   AS last_node,
    latest.node_type   AS last_node_type,
    latest.step_status AS last_step_status,
    latest.timestamp   AS last_event_time,
    entry.min_ts       AS entry_time,
    CASE
        WHEN LOWER(latest.node_type) IN ('end', 'endevent') THEN 'completed'
        WHEN LOWER(latest.node_type) = 'exit'               THEN 'exited'
        ELSE 'active'
    END AS journey_status
FROM events latest
JOIN (
    SELECT instance_id, MIN(timestamp) AS min_ts FROM events GROUP BY instance_id
) entry ON latest.instance_id = entry.instance_id
WHERE latest.rn = 1
  {active_filter}
ORDER BY latest.timestamp DESC
""".strip()

            body = {
                "dbName": f"{effective_sandbox}:all",
                "sql": sql,
                "name": f"journey_history_{identity_id[:12]}",
            }
            query = aep_post("/data/foundation/query/queries", body, sandbox=sandbox or None)
            query_id = query.get("id", "")

            # Poll up to ~15 s for results
            for _ in range(5):
                time.sleep(3)
                status = aep_get(
                    f"/data/foundation/query/queries/{query_id}",
                    sandbox=sandbox or None,
                )
                state = status.get("state", "")
                if state == "SUCCESS":
                    return {
                        "query_id": query_id,
                        "state": state,
                        "dataset": jse_name,
                        "rowCount": status.get("rowCount", 0),
                        "data": status.get("data") or status.get("result"),
                    }
                if state in ("FAILED", "CANCELLED"):
                    return {
                        "query_id": query_id,
                        "state": state,
                        "errors": status.get("errors"),
                    }

            return {
                "query_id": query_id,
                "state": "PENDING",
                "message": "Query submitted. Use get_query to check status.",
                "dataset": jse_name,
            }

        except Exception as exc:
            return {"error": str(exc)}
