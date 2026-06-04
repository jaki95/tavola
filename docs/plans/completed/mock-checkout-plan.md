# Plan: Mock Checkout

**Generated**: 2026-06-04
**Estimated Complexity**: Medium

## Overview

Build Tavola's third commerce feature as a focused vertical slice: customers can
review their backend-owned basket, enter required pickup checkout details, choose
a backend-defined pickup window, and create an in-memory order
without real payment processing.

The checkout flow should stay deliberately small. It should not introduce
customer accounts, shipping, payment providers, order management, promotions, or
inventory reservation. The backend remains the pricing and validation authority:
checkout revalidates the current basket against the catalog, calculates totals
server-side, snapshots order lines, persists the order in memory, and clears
the checked-out basket so the same basket cannot be submitted twice by accident.

## Clarifying Decisions

- Checkout is pickup-only.
- Checkout requires contact details and one backend-defined pickup window.
- Pickup windows are static seed data for the demonstrator, not live scheduling
  or capacity management.
- Checkout creates an in-memory order; no database is introduced.
- Payment, tax breakdowns, delivery, accounts, coupons, and order emails remain
  out of scope.
- Order totals are calculated by the backend from current catalog prices at
  checkout time.
- Order lines are snapshots of customer-facing SKU details and prices at the
  time the order is created.
- A successful checkout clears the current basket by saving the same basket ID
  with no lines.
- Empty baskets cannot be checked out.
- Basket and SKU validation failures should be user-visible and deterministic,
  not hidden behind a generic checkout error.
- The first checkout UI lives in the existing desktop storefront workspace
  beside the basket flow, not on a new mobile-specific route.

## Prerequisites

- Catalog browsing and basket creation/editing are implemented and passing.
- Backend dependencies are installed with `cd backend && uv sync`.
- Frontend dependencies are installed with `cd frontend && npm install`.
- No new external libraries are expected; use FastAPI, Pydantic, React,
  TypeScript, and Vitest already present in the repository.

## Proposed API Shape

- `GET /api/checkout/pickup-windows`
  - Returns backend-defined pickup windows in display order.
  - Response: `{ "pickup_windows": PickupWindowResponse[] }`.
- `POST /api/checkout`
  - Request:
    `{ "basket_id": string, "contact_name": string, "contact_email": string,
    "pickup_window_id": string }`.
  - Creates an order from the basket.
  - Returns `CheckoutResponse` containing the created `order` and the now-empty
    `basket`.

`PickupWindowResponse` should include:

- `pickup_window_id`
- `label`
- `display_order`

`OrderResponse` should include:

- `order_id`
- `basket_id`
- `contact_name`
- `contact_email`
- `pickup_window`
- `lines`
- `total_minor`
- `currency`
- `item_count`
- `line_count`

Each order line should include:

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

## Sprint 1: Checkout Domain And Application Use Cases

**Goal**: Add framework-free checkout and order behavior that can be tested
without HTTP or React.

**Demo/Validation**:

- `cd backend && uv run pytest tests/test_checkout_domain.py tests/test_checkout_use_cases.py`
- A developer can create an order from a populated basket, verify order
  totals and line snapshots, and see the source basket cleared after checkout.

### Task 1.1: Add Checkout Domain Model

- **Location**: `backend/src/tavola/domain/checkout.py`,
  `backend/tests/test_checkout_domain.py`
- **Description**: Add domain types for `OrderId`, `PickupWindow`,
  `ContactDetails`, `OrderLine`, and `Order`.
- **Dependencies**: Existing basket and catalog domain models.
- **Acceptance Criteria**:
  - Domain module imports no FastAPI or Pydantic symbols.
  - Order IDs, contact names, contact emails, and pickup window IDs are
    non-empty.
  - Contact email validation stays lightweight and demonstrator-appropriate:
    require text before and after a basic `@` separator.
  - Pickup windows have stable IDs, customer-facing labels, and positive display
    order.
  - Order lines snapshot SKU display details, quantity, unit price, line total,
    currency, and image ID.
  - Order totals and counts are calculated from order lines.
  - Empty order line lists are rejected.
- **Validation**: Domain tests for valid order creation, total calculation,
  contact detail validation, pickup window validation, and empty-line rejection.

### Task 1.2: Add Pickup Window Repository

- **Location**: `backend/src/tavola/application/checkout.py`,
  `backend/src/tavola/infrastructure/checkout_repository.py`,
  `backend/tests/test_checkout_repository.py`
- **Description**: Define an application-facing `PickupWindowRepository`
  protocol and implement a static seed adapter for checkout window choices.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - Application code depends on a protocol, not concrete seed data.
  - Static windows are returned in backend-owned display order.
  - Lookup by pickup window ID returns one window or `None`.
  - Seed window labels avoid promising real-time capacity or exact operational
    scheduling.
- **Validation**: Repository tests for list order, ID lookup, and missing lookup.

### Task 1.3: Add Order Repository

- **Location**: `backend/src/tavola/application/checkout.py`,
  `backend/src/tavola/infrastructure/checkout_repository.py`,
  `backend/tests/test_checkout_repository.py`
- **Description**: Define an application-facing `OrderRepository` protocol and
  implement a process-lifetime in-memory order store with replaceable ID
  generation.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - Repository can create, save, and fetch orders by ID.
  - Missing order lookup returns `None` for application-level tests; no public
    order lookup endpoint is added in this slice.
  - In-memory order state lasts for the lifetime of the FastAPI process.
  - Order ID generation is deterministic when injected in tests.
- **Validation**: Repository tests for create/save/fetch, missing fetch, and
  deterministic test IDs.

### Task 1.4: Add Checkout Use Cases

- **Location**: `backend/src/tavola/application/checkout.py`,
  `backend/tests/test_checkout_use_cases.py`
- **Description**: Add `ListPickupWindows` and `CreateCheckoutOrder` use cases.
  Coordinate basket lookup, catalog revalidation, pickup window lookup, order
  creation, order persistence, and basket clearing.
- **Dependencies**: Tasks 1.1, 1.2, 1.3 and existing basket/catalog
  repositories.
- **Acceptance Criteria**:
  - Listing pickup windows returns backend-defined windows in display order.
  - Checkout returns typed application errors for missing basket, empty basket,
    missing pickup window, invalid contact details, missing SKU, unavailable
    SKU, and basket quantity problems.
  - Checkout resolves every basket line's SKU from the current catalog before
    creating order line snapshots.
  - Checkout calculates totals from current catalog prices.
  - Successful checkout persists the order and saves the source basket as empty.
  - Application errors can be mapped by the API without leaking domain exception
    strings directly.
- **Validation**: Use-case tests for happy path, basket clearing, order snapshot
  totals, and each validation/not-found branch.

## Sprint 2: Checkout API Contract

**Goal**: Expose pickup windows and order creation through stable HTTP endpoints
while keeping checkout rules outside the transport layer.

**Demo/Validation**:

- `cd backend && uv run pytest tests/test_checkout_api.py tests/test_checkout_use_cases.py`
- `GET /api/checkout/pickup-windows` returns ordered pickup choices.
- `POST /api/checkout` creates an order from a populated basket and returns the
  created order plus an empty basket.

### Task 2.1: Add Checkout API Schemas

- **Location**: `backend/src/tavola/api/schemas/checkout.py`,
  `backend/tests/test_checkout_api.py`
- **Description**: Add Pydantic request and response models for pickup windows,
  checkout submission, order lines, order totals, and checkout responses.
- **Dependencies**: Sprint 1.
- **Acceptance Criteria**:
  - Request schema requires non-blank basket ID, contact name, contact email,
    and pickup window ID.
  - Response schemas mirror backend-owned order and pickup window data.
  - `CheckoutResponse` includes both `order` and the updated empty `basket`.
  - Malformed transport shape uses FastAPI's normal `422` validation behavior.
- **Validation**: API tests assert exact response shape for pickup windows and a
  successful checkout.

### Task 2.2: Add Checkout Router And Dependency Wiring

- **Location**: `backend/src/tavola/api/routers/checkout.py`,
  `backend/src/tavola/api/dependencies.py`,
  `backend/src/tavola/api/main.py`,
  `backend/tests/test_checkout_api.py`
- **Description**: Add checkout routes and wire process-lifetime repositories
  through FastAPI dependencies.
- **Dependencies**: Task 2.1.
- **Acceptance Criteria**:
  - `main.py` registers the checkout router under the existing API prefix.
  - Dependencies expose basket, catalog, pickup window, and order repositories.
  - Dependency overrides can provide deterministic repositories in tests.
  - A basket created and populated through existing basket API routes can be
    checked out through the checkout API route.
- **Validation**: API tests prove cross-route flow from basket creation to
  checkout success and basket clearing.

### Task 2.3: Map Checkout Errors To HTTP Responses

- **Location**: `backend/src/tavola/api/routers/checkout.py`,
  `backend/tests/test_checkout_api.py`
- **Description**: Convert application-level checkout errors into predictable
  HTTP responses and user-readable messages.
- **Dependencies**: Task 2.2.
- **Acceptance Criteria**:
  - Missing basket returns `404`.
  - Empty basket returns `422` with an `empty_basket` error type.
  - Missing pickup window returns `422` with a `pickup_window_not_found` error
    type.
  - Invalid contact name or email returns `422` with field-specific details.
  - Missing or unavailable SKU during checkout returns `422` with SKU-specific
    details.
  - A second checkout attempt against the same basket after a successful
    checkout returns the empty-basket error.
- **Validation**: API tests for each mapped error response.

## Sprint 3: Frontend Checkout Flow

**Goal**: Add a desktop checkout modal, opened from the basket, that lets
customers review the basket, submit pickup details, and see a completed order
confirmation.

**Demo/Validation**:

- `cd frontend && npm test -- CheckoutPanel checkout useCheckout`
- With backend and frontend running, add products to the basket, open checkout
  from the basket, choose a pickup window, submit contact details, and see an
  order confirmation with the basket cleared.

### Task 3.1: Add Checkout Frontend Types And API Client

- **Location**: `frontend/src/types/checkout.ts`,
  `frontend/src/api/checkout.ts`, `frontend/src/api/checkout.test.ts`
- **Description**: Add TypeScript types, runtime response guards, and client
  calls for pickup windows and checkout submission.
- **Dependencies**: Sprint 2 API shape.
- **Acceptance Criteria**:
  - Client fetches `GET /api/checkout/pickup-windows`.
  - Client posts checkout requests to `POST /api/checkout`.
  - Response guards reject malformed pickup window, order, order line, and
    checkout responses.
  - HTTP and invalid-response errors use existing `ApiResult` conventions.
- **Validation**: API client tests for request paths, JSON bodies, encoded data
  where relevant, valid mapping, malformed response rejection, and HTTP errors.

### Task 3.2: Add `useCheckout` Hook

- **Location**: `frontend/src/features/checkout/useCheckout.ts`,
  `frontend/src/features/checkout/useCheckout.test.ts`
- **Description**: Manage pickup-window loading, checkout submission state,
  successful order state, and checkout error messages for the checkout modal.
- **Dependencies**: Task 3.1.
- **Acceptance Criteria**:
  - Hook loads pickup windows when the checkout modal mounts.
  - Hook exposes loading, success, empty, and error states for pickup windows.
  - Hook prevents submission when no basket is available or the basket is empty.
  - Hook submits contact details and basket ID through the API client.
  - On success, hook returns the created order and updated empty basket so the
    parent basket state can be synchronized.
  - Hook exposes a reset action for placing another order after confirmation.
- **Validation**: Hook tests for load success, load error, blocked empty basket,
  submit success, submit validation error, and reset behavior.

### Task 3.3: Add Checkout Modal Component

- **Location**: `frontend/src/features/checkout/CheckoutPanel.tsx`,
  `frontend/src/features/checkout/CheckoutPanel.test.tsx`
- **Description**: Render a modal dialog with basket review, contact name/email
  inputs, pickup window selection, submit button, errors, loading states, and
  completed order confirmation.
- **Dependencies**: Tasks 3.1 and 3.2.
- **Acceptance Criteria**:
  - Empty basket state clearly blocks checkout if the modal is reached without
    a populated basket.
  - Modal includes a clear way back to the basket so customers can keep editing.
  - Loading pickup windows state is visible and does not shift the surrounding
    layout unexpectedly.
  - Pickup window load errors include a retry control.
  - Form labels are accessible and keyboard-friendly.
  - Submit button is disabled while submission is pending.
  - Backend validation errors render near the checkout form.
  - Confirmation shows order ID, pickup window, contact email, line summary,
    server total, and item count.
  - Copy stays practical and does not mention payment processing as a customer
    task.
- **Validation**: Component tests for empty, loading, error, ready, pending,
  validation error, and confirmation states.

### Task 3.4: Integrate Checkout Into Home Page Workflow

- **Location**: `frontend/src/pages/HomePage.tsx`,
  `frontend/src/App.test.tsx`, `frontend/src/styles.css`
- **Description**: Add a checkout button to the basket panel, open checkout as a
  modal dialog in the existing storefront workspace, and synchronize the basket
  returned by checkout with the basket panel.
- **Dependencies**: Task 3.3.
- **Acceptance Criteria**:
  - Basket exposes a checkout action only when checkout can proceed.
  - Checkout opens in a modal dialog rather than as a permanently visible panel
    underneath the basket.
  - Catalog and basket remain visible as the main desktop shopping workflow.
  - Successful checkout updates the basket panel to an empty basket without a
    page refresh.
  - Styles follow the existing Tavola palette and compact operational UI, with
    no mobile-specific breakpoint work.
  - Text fits within form controls, buttons, modal content, and confirmation
    summary at the supported desktop viewport.
- **Validation**: App/page tests for the basket checkout action, modal open/back
  behavior, empty basket state, and successful basket synchronization.

## Sprint 4: End-To-End Smoke And Handoff

**Goal**: Verify the completed checkout flow across backend, frontend, and the
browser before handoff.

**Demo/Validation**:

- `cd backend && uv run pytest`
- `cd frontend && npm test`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Run the frontend browser approval check in
  `docs/frontend-browser-approval-check.md`.

### Task 4.1: Run Backend Regression Checks

- **Location**: `backend/tests/`
- **Description**: Run backend tests after checkout routes and repositories are
  wired with existing catalog and basket behavior.
- **Dependencies**: Sprints 1 and 2.
- **Acceptance Criteria**:
  - Existing catalog and basket tests still pass.
  - Checkout domain, repository, use-case, and API tests pass.
- **Validation**: `cd backend && uv run pytest`.

### Task 4.2: Run Frontend Regression Checks

- **Location**: `frontend/src/`
- **Description**: Run frontend test, lint, and build checks after checkout UI
  integration.
- **Dependencies**: Sprint 3.
- **Acceptance Criteria**:
  - Existing catalog and basket UI tests still pass.
  - Checkout API, hook, component, and app integration tests pass.
  - Frontend production build completes.
- **Validation**: `cd frontend && npm test`, `cd frontend && npm run lint`,
  `cd frontend && npm run build`.

### Task 4.3: Complete Browser Approval Check

- **Location**: `docs/frontend-browser-approval-check.md`
- **Description**: Run the backend and frontend together and verify the changed
  user-facing checkout workflow through the Vite proxy in the Codex in-app
  Browser.
- **Dependencies**: Tasks 4.1 and 4.2.
- **Acceptance Criteria**:
  - Loading, empty, error, ready, pending, and success states touched by checkout
    are verified where practical.
  - Catalog add-to-basket, checkout modal open/back behavior, basket review,
    checkout submission, order confirmation, and post-checkout empty basket are
    verified at the supported desktop viewport.
  - Any unchecked browser approval items are documented in handoff.
- **Validation**: Manual browser approval notes in the final implementation
  handoff.

## Testing Strategy

- Domain tests own checkout invariants: required contact detail fields, pickup window
  validity, non-empty orders, line snapshots, totals, and counts.
- Application tests own workflow outcomes: basket lookup, empty basket rejection,
  catalog revalidation, pickup window lookup, order persistence, and basket
  clearing.
- API tests own request/response shape, dependency overrides, cross-route basket
  to checkout behavior, and application-error-to-HTTP mapping.
- Frontend API tests own runtime response guards and request construction.
- Frontend hook/component tests own user-facing state transitions and accessible
  interactions.
- Browser approval owns final workflow confidence across Vite, FastAPI, and the
  desktop storefront UI.

## Potential Risks & Gotchas

- **Basket staleness**: Basket lines currently carry SKU objects from the time
  they were added. Checkout must resolve current catalog SKUs before creating
  order snapshots so price and availability remain backend-owned.
- **Duplicate checkout**: Returning only an order while leaving the basket
  populated would allow accidental duplicate submissions. Clearing the basket on
  success keeps the demonstrator flow legible.
- **Over-real pickup windows**: Dynamic dates and capacity rules would pull the
  feature toward scheduling infrastructure. Static backend-defined windows keep
  this slice small.
- **Email validation scope creep**: Full email validation is unnecessary here.
  Keep validation lightweight and user-readable.
- **Frontend state sync**: The checkout response should include the updated
  empty basket so the basket panel does not need to infer or refetch state after
  a successful order.
- **Order history temptation**: Fetching past orders or managing order status is
  out of scope for this slice unless explicitly requested.

## Rollback Plan

- Remove the checkout router registration from `backend/src/tavola/api/main.py`.
- Remove checkout dependencies from `backend/src/tavola/api/dependencies.py`.
- Delete checkout-specific backend domain, application, infrastructure, schemas,
  router, and tests.
- Remove checkout frontend API/types/hooks/components and undo `HomePage`
  integration.
- Revert checkout styles from `frontend/src/styles.css`.
- Existing catalog and basket flows should remain usable because checkout is a
  new vertical slice layered on top of the current basket API.
