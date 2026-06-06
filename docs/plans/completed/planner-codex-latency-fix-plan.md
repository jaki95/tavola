# Plan: Planner Codex Latency Fix

**Generated**: 2026-06-04
**Estimated Complexity**: High

## Overview

Reduce the real Codex-backed Planner end-to-end run time from the current
50-second-plus behavior to an ideal target below 10 seconds, with 30 seconds as
the acceptable upper benchmark. Tavola must continue to use the Codex SDK; this
plan does not introduce a fake runtime planner, direct Responses API fallback,
or any alternate model route outside the SDK.

The prior real-flow finding is clear: a sanitized live run for
`Vegetarian dinner for 4 around GBP 50` took about 50,481 ms total while Tavola
MCP tool handlers took about 2 ms. The fix should therefore focus on Codex SDK
turn setup, model/config selection, prompt/tool contract size, and user-facing
progress during unavoidable wait time.

Approach:

- Instrument the real SDK path enough to separate SDK startup, thread start,
  model turn time, MCP tool calls, repair retries, parsing, and Tavola
  validation.
- Benchmark several SDK-safe configurations and prompts against the same
  planner personas.
- Compress the Codex task so the model has fewer decisions and less prose to
  generate while preserving deterministic Tavola validation.
- Change the live Planner flow from a blocking submission to a planning session
  with customer-safe progress updates, so the UI has one stable lifecycle even
  when Codex latency varies.

Official OpenAI docs checked on 2026-06-04:

- `https://developers.openai.com/api/docs/models/gpt-5.2-codex`
- `https://developers.openai.com/api/docs/models/gpt-5.3-codex`
- `https://developers.openai.com/api/docs/models/codex-mini-latest`

Relevant notes:

- GPT-5.2-Codex and GPT-5.3-Codex are documented as optimized for agentic
  coding tasks and support reasoning effort settings.
- `codex-mini-latest` is documented as optimized for Codex CLI and faster/lower
  output cost, but the docs recommend a different API starting point for direct
  API use. Because Tavola must use the Codex SDK, model availability must be
  proven through the current SDK credential path rather than assumed from public
  API docs.

## Prerequisites

- Real Codex credentials available locally through the existing Tavola-supported
  credential path.
- No secrets, raw Codex transcripts, SDK traces, stack traces, or credential
  paths are committed or pasted into handoff notes.
- Backend dependencies are installed with `cd backend && uv sync`.
- Frontend dependencies are installed with `cd frontend && npm install`.
- The implementation continues to keep Codex imports in
  `backend/src/tavola/infrastructure/`.
- Normal tests must remain fake-agent based; real Codex benchmarks stay opt-in.

## Sprint 1: Reproduce And Measure

**Goal**: Turn the current "50+ seconds" complaint into stable timing evidence
that points at specific controllable causes.

**Demo/Validation**:

- One opt-in benchmark command reports per-phase timings without raw transcripts.
- A real browser run can be matched to backend timing data.
- Current behavior is preserved while measurement is added.

### Task 1.1: Add Sanitized Planner Timing Events

- **Location**:
  - `backend/src/tavola/infrastructure/codex_planner.py`
  - `backend/tests/test_codex_planner_adapter.py`
- **Description**: Add an optional timing sink or internal run metadata to the
  Codex SDK adapter. Capture only safe events: SDK client creation, thread
  start, turn run, detected tool names, repair attempt count, timeout, parse
  result, and total elapsed milliseconds.
- **Dependencies**: None.
- **Acceptance Criteria**:
  - Timing does not include prompts, final JSON, tool arguments, transcripts,
    credentials, stack traces, or customer request text.
  - Fake SDK tests can assert timing callbacks without real Codex.
  - Existing adapter behavior and public API response shapes are unchanged.
- **Validation**:
  - `cd backend && uv run pytest tests/test_codex_planner_adapter.py`

### Task 1.2: Add Opt-In Benchmark Smoke Command

- **Location**:
  - `backend/src/tavola/infrastructure/codex_planner_smoke.py`
  - `backend/README.md`
- **Description**: Extend the smoke command with `--benchmark` and
  `--repeat N`. Report status, total elapsed milliseconds, timing phases,
  selected model, timeout, retry count, and whether the result hit the 10-second
  or 30-second benchmark. Classify successful runs as `ideal`, `acceptable`, or
  `slow`. Keep proposal output optional and off by default in benchmark mode.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - Benchmark mode is opt-in and real-Codex only.
  - Output is safe to paste into handoff notes.
  - Repeated runs produce min/median/max totals.
  - Runs over 30 seconds are reported as `slow` benchmark misses, but exit zero
    if they still return a valid proposal before the technical timeout.
  - The command exits nonzero only for actual planner failure, timeout at the
    technical ceiling, malformed output, missing tool use, or configuration
    absence.
- **Validation**:
  - Fake/unit test for argument handling if feasible.
  - Manual opt-in run:
    `cd backend && TAVOLA_PLANNER_CODEX_ENABLED=true TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true uv run python -m tavola.infrastructure.codex_planner_smoke --benchmark --repeat 3 "Vegetarian dinner for 4 around GBP 50"`

### Task 1.3: Correlate Browser And Backend Timing

- **Location**:
  - `frontend/src/features/planner/usePlanner.ts`
  - `frontend/src/features/planner/PlannerWorkspace.tsx`
  - `frontend/src/features/planner/usePlanner.test.ts`
  - `frontend/src/features/planner/PlannerWorkspace.test.tsx`
- **Description**: Add frontend-side elapsed-time measurement for the planning
  request and use it only for tests/dev diagnostics or customer-safe progress
  copy. Do not expose SDK internals.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - UI tests can prove loading/progress copy changes over elapsed time.
  - Browser approval can record elapsed user-visible wait.
  - Customer-facing copy says what Tavola is doing, not Codex internals.
- **Validation**:
  - `cd frontend && npm test -- PlannerWorkspace usePlanner`

### Sprint 1 Implementation Note

- Added sanitized backend timing events for SDK client creation, thread start,
  turn run, detected tool names, parse result, repair attempts, timeout, and
  total elapsed time.
- Added opt-in benchmark smoke output with repeat runs, threshold
  classification, and min/median/max totals; proposal JSON remains off by
  default in benchmark mode.
- Added frontend elapsed-time tracking for pending planner requests and
  customer-safe progress copy that avoids Codex SDK internals.
- Real Codex benchmark on `gpt-5.5` for `Vegetarian dinner for 4 around GBP 50`
  produced three slow runs: one timeout at 60,004 ms and two valid proposals at
  51,976 ms and 53,332 ms.
- Browser approval was run against isolated ports `8011` and `5175` with real
  Codex enabled. The live UI showed the 0/5/15/30-second progress messages and
  then surfaced a customer-visible timeout failure for `Classic Italian dinner
  for 2`.

## Sprint 2: Shrink The Codex Turn

**Goal**: Reduce model reasoning time while preserving the bounded catalog,
tool-use, and deterministic validation contract.

**Demo/Validation**:

- The benchmark command compares baseline prompt/config against the optimized
  prompt/config.
- Happy-path real runs stay proposal-ready.
- Safety tests still reject missing tool use, malformed output, unknown SKUs,
  unsupported constraints, and invalid quantities.

### Task 2.1: Establish Supported SDK Model Matrix

- **Location**:
  - `backend/src/tavola/config/settings.py`
  - `backend/tests/test_settings.py`
  - `backend/README.md`
  - `docs/demo-codex-planner.md`
- **Description**: Reconcile the current model documentation drift:
  `Settings` defaults to `gpt-5.5`, while `backend/README.md` still says
  `gpt-5.2-codex`. Use the benchmark smoke to test only SDK-accepted model
  strings for the current credential path. Candidate model strings should
  include the current default, any supported current Codex model exposed to the
  credential path, and a faster/lower-effort SDK-supported option if available.
- **Dependencies**: Sprint 1.
- **Acceptance Criteria**:
  - Default model is documented consistently.
  - Unsupported model attempts fail safely and are not selected as defaults.
  - The plan does not assume API-doc model availability equals SDK credential
    availability.
  - Any model change is backed by benchmark data and proposal quality checks.
- **Validation**:
  - `cd backend && uv run pytest tests/test_settings.py`
  - Opt-in benchmark table added to handoff or demo docs without secrets.

### Task 2.2: Add SDK Config Hooks For Reasoning Effort If Supported

- **Location**:
  - `backend/src/tavola/infrastructure/codex_planner.py`
  - `backend/src/tavola/config/settings.py`
  - `backend/tests/test_codex_planner_adapter.py`
  - `backend/tests/test_settings.py`
- **Description**: Inspect the installed `openai-codex` SDK surface and add a
  Tavola setting for reasoning effort only if the SDK exposes a supported,
  typed way to pass it. Benchmark `low` first for this constrained planner task,
  then compare against the current default.
- **Dependencies**: Task 2.1.
- **Acceptance Criteria**:
  - No unsupported kwargs or speculative SDK fields are added.
  - Invalid setting values fail at settings construction.
  - Benchmark captures latency and proposal validity for each effort.
  - If the SDK does not expose reasoning effort, document that finding and skip
    the code hook.
- **Validation**:
  - `cd backend && uv run pytest tests/test_settings.py tests/test_codex_planner_adapter.py`
  - Opt-in benchmark run for each supported effort.

### Task 2.3: Replace The Defensive Prompt With A Short Contract

- **Location**:
  - `backend/src/tavola/infrastructure/codex_planner.py`
  - `backend/tests/test_codex_planner_adapter.py`
- **Description**: Rewrite `_build_planner_prompt` so it states the minimum
  Tavola contract: use package templates, search catalog, validate proposal,
  return one JSON object, ask for party size if missing, and do not invent
  products or prices. Remove repeated negative instructions and long-order
  commentary where tests prove the shorter contract is enough.
- **Dependencies**: Sprint 1.
- **Acceptance Criteria**:
  - Prompt is materially shorter than the current prompt.
  - Required tool names remain enforced in adapter code.
  - Final JSON contract remains explicit but compact.
  - Tests assert behavior-oriented clauses instead of brittle full wording.
- **Validation**:
  - `cd backend && uv run pytest tests/test_codex_planner_adapter.py tests/test_planner_use_cases.py`
  - Opt-in benchmark before/after prompt comparison.

### Task 2.4: Make MCP Tool Descriptions And Payloads More Decisive

- **Location**:
  - `backend/src/tavola/infrastructure/planner_mcp_server.py`
  - `backend/tests/test_planner_mcp_tools.py`
- **Description**: Reduce model search/refinement time by making tool outputs
  easier to act on. Consider adding compact template guidance, limiting
  `search_catalog` results, adding category/template hints, and returning a
  short "recommended_next_action" string that points Codex directly to
  validation. Keep full product data only where needed for proposal construction.
- **Dependencies**: Task 2.3.
- **Acceptance Criteria**:
  - Tool payloads are smaller or more structured for the same customer request.
  - `search_catalog` still returns enough fields to avoid routine
    `get_sku_detail` calls.
  - Validation still calculates authoritative totals.
  - Tool tests prove result limits and payload shape.
- **Validation**:
  - `cd backend && uv run pytest tests/test_planner_mcp_tools.py`
  - Opt-in benchmark checks number of search calls and total elapsed time.

### Task 2.5: Evaluate A Single Planning Tool Variant

- **Location**:
  - `backend/src/tavola/infrastructure/planner_mcp_server.py`
  - `backend/src/tavola/infrastructure/codex_planner.py`
  - `backend/tests/test_planner_mcp_tools.py`
  - `backend/tests/test_codex_planner_adapter.py`
- **Description**: Spike a consolidated `draft_validated_menu_proposal` MCP tool
  only if the previous tasks do not meet the 30-second benchmark. The tool would
  accept the customer request plus structured choices, run deterministic catalog
  validation, and return a validated payload. Codex still controls the planning
  turn through the SDK and MCP; Tavola still owns catalog and validation truth.
- **Dependencies**: Tasks 2.3 and 2.4.
- **Acceptance Criteria**:
  - The tool does not become a deterministic fake planner.
  - Codex still supplies customer-facing composition choices and rationales.
  - Adapter required-tool checks are updated intentionally.
  - Benchmark proves whether fewer tool decisions reduce total time.
- **Validation**:
  - `cd backend && uv run pytest tests/test_planner_mcp_tools.py tests/test_codex_planner_adapter.py tests/test_planner_use_cases.py`
  - Opt-in real benchmark against the same persona set.

### Task 2.6: Tighten Retry Policy For Demo Latency

- **Location**:
  - `backend/src/tavola/config/settings.py`
  - `backend/src/tavola/infrastructure/codex_planner.py`
  - `backend/tests/test_settings.py`
  - `backend/tests/test_codex_planner_adapter.py`
- **Description**: Set the real demo default to
  `TAVOLA_PLANNER_CODEX_MAX_RETRIES=0`. A repair turn can double user wait time,
  and planning-first UX gives the customer a safe failed state when malformed
  output occurs. Keep retries configurable for experiments and tests.
- **Dependencies**: Tasks 2.3 and 2.4.
- **Acceptance Criteria**:
  - Settings default `TAVOLA_PLANNER_CODEX_MAX_RETRIES` to `0` for the live
    demo path.
  - Adapter repair tests continue to pass by explicitly setting
    `max_retries=1`.
  - Retry defaults are documented.
  - Malformed-output failures remain customer-safe.
  - Progress and timeout copy never mention repair attempts or retries.
- **Validation**:
  - `cd backend && uv run pytest tests/test_settings.py tests/test_codex_planner_adapter.py`
  - Benchmark includes malformed-output or repair-observed run notes if seen.

### Sprint 2 Implementation Note

- Reconciled Tavola's real planner default model documentation around
  `gpt-5.5`; the stale `.env.example` `gpt-5.2-codex` reference was removed.
- Added `TAVOLA_PLANNER_CODEX_REASONING_EFFORT`, defaulting to `low`, because
  installed `openai-codex` 0.1.0b3 exposes a typed `Thread.run(effort=...)`
  hook. `sdk-default` omits the effort argument for benchmark comparisons.
- Compressed the planner prompt into a short contract that still requires
  package templates, catalog search, validation, party-size follow-up handling,
  no invented products or prices, and final JSON only.
- Made MCP tool outputs more decisive with bounded `search_catalog` results,
  result counts, and `recommended_next_action` guidance while preserving
  Tavola's authoritative validation totals.
- Set the live demo retry default to
  `TAVOLA_PLANNER_CODEX_MAX_RETRIES=0`; repair tests opt in with
  `max_retries=1`.
- Did not add the consolidated `draft_validated_menu_proposal` tool from
  Task 2.5 in this pass; that spike remains conditional on post-change
  benchmarks still missing the 30-second acceptable threshold.
- Real Codex benchmark on `gpt-5.5` with `low` reasoning effort for
  `Vegetarian dinner for 4 around GBP 50` produced three slow runs:
  two technical timeouts at 60,007 ms and 60,003 ms, and one valid proposal at
  57,368 ms. Summary: 1 successful run, 2 failed timeout runs, min 57,368 ms,
  median 60,003 ms, max 60,007 ms. This misses both the 10-second ideal and
  30-second acceptable benchmarks, so Task 2.5 remains a live candidate for the
  next latency pass.
- `codex-mini-latest` was checked through the same live SDK credential path.
  With `low` reasoning effort it failed before Tavola validation in 4,895 ms;
  with `sdk-default` reasoning effort it failed before Tavola validation in
  4,223 ms. Both runs were fast but returned `tool_failure` with no detected
  Tavola tool usage, so the mini model is not currently a viable default for
  Tavola's MCP-backed planner flow.
- `gpt-5.4-mini` was accepted by the same live SDK credential path and produced
  a valid proposal with required Tavola tool usage at 39,928 ms. This improves
  over `gpt-5.5` but still misses the 30-second acceptable benchmark.
- `gpt-5.3-codex-spark` was accepted by the same live SDK credential path but
  did not use Tavola tools. With `low` reasoning effort it failed with
  `missing_tool_use` at 17,975 ms; with `sdk-default` reasoning effort it failed
  with `missing_tool_use` at 35,557 ms. Spark is fast enough to be interesting,
  but not currently viable for Tavola's required MCP validation contract.

## Sprint 3: Add Planning-First User Experience

**Goal**: Make live planner submissions enter a planning session immediately,
then progress to a follow-up question, menu proposal, or failure while the
customer can keep browsing.

**Demo/Validation**:

- Submitting a planner request returns quickly with a planning session.
- The UI shows changing, customer-safe progress states while the backend work
  continues.
- The user can continue browsing the catalog while planning is in progress.
- The browser approval check covers planning, success, failure, and timeout.

### Task 3.1: Add Planning State To Planner Sessions

- **Location**:
  - `backend/src/tavola/domain/planner.py`
  - `backend/src/tavola/application/planner.py`
  - `backend/src/tavola/infrastructure/planner_repository.py`
  - `backend/tests/test_planner_domain.py`
  - `backend/tests/test_planner_repository.py`
  - `backend/tests/test_planner_use_cases.py`
- **Description**: Add a `planning` session status that can exist without a
  follow-up question, proposal, or validation error. Do not add server-side
  progress phases unless they can be proven from real backend events.
- **Dependencies**: None; benchmark evidence still informs timeout and progress
  thresholds.
- **Acceptance Criteria**:
  - Domain invariants allow `planning` but still require proposals for
    `proposal_ready` and errors for `failed`.
  - Repository saves and retrieves planning sessions.
  - Existing statuses keep their current behavior.
- **Validation**:
  - `cd backend && uv run pytest tests/test_planner_domain.py tests/test_planner_repository.py tests/test_planner_use_cases.py`

### Task 3.2: Split Session Creation From Planner Execution

- **Location**:
  - `backend/src/tavola/application/planner.py`
  - `backend/src/tavola/api/routers/planner.py`
  - `backend/src/tavola/api/schemas/planner.py`
  - `backend/tests/test_planner_api.py`
- **Description**: Change `POST /planner/sessions` so it creates a planning
  session quickly and dispatches the Codex run in a bounded background worker.
  The existing `GET /planner/sessions/{id}` route becomes the polling source for
  final state. Apply the same lifecycle to follow-up answers: submitting a
  follow-up answer updates the existing session back to `planning`, then polling
  observes `proposal_ready` or `failed`.
- **Dependencies**: Task 3.1.
- **Acceptance Criteria**:
  - Disabled Planner mode does not create a planning session; submission remains
    blocked by planner availability and backend disabled errors.
  - The create route returns in less than 1 second in tests with a blocking fake
    agent.
  - The follow-up answer route returns the existing session in `planning`
    quickly, then background completion updates the same session.
  - Background completion updates the same session to `needs_input`,
    `proposal_ready`, or `failed`.
  - Worker failures are mapped to existing customer-safe validation errors.
  - The demonstrator allows one live Codex planning task per backend process.
    Additional submissions while one is already planning return a customer-safe
    busy/unavailable error instead of queueing behind a slow run.
- **Validation**:
  - `cd backend && uv run pytest tests/test_planner_api.py tests/test_planner_use_cases.py`

### Task 3.3: Add Frontend Polling And Progress Copy

- **Location**:
  - `frontend/src/types/planner.ts`
  - `frontend/src/api/planner.ts`
  - `frontend/src/api/planner.test.ts`
  - `frontend/src/features/planner/usePlanner.ts`
  - `frontend/src/features/planner/usePlanner.test.ts`
  - `frontend/src/features/planner/PlannerWorkspace.tsx`
  - `frontend/src/features/planner/PlannerWorkspace.test.tsx`
- **Description**: Support the new `planning` status in the client and hook.
  After creating a session, poll `fetchPlannerSession` until the session reaches
  `needs_input`, `proposal_ready`, or `failed`. Show time-based customer
  guidance while planning, not claimed server-side progress phases. Use polling
  for v1 rather than SSE, WebSockets, or Codex streaming.
- **Dependencies**: Task 3.2.
- **Acceptance Criteria**:
  - User can keep browsing while the planner is planning.
  - Progress messages change over time and remain Tavola/customer language.
  - Customer UI does not show an explicit elapsed-time counter.
  - Progress copy does not say Tavola will ask the customer to try again.
  - Suggested time-based copy is: "Tavola is planning your menu.", "Checking the
    catalog and shaping a menu.", "Validating products and prices.", and
    "Still planning."
  - Polling runs about every 2 seconds while the visible session is in
    `planning`.
  - Polling stops on completion, failure, unmount, or new prompt submission.
  - Starting a new prompt stops polling the old session from the frontend; v1
    does not add a cancellation API for in-flight backend Codex work.
  - Long waits do not show raw tool names, model names, counts, retries, traces,
    or credentials.
- **Validation**:
  - `cd frontend && npm test -- planner`

### Task 3.4: Add Slow-State And Timeout Recovery UX

- **Location**:
  - `backend/src/tavola/config/settings.py`
  - `backend/src/tavola/application/planner.py`
  - `frontend/src/features/planner/usePlanner.ts`
  - `frontend/src/features/planner/PlannerWorkspace.tsx`
  - Relevant backend/frontend tests
- **Description**: Align the 30-second benchmark threshold, backend timeout,
  and frontend recovery copy. At 30 seconds, keep the session in `planning` and
  show neutral slow-state copy such as "Still planning." If the run exceeds the
  configured technical timeout, mark the session failed with a customer-safe
  message. The customer may submit a revised or new request, but Tavola should
  not phrase this as the planner asking them to try again. Timeout remains an
  internal agent error code, not a separate planner session status. Keep the
  live demo `TAVOLA_PLANNER_CODEX_TIMEOUT_SECONDS` at `60` unless later
  benchmarks prove a lower technical timeout is demo-safe.
- **Dependencies**: Tasks 3.2 and 3.3.
- **Acceptance Criteria**:
  - Thirty seconds is a benchmark and slow-state threshold, not an automatic
    session failure.
  - Backend README and settings tests document `60` as the live demo technical
    timeout while still documenting the 30-second acceptable benchmark.
  - Timed-out planner work is represented as a `failed` planner session with a
    customer-safe validation message.
  - Timeout copy does not say Tavola will ask the customer to try again.
  - The UI never spins indefinitely.
  - Retrying creates a new session and cancels/poll-stops the old frontend wait.
- **Validation**:
  - Backend fake-agent timeout tests.
  - Frontend fake-timer tests for progress and timeout copy.

### Sprint 3 Implementation Note

- Added `planning` as a valid planner session status with clean domain
  invariants: no follow-up question, proposal, or validation errors while work
  is in progress.
- Split API session creation from planner execution. `POST /planner/sessions`
  and follow-up answers now return quickly with the same session in `planning`,
  then a one-at-a-time in-process background runner completes the session as
  `needs_input`, `proposal_ready`, or `failed`.
- Disabled planner mode now returns an unavailable error before creating a
  session, and concurrent planner submissions return a customer-safe busy error
  instead of queueing behind a slow live run.
- Frontend planner types and API validation now accept `planning`; the planner
  hook polls `fetchPlannerSession` about every two seconds, stops polling on
  terminal states, unmount, or a newer prompt, and keeps progress copy in Tavola
  customer language.
- The Plan composer remains usable during planning so a customer can submit a
  revised request while the previous backend task finishes out of band.

## Sprint 4: Benchmark, Browser Approval, And Documentation

**Goal**: Prove the chosen fix in automated tests, opt-in real Codex benchmarks,
and desktop browser approval.

**Demo/Validation**:

- Optimized real Codex benchmark meets either the below-10-second ideal or the
  below-30-second acceptable benchmark, while demo runs may continue until the
  technical timeout.
- Browser UX is acceptable at the supported desktop viewport.
- Documentation reflects the real default configuration and the benchmark
  procedure.

### Task 4.1: Add A Real-Codex Benchmark Checklist

- **Location**:
  - `docs/demo-codex-planner.md`
  - `docs/plans/in_progress/real-codex-flow-e2e-testing-plan.md`
  - `backend/README.md`
- **Description**: Document the benchmark personas, command, thresholds, and
  handoff format. Include the known finding that MCP tools were effectively
  instant in the prior run.
- **Dependencies**: Sprints 1 and 2.
- **Acceptance Criteria**:
  - Docs state ideal target below 10 seconds and acceptable target below
    30 seconds.
  - Docs state that Codex SDK remains the only runtime path.
  - Docs include what to record and what not to record.
- **Validation**:
  - Manual doc review.

### Task 4.2: Run Backend Regression Checks

- **Location**: `backend/`
- **Description**: Run focused tests first, then the full backend suite once the
  selected implementation is stable.
- **Dependencies**: All backend implementation tasks.
- **Acceptance Criteria**:
  - Planner adapter, MCP tools, domain, use case, API, settings, and repository
    tests pass.
  - Full backend suite passes.
- **Validation**:
  - `cd backend && uv run pytest tests/test_codex_planner_adapter.py tests/test_planner_mcp_tools.py tests/test_planner_domain.py tests/test_planner_repository.py tests/test_planner_use_cases.py tests/test_planner_api.py tests/test_settings.py`
  - `cd backend && uv run pytest`
  - `cd backend && uv run ruff check .`
  - `cd backend && uv run ruff format --check .`

### Task 4.3: Run Frontend Regression Checks

- **Location**: `frontend/`
- **Description**: Verify planner client/hook/workspace tests plus the full
  frontend suite and build.
- **Dependencies**: All frontend implementation tasks.
- **Acceptance Criteria**:
  - Planner polling/progress tests pass.
  - Existing catalog, basket, checkout, and app tests pass.
  - Production build succeeds.
- **Validation**:
  - `cd frontend && npm test -- planner`
  - `cd frontend && npm test`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`

### Task 4.4: Run Desktop Browser Approval

- **Location**:
  - `docs/frontend-browser-approval-check.md`
  - Running backend and frontend
- **Description**: Use the Codex in-app Browser at the supported desktop
  viewport to verify planner availability, planning/progress, proposal-ready,
  needs-input, failed/timeout, edit, add-to-basket, and replace-basket states.
- **Dependencies**: Tasks 4.2 and 4.3.
- **Acceptance Criteria**:
  - Browser shows progress during a real Codex run.
  - Proposal-ready state renders title, notes, courses, product lines, total,
    edit controls, and accept actions.
  - Customer-facing copy avoids `SKU`, raw tool names, model names, SDK details,
    transcripts, stack traces, and secrets.
  - Catalog remains usable and visible around the Planner flow.
  - Browser console has no relevant errors.
- **Validation**:
  - Follow `docs/frontend-browser-approval-check.md`.
  - Record checked and unchecked states in handoff.

### Task 4.5: Record Final Benchmark Decision

- **Location**:
  - `docs/demo-codex-planner.md`
  - Final implementation handoff
- **Description**: Record the final benchmark table and decision:
  below 10 seconds achieved, below 30 seconds accepted, or above 30 seconds
  allowed only as a demo slow-path with improved Planning UX.
- **Dependencies**: Task 4.4.
- **Acceptance Criteria**:
  - Handoff includes min/median/max timing for at least three real runs of the
    primary persona.
  - Handoff names the selected SDK model/config without exposing credential
    details.
  - Runs above 30 seconds are recorded as benchmark misses even if the demo
    continues until the technical timeout and eventually returns a proposal.
- **Validation**:
  - Manual review of benchmark output and browser approval notes.

### Sprint 4 Implementation Note

- Added the real-Codex latency benchmark checklist, thresholds, safe handoff
  format, and prior MCP timing finding to `docs/demo-codex-planner.md`,
  `docs/plans/in_progress/real-codex-flow-e2e-testing-plan.md`, and `backend/README.md`.
- Reconciled the real-flow plan's malformed-output note with the current live
  demo default of zero repair retries.
- Backend focused planner/settings checks passed:
  `uv run pytest tests/test_codex_planner_adapter.py tests/test_planner_mcp_tools.py tests/test_planner_domain.py tests/test_planner_repository.py tests/test_planner_use_cases.py tests/test_planner_api.py tests/test_settings.py`.
- Full backend regression checks passed: `uv run pytest`,
  `uv run ruff check .`, and `uv run ruff format --check .`.
- Frontend planner and full regression checks passed: `npm test -- planner`,
  `npm test`, `npm run lint`, and `npm run build`.
- After explicit operator approval, the real Codex benchmark command ran for
  `Vegetarian dinner for 4 around GBP 50` with `gpt-5.5`, `low` reasoning
  effort, a 60-second timeout, and zero retries. Results: 2 valid proposals,
  1 technical timeout, all classified `slow`; min 36,493 ms, median 50,090 ms,
  max 60,007 ms. Final decision: above 30 seconds remains a demo slow-path, not
  an acceptable benchmark hit.
- A local Codex-disabled desktop browser pass ran on isolated ports `8011` and
  `5175`. Checked: Shop initial load, catalog visibility, persistent Basket,
  Plan disabled/unavailable state, Vite proxy-backed planner status requests,
  catalog API requests, basket API requests, Add-to-basket success, and absence
  of obvious runtime-detail leak text in visible copy.
- A real Codex browser approval pass then ran on the same isolated ports.
  Checked: live planner availability, progress copy at about 1/5/15/30 seconds,
  proposal-ready review, proposal quantity edit/revalidation, planner
  add-to-basket, live timeout/failure copy, Shop usability while planning, and
  persistent Basket visibility. Browser-observed proposal readiness for the
  successful run was about 65 seconds.
- The live pass exposed customer-facing internal wording (`SKU` in proposal
  notes and `Tavola tools` in a failed under-specified run). Fixed by changing
  the backend missing-tool-use message to `Tavola checks` and adding frontend
  customer-text sanitization at the API and display boundaries.
- Live browser states still unchecked because repeated real runs timed out or
  failed before reaching the needed state: needs-input follow-up completion,
  planner replace-basket with a fresh non-empty-basket proposal, and
  proposal-ready navigation badge.

## Testing Strategy

- Backend unit tests for settings, adapter prompt/config, MCP payloads, planner
  domain invariants, repository persistence, use cases, and API routes.
- Frontend tests for planner API response mapping, hook state transitions,
  polling cancellation, progress copy, timeout/failure copy, and workspace
  rendering.
- Opt-in real Codex benchmark runs for latency and proposal validity. These
  should never run in normal CI.
- Desktop browser approval for the real user flow through Vite and FastAPI.

Benchmark personas:

- `Vegetarian dinner for 4 around GBP 50`
- `Classic Italian dinner for 2`
- `Antipasti spread for a party`
- `Help me plan Sunday lunch` followed by a party-size answer
- One unsupported constraint prompt, such as a safety/allergy-like request that
  Tavola cannot honestly satisfy from current facets

## Potential Risks & Gotchas

- **SDK model availability may differ by credential path**: Public model docs
  are not enough. Mitigation: benchmark only model strings accepted by the
  installed SDK and active local credential path.
- **Reasoning-effort support may not be exposed by the Python Codex SDK**:
  Mitigation: inspect the SDK surface before adding settings; document and skip
  if unsupported.
- **Prompt compression could weaken safety**: Mitigation: keep adapter-required
  tool checks and Tavola validation; add tests for missing tools and invalid
  proposals before benchmark acceptance.
- **A consolidated MCP tool could accidentally become a deterministic planner**:
  Mitigation: only spike it after prompt/tool payload improvements fail, and
  keep Codex responsible for planning choices while Tavola validates.
- **Background execution introduces lifecycle complexity**: Mitigation: use a
  small bounded worker, explicit planning sessions, polling cancellation, and
  customer-safe failure states.
- **In-memory background sessions are demonstrator-only**: Mitigation: document
  that this is acceptable for Tavola's lightweight local demonstrator and not a
  production queue.
- **Progress copy can overpromise**: Mitigation: use generic Tavola language
  such as checking catalog, shaping menu, validating items, and preparing review.
- **Repair retries can double latency**: Mitigation: benchmark retry policy and
  consider defaulting to zero retries for the live demo if malformed output is
  rare after prompt changes.

## Rollback Plan

- Revert prompt/config/tool payload changes to the prior Codex adapter contract.
- Reset planner timeout and retry settings to previous defaults.
- If async planning causes regressions, restore synchronous
  `POST /planner/sessions` behavior while keeping sanitized benchmark tooling.
- Keep deterministic Tavola validation and fake-agent tests in place throughout
  rollback.
- Disable live planner mode with `TAVOLA_PLANNER_CODEX_ENABLED=false` if real
  Codex latency or availability prevents a reliable demo.
