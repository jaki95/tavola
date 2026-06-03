# Plan: Backend and Frontend Scaffold

**Generated**: 2026-06-03
**Estimated Complexity**: Medium

## Overview

Create Tavola's first runnable foundation: a Python/FastAPI backend managed by
uv and a React/TypeScript frontend managed by npm. The scaffold should be small,
demoable, and shaped around the repository's domain-driven boundaries before any
commerce feature logic is added.

This plan assumes the scaffold is a vertical technical foundation, not the first
catalog slice. It should prove that backend and frontend can install, run, test,
lint, and communicate through a minimal health/status flow. Later slices can then
add catalog browsing, basket editing, checkout, and planner workflows without
reorganizing the project.

## Clarifying Assumptions

- Backend lives under `backend/` with package source in `backend/src/tavola/`.
- Frontend lives under `frontend/` as a Vite React TypeScript SPA.
- No database, auth, payment, Docker, deployment, or AI integration is included
  in this scaffold.
- Backend local port is `8000`; frontend local port is Vite's default `5173`.
- Local frontend-to-backend calls use a Vite dev proxy for `/api/*`; backend CORS
  is deferred until a deployment shape requires cross-origin browser requests.
- Tests should be meaningful but minimal: backend health/API tests and frontend
  app/API-client tests.
- Domain, application, API, infrastructure, and config packages are created early
  even if most contain placeholders only.
- README and AGENTS command references are kept accurate as scaffold tooling is
  added.

## Decisions

- Use a plain Vite React TypeScript SPA for the first demonstrator. Add routing
  later when real catalog, basket, checkout, and planner review screens need it.
- Use Vite's development proxy for local API calls instead of adding CORS
  middleware to the backend scaffold.
- Defer Docker and any root-level process runner until after catalog and basket
  behavior exists.
- Create backend domain/application packages as empty placeholders only during
  scaffold work; do not add example domain objects before the first real feature
  slice needs them.

## References Consulted

- FastAPI bigger applications and `APIRouter`:
  https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI testing:
  https://fastapi.tiangolo.com/tutorial/testing/
- uv project workflow:
  https://docs.astral.sh/uv/guides/projects/
- Ruff formatter:
  https://docs.astral.sh/ruff/formatter/
- Vite guide:
  https://vite.dev/guide/
- React app setup guidance:
  https://react.dev/learn/start-a-new-react-project
- Vitest guide:
  https://vitest.dev/guide/

## Prerequisites

- Python 3.12+ available locally or installable through uv.
- uv available for backend dependency management and command execution.
- Node.js and npm available for frontend dependency management.
- Existing `CONTEXT.md` and `AGENTS.md` remain the source of product and agent
  architecture guidance.

## Sprint 1: Repository Tooling Skeleton

**Goal**: Establish backend and frontend project roots with installable tooling,
without user-facing product behavior yet.

**Demo/Validation**:

- `cd backend && uv sync` completes.
- `cd frontend && npm install` completes.
- Backend and frontend command surfaces are documented.

### Task 1.1: Add Backend uv Project Metadata

- **Location**: `backend/pyproject.toml`, `backend/.python-version`,
  `backend/README.md`
- **Description**: Define a Python 3.12+ uv project named `tavola-backend` with
  runtime dependencies for FastAPI and Uvicorn, and development dependencies for
  pytest, Ruff, and HTTPX/TestClient support.
- **Dependencies**: None
- **Acceptance Criteria**:
  - `uv sync` creates a lockfile and project environment.
  - `uv run python -c "import tavola"` works after source package task is done.
  - Tool versions are pinned through `uv.lock`, not ad hoc requirements files.
- **Validation**: `cd backend && uv sync`

### Task 1.2: Add Backend Package Directory Layout

- **Location**: `backend/src/tavola/`, `backend/tests/`
- **Description**: Create package directories for `api`, `application`,
  `domain`, `infrastructure`, and `config`, each with `__init__.py`. Add a
  minimal test package structure.
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - The expected Tavola backend layering exists on disk.
  - Domain package has no FastAPI imports.
  - Empty package files avoid import ambiguity.
- **Validation**: `cd backend && uv run python -c "import tavola.api, tavola.domain"`

### Task 1.3: Add Frontend Vite React TypeScript Project Metadata

- **Location**: `frontend/package.json`, `frontend/package-lock.json`,
  `frontend/tsconfig*.json`, `frontend/vite.config.ts`, `frontend/index.html`
- **Description**: Scaffold a Vite React TypeScript app with npm scripts for
  development, build, preview, test, and lint.
- **Dependencies**: None
- **Acceptance Criteria**:
  - `npm install` produces a lockfile.
  - `npm run dev`, `npm run build`, and `npm test` are defined.
  - TypeScript strictness is enabled enough to catch transport shape mistakes.
- **Validation**: `cd frontend && npm install`

### Task 1.4: Add Frontend Source Directory Layout

- **Location**: `frontend/src/api/`, `frontend/src/components/`,
  `frontend/src/features/`, `frontend/src/pages/`, `frontend/src/types/`
- **Description**: Create the expected frontend structure with a minimal app
  entry point and test setup file.
- **Dependencies**: Task 1.3
- **Acceptance Criteria**:
  - `frontend/src/main.tsx` renders a root React component.
  - `frontend/src/App.tsx` is small and delegates workflow composition to pages
    or features.
  - API transport details are kept under `frontend/src/api/`.
- **Validation**: `cd frontend && npm run build`

### Task 1.5: Add Shared Ignore and Environment Examples

- **Location**: `.gitignore`, `backend/.env.example`, `frontend/.env.example`
- **Description**: Ignore Python environments, uv/cache artifacts, Node modules,
  build output, coverage output, and local `.env` files. Provide example env
  variables for backend app settings and frontend API base URL.
- **Dependencies**: Tasks 1.1, 1.3
- **Acceptance Criteria**:
  - Generated dependencies and local secrets are not tracked.
  - Required local configuration is discoverable without reading code.
- **Validation**: `git status --short` after install does not show generated
  dependency directories or local env files.

## Sprint 2: Backend Runnable API Foundation

**Goal**: Make the backend runnable and testable with a minimal API surface that
respects Tavola's layer boundaries.

**Demo/Validation**:

- `cd backend && uv run uvicorn tavola.api.main:app --reload` starts.
- `GET /api/health` returns a stable JSON response.
- `cd backend && uv run pytest` passes.

### Task 2.1: Create FastAPI Application Entrypoint

- **Location**: `backend/src/tavola/api/main.py`
- **Description**: Define the FastAPI app, app metadata, and router inclusion.
  Keep app creation thin and HTTP-focused.
- **Dependencies**: Tasks 1.1, 1.2
- **Acceptance Criteria**:
  - App can be imported as `tavola.api.main:app`.
  - API routes are attached through routers, not scattered in the entrypoint.
  - OpenAPI docs are available in local development.
- **Validation**: `cd backend && uv run python -c "from tavola.api.main import app; print(app.title)"`

### Task 2.2: Add Config Module

- **Location**: `backend/src/tavola/config/settings.py`
- **Description**: Add a small typed settings object for app name, environment,
  and API prefix. Keep defaults local-development friendly.
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - API prefix can be configured without code changes.
  - Settings remain infrastructure/config concerns, not domain concepts.
- **Validation**: Unit test settings defaults.

### Task 2.3: Add Health Router

- **Location**: `backend/src/tavola/api/routers/health.py`
- **Description**: Add `GET /api/health` returning service name and status.
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - Response shape is stable and typed through API schema or return annotation.
  - Route has no dependency on future catalog/basket implementation.
- **Validation**: API test asserts 200 response and JSON body.

### Task 2.4: Add Backend Test and Quality Configuration

- **Location**: `backend/pyproject.toml`, `backend/tests/test_health.py`
- **Description**: Configure pytest and Ruff. Add focused tests for app import,
  health route behavior, and settings defaults.
- **Dependencies**: Tasks 2.1 through 2.3
- **Acceptance Criteria**:
  - `uv run pytest` passes.
  - `uv run ruff check .` passes.
  - `uv run ruff format --check .` passes.
- **Validation**: Run the listed commands.

## Sprint 3: Frontend Runnable App Foundation

**Goal**: Make the frontend runnable and testable with a minimal Tavola app shell
that can read backend health without coupling UI components to transport details.

**Demo/Validation**:

- `cd frontend && npm run dev` starts Vite.
- The first screen renders a practical Tavola storefront shell, not a marketing
  landing page.
- The frontend can call the backend health endpoint through an API client.
- `cd frontend && npm test` and `cd frontend && npm run build` pass.

### Task 3.1: Create Frontend API Client

- **Location**: `frontend/src/api/client.ts`, `frontend/src/api/health.ts`,
  `frontend/src/types/health.ts`
- **Description**: Add a small fetch wrapper using `VITE_API_BASE_URL`, plus a
  typed health request.
- **Dependencies**: Tasks 1.3, 1.4, 2.3
- **Acceptance Criteria**:
  - API base URL defaults to `/api` when not configured.
  - Transport errors are converted into predictable frontend error values.
  - Components do not build request URLs directly.
- **Validation**: Unit test the health client with mocked fetch.

### Task 3.2: Configure Local API Dev Proxy

- **Location**: `frontend/vite.config.ts`, `frontend/.env.example`
- **Description**: Configure Vite to proxy local `/api/*` requests to the
  backend at `http://localhost:8000` during development.
- **Dependencies**: Tasks 1.3, 2.3, 3.1
- **Acceptance Criteria**:
  - Frontend code can call `/api/health` without knowing the backend origin.
  - Local browser requests avoid cross-origin plumbing in the backend scaffold.
  - The proxy target is documented and can be overridden later if needed.
- **Validation**: Run both services and verify the frontend health request
  succeeds through the Vite dev server.

### Task 3.3: Add App Shell and Home Page

- **Location**: `frontend/src/App.tsx`, `frontend/src/pages/HomePage.tsx`,
  `frontend/src/components/`
- **Description**: Render a lightweight storefront workspace with Tavola identity,
  navigation placeholders for catalog, basket, and checkout, and a backend status
  indicator.
- **Dependencies**: Tasks 1.4, 3.1, 3.2
- **Acceptance Criteria**:
  - First screen feels like the actual application foundation.
  - Loading, success, and error states for backend status are explicit.
  - No future feature is presented as working before it exists.
- **Validation**: Component test asserts app title/navigation/status states.

### Task 3.4: Add Frontend Styling Baseline

- **Location**: `frontend/src/styles/`, `frontend/src/index.css`
- **Description**: Add a restrained visual baseline suitable for a local Italian
  deli commerce app: readable typography, accessible focus states, responsive
  layout, and non-monochrome palette.
- **Dependencies**: Task 3.3
- **Acceptance Criteria**:
  - Text does not overflow at common mobile and desktop widths.
  - Buttons/links have visible focus states.
  - Layout is stable when backend status changes.
- **Validation**: Manual browser check at desktop and mobile viewport widths.

### Task 3.5: Add Frontend Tests and Linting

- **Location**: `frontend/package.json`, `frontend/src/**/*.test.tsx`,
  `frontend/eslint.config.*`
- **Description**: Configure Vitest, React Testing Library, jsdom, and ESLint
  for the scaffold.
- **Dependencies**: Tasks 3.1 through 3.4
- **Acceptance Criteria**:
  - `npm test` runs non-watch tests suitable for CI/local verification.
  - `npm run lint` passes.
  - Tests cover app rendering and health API behavior.
- **Validation**: Run `cd frontend && npm test && npm run lint`.

## Sprint 4: Cross-Service Developer Workflow

**Goal**: Make it easy to run, verify, and hand off the scaffold as the base for
catalog and basket slices.

**Demo/Validation**:

- Backend and frontend run together locally.
- Frontend status indicator succeeds against the live backend.
- README/AGENTS commands match actual tooling.

### Task 4.1: Document Local Development Workflow

- **Location**: `README.md`, `backend/README.md`, `frontend/README.md`,
  `AGENTS.md`
- **Description**: Document install, run, test, lint, and format commands for
  each app. Update existing command notes if scaffold tooling changes them.
- **Dependencies**: Sprints 1 through 3
- **Acceptance Criteria**:
  - A new contributor can start both services from documentation alone.
  - AGENTS command list has no dangling or stale bullets.
- **Validation**: Follow commands exactly from docs in a clean shell.

### Task 4.2: Add Smoke Verification Checklist

- **Location**: `README.md` or `docs/scaffold-smoke-check.md`
- **Description**: Add a concise checklist for verifying backend health,
  frontend rendering, the local API dev proxy, tests, linting, and builds.
- **Dependencies**: Task 4.1
- **Acceptance Criteria**:
  - Checklist is specific enough for future agents to run after scaffold changes.
  - It distinguishes automated checks from manual browser verification.
- **Validation**: Complete the checklist locally.

### Task 4.3: Run Full Scaffold Verification

- **Location**: No code changes expected
- **Description**: Run the complete verification command set and record results
  in the handoff/PR summary.
- **Dependencies**: Tasks 4.1, 4.2
- **Acceptance Criteria**:
  - Backend tests, lint, and format checks pass.
  - Frontend tests, lint, and build pass.
  - Live frontend-to-backend health call works through the Vite dev proxy in a
    browser.
- **Validation**:
  - `cd backend && uv run pytest`
  - `cd backend && uv run ruff check .`
  - `cd backend && uv run ruff format --check .`
  - `cd frontend && npm test`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`

## Parallel Execution Notes

- Tasks 1.1 and 1.3 can be done in parallel.
- Tasks 1.2 and 1.4 can be done in parallel after their respective metadata
  tasks.
- Backend Sprint 2 can proceed independently of frontend Sprint 3 after Sprint 1.
- Task 3.1 depends on the agreed backend API shape but can be mocked until the
  health route exists.
- Documentation tasks should wait until command names and scripts are settled.

## Testing Strategy

- Backend unit/API tests live under `backend/tests/` and use FastAPI's test
  client for import, health, and settings checks.
- Backend quality gates are pytest, Ruff lint, and Ruff format check.
- Frontend tests cover app rendering, loading/error/success states, and API
  client behavior with mocked fetch.
- Frontend quality gates are Vitest, ESLint, TypeScript build, and Vite build.
- Manual verification checks both services running together in a browser.

## Potential Risks & Gotchas

- **Vite versus a fuller React framework**: React's docs prefer frameworks for
  many production apps, but Tavola's current scope is a lightweight demonstrator
  SPA with a separate FastAPI backend. Vite keeps the scaffold smaller.
- **Over-modeling too early**: Creating domain/application directories is useful,
  but adding abstract repositories or placeholder business objects before the
  catalog slice would add noise. Keep placeholders minimal.
- **Proxy versus CORS**: The scaffold avoids backend CORS by using Vite's local
  dev proxy. Revisit explicit CORS settings later if frontend and backend are
  deployed on different origins.
- **Test command behavior**: Frontend `npm test` should run once and exit, not
  default to watch mode, so it is usable by agents and CI.
- **Lockfile churn**: Scaffold tasks should commit `uv.lock` and
  `package-lock.json` once generated, while ignoring environment and build
  folders.
- **Visual polish debt**: A sparse scaffold can accidentally feel like a generic
  starter template. The frontend shell should look like Tavola's actual commerce
  surface while being honest about unfinished features.

## Rollback Plan

- Because this scaffold is additive, rollback can remove the new `backend/` and
  `frontend/` directories plus any root documentation and ignore-file changes.
- If only one side causes trouble, keep the working side and revert the other
  app's directory independently.
- Keep generated lockfiles aligned with their project metadata; do not keep a
  lockfile after reverting its corresponding manifest.
