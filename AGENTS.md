# Tavola Agent Guide

Before making product architecture or scope decisions, read `CONTEXT.md`.
`AGENTS.md` defines how to work in this repository. `CONTEXT.md` defines what the
product is and why it exists.

## Project Overview

Tavola is an e-commerce web application with a Python backend and a React frontend.
The codebase should be shaped around domain-driven architecture, with clear
boundaries between API concerns, application/business orchestration, domain logic,
and infrastructure.

This is a lightweight demonstrator app, not a fully fledged commerce platform.
Keep the domain model focused on the features needed to demonstrate the
architecture and current user flow. Do not add advanced commerce capabilities
unless explicitly requested.

Future agents should preserve these boundaries when adding features, fixing bugs,
or refactoring. Prefer small, vertical changes that keep behavior easy to reason
about and test.

## Technology Choices

Backend:

- Python 3.12+
- FastAPI for HTTP APIs
- Pydantic for backend request/response schemas and boundary validation where
  useful
- uv for dependency management and Python task execution
- pytest for tests
- Ruff for linting and formatting

Frontend:

- React
- TypeScript
- npm for dependency management and scripts

## Repository Structure

Expected backend structure:

```text
backend/
  src/tavola/
    api/
    application/
    domain/
    infrastructure/
    config/
  tests/
```

Expected frontend structure:

```text
frontend/
  src/
    api/
    components/
    features/
    pages/
    types/
```

Planning documents should live in `docs/plans/`.

## Commands

These commands may change as the repository evolves. Keep this section updated
when tooling, scripts, or project layout changes.

Backend:

- Install dependencies: `cd backend && uv sync`
- Run development server:
  `cd backend && uv run uvicorn tavola.api.main:app --reload`
- Run tests: `cd backend && uv run pytest`
- Run formatting: `cd backend && uv run ruff format .`
- Check formatting: `cd backend && uv run ruff format --check .`
- Run linting: `cd backend && uv run ruff check .`
- Apply lint fixes: `cd backend && uv run ruff check . --fix`

Frontend:

- Install dependencies: `cd frontend && npm install`
- Run development server: `cd frontend && npm run dev`
- Run tests: `cd frontend && npm test`
- Run linting: `cd frontend && npm run lint`
- Run production build: `cd frontend && npm run build`
- Preview production build: `cd frontend && npm run preview`

## Architecture Principles

### Backend Layering

Keep backend responsibilities separated by layer:

- API: HTTP concerns only.
- Application: use cases and workflow coordination.
- Domain: business rules and invariants, with no framework or infrastructure
  dependencies.
- Infrastructure: persistence and external system adapters.

Domain rules should stay in the domain layer, even when triggered by API calls.
Application code may coordinate behavior, but should not own domain invariants.

### Frontend Layering

Keep React code organized around the user workflow in the feature slice currently
being implemented.

Prefer:

- Components for rendering and local interaction.
- Hooks or client services for API calls and reusable UI behavior.
- Route/page modules for screen composition.
- Shared UI primitives only when they are reused in multiple places.
- Explicit state ownership for interactive flows.

Avoid coupling presentational components directly to backend transport details
when a small client/service abstraction would keep the UI easier to change.

## Backend Guidance

- Use FastAPI idioms for routing, dependency injection, request validation, and
  response models in the API layer.
- Prefer Pydantic models for structured type validation at API, DTO, settings,
  and external-data boundaries where they reduce ambiguity or boilerplate.
- Keep Pydantic validation focused on data shape and boundary constraints;
  enforce commerce invariants in the domain layer.
- Keep framework-specific imports out of the domain layer.
- Define repository or gateway interfaces at the application/domain boundary when
  use cases need persistence or external systems.
- Put concrete database, payment, email, storage, and queue implementations in
  infrastructure.
- Validate transport shape at the API boundary; validate business invariants in
  the domain.
- Keep application use cases deterministic where possible and pass time, identity,
  and external effects through explicit collaborators.
- Prefer typed Python and clear DTO/schema boundaries for API inputs and outputs.
- Add tests at the layer where behavior lives: domain tests for invariants,
  application tests for workflows, API tests for routing and serialization.

## Frontend Guidance

- Write frontend code in TypeScript.
- Treat Tavola as a desktop-first demonstrator. Do not design or test
  mobile-specific layouts, breakpoints, or interactions unless explicitly
  requested.
- Keep user workflows efficient and easy to scan.
- Make loading, empty, error, and success states explicit for user-facing flows.
- Do not hide critical user-facing state inside purely visual components.
- Prefer accessible controls, semantic HTML, and keyboard-friendly interactions.
- Keep API response mapping close to the frontend client/service layer rather than
  scattering transport assumptions across components.

## Testing Expectations

For meaningful changes, add or update focused tests.

- Domain behavior: fast unit tests with no database or network dependency.
- Application use cases: tests around workflow outcomes and collaborator calls.
- API behavior: request/response tests for status codes, validation, auth, and
  serialization.
- Infrastructure: integration tests when persistence, external adapters, or
  migrations are involved.
- Frontend: component or user-flow tests for interactive behavior in the current
  feature slice.

If tests cannot be run, explain exactly what was not run and why.

After scaffold or cross-service workflow changes, run the checklist in
`docs/scaffold-smoke-check.md` and report any unchecked items.

## Agent Workflow

- Read the relevant files before changing code.
- Respect existing naming, formatting, and module boundaries.
- Keep edits scoped to the requested change.
- Do not introduce new frameworks, service containers, state libraries, or build
  tools without a strong reason.
- Preserve user changes in the working tree. Never revert unrelated changes unless
  explicitly asked.
- Prefer `rg`/`rg --files` for searching.
- Prefer `uv` for backend dependency and command execution.
- Prefer `npm` for frontend dependency and script execution.
- Use structured parsers and framework APIs instead of ad hoc string processing
  when practical.
- Run the narrowest useful tests first, then broader checks when the change has
  wider impact.

## Pull Request Notes

When preparing a PR or handoff, summarize:

- The user-facing behavior changed.
- The domain/application concepts touched.
- Any API contract changes.
- Any database or infrastructure changes.
- Tests run and any remaining gaps.
