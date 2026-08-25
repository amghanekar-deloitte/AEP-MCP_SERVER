# Generate Documentation

Create or update documentation for the AEP pipeline or its components.

## When to Use
- Documenting a completed pipeline stage
- Writing a runbook for operating the AEP pipeline
- Creating architecture decision records (ADRs) for schema or ingestion decisions
- Updating README files for pipeline modules

## Usage
```
/generate-docs <description of what to document>
/generate-docs runbook for the ingestion stage
/generate-docs ADR for the identity namespace strategy
/generate-docs README for the schema-processor module
```

## Workflow
1. Determine documentation type from the request:
   - **Runbook**: operational steps for running a pipeline stage, troubleshooting, recovery
   - **ADR**: architecture decision with context, options considered, and rationale
   - **README**: module overview, inputs, outputs, usage
   - **Reference**: API patterns, field mappings, configuration reference
2. Search the codebase for relevant code, configs, and existing docs to base the documentation on
3. Propose structure and wait for approval on new ADRs or high-impact documentation
4. Create or update documentation in the appropriate location:
   - Runbooks: `docs/runbooks/`
   - ADRs: `docs/adr/`
   - READMEs: alongside the relevant module
5. Validate markdown syntax and link integrity

Context: $ARGUMENTS
