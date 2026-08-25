---
name: ajo-campaign
description: AJO campaign lifecycle patterns — campaign types (scheduled and API-triggered), creation API payload formats, surface configuration, audience targeting, publish flow, trigger patterns, Content Decisioning campaigns, campaign duplication, and known API limitations. Load when creating or managing AJO campaigns.
---

# AJO Campaign Management

Load this skill when:

- Creating AJO campaigns via API
- Publishing or triggering campaigns
- Reading campaign variant HTML
- Understanding campaign lifecycle states
- Managing Content Decisioning campaigns

Do NOT load this skill for:

- Journey design (use ajo-journey skill)
- Email template content creation (use ajo-email-template skill)
- Segment creation (use segment-management skill)

---

## Campaign Types

| Type                              | Trigger             | Use Case                                              |
| --------------------------------- | ------------------- | ----------------------------------------------------- |
| **Scheduled — Marketing**         | Scheduled date/time | Newsletter, promotional, lifecycle outreach           |
| **Scheduled — Transactional**     | Scheduled date/time | Transactional alerts at scheduled times               |
| **API-Triggered — Marketing**     | REST API call       | Event-driven marketing (loyalty tier change, welcome) |
| **API-Triggered — Transactional** | REST API call       | Real-time transactional (order confirm, alert)        |

---

## Campaign Lifecycle States

```
DRAFT → PROCESSING → LIVE → COMPLETED | STOPPED
```

- **DRAFT**: Created, not yet published. Email content configured in UI.
- **PROCESSING**: Publish requested, AJO validating and scheduling.
- **LIVE**: Campaign is active. Scheduled campaigns are executing/scheduled. API-triggered campaigns await trigger calls.
- **COMPLETED**: Campaign run completed (for scheduled with end date).
- **STOPPED**: Manually stopped.

---

## Campaign Base URL

```
{AEP_BASE_URL}/journey/campaigns/service/campaigns
```

---

## Create Scheduled Campaign

```json
POST {AEP_BASE_URL}/journey/campaigns/service/campaigns

{
  "name": "Campaign Name — clear, unique identifier",
  "description": "Campaign description",
  "campaignType": "Scheduled",
  "category": "Marketing",
  "audience": {
    "audienceId": "AEP_SEGMENT_UUID",
    "namespace": "Email"
  },
  "schedule": {
    "startTime": "2024-03-15T09:00:00Z",
    "endTime": "2024-03-15T23:59:59Z"
  },
  "packages": [{
    "messages": [{
      "channel": "email",
      "channelRef": "SURFACE_CHANNEL_REF_ID",
      "messageAttributes": {
        "subject": "Email subject line here"
      }
    }]
  }]
}
```

Note: `channelRef` comes from GET /surfaces response. Look for the `channelRef` field in the surface object.

---

## Create API-Triggered Campaign

```json
POST {AEP_BASE_URL}/journey/campaigns/service/campaigns

{
  "name": "Campaign Name",
  "description": "API-triggered transactional campaign",
  "campaignType": "ApiTriggered",
  "category": "Transactional",
  "audience": {
    "namespace": "Email"
  },
  "packages": [{
    "messages": [{
      "channel": "email",
      "channelRef": "SURFACE_CHANNEL_REF_ID",
      "messageAttributes": {
        "subject": "Your transaction subject"
      }
    }]
  }]
}
```

---

## List Surfaces (Get channelRef)

```bash
GET {AEP_BASE_URL}/journey/campaigns/service/surfaces?channel=email&count=50
```

Response includes `channelRef` per surface — use this in campaign creation payload.

---

## Publish Campaign

```bash
PUT {AEP_BASE_URL}/journey/campaigns/service/campaigns/{campaignId}/publish
```

Poll for status change every 10 seconds:

```bash
while true; do
  STATUS=$(curl -s "${AEP_BASE_URL}/journey/campaigns/service/campaigns/${CAMPAIGN_ID}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "x-api-key: ${AEP_CLIENT_ID}" \
    -H "x-gw-ims-org-id: ${AEP_ORG_ID}" \
    -H "x-sandbox-name: ${AEP_SANDBOX_NAME}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "Status: ${STATUS}"
  [ "${STATUS}" = "LIVE" ] && break
  [ "${STATUS}" = "FAILED" ] && { echo "Campaign failed to publish"; exit 1; }
  sleep 10
done
```

---

## Trigger API-Triggered Campaign

### Audience Trigger (batch of profiles from segment)

```json
POST {AEP_BASE_URL}/ajo/im/executions/audience

{
  "campaignId": "CAMPAIGN_UUID",
  "audience": {
    "id": "SEGMENT_UUID"
  },
  "additionalData": {
    "customKey": "customValue",
    "offerCode": "PROMO2024"
  }
}
```

Access in email: `{%= additionalData.customKey %}`

### Unitary Trigger (single profile)

```json
POST {AEP_BASE_URL}/ajo/im/executions/unitary

{
  "campaignId": "CAMPAIGN_UUID",
  "recipients": [
    {
      "namespace": {
        "code": "Email"
      },
      "userId": "customer@example.com",
      "context": {
        "orderNumber": "ORD-12345",
        "orderTotal": "250.00"
      }
    }
  ]
}
```

Access in email: `{%= context.orderNumber %}`

---

## Campaign Operations Reference

| Operation          | Method | Path                                                             |
| ------------------ | ------ | ---------------------------------------------------------------- |
| List campaigns     | GET    | `/campaigns?count=50&property=status%3D{LIVE\|DRAFT\|SCHEDULED}` |
| Get campaign by ID | GET    | `/campaigns/{campaignId}`                                        |
| Duplicate campaign | POST   | `/campaigns/{campaignId}/duplicate`                              |
| Delete campaign    | DELETE | `/campaigns/{campaignId}` (DRAFT only)                           |
| Get variant IDs    | GET    | `/campaigns/{campaignId}/messages/{messageId}/variants`          |
| Read variant HTML  | GET    | `/campaigns/{messageId}/email/variants/{variantId}`              |

---

## Content Decisioning Campaign

For offer decisioning with multiple content variants:

```json
POST {AEP_BASE_URL}/journey/campaigns/service/campaigns

{
  "name": "CD Campaign with Decision Policy",
  "campaignType": "Scheduled",
  "category": "Marketing",
  "audience": {"audienceId": "SEGMENT_UUID", "namespace": "Email"},
  "packages": [{
    "messages": [
      {
        "channel": "email",
        "channelRef": "SURFACE_REF",
        "messageAttributes": {"subject": "Your personalized offer"},
        "decisionPolicies": [{"id": "DECISION_POLICY_ID"}]
      }
    ]
  }]
}
```

Retrieve decision policy IDs from AJO Decision Management → Decisions.

---

## Known API Limitations

| Feature                            | Status                           | Workaround                                                                            |
| ---------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------- |
| Write/edit email HTML body via API | NOT SUPPORTED (404)              | Must use AJO Email Designer in UI                                                     |
| Create journeys via API            | NOT SUPPORTED                    | Must use AJO Journey UI                                                               |
| Create decision policies via API   | NOT SUPPORTED for standard setup | Use AJO Decision Management UI                                                        |
| Create surfaces via API            | NOT SUPPORTED                    | Use Administration → Channels → Channel surfaces in UI                                |
| OLAC 403 error                     | Permissions issue                | AEP → Permissions → Roles → Add View/Manage/Publish Campaigns → Assign API credential |

---

## Pre-Creation Checklist

Before creating any campaign:

- [ ] Surface exists and is ACTIVE (GET /surfaces)
- [ ] Segment exists and has been evaluated (GET /segment/definitions)
- [ ] Email content template is designed and published in AJO UI
- [ ] Campaign schedule confirmed (start/end datetime in ISO 8601 UTC)
- [ ] Campaign name follows naming convention: `{ProjectName} - {UseCase} - {Date}`

---

## Anti-Patterns

- MUST NOT create campaign before verifying surface exists
- MUST NOT hardcode segment IDs or surface refs — always look up first
- MUST NOT publish campaign before email content is configured in AJO UI Email Designer
- MUST NOT use API trigger on a Scheduled campaign (use campaign type that matches trigger method)
- MUST NOT trigger campaign multiple times without checking current status first

## Security

- Require explicit user confirmation before publishing or activating any campaign — publication triggers immediate audience delivery and cannot be undone without a manual stop.
- Require explicit user confirmation before sending an API trigger — repeated triggers deliver duplicate messages to profiles.
- Present the proposed campaign name, audience, and surface to the user and wait for approval before calling the publish or trigger endpoints.
- Treat campaign publication as a one-way door: confirm once, then execute — do not auto-retry on transient errors without re-confirming.
