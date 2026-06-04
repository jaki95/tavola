# Plan: Basket Creation And Editing

**Generated**: 2026-06-04
**Estimated Complexity**: Medium

## Overview

Build Tavola's second product feature as a small vertical slice: customers can
create an anonymous backend-owned basket, add available catalog SKUs from both
catalog cards and product detail, edit quantities, remove lines, and see
server-calculated totals in a persistent basket surface.

The basket remains deliberately lightweight for the demonstrator. It is stored
in memory on the backend, identified by a generated basket ID, and references
SKUs as the source of catalog identity, availability, unit labels, and pricing.
The frontend stores only the current `basket_id` in `localStorage`; basket
contents are always fetched or mutated through the backend. If a backend restart
causes the saved basket ID to disappear, the frontend creates a fresh empty
basket and replaces the stored ID.

## Clarifying Decisions

- Add-to-basket actions appear on both catalog cards and product detail.
- The basket UI is persistent on the main catalog experience, not hidden behind
  a separate route for this slice.
- The frontend stores only `basket_id` in `localStorage`; it does not cache
  basket contents.
- Adding an SKU already in the basket merges into the existing line by
  increasing quantity.
- Quantity editing supports both stepper buttons and direct numeric input.
- Quantity above the per-line maximum of 10 is rejected with a user-visible
  backend validation error.
- Removing the last line keeps the same empty basket.
- The plan includes basket API response and mutation shape needed by future
  checkout.
- Basket business-rule validation failures use HTTP `422`; missing addressed
  resources such as basket ID or line SKU in the URL use HTTP `404`.
- `PATCH /lines/{sku_id}` edits an existing line only; it does not create a line.
- A basket ID is an opaque generated identifier, not a meaningful customer or
  order number.
- `item_count` is the sum of basket line quantities; `line_count` is the number
  of unique SKU lines.
- The persistent basket should be created when the catalog page loads, not only
  when the first product is added, so the visible basket surface has one
  backend-owned current basket from the beginning of the workflow.

## Prerequisites

- Existing catalog browsing slice is implemented and passing.
- Backend dependencies are installed with `cd backend && uv sync`.
- Frontend dependencies are installed with `cd frontend && npm install`.
- No new external libraries are expected; use FastAPI, Pydantic, React,
  TypeScript, and Vitest already present in the repository.

## Proposed API Shape

- `POST /api/baskets`
  - Creates a new empty basket.
  - Response: `BasketResponse`.
- `GET /api/baskets/{basket_id}`
  - Returns an existing basket.
  - Missing basket returns `404`.
- `POST /api/baskets/{basket_id}/lines`
  - Request: `{ "sku_id": string, "quantity": number }`.
  - Adds a new SKU line or merges into the existing line.
  - Quantity defaults should stay explicit in frontend calls; do not rely on a
    hidden API default for the first slice.
  - Missing basket returns `404`.
  - Missing SKU, unavailable SKU, non-positive quantity, or merged quantity over
    10 returns a `422` validation error.
- `PATCH /api/baskets/{basket_id}/lines/{sku_id}`
  - Request: `{ "quantity": number }`.
  - Sets the exact line quantity.
  - Does not create a missing line.
  - Missing basket or missing line returns `404`.
  - Non-positive quantity or quantity over 10 returns a `422` validation error.
- `DELETE /api/baskets/{basket_id}/lines/{sku_id}`
  - Removes a line and returns the updated basket.
  - Removing the final line returns the same basket with an empty `lines` list.
  - Missing basket or missing line returns `404`.

`BasketResponse` should include:

- `basket_id`
- `lines`
- `total_minor`
- `currency`
- `item_count`
- `line_count`

`item_count` is the sum of all line quantities. `line_count` is the number of
unique SKU lines.

Each line should include:

- `sku_id`
- `name`
- `category_id`
- `category_label`
- `unit_label`
- `quantity`
- `unit_price_minor`
- `line_total_minor`
- `currency`
- `image_id`

## Sprint 1: Basket Domain And Application Use Cases

**Goal**: Add framework-free basket rules and use cases that can be tested
without HTTP or React.

**Demo/Validation**:

- `cd backend && uv run pytest tests/test_basket_domain.py tests/test_basket_use_cases.py`
- A developer can create a basket, add an available SKU, merge quantities, edit
  quantity, remove the line, and inspect backend-calculated totals.

### Task 1.1: Add Basket Domain Model

- **Location**: `backend/src/tavola/domain/basket.py`,
  `backend/tests/test_basket_domain.py`
- **Description**: Add immutable or carefully encapsulated domain types for
  `BasketId`, `BasketLine`, and `Basket`. Enforce SKU line quantity invariants
  and total calculation from catalog prices.
- **Dependencies**: Existing catalog domain model.
- **Acceptance Criteria**:
  - Domain module imports no FastAPI or Pydantic symbols.
  - Basket IDs are non-empty stable identifiers.
  - Basket lines reference catalog `CatalogSku` values or a domain-safe snapshot
    derived from them.
  - Quantity is a positive integer and cannot exceed `MAX_BASKET_LINE_QUANTITY`
    of 10.
  - Adding an existing SKU merges quantity into one line.
  - Merged quantity over 10 raises a clear domain validation error.
  - Setting line quantity replaces the exact quantity.
  - Removing the final line keeps a valid empty basket.
  - Basket totals are calculated from line unit prices and quantities.
- **Validation**: Domain unit tests for empty basket, add, merge, set quantity,
  remove, total calculation, invalid quantity, and max quantity rejection.

### Task 1.2: Add Basket Repository Protocol And In-Memory Adapter

- **Location**: `backend/src/tavola/application/basket.py`,
  `backend/src/tavola/infrastructure/basket_repository.py`,
  `backend/tests/test_basket_repository.py`
- **Description**: Define an application-facing `BasketRepository` protocol and
  implement an in-memory adapter for anonymous baskets.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - Application code depends on a protocol, not the concrete in-memory store.
  - Repository can create, save, and fetch baskets by ID.
  - Missing basket lookup returns `None`.
  - The in-memory repository preserves basket state across requests for the
    lifetime of the FastAPI process.
  - Basket ID generation is explicit and replaceable in tests.
- **Validation**: Repository tests for create, fetch, save, missing fetch, and
  deterministic test ID generation.

### Task 1.3: Add Basket Use Cases

- **Location**: `backend/src/tavola/application/basket.py`,
  `backend/tests/test_basket_use_cases.py`
- **Description**: Add use cases for `CreateBasket`, `GetBasket`, `AddBasketLine`,
  `SetBasketLineQuantity`, and `RemoveBasketLine`. Coordinate basket repository
  persistence with catalog SKU lookup and availability checks.
- **Dependencies**: Tasks 1.1, 1.2 and existing `CatalogRepository`.
- **Acceptance Criteria**:
  - Creating a basket returns an empty persisted basket.
  - Getting a known basket returns the current basket.
  - Getting an unknown basket returns a predictable not-found result.
  - Adding a line validates basket existence, SKU existence, SKU availability,
    positive quantity, and max quantity.
  - Adding a duplicate SKU merges into the existing line.
  - Setting quantity validates basket existence, line existence, positive
    quantity, and max quantity.
  - Removing a line validates basket existence and line existence.
  - Use cases expose typed application errors that the API can map to HTTP
    responses without leaking domain exception strings directly.
- **Validation**: Use-case tests for happy paths and each validation/not-found
  branch.

## Sprint 2: Basket API Contract

**Goal**: Expose basket creation and editing through stable HTTP endpoints while
keeping domain rules outside the transport layer.

**Demo/Validation**:

- `cd backend && uv run pytest tests/test_basket_api.py tests/test_basket_use_cases.py`
- `POST /api/baskets` returns an empty basket.
- `POST /api/baskets/{basket_id}/lines` adds or merges an available SKU.
- `PATCH /api/baskets/{basket_id}/lines/{sku_id}` edits quantity.
- `DELETE /api/baskets/{basket_id}/lines/{sku_id}` removes a line and keeps the
  basket.

**Progress**: Completed on 2026-06-04.

- Added basket API schemas, router, and dependency wiring.
- Added process-lifetime in-memory basket repository dependency for API requests.
- Added API tests for response shapes, persisted fetch/edit behavior, and
  application error to HTTP response mapping.
- Fixed blank/whitespace SKU IDs to fail at the Pydantic request boundary.
- Validation run: `cd backend && uv run pytest tests/test_basket_api.py tests/test_basket_use_cases.py`.

### Task 2.1: Add Basket API Schemas

**Status**: Completed on 2026-06-04.

- **Location**: `backend/src/tavola/api/schemas/basket.py`,
  `backend/tests/test_basket_api.py`
- **Description**: Add Pydantic request and response models for basket creation,
  line mutation, line display, totals, and validation errors.
- **Dependencies**: Sprint 1.
- **Acceptance Criteria**:
  - `BasketLineResponse` includes SKU identity, customer-facing catalog fields,
    quantity, unit price, line total, currency, and image ID.
  - `BasketResponse` includes basket ID, lines, total, currency, item count, and
    line count.
  - Request schemas require integer quantities and non-empty SKU IDs.
  - Pydantic handles malformed transport shape with FastAPI's normal `422`
    validation behavior.
- **Validation**: API tests assert exact response shape for an empty basket and a
  one-line basket.

### Task 2.2: Add Basket Router And Dependency Wiring

**Status**: Completed on 2026-06-04.

- **Location**: `backend/src/tavola/api/routers/basket.py`,
  `backend/src/tavola/api/dependencies.py`,
  `backend/src/tavola/api/main.py`,
  `backend/tests/test_basket_api.py`
- **Description**: Add basket routes and wire a process-lifetime in-memory basket
  repository through FastAPI dependencies.
- **Dependencies**: Task 2.1.
- **Acceptance Criteria**:
  - `main.py` registers the basket router under the existing API prefix.
  - API dependencies expose both catalog and basket repositories without a
    service container.
  - Dependency overrides can provide deterministic repositories in tests.
  - The in-memory basket repository instance is shared across requests during
    the process lifetime.
- **Validation**: API tests prove a basket created in one request can be fetched
  and edited by later requests.

### Task 2.3: Map Application Errors To HTTP Responses

**Status**: Completed on 2026-06-04.

- **Location**: `backend/src/tavola/api/routers/basket.py`,
  `backend/tests/test_basket_api.py`
- **Description**: Convert application-level basket errors into predictable HTTP
  responses and user-readable messages.
- **Dependencies**: Task 2.2.
- **Acceptance Criteria**:
  - Missing basket returns `404`.
  - Missing line on edit or remove returns `404`.
  - Missing or unavailable SKU returns a `422` validation response.
  - Quantity over 10 returns a `422` validation response that includes the max value.
  - Non-positive quantity from a well-formed request returns a validation
    response with status `422`.
  - Response messages are stable enough for frontend error display tests.
- **Validation**: API tests cover missing basket, missing line, missing SKU,
  unavailable SKU via test fixture, non-positive quantity, and over-max quantity.

## Sprint 3: Frontend Basket Client And State

**Goal**: Add a typed frontend basket client and state hook that persists only
the basket ID while treating the backend as the source of basket contents.

**Demo/Validation**:

- `cd frontend && npm test -- --run src/api/basket.test.ts src/features/basket/useBasket.test.ts`
- In tests, the hook creates a basket when no stored ID exists, recovers from a
  missing stored basket, and updates state after add, edit, and remove calls.

**Progress**: Completed on 2026-06-04.

- Added a shared JSON mutation helper with FastAPI detail-message extraction for
  user-visible basket validation errors.
- Added basket response types, runtime guards, and API functions for create,
  fetch, add, edit, and remove line operations.
- Added `useBasket` with basket ID storage, restart recovery, reload, mutation
  state, and backend-owned basket content updates.
- Validation run: `cd frontend && npm test -- --run src/api/basket.test.ts src/features/basket/useBasket.test.ts`.

### Task 3.1: Extend The API Client For JSON Mutations

**Status**: Completed on 2026-06-04.

- **Location**: `frontend/src/api/client.ts`,
  `frontend/src/api/client.test.ts`
- **Description**: Add a small typed helper for JSON requests with method and
  optional body so basket POST, PATCH, and DELETE calls can reuse error handling.
- **Dependencies**: Existing `apiGetJson`.
- **Acceptance Criteria**:
  - Existing GET behavior remains unchanged.
  - Mutation helper sends `Content-Type: application/json` when a body is
    provided.
  - It parses JSON success responses through the same result shape as
    `apiGetJson`.
  - HTTP, network, and invalid response errors remain explicit.
- **Validation**: Client tests for method, body, headers, HTTP error, and invalid
  JSON handling.

### Task 3.2: Add Basket Types And API Mapper

**Status**: Completed on 2026-06-04.

- **Location**: `frontend/src/types/basket.ts`,
  `frontend/src/api/basket.ts`,
  `frontend/src/api/basket.test.ts`
- **Description**: Add TypeScript types and runtime response guards for the
  basket API contract.
- **Dependencies**: Task 3.1 and Sprint 2 API shape.
- **Acceptance Criteria**:
  - Frontend basket line and basket response types match the backend contract.
  - API functions exist for create, get, add line, set line quantity, and remove
    line.
  - Runtime guards reject malformed basket responses before UI state uses them.
  - Invalid API response errors use basket-specific user-readable messages.
- **Validation**: API mapper tests for valid basket responses and malformed
  responses.

### Task 3.3: Add Basket State Hook With LocalStorage ID Persistence

**Status**: Completed on 2026-06-04.

- **Location**: `frontend/src/features/basket/useBasket.ts`,
  `frontend/src/features/basket/useBasket.test.ts`
- **Description**: Add a hook that loads or creates the current basket, stores
  `basket_id` in `localStorage`, and exposes add, quantity edit, remove, reload,
  and error state operations.
- **Dependencies**: Task 3.2.
- **Acceptance Criteria**:
  - When no stored ID exists, the hook creates a basket and stores its ID.
  - When a stored ID exists, the hook fetches that basket.
  - If fetching the stored ID returns `404`, the hook creates a fresh basket and
    replaces the stored ID.
  - Basket contents are not stored in `localStorage`.
  - Add, edit, and remove operations update state from the backend response.
  - Backend validation errors are preserved for user-visible display.
  - Pending mutation state is explicit so controls can avoid duplicate submits.
- **Validation**: Hook tests for first load, stored-ID load, restart recovery,
  add, merged add response, edit, remove final line, validation error, and reload.

## Sprint 4: Persistent Basket UI And Catalog Integration

**Goal**: Let customers add products from the catalog and manage the current
basket in a persistent desktop-first surface.

**Demo/Validation**:

- `cd frontend && npm test -- --run src/features/basket src/features/catalog`
- `cd frontend && npm run build`
- With the backend and frontend dev servers running, a customer can add from a
  card or detail panel, edit quantity with buttons or numeric input, remove
  lines, and see totals update.

**Progress**: Completed on 2026-06-04.

- Added persistent basket presentation components with empty, loading, error,
  validation-error, line editing, removal, and server-total display states.
- Added add-to-basket controls to catalog cards and product detail while
  preserving detail browsing.
- Lifted basket state into the home page so catalog actions and the basket panel
  share the backend-owned current basket.
- Polished the persistent desktop layout after browser review:
  - Basket panel aligns with the catalog browser header at the top of the page.
  - Product detail opens as a modal dialog instead of reserving a permanent
    side-panel column, so catalog cards keep enough width beside the basket.
  - Basket panel is sticky but viewport-bounded with its own internal scroll
    when many lines overflow the visible page height.
  - Catalog card and product-detail add buttons show existing basket quantity
    inside the button itself, for example `Add another` with `1 in basket`,
    instead of using a separate status pill.
- Validation run: `cd frontend && npm test`; `cd frontend && npm run build`.
- Browser approval run through the in-app browser with frontend dev server and
  backend on the Vite proxy target.

### Task 4.1: Add Basket Presentation Components

**Status**: Completed on 2026-06-04.

- **Location**: `frontend/src/features/basket/BasketPanel.tsx`,
  `frontend/src/features/basket/BasketLineItem.tsx`,
  `frontend/src/features/basket/BasketPanel.test.tsx`,
  `frontend/src/features/basket/basketFormat.ts`,
  `frontend/src/features/basket/basketFormat.test.ts`
- **Description**: Build a persistent basket panel with empty, loading, error,
  success, and validation-error states.
- **Dependencies**: Sprint 3.
- **Acceptance Criteria**:
  - Empty basket state keeps the basket visible and ready for additions.
  - Each line displays product name, unit label, unit price, quantity, line
    total, and remove control.
  - Quantity can be changed with decrement/increment buttons and a numeric input.
  - Quantity input does not allow the UI layout to jump as values change.
  - Backend validation messages are displayed near the basket controls.
  - Totals use server-provided values, not frontend recalculation.
  - Controls are semantic, keyboard-friendly, and accessible.
  - Long baskets remain usable because the persistent basket surface scrolls
    internally within the desktop viewport.
- **Validation**: Component tests for empty state, populated state, quantity
  controls, remove action, validation error rendering, and total display.

### Task 4.2: Add Catalog Add-To-Basket Controls

**Status**: Completed on 2026-06-04.

- **Location**: `frontend/src/features/catalog/CatalogCard.tsx`,
  `frontend/src/features/catalog/CatalogDetail.tsx`,
  `frontend/src/features/catalog/CatalogGrid.tsx`,
  `frontend/src/features/catalog/CatalogGrid.test.tsx`,
  `frontend/src/features/catalog/CatalogDetail.test.tsx`
- **Description**: Add explicit add-to-basket buttons to catalog cards and
  product detail while preserving existing detail browsing behavior.
- **Dependencies**: Task 4.1.
- **Acceptance Criteria**:
  - Every catalog card has a visible add action and a separate detail action.
  - Product detail has an add action for the selected SKU.
  - Add actions send quantity `1` through the basket hook.
  - Add buttons expose pending state during mutation.
  - Add buttons expose existing basket quantity in the button text when the SKU
    is already present, while still allowing duplicate adds to merge quantities.
  - Validation errors from add attempts surface in the persistent basket panel.
  - Existing detail open/close behavior remains covered, with detail shown as a
    modal dialog for the basket workflow.
- **Validation**: Catalog component tests for card add action, detail add action,
  and preserving existing detail behavior.

### Task 4.3: Compose Basket State Into The Home Page

**Status**: Completed on 2026-06-04.

- **Location**: `frontend/src/pages/HomePage.tsx`,
  `frontend/src/features/catalog/CatalogBrowser.tsx`,
  `frontend/src/App.test.tsx`,
  `frontend/src/styles.css`
- **Description**: Wire `useBasket` into the main page and lay out catalog plus
  persistent basket in a desktop-first workflow.
- **Dependencies**: Tasks 4.1 and 4.2.
- **Acceptance Criteria**:
  - Basket state is owned high enough that catalog cards, detail, and panel share
    the same current basket.
  - The basket panel remains visible while filtering, searching, and opening
    product detail.
  - Product detail does not consume a permanent catalog column; it opens as a
    dismissible modal so the catalog grid and persistent basket both stay
    readable.
  - The layout stays desktop-first and scannable without adding mobile-specific
    breakpoints.
  - Existing backend status and catalog loading states remain visible.
  - Styling fits the current Tavola visual language and avoids nested cards.
- **Validation**: App/page tests for rendering the persistent basket alongside
  catalog and for wiring add actions into the panel state.

## Sprint 5: Cross-Service Workflow Verification

**Goal**: Prove the basket slice works end to end and leaves a stable foundation
for mock pickup checkout.

**Demo/Validation**:

- `cd backend && uv run pytest`
- `cd frontend && npm test`
- `cd frontend && npm run build`
- Run the scaffold smoke checklist where relevant and report unchecked items.

### Task 5.1: Add End-To-End Manual Smoke Script

**Status**: Completed on 2026-06-04.

- **Location**: `docs/scaffold-smoke-check.md` or a new checklist section in
  `docs/plans/basket-creation-editing-plan.md`
- **Description**: Document the manual browser workflow for basket creation and
  editing using the existing backend and frontend dev servers.
- **Dependencies**: Sprint 4.
- **Acceptance Criteria**:
  - Manual steps cover backend startup, frontend startup, basket creation,
    adding from card, adding from detail, duplicate merge, quantity edit, over-10
    rejection, remove final line, refresh with stored basket ID, and backend
    restart recovery.
  - The checklist states that contents are backend-owned and only the ID is
    stored in `localStorage`.
- **Validation**: Execute the checklist during implementation handoff and note
  any unchecked items.

### Task 5.2: Run Full Backend And Frontend Checks

**Status**: Completed on 2026-06-04.

- **Location**: repository root.
- **Description**: Run the broad verification suite after the vertical slice is
  complete.
- **Dependencies**: Task 5.1.
- **Acceptance Criteria**:
  - Backend tests pass.
  - Frontend tests pass.
  - Frontend production build passes.
  - Any failures are triaged to either product code, test setup, or existing
    unrelated issues.
- **Validation**: Command outputs from backend pytest, frontend tests, and
  frontend build.

## Testing Strategy

- Domain tests prove basket invariants, merge behavior, max quantity, and totals.
- Application tests prove workflow coordination, repository calls, catalog
  validation, and typed errors.
- API tests prove request/response shape, process-lifetime in-memory persistence,
  status codes, and validation messages.
- Frontend API tests prove response guards and mutation request construction.
- Frontend hook tests prove `localStorage` basket ID behavior, backend restart
  recovery, mutation state, and error propagation.
- Component tests prove persistent basket rendering, add actions, quantity
  editing, removal, server-total display, product detail modal behavior, and
  add-button basket quantity indicators.
- Manual smoke testing proves the full browser workflow across backend and
  frontend.

## Potential Risks & Gotchas

- A new in-memory repository per request would make baskets disappear
  immediately. Mitigate by creating one process-lifetime repository in
  `api/dependencies.py` and overriding it in tests.
- `localStorage` recovery must distinguish a missing basket from general network
  failure. Only a `404` for the stored ID should trigger fresh basket creation;
  network errors should remain visible to the user.
- FastAPI's automatic `422` response for malformed request bodies may differ
  from application validation errors for business rules. Keep shape validation
  and basket-rule validation separate, with stable user-readable business error
  messages.
- Using SKU ID as the line route identity works because the first catalog has one
  line per SKU and duplicate adds merge. If future planner metadata creates
  grouped lines, grouping should be basket metadata, not a reason to duplicate
  SKU lines in this slice.
- Frontend totals should not be recalculated from line prices except for display
  formatting. Checkout will depend on backend-owned totals being the trusted
  value.
- Direct numeric input can temporarily contain empty or invalid text while a user
  is typing. Keep draft input state local to the line control and submit only a
  valid integer mutation, while preserving backend rejection for over-max values.
- The persistent basket must not make the catalog UI feel cramped. Favor a
  stable desktop two-column layout with restrained density and no mobile-specific
  redesign. Product detail should remain modal in this basket workflow instead
  of taking a permanent middle column between catalog cards and the basket.
- Sticky basket panels need a viewport-bounded internal scroll area; otherwise
  long baskets can overflow below the visible page and hide lower line controls.
- Existing basket quantity belongs in the add action itself. A separate pill can
  read like a product attribute rather than current basket state.

## Rollback Plan

- Remove the basket router registration from `backend/src/tavola/api/main.py` to
  disable HTTP access while leaving catalog browsing intact.
- Remove basket dependency exports from `backend/src/tavola/api/dependencies.py`
  if the API layer needs to return to catalog-only behavior.
- Remove frontend basket composition from `frontend/src/pages/HomePage.tsx` and
  restore catalog components to detail-only actions.
- Keep catalog domain, seed data, and existing catalog tests unchanged
  throughout the slice so rollback does not affect feature one.
