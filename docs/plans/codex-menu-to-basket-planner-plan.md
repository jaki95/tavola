# Plan: Codex Menu-To-Basket Planner

**Generated**: 2026-06-04
**Estimated Complexity**: High

## Overview

Build Tavola's main AI feature as a Codex-powered menu-to-basket planner. A
customer enters a free-text meal or occasion request, Codex uses bounded catalog
and validation tools, and Tavola returns a reviewable proposal made only from
real products. Internally those products map to SKU identities, but customer
copy should never use the word SKU. The proposal can ask a follow-up question
when required information is missing, such as party size, but the first slice
should otherwise feel like a single guided planning flow rather than an
open-ended chat product.

Chosen integration: use the Python Codex SDK from the FastAPI backend, behind an
infrastructure adapter that implements an application-level planner port. This
fits the current Python backend, keeps the browser away from Codex transport and
auth details, and lets tests use a deterministic fake planner. Codex App Server
is not part of the v1 implementation; it remains a later upgrade option only if
Tavola needs rich streamed agent events, thread history controls, or a deeper
custom client integration.

The most impressive first UI is a planning workspace in the existing desktop
storefront: a compact prompt composer above a live proposal review surface with
course sections, product lines, rationale, totals, editable quantities, remove
controls, and explicit "Add to basket" or "Replace basket" acceptance actions.
This shows the AI's value while preserving Tavola's deterministic commerce
flow.

## Clarifying Decisions

- Use real Codex access for the demonstrator, not a fake-only planner.
- Keep Codex server-side; do not expose Codex SDK or App Server directly to the
  browser.
- Use the Python Codex SDK because the backend is Python and the SDK is intended
  for programmatic server-side Codex control.
- Treat "Codex API Server" as Codex App Server in current official terminology.
- Use Codex tools for catalog search, product detail lookup, package-template
  listing, and deterministic proposal validation.
- Persist planner sessions in memory for the lifetime of the backend process,
  like baskets and orders.
- Planner sessions store minimal customer text and normalized planning context,
  not full Codex/tool transcripts.
- Menu proposals include customer-facing planner notes, but Codex runtime
  metadata stays internal.
- Customer-facing planner UI and notes say product or item, never SKU.
- Let the customer choose whether an accepted proposal appends to the existing
  basket or replaces it.
- Codex may ask follow-up questions when necessary, but v1 should not become a
  fully general multi-turn assistant.
- Each planner session has at most one current menu proposal in v1; multiple
  simultaneous options/comparison is out of scope.
- Basket mutation happens only after customer acceptance and final deterministic
  validation.
- Accepting a menu proposal is terminal for that planner session's current
  proposal; duplicate accept attempts should be rejected.
- Runtime image generation, real payments, accounts, inventory reservation,
  recipe instructions, and exact serving guarantees remain out of scope.

## Documentation Notes

Official OpenAI/Codex documentation consulted on 2026-06-04:

- Codex SDK: server-side TypeScript and Python SDKs for programmatic Codex
  control; Python package is `openai-codex` and controls a local app-server.
- Codex App Server: rich-client JSON-RPC interface for authentication,
  conversation history, approvals, and streamed events; WebSocket transport is
  documented as experimental and unsupported.
- Codex MCP: Codex can connect to STDIO and HTTP MCP servers for tools and
  context.
- Codex environment/security notes: keep network access scoped, protect tokens,
  and avoid exposing local app-server transports remotely without auth.

## Prerequisites

- Existing catalog, basket, and checkout slices are implemented and passing.
- Backend dependencies are installed with `cd backend && uv sync`.
- Frontend dependencies are installed with `cd frontend && npm install`.
- Local development has working real Codex/OpenAI credentials.
- Codex CLI/runtime is available or installable through the Python Codex SDK's
  pinned runtime.
- A local Codex configuration path can be scoped for Tavola planner sessions so
  the planner sees only intended MCP tools and sandbox settings.

## Proposed Architecture

Add a planner feature slice with these layers:

- **Domain**: framework-free planner concepts such as planner session, package
  template, course proposal, proposal line, follow-up question, proposal status,
  and validation errors.
- **Application**: use cases for starting/continuing a planner session,
  validating proposals, and accepting a proposal into a basket.
- **Infrastructure**: in-memory planner repository, Codex planner adapter, and
  local MCP tool server for catalog/search/validation tools.
- **API**: planner routes and Pydantic request/response schemas.
- **Frontend**: planner workspace components, planner API client, state hook,
  proposal review UI, and basket acceptance controls.

Codex should never own pricing or basket truth. The application layer validates
all proposed product identities, quantities, totals, and acceptance modes before
returning a proposal or mutating a basket.

## Proposed API Shape

- `POST /api/planner/sessions`
  - Request: `{ "message": string }`
  - Starts a planner session from free text, independent of the current basket.
  - Returns a planner session with either `needs_input`, `proposal_ready`, or
    `failed` status.
- `POST /api/planner/sessions/{planner_session_id}/follow-up-answer`
  - Request: `{ "message": string }`
  - Answers a required follow-up question when the session is in `needs_input`.
  - Rejects answers once a menu proposal is ready or accepted.
- `POST /api/planner/sessions/{planner_session_id}/proposal/validate`
  - Request: customer-edited menu proposal lines and optional course grouping.
  - Revalidates product identity, quantities, course structure, totals, and
    menu proposal consistency without changing the basket.
- `POST /api/planner/sessions/{planner_session_id}/accept`
  - Request:
    `{ "basket_id": string, "mode": "append" | "replace", "lines": [...] }`
  - Final-validates the menu proposal and applies it to the basket according to
    the customer-selected mode.
  - Returns the updated basket and accepted meal-plan grouping metadata.
- `GET /api/planner/sessions/{planner_session_id}`
  - Returns current in-memory session state for refresh/retry support.

Planner responses should include:

- `planner_session_id`
- `status`
- `customer_request`
- optional `follow_up_question`
- optional `menu_proposal`
- optional `validation_errors`

Menu proposal responses should include:

- customer-readable title and explanation
- structured planner notes explaining party size, template choice, dietary
  constraints, catalog validation, server pricing, and assumptions
- party-size assumption when known or inferred
- package template used
- course sections
- product lines with quantity, unit label, price, line total, image ID, and concise
  rationale
- total, item count, and line count calculated by Tavola
- warnings for assumptions, substitutions, or removed lines

## Sprint 1: Planner Domain And Validation Core

**Goal**: Define planner concepts and deterministic validation without Codex,
HTTP, or React.

**Demo/Validation**:

- `cd backend && uv run pytest tests/test_planner_domain.py tests/test_planner_use_cases.py`
- A developer can validate a hand-written menu proposal and see invalid SKU,
  invalid quantity, duplicate line, unsupported course, and defensive
  availability errors deterministically.

### Task 1.1: Add Catalog Planner Data-Quality Tests

- **Location**: `backend/tests/test_catalog_seed.py`
- **Description**: Add seed catalog consistency tests that protect the planner's
  hard-constraint guarantees before Codex uses catalog tags for discovery.
- **Dependencies**: Existing seed catalog.
- **Acceptance Criteria**:
  - A `vegan` tag requires the vegan structured facet.
  - A `vegetarian` tag requires the vegetarian structured facet.
  - A `gluten-free` tag requires the gluten-free structured facet.
  - Alcohol-related tags or terms are consistent with `contains_alcohol`.
  - Hard constraint validation can trust structured facets over tags.
- **Validation**: `cd backend && uv run pytest tests/test_catalog_seed.py`

### Task 1.2: Add Planner Domain Model

- **Location**: `backend/src/tavola/domain/planner.py`,
  `backend/tests/test_planner_domain.py`
- **Description**: Add domain types for planner sessions, package templates,
  courses, proposal lines, course proposals, menu proposals, follow-up
  questions, proposal statuses, and validation errors.
- **Dependencies**: Task 1.1 and existing catalog and basket domain concepts.
- **Acceptance Criteria**:
  - Domain module imports no FastAPI, Pydantic, Codex, or infrastructure
    symbols.
  - Supported package templates are exactly Antipasto + Primo + Dessert,
    Antipasto + Primo, Primo + Dessert, Primo only, and Aperitivo.
  - Supported courses are Antipasto, Primo, Dessert, and Aperitivo.
  - Proposal lines require stable SKU IDs, positive integer quantities, and
    concise customer-facing rationale.
  - A proposal may represent a follow-up state without SKU lines.
- **Validation**: Domain tests for valid proposals, template/course validation,
  required text, quantity validation, and follow-up question state.

### Task 1.3: Add Menu Proposal Validation Service

- **Location**: `backend/src/tavola/application/planner.py`,
  `backend/tests/test_planner_use_cases.py`
- **Description**: Add deterministic menu proposal validation that resolves
  proposed SKU lines against the catalog, enforces basket quantity rules, merges
  duplicate SKUs, recalculates prices, and returns normalized proposal data.
- **Dependencies**: Task 1.2, existing `CatalogRepository`, basket quantity
  rules.
- **Acceptance Criteria**:
  - Unknown SKUs are rejected with typed validation errors.
  - Defensive catalog availability guards are enforced before any basket
    mutation if a fixture or future catalog marks a SKU unavailable.
  - Duplicate SKUs are merged or rejected according to one documented rule.
  - Totals are calculated from backend catalog prices.
  - Course grouping is preserved while SKU lines remain the source of pricing
    truth.
  - Validation can run on raw Codex output and on customer-edited proposals.
- **Validation**: Use-case tests for happy path, invalid SKU, invalid quantity,
  duplicate SKU handling, total recalculation, course grouping preservation, and
  defensive availability handling.

### Task 1.4: Add Planner Session Repository

- **Location**: `backend/src/tavola/application/planner.py`,
  `backend/src/tavola/infrastructure/planner_repository.py`,
  `backend/tests/test_planner_repository.py`
- **Description**: Define a planner repository protocol and implement an
  in-memory repository with deterministic ID generation for tests.
- **Dependencies**: Task 1.2.
- **Acceptance Criteria**:
  - Sessions can be created, saved, fetched, and updated by ID.
  - Missing session lookup returns `None` at the repository boundary.
  - Session state lasts for the process lifetime.
  - Tests can inject deterministic IDs.
- **Validation**: Repository tests for create/save/fetch, missing lookup, and
  deterministic ID behavior.

## Sprint 2: Codex Tooling And Adapter Proof

**Goal**: Prove the chosen Python Codex SDK adapter can run real Codex from the
backend with bounded Tavola catalog and validation tools before wiring the
customer-facing feature.

**Demo/Validation**:

- `cd backend && uv run pytest tests/test_codex_planner_adapter.py`
- With real credentials, a local smoke command starts a Codex-backed planner run
  against the seed catalog and produces a JSON proposal that passes Tavola
  validation.

### Task 2.1: Add Planner Agent Port And Fake Adapter

- **Location**: `backend/src/tavola/application/planner.py`,
  `backend/src/tavola/infrastructure/codex_planner.py`,
  `backend/tests/test_planner_use_cases.py`
- **Description**: Define a `MenuPlannerAgent` protocol used by application
  use cases. Add a deterministic fake adapter for tests and an empty Codex
  adapter shell for later tasks.
- **Dependencies**: Sprint 1.
- **Acceptance Criteria**:
  - Application use cases depend on `MenuPlannerAgent`, not the Codex SDK.
  - Fake adapter can return follow-up questions, valid proposals, and malformed
    proposals for tests.
  - Codex imports stay in infrastructure.
- **Validation**: Use-case tests cover planner states through the fake adapter.

### Task 2.2: Add Tavola Planner MCP Tool Server

- **Location**: `backend/src/tavola/infrastructure/planner_mcp_server.py`,
  `backend/tests/test_planner_mcp_tools.py`
- **Description**: Build a local STDIO MCP server exposing bounded planner
  tools: list package templates, search catalog, get SKU detail, and validate a
  proposal.
- **Dependencies**: Sprint 1.
- **Acceptance Criteria**:
  - Tools expose only customer-safe catalog and validation data.
  - Tool outputs include SKU IDs, names, categories, unit labels, tags,
    dietary facets, availability, and backend-calculated prices where useful.
  - Validation tool returns structured errors and normalized totals.
  - No tool can mutate a basket or checkout an order.
  - Tool instructions tell Codex that SKU validity, availability, quantity, and
    totals must come from Tavola tools.
- **Validation**: Tool tests call handlers directly without launching Codex.

### Task 2.3: Add Codex SDK Dependency And Configuration

- **Location**: `backend/pyproject.toml`, `backend/.env.example`,
  `backend/src/tavola/config/settings.py`, `backend/tests/test_settings.py`,
  `backend/README.md`
- **Description**: Add `openai-codex` and planner settings for enabling real
  Codex runs, selecting model/sandbox behavior, and configuring a planner
  timeout.
- **Dependencies**: Task 2.1.
- **Acceptance Criteria**:
  - Real Codex is configurable through environment/settings.
  - Tests can disable real Codex and use the fake adapter.
  - Credentials are documented but not committed.
  - Planner timeouts and max retry counts are configurable.
  - Default sandbox for Codex planner runs is read-only unless the adapter
    spike proves a stricter/different setting is required for MCP.
- **Validation**: Settings tests for defaults, environment overrides, and
  missing credential behavior.

### Task 2.4: Prove Python Codex SDK Tool Wiring

- **Location**: `backend/src/tavola/infrastructure/codex_planner.py`,
  `backend/tests/test_codex_planner_adapter.py`, `backend/README.md`
- **Description**: Implement a narrow real Codex adapter smoke path that starts
  a Codex thread through the Python SDK, configures the Tavola MCP tool server,
  asks for one menu proposal, parses the final JSON, and runs deterministic
  validation.
- **Dependencies**: Tasks 2.2 and 2.3.
- **Acceptance Criteria**:
  - Adapter can run against real Codex locally when credentials are present.
  - Adapter captures enough run metadata for debugging without logging secrets
    or excessive prompt content.
  - Malformed JSON, missing tool use, tool failures, and timeout errors map to
    typed application errors.
  - The proof documents the required backend-owned SDK configuration for local
    catalog and validation tools.
- **Validation**: Unit tests with a fake SDK client plus an opt-in real Codex
  smoke command documented in `backend/README.md`.

## Sprint 3: Planner Application And API

**Goal**: Expose planner sessions, follow-ups, proposal validation, and basket
acceptance through stable backend APIs.

**Demo/Validation**:

- `cd backend && uv run pytest tests/test_planner_api.py tests/test_planner_use_cases.py`
- A client can start a planner session, answer a follow-up if needed, receive a
  validated proposal, edit quantities, revalidate, and accept it into a basket.

### Task 3.1: Add Start And Follow-Up Answer Planner Use Cases

- **Location**: `backend/src/tavola/application/planner.py`,
  `backend/tests/test_planner_use_cases.py`
- **Description**: Add use cases to start a planner session from free text and
  answer a required follow-up question before a menu proposal exists.
- **Dependencies**: Sprints 1 and 2.
- **Acceptance Criteria**:
  - Empty prompt text is rejected.
  - Sessions save the original customer request and subsequent follow-up
    answers.
  - Follow-up answers are accepted only while the session is in `needs_input`.
  - Codex output is normalized into either `needs_input`, `proposal_ready`, or
    `failed`.
  - Proposal-ready responses include deterministic validation results and
    server-calculated totals.
  - Application errors remain typed and API-mappable.
- **Validation**: Use-case tests for successful proposal, follow-up needed,
  follow-up completion, rejected follow-up after proposal readiness, failed
  planner run, invalid Codex output, and missing session.

### Task 3.2: Add Proposal Revalidation Use Case

- **Location**: `backend/src/tavola/application/planner.py`,
  `backend/tests/test_planner_use_cases.py`
- **Description**: Allow customer-edited proposal lines to be revalidated before
  acceptance.
- **Dependencies**: Task 3.1.
- **Acceptance Criteria**:
  - Edited quantities and removed lines are validated deterministically.
  - Totals are recalculated from current catalog prices.
  - Planner notes are refreshed for the edited menu proposal.
  - Empty proposal acceptance is rejected.
  - Course sections remain coherent after line removal.
- **Validation**: Use-case tests for edited quantity, removed line, empty
  proposal, stale SKU, and total recalculation.

### Task 3.3: Add Proposal Acceptance Use Case

- **Location**: `backend/src/tavola/application/planner.py`,
  `backend/src/tavola/application/basket.py`,
  `backend/src/tavola/domain/basket.py`,
  `backend/tests/test_planner_use_cases.py`,
  `backend/tests/test_basket_domain.py`
- **Description**: Apply a final validated proposal to a basket in `append` or
  `replace` mode.
- **Dependencies**: Task 3.2.
- **Acceptance Criteria**:
  - `append` adds/merges proposal lines into the existing basket.
  - `replace` clears current basket lines and applies proposal lines.
  - Final validation runs immediately before mutation.
  - Duplicate acceptance of an already accepted proposal is rejected.
  - Quantity maximums and availability rules are enforced through existing
    basket/catalog rules.
  - Accepted meal-plan grouping metadata is returned for display but does not
    change pricing truth.
  - Grouping metadata remains coherent after basket edits by dropping empty
    courses or the whole grouping when all grouped products are removed.
- **Validation**: Use-case tests for append, replace, quantity merge limits,
  missing basket, accepted grouping metadata, and defensive availability
  handling.

### Task 3.4: Add Planner API Schemas

- **Location**: `backend/src/tavola/api/schemas/planner.py`,
  `backend/tests/test_planner_api.py`
- **Description**: Add Pydantic request/response models for planner sessions,
  follow-up answers, proposals, course sections, proposal lines, validation
  errors, and acceptance requests.
- **Dependencies**: Tasks 3.1 to 3.3.
- **Acceptance Criteria**:
  - Request schemas reject blank message text, blank basket IDs where required,
    invalid acceptance modes, and invalid quantities.
  - Response schemas expose customer-safe planner data only.
  - API response line shape is close to basket/catalog response line shapes for
    frontend reuse.
  - Planner notes include a note type, source, and customer-facing message.
- **Validation**: API schema tests through FastAPI request validation and exact
  response shape assertions.

### Task 3.5: Add Planner Router And Dependency Wiring

- **Location**: `backend/src/tavola/api/routers/planner.py`,
  `backend/src/tavola/api/dependencies.py`, `backend/src/tavola/api/main.py`,
  `backend/tests/test_planner_api.py`
- **Description**: Add planner routes and wire planner repository, Codex/fake
  adapter, catalog repository, and basket repository through dependencies.
- **Dependencies**: Task 3.4.
- **Acceptance Criteria**:
  - Routes follow existing `/api/...` conventions.
  - Tests can override the planner agent dependency with a fake.
  - Missing sessions and baskets return `404`.
  - Validation errors return structured `422` details.
  - Planner failures return user-safe error messages and retain debug details
    only in server-side logs or internal fields.
- **Validation**: API tests for start, continue, validate, accept append,
  accept replace, missing session, missing basket, and validation errors.

## Sprint 4: Planner Workspace Frontend

**Goal**: Add an impressive desktop planner experience that reviews proposals
before basket mutation.

**Demo/Validation**:

- `cd frontend && npm test`
- `cd frontend && npm run lint`
- With backend and frontend running, a customer can enter a meal request,
  answer a follow-up, review a proposal, edit/remove lines, and choose append or
  replace basket.

### Task 4.1: Add Planner Types And API Client

- **Location**: `frontend/src/types/planner.ts`,
  `frontend/src/api/planner.ts`, `frontend/src/api/planner.test.ts`
- **Description**: Add frontend types and client functions for planner session
  creation, follow-up messages, proposal validation, session fetch, and proposal
  acceptance.
- **Dependencies**: Sprint 3 API shape.
- **Acceptance Criteria**:
  - Client maps transport errors into existing API result conventions.
  - Types match backend response fields.
  - Tests cover success and error mapping for each endpoint.
- **Validation**: Frontend API client tests.

### Task 4.2: Add Planner State Hook

- **Location**: `frontend/src/features/planner/usePlanner.ts`,
  `frontend/src/features/planner/usePlanner.test.ts`
- **Description**: Add a hook that owns planner session state, prompt submit,
  follow-up submit, proposal editing, validation, and acceptance.
- **Dependencies**: Task 4.1.
- **Acceptance Criteria**:
  - Loading, empty, needs-input, proposal-ready, validation-error, accept
    pending, success, and failure states are explicit.
  - Proposal edits are local until revalidated or accepted.
  - The hook tracks one current menu proposal per planner session.
  - Customer-facing error text uses product/item language and never says SKU.
  - Accept actions call the selected `append` or `replace` mode.
  - Basket returned by acceptance can update the existing `useBasket` state.
- **Validation**: Hook tests for state transitions and API calls.

### Task 4.3: Add Planner Workspace Component

- **Location**: `frontend/src/features/planner/PlannerWorkspace.tsx`,
  `frontend/src/features/planner/PlannerWorkspace.test.tsx`
- **Description**: Build the desktop planner workspace with prompt composer,
  follow-up question state, proposal courses, editable line quantities, remove
  controls, totals, warnings, and acceptance buttons.
- **Dependencies**: Task 4.2.
- **Acceptance Criteria**:
  - Prompt entry is a textarea with a clear submit button.
  - Planner panel includes a small "powered by Codex" attribution.
  - Follow-up question state keeps the original request visible.
  - Proposal lines show product name, unit label, quantity, price, rationale, and
    validation state.
  - Proposal-level planner notes are shown separately from per-line product
    rationale.
  - Customers can remove lines and adjust quantities before acceptance.
  - Customers cannot rename courses or move products between courses in v1.
  - Customers can choose "Add to basket" or "Replace basket".
  - Replace basket requires lightweight confirmation when the current basket is
    non-empty.
  - UI is accessible by keyboard and uses semantic controls.
  - No mobile-specific layout work is introduced.
- **Validation**: Component tests for prompt submission, follow-up answer,
  quantity edit, remove line, append accept, replace accept, and error states.

### Task 4.4: Compose Planner Into Home Page

- **Location**: `frontend/src/pages/HomePage.tsx`,
  `frontend/src/App.test.tsx`, `frontend/src/styles.css`
- **Description**: Add the planner workspace to the existing storefront without
  disrupting catalog, basket, or checkout flows.
- **Dependencies**: Task 4.3.
- **Acceptance Criteria**:
  - Planner appears as a first-class workspace above or beside catalog browsing
    in the desktop storefront.
  - Basket updates after accepted proposals without a full page reload.
  - Existing catalog add-to-basket and checkout flows still work.
  - Visual design stays consistent with Tavola's current restrained deli
    storefront style.
- **Validation**: App/page tests for integrated planner and basket update.

## Sprint 5: Real Codex Hardening And Browser Approval

**Goal**: Make the real-Codex planner reliable enough for a demonstrator and
verify the full browser workflow.

**Demo/Validation**:

- Backend and frontend run together through the Vite proxy.
- Browser approval check covers loading, empty, follow-up, proposal, validation
  error, accept append, accept replace, and success states.

### Task 5.1: Add Prompt And Output Contract Hardening

- **Location**: `backend/src/tavola/infrastructure/codex_planner.py`,
  `backend/tests/test_codex_planner_adapter.py`
- **Description**: Tighten Codex instructions, JSON output parsing, retry
  behavior, and failure handling.
- **Dependencies**: Sprints 2 and 3.
- **Acceptance Criteria**:
  - Codex is instructed to use Tavola tools before proposing SKUs.
  - Codex final output must match a documented JSON contract.
  - Adapter retries once for malformed output with a repair prompt.
  - Adapter returns safe fallback errors when real Codex fails.
  - Logs omit credentials and avoid dumping excessive customer prompt text.
- **Validation**: Adapter tests for valid output, malformed JSON repair,
  validation failure repair, timeout, and safe error mapping.

### Task 5.2: Add Planner Observability And Demo Controls

- **Location**: `backend/src/tavola/config/settings.py`,
  `backend/src/tavola/application/planner.py`,
  `backend/README.md`, `frontend/src/features/planner/PlannerWorkspace.tsx`
- **Description**: Add practical demo controls such as planner enabled/disabled
  setting, real/fake planner mode visibility, and concise run summary.
- **Dependencies**: Sprint 4.
- **Acceptance Criteria**:
  - Missing credentials produce a clear disabled/error state.
  - Demo operator can tell whether fake or real planner mode is active.
  - User-facing copy does not expose internal SDK, token, or stack details.
- **Validation**: Settings tests, API tests for disabled planner, frontend tests
  for disabled state.

### Task 5.3: Run Full Verification

- **Location**: `docs/frontend-browser-approval-check.md`,
  `docs/scaffold-smoke-check.md`
- **Description**: Run backend tests, frontend tests/lint, production build, and
  browser approval for the complete planner flow.
- **Dependencies**: Tasks 5.1 and 5.2.
- **Acceptance Criteria**:
  - Backend tests pass.
  - Frontend tests and lint pass.
  - Production build passes.
  - Browser approval check records tested planner states and any unchecked
    states.
  - Scaffold smoke check is run if dependency/config changes require it.
- **Validation**:
  - `cd backend && uv run pytest`
  - `cd backend && uv run ruff check .`
  - `cd backend && uv run ruff format --check .`
  - `cd frontend && npm test`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`
  - Manual/in-app browser verification with backend and frontend running.

### Task 5.4: Add Codex Planner Demo Guide

- **Location**: `docs/demo-codex-planner.md`, `backend/README.md`,
  `frontend/README.md`
- **Description**: Document how to run and present the Codex-powered planner
  without exposing interview-specific context. Include required credential
  setup, backend/frontend commands, the "powered by Codex" attribution, and a
  small set of demo personas with sample prompts and expected trustworthy
  planner notes.
- **Dependencies**: Tasks 5.1 to 5.3.
- **Acceptance Criteria**:
  - Demo guide includes the Vegetarian dinner host persona with a prompt such as
    "Vegetarian dinner for 4 around £50".
  - Demo guide includes the Aperitivo organiser persona with a prompt such as
    "Aperitivo for 6 with drinks".
  - Demo guide includes the optional Under-specified family lunch persona with a
    prompt such as "Help me plan Sunday lunch" to show follow-up behavior.
  - Each persona includes a sample prompt, expected follow-up behavior if any,
    expected menu proposal shape, and expected planner notes.
  - Demo guide explains that customer-facing copy says product/item rather than
    SKU.
  - README files link to the demo guide where useful.
- **Validation**: Manual review of the guide against the browser-verified
  planner flow.

## Testing Strategy

- Domain tests cover planner invariants, package templates, proposal shape, and
  quantity rules.
- Application tests cover fake planner flows, deterministic validation, proposal
  revalidation, and basket acceptance.
- Infrastructure tests cover in-memory repositories, MCP tool handlers, Codex
  adapter parsing, timeout handling, and fake SDK behavior.
- API tests cover request validation, response shapes, typed errors, dependency
  overrides, and acceptance modes.
- Frontend tests cover planner API mapping, hook state transitions, proposal
  editing, follow-up handling, accept append, accept replace, and error states.
- Real Codex smoke testing is opt-in so normal CI/local test runs remain fast
  and deterministic.
- Browser approval verifies the changed desktop workflow end to end with
  loading, empty, follow-up, proposal-ready, validation error, and success
  states.

## Potential Risks & Gotchas

- Python Codex SDK tool wiring needs to be proven in Tavola's backend context.
  Mitigation: keep the integration proof early in Sprint 2 and preserve the
  `MenuPlannerAgent` port so SDK configuration details stay in infrastructure.
- Codex App Server WebSocket transport is documented as experimental and
  unsupported. Mitigation: do not expose it to the browser in v1; reserve App
  Server for a later richer-client upgrade, not the first planner slice.
- Codex is a software-development agent, so a customer meal planner must be
  heavily bounded. Mitigation: use catalog-only tools, deterministic validation,
  strict JSON output, and no direct basket mutation.
- Real Codex latency may make the UI feel slow. Mitigation: explicit pending
  states, timeout handling, and a compact run summary; defer streaming UI until
  after the first working slice.
- AI output may invent SKUs or serving guarantees. Mitigation: reject unknown
  SKUs, expose assumptions, and avoid exact serving promises.
- Proposal acceptance can conflict with current basket quantities. Mitigation:
  final-validate immediately before mutation and surface quantity-limit errors.
- In-memory sessions disappear on backend restart. Mitigation: communicate this
  as acceptable demonstrator behavior, matching baskets and orders.
- Customer prompts can contain sensitive text. Mitigation: avoid unnecessary
  logging and keep run summaries concise.
- MCP tools could accidentally expose too much internal data. Mitigation: tool
  outputs are customer-safe and mutation-free.
- Frontend proposal edits can drift from server state. Mitigation: revalidate
  before acceptance and replace local proposal state with the normalized server
  response.

## Rollback Plan

- Disable the planner with a backend setting if real Codex integration is
  unstable.
- Remove planner route registration from `backend/src/tavola/api/main.py` to
  hide the API while keeping implemented code for later repair.
- Remove `PlannerWorkspace` composition from `frontend/src/pages/HomePage.tsx`
  to return to catalog/basket/checkout only.
- Keep basket and checkout APIs unchanged so ordinary commerce remains
  unaffected.
- If `openai-codex` causes dependency issues, revert the dependency/config tasks
  while preserving domain/application planner tests that use the fake adapter.
