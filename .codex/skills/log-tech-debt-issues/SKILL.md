---
name: log-tech-debt-issues
description: Reconcile project documentation for deferred work, shortcuts, known gaps, and architecture or testing debt, then create GitHub issues for actionable tech debt. Use when Codex is asked to log tech debt from docs, audit documentation for deferred work, reconcile plans or ADRs into issues, run a manual debt sweep, or support an automation that periodically opens GitHub issues from documented debt.
---

# Log Tech Debt Issues

## Purpose

Use this skill to turn documented deferred work into explicit GitHub issues without flooding the tracker with vague reminders.

Support both manual runs and automations. An automation should follow the same workflow, but must be conservative: draft or open only issues with clear evidence and skip anything ambiguous.

## Inputs

Start from the repository root unless the user gives another path.

Inspect:

- `AGENTS.md`, `CONTEXT.md`, and docs under `docs/`.
- Plans, ADRs, runbooks, TODO docs, handoff notes, and status notes.
- Existing GitHub issues before opening new ones.

Ignore generated outputs, dependency folders, build artifacts, `.git`, and ordinary source-code TODOs unless a documentation finding points to them.

## Candidate Scan

Run the bundled scanner first:

```bash
python3 .codex/skills/log-tech-debt-issues/scripts/find_doc_debt.py --root .
```

Use `--json` when an automation or follow-up script needs structured output.

The script finds likely evidence. It does not decide whether something deserves an issue.

Also search manually for domain-specific phrasing that the scanner may miss:

```bash
rg -n -i "defer|follow.?up|later|future|gap|known issue|known limitation|temporary|shortcut|workaround|not yet|needs|missing|todo|tech debt|debt" AGENTS.md CONTEXT.md docs
```

## Reconciliation Workflow

1. Read each candidate in context.
   - Open the surrounding section, not just the matching line.
   - Decide whether it is still relevant to the current product scope.
   - Prefer `CONTEXT.md` for product boundaries and language.

2. Classify each candidate.
   - **Issue-worthy**: actionable, still relevant, has a clear owner surface or acceptance condition, and is not already tracked.
   - **Already tracked**: covered by an open GitHub issue; do not duplicate it.
   - **Not debt**: aspirational future scope, explicitly out of scope, stale, vague, or not actionable.

3. Check existing GitHub issues before creating anything.
   - Use the GitHub app tools when available.
   - Otherwise use `gh issue list --search "<keywords> repo:<owner>/<repo>" --state open`.
   - Compare by behavior and affected area, not only exact wording.

4. Create one issue per coherent debt item.
   - Do not bundle unrelated debt.
   - Do bundle duplicate references to the same underlying gap.
   - Use the repository's existing labels if known; otherwise avoid inventing labels unless the user asked for them.

5. Report what happened.
   - List created issues with links.
   - List skipped candidates and why, grouped briefly as already tracked, not actionable, or out of scope.
   - If running as an automation, keep the summary short and include enough evidence for auditability.

## Issue Standard

Open a GitHub issue only when you can write all of these:

- **Title**: starts with a verb and names the affected area.
- **Evidence**: cites source doc path and line number.
- **Problem**: explains the risk or maintenance cost.
- **Suggested resolution**: gives a plausible next step without over-designing.
- **Acceptance checks**: names how completion can be verified.

Prefer this body shape:

```markdown
## Evidence
- `docs/path.md:42` notes ...

## Problem
...

## Suggested resolution
...

## Acceptance checks
- [ ] ...
```

## Automation Guardrails

When launched by an automation:

- Do not ask the user clarifying questions.
- Do not create issues from weak signals such as "future" when the text describes optional roadmap scope.
- Limit created issues to the clearest findings. If there are many, create the top few and report the rest as candidates.
- Include the automation run date in the issue body if helpful for auditability.
- Never close, edit, or relabel existing issues unless explicitly requested.

## GitHub Fallback

If no GitHub tool or authenticated `gh` CLI is available, produce issue drafts instead of pretending issues were created. Include titles, labels if known, and full bodies so the user can create them later.
