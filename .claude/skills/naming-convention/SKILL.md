---
name: naming-convention
description: APEX AEP artifact naming convention rules for Schemas (Mixins, Classes, Global Attributes), Identity Namespaces, Datasets, Segments, Journeys, Sources/Data Ingestion Workflows, and Destinations. Load this skill before naming or validating any AEP artifact. Source: Adobe CDP Artifacts Naming Conventions v1.0.
---

# APEX AEP Artifacts Naming Conventions

**Version:** 1.0  
**Source:** Adobe CDP Artifacts Naming Conventions (APEX Governance)

Load this skill when:

- Proposing names for any AEP artifact (schema, dataset, segment, journey, destination, namespace, source)
- Validating whether an existing artifact name complies with APEX conventions
- Generating naming suggestions prior to handing off to `schema-processor`, `dataset-creator`, `segment-builder`, or any pipeline agent

Do NOT load this skill for:

- XDM field type mapping (use `xdm-schema-design`)
- AEP API authentication (use `aep-fundamentals`)
- Data quality scoring (use `data-quality-scoring`)

---

## Why Naming Conventions Matter

A consistent naming convention enables:

- Improved discoverability and management across teams and sandboxes
- Ease of reporting and auditing (AEP, Adobe Target, Adobe Analytics)
- Enhanced collaboration between data engineers, marketers, and analysts
- Reduced errors and misinterpretation of data elements and audience segments
- Streamlined governance and access control

---

## Global Rules (Apply to ALL Artifacts)

| Rule | Requirement |
|---|---|
| **Prefix** | ALWAYS ask the user — never assume a default. May be project-level (`APEX`, `ACME`), BU-specific (`RETAIL`, `LOYALTY`, `B2B`), or geographic (`US`, `EU`, `APAC`, `UK`) |
| **Casing — Classes & Mixins** | PascalCase (e.g., `[Prefix] Master Profile Class`) |
| **Casing — Schema Attributes** | camelCase (e.g., `apex.customerID`) |
| **Casing — Segments & Journeys** | Sentence case with delimiters (pipe `|` or dash `-`) |
| **Special characters** | Avoid in class/mixin names. Use `|` or `-` as delimiters in segments/journeys only |
| **Reserved words** | NEVER use SQL or programming language keywords as token values or attribute names (see Reserved Words list below) |
| **Descriptions** | Document EVERY artifact with a clear description in the AEP UI |
| **Version suffix** | Use `v1`, `v2`, etc. for iterative builds (segments, journeys) |

---

## Reserved Words (Prohibited in All Artifact Names)

AEP artifact names and schema field names must NOT use SQL or programming language reserved keywords. These words cause failures in AEP Query Service (PostgreSQL-based), schema parsing, and downstream API integrations.

**Prohibited SQL keywords:**

`SELECT` `FROM` `WHERE` `JOIN` `GROUP` `ORDER` `HAVING` `INSERT` `UPDATE` `DELETE` `DROP` `CREATE` `TABLE` `INDEX` `VIEW` `SCHEMA` `DATABASE` `NULL` `TRUE` `FALSE` `AND` `OR` `NOT` `IN` `ON` `AS` `BY` `DISTINCT` `UNION` `ALL` `ANY` `EXISTS` `BETWEEN` `LIKE` `IS` `SET` `INTO` `WITH` `VALUES` `DEFAULT` `KEY` `PRIMARY` `FOREIGN` `REFERENCES` `CONSTRAINT` `UNIQUE` `ALTER` `TRUNCATE` `MERGE` `CASE` `WHEN` `THEN` `ELSE` `END` `LIMIT` `OFFSET` `OVER` `PARTITION` `COUNT` `SUM` `AVG` `MIN` `MAX` `RANK` `ROW`

**Prohibited programming keywords:**

`if` `else` `for` `while` `return` `class` `import` `export` `null` `true` `false` `var` `let` `const` `function` `void` `new` `this` `try` `catch` `throw` `switch` `break` `continue` `do` `typeof` `delete` `async` `await` `static` `public` `private` `protected` `abstract` `interface` `extends` `implements`

**Why this matters:** AEP Query Service is built on PostgreSQL. Field names and artifact identifiers that match reserved words must be quoted at query time, which breaks ad-hoc queries, segmentation PQL, and computed attributes. Avoiding them entirely eliminates this class of errors.

**If a natural name collides with a reserved word**, append a business-context suffix:

- `order` → `purchaseOrder` or `orderRecord`
- `group` → `customerGroup` or `loyaltyGroup`
- `select` → `productSelection`
- `value` → `monetaryValue` or `pointValue`

---

## 1. Data Schemas — Mixins (Field Groups)

**Pattern:** `[Prefix] [Subject] [Type] [Extension]`

| Token | Description | Examples |
|---|---|---|
| `Prefix` | User-confirmed prefix — project, BU, or geographic | `APEX`, `RETAIL`, `US` |
| `Subject` | Clear descriptor of the data covered | `Customer`, `Order`, `Clickstream`, `Digital Interaction` |
| `Type` | Category of mixin | `Profile`, `Event`, `Lookup` |
| `Extension` | **Optional** — used when extending a standard XDM mixin | `Extension`, `Info` |

**Valid examples — varied prefixes:**

| Prefix Type | Example Name |
|---|---|
| Project-level | `APEX Customer Profile Extension` |
| BU-specific | `RETAIL Digital Interaction Info` |
| Geographic | `US Loyalty Profile Extension` |
| BU-specific, no Extension (optional) | `LOYALTY Order Event` |

**Rules:**

- MUST start with the user-confirmed prefix
- Always PascalCase — no special characters
- `Extension` token is optional — omit if not extending a standard XDM field group
- Subject must clearly identify what data the mixin covers

---

## 2. Data Schemas — Classes

**Pattern:** `[Prefix] [Context] [Class Type]`

| Token | Description | Examples |
|---|---|---|
| `Prefix` | User-confirmed prefix — project, BU, or geographic | `APEX`, `RETAIL`, `EU` |
| `Context` | Broad domain of the class | `Master`, `Campaign`, `Loyalty`, `Web` |
| `Class Type` | XDM base type | `Profile Class`, `ExperienceEvent Class` |

**Valid examples — varied prefixes:**

| Prefix Type | Example Name |
|---|---|
| Project-level | `APEX Master Profile Class` |
| BU-specific | `RETAIL Web Interaction Event Class` |
| Geographic | `EU Loyalty Profile Class` |

**Rules:**

- MUST start with the user-confirmed prefix
- PascalCase throughout — no special characters
- `Class Type` must reference the XDM base type explicitly

---

## 3. Data Schemas — Global Attributes (Schema Fields)

**Pattern (inside Field Groups):** `[tenantId].[attributeName]`

| Token | Description | Examples |
|---|---|---|
| `tenantId` | Lowercase project/org identifier | `apex` |
| `attributeName` | camelCase field name | `customerID`, `loyaltyPointsBalance`, `lastPurchaseDate` |

**Valid examples:**

- `apex.customerID`
- `apex.loyaltyPointsBalance`
- `apex.lastPurchaseDate`
- `apex.emailOptInStatus`

**Rules:**

- `tenantId` is always lowercase
- `attributeName` is always camelCase
- Must be unique across the schema — no conflicts with other fields
- Every attribute MUST have a description in the AEP UI

---

## 4. Identity Namespaces

**Pattern:** `[ID Type]`

| Token | Description | Examples |
|---|---|---|
| `ID Type` | Source or type of identifier — no prefix required | `EID`, `CRM_ID`, `Loyalty_ID`, `Email_ID` |

**Valid examples:**

- `EID`
- `CRM_ID`
- `Loyalty_ID`
- `Email_ID`

**Rules:**

- No prefix — identity namespace names consist of the ID Type alone
- `ID Type` must clearly reference the source system or identifier type
- Must be correctly categorized: Cross-device vs. Device-only
- Use underscores within `ID Type` if it is a compound identifier

**B2B reserved namespaces (do NOT rename — applies ONLY to B2B use cases):** When the project is
genuinely B2B, the B2B system namespaces use Adobe's fixed codes and idTypes and are EXEMPT from this
APEX naming pattern — do not propose APEX-style renames for them: `b2b_account` (`B2B_ACCOUNT`),
`b2b_person` (`CROSS_DEVICE`), `b2b_account_person_relation` (`B2B_ACCOUNT_PERSON`), `b2b_opportunity`
(`B2B_OPPORTUNITY`), etc. The idType is fixed by entity type. For B2C / standard projects this note does
not apply — name custom namespaces per the pattern above. See `xdm-schema-design` → "B2B Edition Schema
Architecture" for when B2B applies.

---

## 5. Datasets

**Pattern:** `[Prefix] [Source System] [Data Type] [Frequency]`

| Token | Description | Examples |
|---|---|---|
| `Prefix` | User-confirmed prefix — project, BU, or geographic | `APEX`, `RETAIL`, `EU`, `APAC` |
| `Source System` | Origin of the data | `SFDC`, `SAP`, `S3`, `AdobeAnalytics`, `Snowflake` |
| `Data Type` | What the data represents | `Transactions`, `Leads`, `PageViews`, `Contacts`, `WebEvents` |
| `Frequency` | Ingestion cadence | `Batch`, `Streaming`, `Daily`, `Hourly`, `Real-time` |

**Valid examples — varied prefixes:**

| Prefix Type | Example Name |
|---|---|
| Project-level | `APEX SFDC Contacts Daily` |
| BU-specific | `RETAIL AdobeAnalytics WebEvents Hourly` |
| Geographic | `EU SAP Transactions Batch` |
| Geographic | `APAC S3 PageViews Streaming` |

**Rules:**

- All four tokens are required — no omissions
- `Source System` abbreviation must be consistent across all datasets from the same source
- `Frequency` reflects the actual ingestion cadence — update if cadence changes

---

## 6. Segments (Audiences)

**Pattern:** `[Country/Region] | [Business Unit] | [Audience Name] | [Version]`

| Token | Description | Examples |
|---|---|---|
| `Country/Region` | Geographic scope | `US`, `UK`, `GLOBAL`, `APAC` |
| `Business Unit` | Line of business | `RETAIL`, `LOYALTY`, `B2B`, `DIGITAL` |
| `Audience Name` | Descriptive label reflecting the logic | `High Spenders Past 30 Days`, `Dormant Members` |
| `Version` | Iteration number | `v1`, `v2` |

**Valid examples:**

- `US | RETAIL | High Spenders Past 30 Days | v1`
- `UK | LOYALTY | Dormant Members | v2`
- `GLOBAL | B2B | Enterprise Accounts Active Q1 | v1`
- `APAC | DIGITAL | Cart Abandoners Last 7 Days | v1`

**Rules:**

- Use pipe `|` (preferred) or dash `-` as delimiter — be consistent within a project
- Audience Name must be descriptive of the logic used (not a code or internal ID)
- Version suffix is mandatory for iterative builds
- All tokens must be present

---

## 7. Journeys

**Pattern:** `[Prefix] [Campaign Name] [Trigger Type] [Status]`

| Token | Description | Examples |
|---|---|---|
| `Prefix` | User-confirmed prefix — project, BU, or geographic | `APEX`, `LOYALTY`, `UK` |
| `Campaign Name` | Marketing campaign or use case | `Welcome Series`, `Re-engagement`, `Loyalty Upgrade` |
| `Trigger Type` | How the journey starts | `API`, `Segment-Based`, `Event` |
| `Status` | **Optional** lifecycle indicator | `Draft`, `Live`, `Archived` |

**Valid examples — varied prefixes:**

| Prefix Type | Example Name |
|---|---|
| Project-level | `APEX Welcome Series API v1` |
| BU-specific | `LOYALTY Re-engagement Segment-Based Active` |
| Geographic | `UK Abandoned Cart Event Draft` |
| BU-specific, no Status (optional) | `RETAIL Win-Back Segment-Based` |

**Rules:**

- MUST start with the user-confirmed prefix
- `Trigger Type` must accurately describe the entry condition
- `Status` is optional but recommended for governance visibility

---

## 8. Sources & Data Ingestion Workflows

**Pattern:** `[Source] [Object] [Ingestion Type]`

| Token | Description | Examples |
|---|---|---|
| `Source` | Origin system | `SFDC`, `SAP`, `S3`, `Snowflake`, `AdobeAnalytics` |
| `Object` | Data entity being ingested | `Contacts`, `Transactions`, `WebEvents`, `PageViews` |
| `Ingestion Type` | Mode of ingestion | `Batch`, `Streaming`, `Daily`, `Hourly`, `Real-time` |

**Valid examples — varied sources:**

- `SFDC Contacts Batch`
- `S3 WebEvents Streaming`
- `SAP Transactions Daily`
- `Snowflake PageViews Real-time`
- `AdobeAnalytics ClickEvents Hourly`

**Rules:**

- No directional words — do NOT use `to` or `from` in the name
- Object must clearly identify the entity being ingested
- `Ingestion Type` MUST be one of: `Batch`, `Streaming`, `Daily`, `Hourly`, `Real-time`

---

## 9. Destinations

**Pattern:** `[Platform] [Target Audience] [Export Type]`

| Token | Description | Examples |
|---|---|---|
| `Platform` | Target platform receiving the data | `Facebook`, `Adobe Target`, `Google Ads`, `LinkedIn` |
| `Target Audience` | Segment or audience being exported | `Custom Audience High Spenders`, `Web Personalization` |
| `Export Type` | How data is exported | `Daily`, `Hourly`, `Real-time` |

**Valid examples:**

- `Facebook Custom Audience High Spenders Daily`
- `Adobe Target Web Personalization Real-time`
- `Google Ads Loyalty Members Hourly`
- `LinkedIn Enterprise Contacts Daily`

**Rules:**

- Platform name must use the official platform name (e.g., `Facebook` not `FB`)
- Target Audience must match or reference an existing segment name where possible
- `Export Type` must reflect actual cadence

---

## Validation Checklist

Before confirming any artifact name, verify:

| # | Check | Pass Condition |
|---|---|---|
| 1 | Prefix present and confirmed | Starts with the user-confirmed prefix (project, BU, or geographic — never assumed) |
| 2 | Correct casing | PascalCase (classes/mixins), camelCase (attributes), Sentence case (segments/journeys) |
| 3 | All required tokens present | No missing tokens for the artifact type |
| 4 | No special characters | Unless pipe `|` for segments or dash `-` for journeys |
| 5 | No SQL or programming reserved keywords | None of the tokens match a word in the Reserved Words list |
| 6 | Source system abbreviation consistent | Same abbreviation used across all datasets from same source |
| 7 | Frequency/Export type accurate | Matches actual ingestion or export cadence |
| 8 | Description added | Every artifact has a description in AEP UI |
| 9 | Version suffix present | Required for segments and journeys during iterative builds |

---

## Quick Reference Table

| Artifact | Pattern | Example (Project) | Example (BU) | Example (Geographic) |
|---|---|---|---|---|
| Mixin | `[Prefix] [Subject] [Type] [Extension*]` | `APEX Customer Profile Extension` | `RETAIL Digital Interaction Info` | `US Loyalty Profile Extension` |
| Class | `[Prefix] [Context] [Class Type]` | `APEX Master Profile Class` | `RETAIL Web Interaction Event Class` | `EU Loyalty Profile Class` |
| Attribute | `[tenantId].[camelCaseAttribute]` | `apex.customerID` | `apex.loyaltyPointsBalance` | `apex.lastPurchaseDate` |
| Identity Namespace | `[ID Type]` | `CRM_ID` | `Loyalty_ID` | `Email_ID` |
| Dataset | `[Prefix] [SourceSystem] [DataType] [Frequency]` | `APEX SFDC Contacts Daily` | `RETAIL AdobeAnalytics WebEvents Hourly` | `EU SAP Transactions Batch` |
| Segment | `[Region] \| [BU] \| [AudienceName] \| [Version]` | `US \| RETAIL \| High Spenders \| v1` | `UK \| LOYALTY \| Dormant Members \| v2` | `APAC \| DIGITAL \| Cart Abandoners \| v1` |
| Journey | `[Prefix] [CampaignName] [TriggerType] [Status*]` | `APEX Welcome Series API v1` | `LOYALTY Re-engagement Segment-Based Active` | `UK Abandoned Cart Event Draft` |
| Source Workflow | `[Source] [Object] [IngestType]` | `SFDC Contacts Batch` | `S3 WebEvents Streaming` | `SAP Transactions Daily` |
| Destination | `[Platform] [TargetAudience] [ExportType]` | `Facebook Custom Audience High Spenders Daily` | `Adobe Target Web Personalization Real-time` | `Google Ads Loyalty Members Hourly` |

*Optional token
