---
name: skill-review
description: Audit skill documentation with systematic review covering standards compliance, official docs verification, code examples accuracy, cross-file consistency, and version drift detection. Auto-fixes unambiguous issues with severity classification. Use when investigating skill issues, major package updates detected (e.g., v1.x to v2.x), skill not verified in over 90 days, before distribution or sharing, or troubleshooting outdated API patterns, contradictory examples, broken links, version drift.
---

# Skill Review

Systematic audit process for skill quality, accuracy, and standards compliance.

## When to Use

**Required:**
- Major package or API version updates affecting a skill
- User reports errors following a skill's instructions
- Before distributing or sharing a skill

**Recommended:**
- Skill last verified over 90 days ago
- After framework or platform breaking changes
- When adding new features to a skill
- Periodic maintenance

**On-demand:**
- Suspected issues or quality concerns
- Investigating user feedback
- Quality assurance before release

## Audit Process

### Phase 1: Pre-Review
- Locate the skill directory
- Check version and last-verified date (if present in metadata)
- Test discovery: does the skill trigger on relevant queries?

### Phase 2: Standards Compliance
Validate against the official skill specification:
- YAML frontmatter has `---` delimiters
- `name` field: kebab-case, no spaces, no capitals, max 64 characters
- `description` field: includes WHAT and WHEN, under 1024 characters, no angle brackets
- Only allowed frontmatter fields: `name`, `description`, `license`, `compatibility`, `allowed-tools`, `metadata`
- No README.md inside the skill folder (all docs in SKILL.md or references/)
- Directory structure follows convention (scripts/, references/, assets/)

### Phase 3: Official Docs Verification
For skills that reference external APIs, libraries, or platforms:
- Verify API patterns against current official documentation (use WebFetch)
- Check for deprecated methods, renamed imports, changed signatures
- Verify package versions against registry (npm, PyPI, Maven, etc.)
- Check GitHub/source repos for breaking changes or maintenance status

### Phase 4: Code Examples Audit
- Verify all imports exist in the referenced packages
- Verify API signatures match current documentation
- Check schema consistency across files (same names, same types)
- Test scripts if present (scripts/ directory)

### Phase 5: Cross-File Consistency
- Compare SKILL.md content against references/ files
- Verify bundled resources listed in SKILL.md actually exist
- Check for contradictory guidance between files

### Phase 6: Dependencies and Versions
- Check all referenced packages for currency
- Identify breaking changes between skill's version and current version
- Verify "Last Verified" date if present

### Phase 7: Issue Categorization

Classify each finding by severity:

| Severity | Meaning | Examples |
|----------|---------|----------|
| CRITICAL | Breaks functionality | Non-existent API imports, invalid config, missing dependencies |
| HIGH | Causes confusion | Contradictory examples, inconsistent patterns, outdated major versions |
| MEDIUM | Reduces quality | Stale minor versions (>90 days), missing doc sections, incomplete error handling |
| LOW | Polish issues | Typos, formatting, missing optional metadata |

### Phase 8: Fix Implementation

**Auto-fix** (unambiguous): correct import from docs, clear evidence, no architectural impact.

**Ask user** (judgment needed): multiple valid approaches, breaking changes, architectural choices.

After fixes:
- Update version in metadata if present
- Major bump (v1 to v2): API patterns change
- Minor bump (v1.0 to v1.1): new features, backward compatible
- Patch bump (v1.0.0 to v1.0.1): bug fixes only

### Phase 9: Post-Fix Verification
- Test skill discovery (triggers correctly)
- Verify no contradictions remain across files
- Confirm all bundled resources are accurate
- Validate YAML frontmatter

## Output Format

```
## Skill Review Report: {skill-name}

Date: {date}
Trigger: {why review was performed}

### Findings

CRITICAL ({N}):
- {file:location} -- {what is wrong} -- {evidence URL}

HIGH ({N}):
- {file:location} -- {what is wrong} -- {evidence URL}

MEDIUM ({N}):
- {file:location} -- {what is wrong}

LOW ({N}):
- {file:location} -- {what is wrong}

### Remediation
- Files modified: {list with changes}
- Files created: {list with purpose}
- Files deleted: {list with reason}
- Version bump: {none / patch / minor / major}

### Verification
- Discovery test: PASS / FAIL
- Consistency check: PASS / FAIL
- Frontmatter valid: PASS / FAIL

### Overall: PASS / WARN / FAIL
```

## Audit Report Template

For detailed audit documentation, use the template in `references/audit-report-template.md`.

## Common Issues Prevented

| Issue | Examples | Severity |
|-------|----------|----------|
| Fake APIs | Non-existent imports or adapters | CRITICAL |
| Stale methods | Changed API signatures | CRITICAL |
| Schema inconsistency | Different table/field names across files | HIGH |
| Outdated scripts | Deprecated patterns in scripts/ | HIGH |
| Version drift | Referenced packages over 90 days old | MEDIUM |
| Contradictory examples | Multiple conflicting patterns | HIGH |
| Broken links | 404 documentation URLs | HIGH |
| YAML errors | Invalid frontmatter | CRITICAL |
| Missing resources | Bundled resources listed but files do not exist | HIGH |
