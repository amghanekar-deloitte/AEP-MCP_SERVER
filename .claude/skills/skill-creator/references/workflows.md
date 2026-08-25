# Workflow Patterns

Use these patterns when designing skill workflows. Choose the pattern that best fits your use case.

## Pattern 1: Sequential Workflow Orchestration

Use when users need multi-step processes in a specific order.

```markdown
# Workflow: Onboard New Customer

### Step 1: Create Account
Call tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

### Step 4: Send Welcome Email
Call tool: `send_email`
Template: welcome_email_template
```

Key techniques:
- Explicit step ordering
- Dependencies between steps
- Validation at each stage
- Rollback instructions for failures

## Pattern 2: Multi-Tool Coordination

Use when workflows span multiple services or MCP servers.

```markdown
### Phase 1: Design Export (Figma MCP)
1. Export design assets
2. Generate design specifications
3. Create asset manifest

### Phase 2: Asset Storage (Drive MCP)
1. Create project folder
2. Upload all assets
3. Generate shareable links

### Phase 3: Task Creation (Linear MCP)
1. Create development tasks
2. Attach asset links to tasks
3. Assign to team

### Phase 4: Notification (Slack MCP)
1. Post handoff summary
2. Include asset links and task references
```

Key techniques:
- Clear phase separation
- Data passing between tools/services
- Validation before moving to next phase
- Centralized error handling

## Pattern 3: Iterative Refinement

Use when output quality improves with iteration.

```markdown
### Initial Draft
1. Fetch data
2. Generate first draft
3. Save to temporary file

### Quality Check
1. Run validation script: `scripts/check_report.py`
2. Identify issues:
   - Missing sections
   - Inconsistent formatting
   - Data validation errors

### Refinement Loop
1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met

### Finalization
1. Apply final formatting
2. Generate summary
3. Save final version
```

Key techniques:
- Explicit quality criteria
- Iterative improvement
- Validation scripts
- Know when to stop iterating

## Pattern 4: Context-Aware Tool Selection

Use when the same outcome requires different tools depending on context.

```markdown
### Decision Tree
1. Check file type and size
2. Determine best storage location:
   - Large files (>10MB): Use cloud storage
   - Collaborative docs: Use document platform
   - Code files: Use version control
   - Temporary files: Use local storage

### Execute Storage
Based on decision:
- Call appropriate tool
- Apply service-specific metadata
- Generate access link

### Provide Context to User
Explain why that storage was chosen
```

Key techniques:
- Clear decision criteria
- Fallback options
- Transparency about choices

## Pattern 5: Domain-Specific Intelligence

Use when the skill adds specialized knowledge beyond tool access.

```markdown
### Before Processing (Compliance Check)
1. Fetch transaction details
2. Apply compliance rules:
   - Check sanctions lists
   - Verify jurisdiction allowances
   - Assess risk level
3. Document compliance decision

### Processing
IF compliance passed:
  - Process transaction
  - Apply appropriate checks
ELSE:
  - Flag for review
  - Create compliance case

### Audit Trail
- Log all compliance checks
- Record processing decisions
- Generate audit report
```

Key techniques:
- Domain expertise embedded in logic
- Compliance before action
- Comprehensive documentation
- Clear governance

## Conditional Workflows

For tasks with branching logic, guide Claude through decision points:

```markdown
1. Determine the modification type:
   **Creating new content?** -> Follow "Creation workflow" below
   **Editing existing content?** -> Follow "Editing workflow" below

2. Creation workflow: [steps]
3. Editing workflow: [steps]
```

## Choosing Your Approach: Problem-First vs. Tool-First

- **Problem-first**: "I need to set up a project workspace" — the skill orchestrates the right tool calls in the right sequence. Users describe outcomes; the skill handles the tools.
- **Tool-first**: "I have an MCP server connected" — the skill teaches Claude the optimal workflows and best practices. Users have access; the skill provides expertise.

Most skills lean one direction. Knowing which framing fits your use case helps you choose the right pattern above.
