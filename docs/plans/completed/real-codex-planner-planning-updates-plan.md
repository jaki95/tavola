# Plan: Real Codex Planner Planning Updates

**Generated**: 2026-06-07
**Estimated Complexity**: Medium

## Overview

Replace the Planner UI's elapsed-time progress messages with backend-owned
**Planning updates**. A Planning update is a customer-visible progress entry
emitted during Planning. It is distinct from session status and runtime
availability.

Keep the existing planning-first flow:

- `POST /planner/sessions` returns a `planning` session quickly.
- The background runner completes the real Codex-backed planning work.
- The frontend polls `GET /planner/sessions/{id}` until the session reaches
  `needs_input`, `proposal_ready`, or `failed`.

Simplifying decisions:

- Use the existing polling session resource; do not add SSE/WebSocket.
- Keep update copy in Tavola language. Keep "powered by Codex" as heading
  attribution only.
- Persist update history in the API, but collapse the visible UI to the terminal
  follow-up, proposal, or failure experience when Planning resolves.
- Do not make lower-level Codex SDK notification streaming part of the first
  slice. Add honest lifecycle updates before/after blocking calls first.

## Prerequisites

- Preserve the planning-first lifecycle in
  `docs/adr/0002-planning-first-live-planner-sessions.md`.
- Keep Codex imports in `backend/src/tavola/infrastructure/`.
- Do not expose raw prompts, transcripts, tool arguments, credential paths,
  stack traces, or SDK traces in Planning updates.
- No fake runtime planner, alternate non-SDK model path, new state library, or
  push transport.

## Sprint 1: Backend Planning Updates

**Goal**: Planner sessions store and return real backend lifecycle updates while
the existing polling flow remains unchanged.

**Demo/Validation**:

- Creating a planner session returns an initial Planning update.
- Polling the session returns appended updates while status is still
  `planning`.
- Terminal states keep update history in the API without changing existing
  session status behavior.

### Task 1.1: Add Planning Updates To Sessions

- **Status**: Completed 2026-06-07. Added closed Planning update stages,
  immutable session update history, queued updates, follow-up queued updates,
  and locked repository append behavior.

- **Location**:
  - `backend/src/tavola/domain/planner.py`
  - `backend/src/tavola/application/planner.py`
  - `backend/src/tavola/infrastructure/planner_repository.py`
  - `backend/tests/test_planner_domain.py`
  - `backend/tests/test_planner_repository.py`
  - `backend/tests/test_planner_use_cases.py`
- **Description**: Add `PlanningUpdate` and `PlanningUpdateStage`, store
  `planning_updates` on `PlannerSession`, and add a thread-safe repository
  append method.
- **Dependencies**: None.
- **Acceptance Criteria**:
  - Update messages are non-blank, customer-safe strings.
  - Updates are append-only and ordered.
  - `CreatePlanningSession` records a `queued` update.
  - `SubmitPlannerFollowUp` records a new update when returning to Planning.
  - Planning sessions still cannot include a proposal, follow-up question, or
    validation errors.
- **Validation**:
  - `cd backend && UV_CACHE_DIR=../.uv-cache uv run pytest tests/test_planner_domain.py tests/test_planner_repository.py tests/test_planner_use_cases.py`

### Task 1.2: Publish Updates During Background Planning

- **Status**: Completed 2026-06-07. Background completion records started,
  validating, and terminal updates; Codex lifecycle timing maps sanitized
  connecting/planning events into session updates.

- **Location**:
  - `backend/src/tavola/application/planner.py`
  - `backend/src/tavola/api/routers/planner.py`
  - `backend/src/tavola/api/dependencies.py`
  - `backend/src/tavola/infrastructure/codex_planner/agent.py`
  - `backend/src/tavola/infrastructure/codex_planner/sdk_client.py`
  - `backend/tests/test_planner_api.py`
  - `backend/tests/test_codex_planner_adapter.py`
- **Description**: Pass a session-specific recorder into
  `CompletePlanningSession` and the Codex agent timing sink. Map only sanitized
  lifecycle events to closed-stage Planning updates.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - Background planning appends `started` before calling the agent.
  - Codex adapter emits honest `connecting` / `planning` updates before blocking
    SDK work where feasible.
  - Tavola validation appends `validating`.
  - Terminal paths append `ready`, `needs_input`, or `failed`.
  - Timing events may inform updates, but raw timing attributes and tool
    arguments are not exposed.
  - Disabled and busy behavior remains unchanged.
- **Validation**:
  - `cd backend && UV_CACHE_DIR=../.uv-cache uv run pytest tests/test_planner_api.py tests/test_codex_planner_adapter.py tests/test_planner_use_cases.py`

### Task 1.3: Expose Updates Through The Planner API

- **Status**: Completed 2026-06-07. Planner session responses now include
  additive `planning_updates` for create and poll calls.

- **Location**:
  - `backend/src/tavola/api/schemas/planner.py`
  - `backend/tests/test_planner_api.py`
- **Description**: Add `planning_updates` to `PlannerSessionResponse`.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - `POST /planner/sessions` includes the initial update.
  - `GET /planner/sessions/{id}` includes all accumulated updates.
  - Response shape is additive; existing status fields remain unchanged.
- **Validation**:
  - `cd backend && UV_CACHE_DIR=../.uv-cache uv run pytest tests/test_planner_api.py`

## Sprint 2: Frontend Rendering And Verification

**Goal**: Remove time-based fake progress from the Planner UI and render only
backend-provided Planning updates.

**Demo/Validation**:

- Planning copy changes only when polled session data changes.
- Long waits keep the latest real update visible without inventing later steps.
- Proposal-ready tab behavior still depends on `proposal_ready`, not updates.

### Task 2.1: Parse Planning Updates In The Frontend

- **Status**: Completed 2026-06-07. Added frontend Planning update stage/types,
  required API response parsing, invalid-shape rejection, and update-message
  sanitization through the planner text sanitizer.

- **Location**:
  - `frontend/src/types/planner.ts`
  - `frontend/src/api/planner.ts`
  - `frontend/src/api/planner.test.ts`
- **Description**: Add frontend types and response validation for
  `planning_updates`, sanitizing messages through the existing planner text
  sanitizer.
- **Dependencies**: Sprint 1 API contract.
- **Acceptance Criteria**:
  - Known stages parse successfully.
  - Invalid update shapes produce the existing invalid-response error.
  - Existing proposal and acceptance parsing remains unchanged.
- **Validation**:
  - `cd frontend && npm test -- planner`

### Task 2.2: Remove Elapsed-Time Progress State

- **Status**: Completed 2026-06-07. Removed elapsed-time state/interval from
  `usePlanner`; Planning UI state now exposes backend session updates only.

- **Location**:
  - `frontend/src/features/planner/usePlanner.ts`
  - `frontend/src/features/planner/usePlanner.test.ts`
- **Description**: Remove `planningStartedAtMs`, `planningElapsedMs`, and the
  elapsed-time interval. Derive visible Planning updates from the current
  session.
- **Dependencies**: Task 2.1.
- **Acceptance Criteria**:
  - Starting a request still enters `planning` immediately.
  - Polling updates replace the current session and expose new updates.
  - Tests no longer depend on elapsed-time thresholds.
  - Polling failure and stale prompt behavior remain unchanged.
- **Validation**:
  - `cd frontend && npm test -- usePlanner`

### Task 2.3: Render Backend Updates In PlannerWorkspace

- **Status**: Completed 2026-06-07. `PlannerWorkspace` renders latest backend
  Planning update in a polite live region, shows update history only during
  Planning, and collapses terminal states to follow-up/proposal/failure UI.

- **Location**:
  - `frontend/src/features/planner/PlannerWorkspace.tsx`
  - `frontend/src/features/planner/PlannerWorkspace.test.tsx`
  - `frontend/src/pages/HomePage.tsx`
  - `frontend/src/App.test.tsx`
  - `frontend/src/styles.css`
- **Description**: Replace `planningProgress(elapsedMs)` with a status surface
  driven by `session.planning_updates`.
- **Dependencies**: Task 2.2.
- **Acceptance Criteria**:
  - Latest Planning update is announced with `aria-live="polite"`.
  - Optional visible history renders only while status is `planning`.
  - Terminal states collapse to follow-up, proposal, or failure UI.
  - Top banner and proposal-ready indicator do not become progress dashboards.
- **Validation**:
  - `cd frontend && npm test -- PlannerWorkspace App`

### Task 2.4: Verify And Update Docs

- **Status**: Completed 2026-06-07. Updated planner docs from elapsed-time UX to
  backend-owned Planning updates; focused/full test suites, build, lint, and
  real browser checks completed. Browser typing-dependent follow-up/edit checks
  were blocked by the in-app browser clipboard integration and are reported in
  handoff.

- **Location**:
  - `docs/frontend-browser-approval-check.md`
  - `docs/demo-codex-planner.md`
  - `docs/plans/in_progress/real-codex-flow-e2e-testing-plan.md`
  - `backend/README.md`
- **Description**: Run focused checks, run the required browser approval check,
  and update docs that still describe time-based progress as intended UX.
- **Dependencies**: Tasks 2.1-2.3.
- **Acceptance Criteria**:
  - Focused backend and frontend planner tests pass.
  - Full suites pass or unrelated pre-existing failures are documented.
  - Browser approval covers planning, disabled, proposal-ready, failed/timeout,
    edit, add-to-basket, and replace-basket states, or marks unchecked items.
  - Docs describe backend-owned Planning updates and historical benchmark notes
    remain clearly labeled as historical.
- **Validation**:
  - `cd backend && UV_CACHE_DIR=../.uv-cache uv run pytest tests/test_planner_domain.py tests/test_planner_repository.py tests/test_planner_use_cases.py tests/test_planner_api.py tests/test_codex_planner_adapter.py`
  - `cd frontend && npm test -- planner`
  - `cd backend && UV_CACHE_DIR=../.uv-cache uv run pytest`
  - `cd frontend && npm test`
  - Follow `docs/frontend-browser-approval-check.md`.

## Optional Follow-Up

Evaluate lower-level `openai-codex` turn notifications only if the delivered
Planning updates are too sparse in real browser runs. Adoption criteria:

- Same final output and tool item data as the current `thread.run(...)` path.
- Timeout behavior remains equivalent.
- No raw notification payloads are persisted or shown to customers.
- Real smoke evidence shows meaningfully richer customer-safe updates.

## Testing Strategy

- Backend: domain invariants, repository append behavior, use-case lifecycle,
  API response shape, Codex timing/update mapping.
- Frontend: API parsing, hook polling behavior, PlannerWorkspace rendering,
  proposal-ready indicator behavior.
- Manual: required desktop browser approval for touched Planner states.

## Risks & Mitigations

- **Sparse real events**: Emit honest lifecycle updates first; defer SDK
  notification streaming until evidence says it is needed.
- **Leaky internals**: Use a closed stage enum and fixed customer-safe messages.
- **False precision**: Prefer modest copy such as "Checking Tavola's catalog."
- **Race conditions**: Keep repository mutation locked and updates immutable.
- **Accessibility noise**: Announce only the latest update in the live region.

## Rollback Plan

- Backend rollback: return an empty `planning_updates` list while preserving
  existing session status behavior.
- Frontend rollback: show one neutral backend-owned Planning message instead of
  elapsed-time phase advancement.
- Operational rollback: keep real Codex planner disabled through existing
  planner runtime configuration.
