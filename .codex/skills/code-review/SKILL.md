---
name: code-review
description: Perform focused code quality reviews that first read repository guidance such as AGENTS.md and CONTEXT.md, then evaluate requested changes or files for security, correctness, maintainability, architecture fit, and unnecessary complexity. Use when the user asks for a code review, review of current changes, PR review, diff review, architecture-aware review, security/correctness pass, or complexity check.
---

# Code Review

## Overview

Review code as a senior engineer looking for concrete defects and avoidable risk. Anchor the review in the repository's own architecture, product direction, and workflow instructions before judging the implementation.

## Workflow

1. Read repository guidance first.
   - Read the applicable `AGENTS.md` instructions before inspecting code. If there are nested `AGENTS.md` files, read the ones that apply to the reviewed files.
   - Read `CONTEXT.md` when it exists, especially before making architecture, product direction, or scope judgments.
   - Note any missing guidance only if it materially limits the review.

2. Establish review scope.
   - If the user names files, commits, a branch, a PR, or a diff, review that scope.
   - If the user asks to review current work, inspect `git status --short` and review the local diff. Prefer `git diff --stat` and targeted `git diff` reads over dumping the whole patch at once.
   - If there is no obvious scope, ask one concise question instead of guessing.

3. Inspect the implementation in context.
   - Read surrounding code, tests, schemas, and call sites needed to validate behavior.
   - Prefer `rg`, `rg --files`, language-aware tools, and framework conventions over broad manual searches.
   - Preserve user changes. Do not modify code during a review unless the user explicitly asks for fixes.

4. Focus findings on real risk.
   - Prioritize security vulnerabilities, data exposure, injection risks, authorization/authentication mistakes, unsafe defaults, and dependency or secret handling issues.
   - Check code correctness: broken behavior, edge cases, races, error handling gaps, invalid assumptions, API contract mismatches, and missing validation.
   - Check architecture fit against `AGENTS.md` and `CONTEXT.md`: layering violations, misplaced domain rules, transport concerns leaking into domain code, inappropriate infrastructure coupling, or scope beyond the product direction.
   - Check complexity: duplicated logic, over-broad abstractions, hard-to-test control flow, confusing ownership, hidden state, or changes that are larger than the behavior requires.
   - Treat missing tests as a finding only when a specific uncovered behavior creates meaningful regression risk.

5. Verify when useful.
   - Run narrow tests, linters, type checks, or static analysis only when they materially improve confidence and are reasonable for the scope.
   - Report exactly what was run and what could not be run.

## Output Format

Lead with findings, ordered by severity. Keep summaries brief and secondary.

For each finding include:

- Severity: `Critical`, `High`, `Medium`, or `Low`.
- Location: file path and line number when possible.
- Problem: the concrete failure mode or risk.
- Rationale: why it matters, tied to observed code or repository guidance.
- Suggested fix: concise direction, not a full patch unless requested.

Use this shape:

```markdown
**Findings**

- `High` [path/to/file.py:42](/absolute/path/to/file.py:42): The endpoint trusts the caller-provided user ID, allowing one user to access another user's data. Derive the user ID from the authenticated principal before calling the use case.

**Open Questions**

- ...

**Tests**

- Ran `...`
```

If no issues are found, say so clearly and mention residual risks or test gaps. Do not pad the review with style preferences, praise, or generic best practices.

## Severity Guide

- `Critical`: exploitable security issue, data loss, production outage, or severe correctness failure.
- `High`: likely user-facing breakage, privilege boundary failure, serious data integrity issue, or major architecture violation with immediate consequences.
- `Medium`: plausible bug, meaningful maintainability risk, missing validation, or complexity likely to cause defects.
- `Low`: minor correctness risk, small cleanup, or local complexity concern worth addressing but not release-blocking.

## Review Discipline

- Prefer fewer, stronger findings over exhaustive commentary.
- Do not report speculative issues without a concrete path to failure.
- Distinguish repository-guidance violations from personal taste.
- Keep architecture feedback proportional to the project stage and stated product scope.
- Avoid rewriting the implementation in the review unless the user asks for fixes.
