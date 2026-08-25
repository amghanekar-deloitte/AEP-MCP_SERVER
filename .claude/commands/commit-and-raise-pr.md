---
description: Intelligent commit workflow with optional rebase and PR prep, optimized for low-noise terminal output.
argument-hint: optional notes about intent, ticket, or target branch
allowed-tools: Read, Grep, Glob, Write
---

# Commit Code

One intelligent workflow to rebase (if needed), standardize commit messages, and prepare PR details with low-noise output.

## When to Use
- You want a single guided flow for rebase, commit, and PR preparation
- You want standardized commit messaging following project conventions
- You want the command to ask for missing info and proceed sequentially

## Workflow

**0. Gather context and intent:**
- Identify current branch, repo status, and staged changes.
- If the user did not provide a target branch, ask for it.
- If a rebase is requested or needed, confirm source and target branches.

**1. Validate working tree (low-noise):**
- `git status -sb | head -n 40`
- `git branch --show-current`
- `git log -1 --oneline`

**2. Rebase flow (conditional, low-noise):**
- If rebase is requested or divergence detected, ask for target branch if missing.
- Run: `git fetch --all --prune`
- Rebase: `git rebase origin/<target-branch> | tail -n 200`
- If conflicts occur, stop and ask for resolution preference.

**3. Pre-commit checks (conditional, low-noise):**
- If repo defines checks, run them with filtered output:
  - Prefer `--quiet` or `-q` where supported.
  - Pipe output: `| tail -n 200` or `| grep -E "ERROR|WARN|FAIL|SUCCESS|BUILD|TEST"`

**4. Standardize commit message:**
- Build a commit message following the project's convention (check recent git log for style):
  - Scope: component/module or area
  - Summary: concise, present tense
  - Optional ticket or issue ID
- If missing, ask for scope and summary.
- Confirm with user before committing.

**5. Commit (low-noise):**
- Stage if needed (confirm if nothing staged).
- Commit with the standardized message.
- Show: `git log -1 --oneline`

**6. PR preparation (optional):**
- Prepare PR title and description from commit and changes.
- If target branch missing, ask for it.
- Provide PR summary text and checklist for the user.

## Output Summary
- Current branch, target branch, and rebase status
- Commit message used
- PR title/body draft if generated

## Notes
- Avoid dumping full terminal logs into context.
- Prefer `head`, `tail`, and `grep -E` for any output longer than a screen.
