---
name: tavola-feature-slice
description: Build or refactor Tavola features as small vertical slices, using the project-local tdd skill for implementation. Use for catalog, basket, checkout, planner proposal, API, use case, domain, infrastructure, frontend, or test work in /Users/jaki/Projects/tavola, including planner-created sprint or task ranges.
---

# Tavola Feature Slice

## Start Here

Read `AGENTS.md`; use `CONTEXT.md` as the authority for product scope,
language, and Tavola-specific constraints.

Use this skill to keep implementation work shaped as one small, demonstrable Tavola workflow.

For all implementation work, use the project-local `$tdd` skill at `.codex/skills/tdd/SKILL.md`. Run each slice or planner task through its red-green-refactor loop unless the user explicitly asks for non-implementation analysis only.

## Planner Plan Execution

When the user points at a plan created by `$planner` and asks to implement a sprint or task range:

1. Locate and read the plan.
   - Use the path the user gives. If none is given, look for `*plan.md` files and ask only if the target is ambiguous.
   - Read the overview, prerequisites, target sprint, target tasks, testing strategy, risks, and rollback notes.
   - Treat the plan as the execution contract, but still enforce `AGENTS.md` and `CONTEXT.md`.

2. Resolve the requested range.
   - Interpret requests like `Sprint 1 task 1.1-1.3` as the listed tasks under that sprint.
   - Include prerequisite tasks when the plan marks them as dependencies.
   - If a task is no longer valid because the codebase changed, adapt narrowly and report the deviation.

3. Make a short execution map.
   - List the tasks to implement.
   - Identify shared files and dependency order.
   - Mark which tasks can run in parallel and which must stay on the lead agent's critical path.

4. Use subagents when available and appropriate.
   - Prefer available worker agents for independent tasks with disjoint write scopes.
   - Give each worker the plan path, exact sprint/task IDs, owned files or modules, relevant acceptance criteria, the project-local `$tdd` skill path, and a reminder not to revert others' changes.
   - Keep tightly coupled, blocking, or integration-heavy work local.
   - While workers run, do non-overlapping local work.
   - Review worker changes before integrating, then run the validation required by the plan.

5. Keep the plan current.
   - If useful, mark completed tasks or add a concise implementation note in the plan.
   - Do not rewrite the plan into a new plan unless the user asks.

## Slice Workflow

1. Name the slice in Tavola language.
   - State the smallest customer-visible outcome.
   - Tie it to the current flow named in `CONTEXT.md`.
   - Call out any scope edge before implementing.

2. Put each responsibility in the layer defined by `AGENTS.md`.

3. Build backend behavior from the inside out when the slice has rules or state.
   - Start where the behavior lives.
   - Move outward only as the slice needs persistence, transport, or UI exposure.

4. Add the matching frontend flow.
   - Keep state ownership obvious.
   - Include the user-facing states expected by `AGENTS.md`.
   - Keep transport mapping at the frontend boundary.

5. Test at the layer where the behavior lives, starting narrow and broadening only when the slice crosses boundaries.

## Tavola-Specific Checks

Before editing or finishing, check the slice against the relevant `CONTEXT.md`
sections. If the request touches planner behavior, basket mutation, pricing,
checkout, package templates, or source-of-truth rules, name the applicable
constraint in your plan or final summary instead of copying the full context.

## Finish

Report the concrete behavior changed, layers touched, API contract changes, infrastructure changes, tests run, and any gaps. Keep the summary in Tavola terms.
