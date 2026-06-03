---
name: tdd
description: Use Tavola's project-local red-green-refactor workflow for feature work, bug fixes, and focused tests. Trigger when the user asks for TDD, test-first work, red-green-refactor, or implementation that needs behavior-driven backend, API, frontend, or integration coverage.
---

# Tavola Test-Driven Development

## Start Here

Read `AGENTS.md`; use `CONTEXT.md` as the authority for product language and
scope. This skill only defines the test-first workflow.

This project-local skill is self-contained. Do not rely on personal skill
references outside this repository.

## Core Principle

Tests should verify behavior through public interfaces, not implementation
details. A refactor should not break tests when behavior is unchanged.

Prefer the highest public interface that proves the behavior without making the
test slow or brittle: domain object, use case, route, client function, component,
or user workflow.

Avoid tests that mock internal collaborators, inspect private state, assert on
incidental helper calls, or query persistence directly when the public interface
can prove the behavior.

## Mocking Guidance

Mock only true boundaries: network APIs, clocks, identity generation, payment,
email, storage adapters, browser APIs, and other external effects.

Do not mock Tavola's own domain objects or internal application services just to
make a unit smaller. If a test needs too many internal mocks, move up to the
public use case, API route, or component workflow that owns the behavior.

When a collaborator is intentionally passed into a use case, use a small fake or
spy that records observable boundary interactions. Keep the assertion about the
outcome first and the collaborator assertion second.

## Anti-Pattern: Horizontal Slices

Do not write all tests first and then all implementation. That outruns the actual
design and tends to test imagined structure rather than real behavior.

Use vertical tracer bullets:

```text
Wrong:
  RED:   test1, test2, test3, test4
  GREEN: impl1, impl2, impl3, impl4

Right:
  RED -> GREEN: test1 -> impl1
  RED -> GREEN: test2 -> impl2
  RED -> GREEN: test3 -> impl3
```

Each test should respond to what the previous cycle revealed.

## Planning

Before editing, identify the public interface and the behaviors that matter most.

State a short plan when the work is non-trivial:

- Public interface under test.
- First tracer-bullet behavior.
- Next two or three behaviors, prioritized by risk and user value.
- Test layer for each behavior.
- Commands you expect to run.

Ask the user only when interface shape or priority is genuinely ambiguous.
Otherwise make a conservative choice that follows `AGENTS.md` and `CONTEXT.md`.

## Red-Green-Refactor Loop

For each behavior:

1. RED: write one focused failing test for observable behavior.
2. Run the narrowest command that proves it fails for the expected reason.
3. GREEN: write the smallest production change that makes the test pass.
4. Run the narrowest command that proves it passes.
5. REFACTOR: clean duplication or naming only while tests are green.
6. Repeat for the next behavior.

Never refactor while red. Never add speculative behavior for a future test.

## Test Design

Good Tavola tests read like requirements:

- `basket_rejects_unknown_sku`
- `checkout_creates_pickup_order_from_valid_basket`
- `catalog_route_returns_available_skus`
- `planner_proposal_must_reference_real_skus`
- `basket_page_shows_server_calculated_total`

Keep fixtures realistic but small. Prefer named catalog and basket data that
matches Tavola's domain over abstract placeholders like `foo` and `bar`.

Use public setup paths when practical. For example, create or update a basket
through the application use case or API route being exercised instead of
constructing private internals unless the test is explicitly a domain test.

## Interface Design For Testability

Design small public interfaces with meaningful behavior behind them. When tests
need time, identity, or external effects, pass those dependencies explicitly so
the behavior can be exercised without hidden global state.

If a test is painful to write, treat that as design feedback. Prefer improving
the public interface over reaching into internals, while preserving the
boundaries defined in `AGENTS.md`.

## Refactor Checks

After tests pass, look for narrow cleanup:

- Duplicate fixture setup that can become a small builder.
- Domain terms that should be renamed to match `CONTEXT.md`.
- Responsibilities drifting away from the layer guidance in `AGENTS.md`.
- Modules with wide interfaces and shallow behavior that can be deepened.

Run the relevant tests after each refactor step.

## Commands

Use the commands listed in `AGENTS.md`. Run the narrowest useful test command
first, then broaden when the change crosses boundaries.

If the repository does not yet contain the referenced project area or command,
say exactly what could not be run and why.

## Per-Cycle Checklist

```text
[ ] Test describes behavior, not implementation
[ ] Test uses the public interface for the layer under test
[ ] Test would survive an internal refactor
[ ] RED failed for the expected reason
[ ] GREEN uses minimal production code
[ ] No speculative features were added
[ ] Relevant narrow tests pass
```
