# Tavola Agent Guide

Before product architecture/scope decisions, read `CONTEXT.md`. This file says
how to work here; `CONTEXT.md` says what Tavola is and why.

## Project

Tavola = lightweight Italian deli e-commerce demonstrator: Python backend,
React frontend, DDD boundaries. Keep scope focused on current flow; no advanced
commerce unless explicit. Prefer small vertical changes, easy reasoning/tests.

## Stack

Backend:

- Python 3.12+
- FastAPI
- Pydantic for boundary validation where useful
- uv
- pytest
- Ruff

Frontend:

- React
- TypeScript
- npm

## Structure

Expected backend:

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

Expected frontend:

```text
frontend/
  src/
    api/
    components/
    features/
    pages/
    types/
```

Plans live in `docs/plans/`.

## Commands

Keep current when tooling/layout changes.

Backend:

- Install deps: `cd backend && uv sync`
- Dev server: `cd backend && uv run uvicorn tavola.api.main:app --reload`
- Tests: `cd backend && uv run pytest`
- Format: `cd backend && uv run ruff format .`
- Format check: `cd backend && uv run ruff format --check .`
- Lint: `cd backend && uv run ruff check .`
- Lint fix: `cd backend && uv run ruff check . --fix`

Codex backend `uv` commands: use workspace cache:
`UV_CACHE_DIR=../.uv-cache`. Example:
`cd backend && UV_CACHE_DIR=../.uv-cache uv run pytest`. Request escalation only
if local cache cannot complete due network/auth/external resource.

Frontend:

- Install deps: `cd frontend && npm install`
- Dev server: `cd frontend && npm run dev`
- Tests: `cd frontend && npm test`
- Lint: `cd frontend && npm run lint`
- Build: `cd frontend && npm run build`
- Preview: `cd frontend && npm run preview`

## Architecture

Backend layers:

- API: HTTP only: routing, request validation, response models.
- Application: use cases/workflows.
- Domain: rules/invariants; no framework/infrastructure deps.
- Infrastructure: persistence/external adapters.

Domain owns commerce invariants. Application coordinates; does not own domain
rules.

Frontend layers:

- Components: rendering/local interaction.
- Hooks/client services: API calls + reusable UI behavior.
- Pages/routes: screen composition.
- Shared UI primitives only when reused.
- Explicit state ownership for interactive flows.

Avoid presentational components coupled directly to backend transport; map API
responses near client/service layer.

## Backend Guidance

- Use FastAPI idioms for routes/DI/validation/responses.
- Use Pydantic at API, DTO, settings, external-data boundaries when it reduces
  ambiguity/boilerplate.
- Keep Pydantic to data shape/boundary constraints; enforce commerce invariants
  in domain.
- Keep framework imports out of domain.
- Define repo/gateway interfaces at app/domain boundary when persistence/external
  systems needed.
- Put concrete DB/payment/email/storage/queue impl in infrastructure.
- Validate transport shape at API boundary; business invariants in domain.
- Keep use cases deterministic when possible; pass time/identity/effects through
  explicit collaborators.
- Prefer typed Python + clear DTO/schema boundaries.
- Test where behavior lives: domain invariants, app workflows, API
  routing/serialization.

## Frontend Guidance

- TypeScript.
- Desktop-first demonstrator. No mobile-specific layout/breakpoints/interactions
  unless explicit.
- Workflows efficient/scannable.
- Loading/empty/error/success states explicit.
- Do not hide critical user state in purely visual components.
- Prefer accessible controls, semantic HTML, keyboard-friendly interactions.
- Keep API response mapping close to frontend client/service.

## Testing

For meaningful changes, add/update focused tests.

- Domain: fast unit tests, no DB/network.
- Application: workflow outcomes + collaborator calls.
- API: req/res status, validation, auth, serialization.
- Infrastructure: integration tests for persistence/adapters/migrations.
- Frontend: component/user-flow tests for current feature slice.

Frontend/user-facing browser workflow changes: run
`docs/frontend-browser-approval-check.md` before handoff. Use Codex in-app
Browser when available. Verify supported desktop viewport plus touched
loading/empty/error/success states. If backend API needed, run backend +
frontend through Vite proxy. Report checks run + unchecked items.

If tests cannot run, say exactly what and why.

After scaffold/cross-service workflow changes, run
`docs/scaffold-smoke-check.md`; report unchecked items.

## Workflow

- Read relevant files before edits.
- Respect naming, formatting, module boundaries.
- Scope edits to request.
- No new frameworks/service containers/state libs/build tools without strong
  reason.
- Preserve user changes. Never revert unrelated changes unless explicit.
- Prefer `rg` / `rg --files`.
- Prefer `uv` for backend deps/commands.
- In Codex, run backend scanners/tests/lint from `backend/` with
  `UV_CACHE_DIR=../.uv-cache`.
- Prefer `npm` for frontend deps/scripts.
- Prefer structured parsers/framework APIs over ad hoc string handling.
- Run narrow useful tests first, then broader checks when impact wider.

## PR/Handoff Notes

Summarize:

- User-facing behavior changed.
- Domain/application concepts touched.
- API contract changes.
- DB/infrastructure changes.
- Tests run + gaps.

## GitHub CLI

`gh` may need unsandboxed execution because auth lives in macOS keyring/network
may be restricted. If `gh auth status` says invalid token or GitHub API commands
fail in sandbox, retry same command with escalation before asking user to
reauthenticate.
