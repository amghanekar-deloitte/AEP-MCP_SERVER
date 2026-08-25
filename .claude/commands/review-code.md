# Review Code

Review code for correctness, security, and AEP pipeline compliance — auto-detects scope.

## When to Use
- Before committing pipeline code (reviews uncommitted changes)
- After a pipeline stage is implemented (reviews files changed on the current branch)
- For pull request review

## Workflow
1. Detect scope automatically:
   - If specific files are provided in `$ARGUMENTS` → scope to those files only
   - Else if uncommitted changes exist (`git status`) → scope to changed files only
   - Else if reviewing completed feature work → compute scope from the current branch diff
   - If none of the above apply → ask the user what to review
2. Review the code directly — scan for critical/high severity issues first:
   - **Security**: hardcoded credentials, AEP URLs, org IDs, sandbox names
   - **AEP compliance**: correct API endpoints, proper auth via `.env`, parquet format for datasets, no auto-profile-enable
   - **Data correctness**: identityMap format includes `authenticatedState`, ISO 8601 timestamps, URL-encoded schema IDs
   - **Reliability**: error handling for AEP API failures, retry logic, batch status polling
3. Report findings with file path, line number, severity, and recommended fix
4. Summary: what needs to change, what needs redesign, whether re-review is needed

Context: $ARGUMENTS
