---
name: journey-analyze-custom-action
description: >
  Diagnose errors and performance issues on AJO journey Custom Action nodes — webhook calls
  to external systems failing, timing out, or running slowly. Load when the user asks "why
  is the custom action node failing", "webhook errors in journey X", "custom action timing
  out", "custom action success rate", or "troubleshoot the API call step in this journey".
  Queries journey step events for custom action node outcomes via mcp__aep__run_query_sync.
---

# Journey Analyze Custom Action

## When to Load

- "why is the custom action node failing"
- "webhook errors in journey [name]"
- "custom action timing out"
- "custom action success rate / performance"
- "troubleshoot the API call step in this journey"

---

## Concept

A Custom Action node calls an external webhook/API mid-journey (e.g., inventory check, loyalty
system update, third-party enrichment) and waits for a response before continuing. Failures
here are external-system failures surfaced inside the journey, not AJO platform failures —
diagnosis needs both the AJO-side event log and the external endpoint's own behavior.

---

## API Approach

### Step 1: Identify the custom action node

```
mcp__aep__get_journey   — locate the Custom Action node, its configured endpoint URL,
                           timeout setting, and retry policy
```

### Step 2: Query custom action outcomes

```
mcp__aep__run_query_sync

SELECT
  status,
  httpStatusCode,
  errorMessage,
  COUNT(*) AS occurrences,
  AVG(responseTimeMs) AS avg_response_ms,
  MAX(responseTimeMs) AS max_response_ms
FROM journey_step_events
WHERE journeyId = '<journey_id>'
  AND nodeId = '<custom_action_node_id>'
  AND timestamp >= now() - interval '<lookback>' day
GROUP BY status, httpStatusCode, errorMessage
ORDER BY occurrences DESC
```

Adjust dataset/column names to the org's actual journey step events schema — confirm via
`explore-datasets` or `analyze-data-fields` if these exact names aren't deployed.

### Step 3: Classify the failure pattern

| Pattern | Likely Cause |
|---|---|
| High rate of `httpStatusCode = 401/403` | Credential/API key expired on the external endpoint |
| High rate of `httpStatusCode = 5xx` | External system outage or overload |
| `status = TIMEOUT`, response times near the configured timeout | Endpoint too slow for the configured timeout window |
| `status = TIMEOUT` with fast avg but occasional max spikes | Intermittent external latency, not a config problem |
| Errors correlated with volume spikes | External system rate-limiting under journey load |
| Consistent single error message across all failures | Payload/schema mismatch — check the request body being sent |

### Step 4: Check retry and fallback configuration

```
mcp__aep__get_journey   — confirm retry policy and whether a fallback/error path exists
```

A custom action with no error branch routes failed profiles nowhere identifiable — flag
this as a design gap regardless of the current failure rate.

---

## Output Format

```
Custom Action Analysis: "Inventory Check" node — Abandoned Cart journey (last 7 days)

  Outcome                          Count    Avg Response    Max Response
  ────────────────────────────────────────────────────────────────────────
  SUCCESS (200)                    8,420    340ms           1.2s
  TIMEOUT                          612      —               5.0s (= configured timeout)
  ERROR (503)                      140      280ms           400ms

Fallout rate: 8.2% (752 of 9,172 calls did not succeed)

Diagnosis:
  TIMEOUT cases cluster at exactly the 5.0s configured timeout, not gradually — endpoint
  is either consistently slow under load or the timeout is set too aggressively for a
  cold-start-prone external service.
  503 errors are a separate, smaller pattern — external system returning "service
  unavailable" intermittently, not journey-side.

Recommendation:
  1. Confirm with the external system owner whether 5s is realistic under peak load
  2. Check whether an error/fallback branch exists for TIMEOUT and 503 outcomes —
     if not, 8.2% of profiles are silently stuck or exiting undocumented
  3. Consider raising timeout to 8-10s if endpoint SLA supports it, or add a retry
     step before falling back
```

---

## Notes

- This skill diagnoses the AJO-side symptom (what the journey observed); it cannot inspect
  the external system's own logs — recommend the user's platform team check server-side
  logs for the same time window when the pattern points to an external cause
- Distinguish TIMEOUT (AJO gave up waiting) from ERROR (external system responded with a
  failure code) — the fix path is different for each
- If failure rate is low (<1%) and errors are non-clustered, this may be normal background
  noise rather than an issue worth escalating — say so rather than over-flagging
