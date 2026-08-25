# Generate Test Cases

Generates a structured test case list for a feature, module, interface, workflow, or implementation. Produces a table with functional and technical test cases, flags each as AI-automatable or manual, and scopes to S and M complexity tasks.

## Usage

```
/generate-test-cases <work-item-id or requirement-reference>
/generate-test-cases <description of what was built>
/generate-test-cases #12345 checkout flow with responsive layout and error states
```

## Execution Steps

### 1. Project Awareness + Gather Context

- Read `<codebase_stack>` from CLAUDE.md — determine project architecture, test framework (pytest), and target environments
- Adapt test categories below based on which AEP pipeline stage is being tested:
  - Stage 0 (data-analyst): CSV profiling, quality scoring, ERD generation tests
  - Stages 1-2 (schema-processor): schema composition, field type mapping, deployment tests
  - Stage 3 (dataset-creator): duplicate check, parquet format, manifest update tests
  - Stage 4 (identity-inspector): descriptor API format, namespace creation tests
  - Stage 5 (profile-operator): three-flag verification, PATCH-not-PUT, tag merge tests
  - Stage 6 (data-ingestion): CSV-to-XDM transform, identityMap format, timestamp conversion, batch upload tests
  - Stage 7 (data-validator): record count comparison, identity resolution, field-level comparison tests
  - Stage 8 (qa-master): all 13 check patterns, remediation logic tests

If a supported work item or requirements reference is provided → invoke the relevant context skill to fetch title, description, and acceptance criteria.

If a description is provided → use it directly as the implementation context.

If both are provided → use the story context as the primary source and the description as supplementary detail.

### 2. Classify Complexity

Based on the implementation scope, assign S or M complexity:
- **S** — single module, endpoint, screen, or file type with no external integrations
- **M** — multiple file types, a new feature surface, or one external integration

If the implementation appears L complexity (cross-cutting, new architectural pattern, multi-environment), warn the user:
> "This appears to be an L-complexity task. Test case generation is scoped to S and M. Proceeding with what is determinable from the provided context."

### 3. Generate Test Cases

Produce a test case table with the following columns:

| # | Category | Test Case | Steps | Expected Result | Type | Execution |
|---|---|---|---|---|---|---|
| 1 | Functional | ... | ... | ... | Positive/Negative/Edge | AI / Manual |

**Categories to cover:**

**Functional:**
- Feature renders or responds correctly with valid data
- Feature renders or responds correctly with missing/empty data (null, empty strings)
- All configured or managed fields appear correctly in the runtime experience
- CTA links/buttons work as expected
- Conditional visibility rules work (show/hide based on dialog values)
- Responsive behavior at mobile (375px), tablet (768px), desktop (1440px)
- RTL layout renders correctly (if applicable)
- Dark theme / variant renders correctly (if applicable)

**Authoring / Content Management** (only when the product has an authoring or admin UI):
- Item can be created through the intended management flow
- Editable fields save and persist correctly
- Required field validation shows error on empty submit
- Preview or draft output matches the published or runtime output

**Accessibility:**
- Accessibility scan passes with no critical/serious violations
- All interactive elements are keyboard reachable
- Focus indicators are visible
- Color contrast meets 4.5:1 for text, 3:1 for large text
- Images have meaningful alt text

**Performance:**
- Performance score meets project threshold (from `<code_standards>`)
- Core web vitals within acceptable range
- Feature loads without layout shift or unexpected runtime jitter

**Security:**
- No XSS in rendered output
- No inline scripts or handlers in HTML output
- CSP compatible

**Execution column rules:**
- **AI** — can be automated as an end-to-end test or accessibility scan (deterministic, no visual judgment required)
- **Manual** — requires visual inspection, business judgment, or authoring interaction

### 4. Output

Present the test case table. After the table:

```
Test Cases: {total count}
AI-Automatable: {count} — can be automated as end-to-end tests or unit tests
Manual: {count} — require human execution

Test environment:
- Management UI / Admin: {management URL from <codebase_stack> or localhost} (content-management validation, if applicable)
- Runtime / App: {runtime URL from <codebase_stack> or localhost} (rendering and behavior validation)
```

Suggest next step:
```
To validate the implementation against these test cases: /validate-implementation
```

Context: $ARGUMENTS
