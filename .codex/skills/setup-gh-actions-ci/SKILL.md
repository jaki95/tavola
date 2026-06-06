---
name: setup-gh-actions-ci
description: Set up or update Tavola GitHub Actions CI pipelines for frontend linting/testing and backend formatting/linting/testing. Use when Codex needs to create, revise, or review `.github/workflows` CI YAML for Tavola's React frontend, FastAPI/uv backend, npm test/lint scripts, uv pytest/ruff checks, or related CI validation.
---

# Setup GitHub Actions CI

## Start Here

Read `AGENTS.md`, `CONTEXT.md`, `frontend/package.json`, and `backend/pyproject.toml` before editing workflows.

Use the templates in `assets/` as the default starting point:

- `assets/frontend-ci.yml` -> `.github/workflows/frontend-ci.yml`
- `assets/backend-ci.yml` -> `.github/workflows/backend-ci.yml`

If workflows already exist, merge deliberately instead of overwriting unrelated jobs, triggers, permissions, or user changes.

## Workflow

1. Inspect the current tool commands.
   - Frontend: use `npm ci`, `npm run lint`, and `npm test` from `frontend/`.
   - Backend: use `uv sync --locked`, `uv run ruff format --check .`, `uv run ruff check .`, and `uv run pytest` from `backend/`.
   - Adjust only when the repo's scripts or lockfiles have changed.

2. Create separate CI workflow files unless the user asks for a combined pipeline.
   - Keep frontend and backend paths scoped so changes in one side do not run the other side unnecessarily.
   - Include `workflow_dispatch` for manual runs.
   - Use read-only repository permissions.

3. Prefer the bundled templates.
   - Use Node `22` for the frontend unless `frontend/package.json` or a repo config specifies otherwise.
   - Use Python `3.12` for the backend unless `backend/pyproject.toml` specifies a different supported version.
   - Verify current major versions for GitHub Actions dependencies when the user asks for latest versions or the templates appear old.

4. Validate locally before handoff.
   - Run `cd frontend && npm run lint && npm test` for frontend workflow changes.
   - Run `cd backend && uv run ruff format --check . && uv run ruff check . && uv run pytest` for backend workflow changes.
   - If changing both services or scaffold behavior, run `docs/scaffold-smoke-check.md`.
   - If validation cannot run, report exactly which commands were skipped and why.

## Guardrails

- Do not introduce deployment, release, Docker, database, secrets, or production environment work unless the user asks.
- Do not add new package managers or CI services.
- Keep CI focused on Tavola's demonstrator stack and existing repository commands.
- Preserve uncommitted workflow changes that you did not make.
