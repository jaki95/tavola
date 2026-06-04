# Plan: Catalog and Planner Tabs

**Generated**: June 4, 2026
**Estimated Complexity**: Medium

## Overview

Add two accessible workflow tabs to the top banner/navigation, labelled
**Shop** and **Plan** for customers while mapping to the internal **Catalog** and
**Planner** workflows. The main content area should show the active workflow while the
basket stays pinned in the right side panel, so basket state, checkout readiness,
and planner acceptance remain visible while the customer moves between browsing
and planning. Basket remains visible on both workflows, including when empty.

The recommended default tab is **Shop**. This keeps Tavola's ordinary commerce
flow first, matches the existing "catalog as first storefront screen" test, and
solves the customer's immediate pain: after reviewing a planner proposal, adding
more catalog items is one tab switch instead of a long scroll. The Plan tab
should remain mounted while hidden so in-progress prompts, follow-up questions,
and proposal edits survive tab switches. Catalog category and search context
should also survive tab switches, but an open product detail surface should close
when the customer leaves Catalog. The Shop workflow heading should be `Shop`;
`Catalog` remains the internal/domain term and may appear in supporting copy.
Switching away from Plan during Planning should not cancel the planner session.
Proposal review edits should also survive workflow switches. Each fresh page
load should start on Shop, and selecting the Tavola brand should return the
customer to Shop without clearing Basket or Planner state.

No backend API or domain changes are expected. This is a frontend header
navigation, composition, state, styling, and test update. The current header
service status and related visible health-check plumbing should be removed from
the customer-facing storefront.

## Prerequisites

- Read `CONTEXT.md` and preserve Tavola's desktop-first demonstrator scope.
- Keep the planner customer-facing language as "Planner"; avoid Codex language
  outside the planner surface.
- Use existing React, TypeScript, CSS, and Testing Library patterns.
- Do not introduce a router, state library, UI framework, or new tab dependency.
  Shop and Plan are in-page workflow tabs, not route-level destinations.

## Sprint 1: Header Workflow Navigation

**Goal**: Introduce top-banner workflow tabs while preserving existing catalog,
planner, and basket behavior.

**Demo/Validation**:

- Run `cd frontend && npm test -- App.test.tsx`.
- Verify the first screen shows the Tavola brand, Shop selected in the top
  banner, Plan available beside it, and Basket still in the sticky right panel.
- Verify backend service status no longer appears in the top banner.
- Verify switching tabs does not reload or lose basket state.
- Verify selecting the Tavola brand returns to Shop without clearing Basket or
  Planner state.

### Task 1.1: Add Header Workflow Tabs

- **Location**: `frontend/src/pages/HomePage.tsx` or a new
  `frontend/src/components/StorefrontWorkflowTabs.tsx`
- **Description**: Create a small controlled top-banner tab navigation with
  `Shop` and `Plan` tabs. It should own only active-tab UI state and pass the
  selected workflow down to the main content area.
- **Dependencies**: None
- **Acceptance Criteria**:
  - Tabs use semantic, keyboard-friendly markup: `role="tablist"`,
    `role="tab"`, `aria-selected`, `aria-controls`, and `role="tabpanel"`.
  - Tabs are reachable by normal keyboard tab order and activate with native
    button keyboard behavior.
  - Tabs update local workflow state only; they do not change the URL or require
    a router.
  - Shop is selected by default.
  - A fresh page load always starts on Shop; active workflow is not stored in
    localStorage or URL state.
  - Selecting the Tavola brand switches to Shop without clearing Basket or
    Planner state.
  - The tabs live in the existing `top-bar` area near the Tavola brand without
    creating a crowded header.
  - Both `CatalogBrowser` and `PlannerWorkspace` remain mounted in the main area
    so local state is preserved across tab switches.
  - Hidden tab panel content is visually and semantically hidden without
    unmounting.
- **Validation**:
  - Add or update App-level tests that assert the default selected tab is
    Shop, Plan can be selected, and the basket remains in
    `.storefront-main__side-panel`.

### Task 1.1a: Remove Header Service Status

- **Location**: `frontend/src/pages/HomePage.tsx`,
  `frontend/src/App.tsx`, `frontend/src/App.test.tsx`
- **Description**: Remove `BackendStatusPanel` from the customer-facing top
  banner, remove the visible health-check plumbing from the storefront, and
  update App-level status assertions.
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - The top banner no longer renders `Service status`, `Checking service`, or
    health-check detail copy.
  - `App` no longer performs a customer-visible health check solely to populate
    the storefront header.
  - `HomePage` no longer accepts `backendStatus` as a prop.
  - Tests no longer assert service status visibility in the storefront header.
- **Validation**:
  - `cd frontend && npm test -- App.test.tsx`

### Task 1.2: Render the Active Workflow in Main Content

- **Location**: `frontend/src/pages/HomePage.tsx`
- **Description**: Replace the stacked primary column with main-content tab
  panels controlled by the top-banner tabs. Pass the existing basket, catalog,
  and planner props through unchanged.
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - `BasketPanel` remains outside the workflow panels in the existing side panel.
  - `BasketPanel` is visible on both Shop and Plan, including empty basket state.
  - `PlannerWorkspace` still receives `basket` and `onBasketAccepted`.
  - `CatalogBrowser` still receives `basketQuantities`, `isAddPending`, and
    `onAddProduct`.
  - The Shop workflow page heading changes from `Catalog` to `Shop`.
  - The Plan workflow page heading remains `Plan a menu`.
  - Checkout behavior remains unchanged.
  - The main content column shows only the active workflow, eliminating the long
    Planner-over-Catalog stack.
- **Validation**:
  - Existing checkout and planner acceptance tests continue passing after test
    updates for tab visibility.

### Task 1.3: Preserve Planner State Across Top-Banner Switches

- **Location**: `frontend/src/pages/HomePage.tsx`,
  `frontend/src/features/planner/PlannerWorkspace.tsx` if needed
- **Description**: Confirm that switching away from Planner during loading,
  follow-up input, proposal review, quantity edits, and accept confirmation does
  not reset local state.
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - A typed meal request remains when switching Shop -> Plan -> Shop -> Plan
    from the top banner.
  - A planner session in Planning continues after switching from Plan to Shop.
  - A returned proposal remains available after switching tabs.
  - Proposal review edits, including removed lines and quantity adjustments,
    persist across workflow switches.
  - Replace confirmation state behaves consistently after tab switches.
- **Validation**:
  - Add focused tests for prompt persistence and proposal persistence across tab
    switches.

### Task 1.4: Preserve Catalog Browsing Context Without Carrying Detail Across Workflows

- **Location**: `frontend/src/features/catalog/CatalogBrowser.tsx`,
  `frontend/src/features/catalog/useCatalogBrowser.ts`,
  `frontend/src/pages/HomePage.tsx`
- **Description**: Keep Catalog category and search state when switching to
  Planner and back, while closing any open product detail when the customer
  leaves Catalog.
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - Selected category, draft search, and committed search remain when returning
    to Catalog.
  - An open product detail is closed after switching to Planner and back.
  - The close behavior is explicit rather than a side effect of unmounting the
    entire Catalog workflow.
- **Validation**:
  - Add App-level or CatalogBrowser tests for preserved filters/search and closed
    detail after a workflow switch.

## Sprint 2: Desktop Layout and Interaction Polish

**Status**: Completed June 4, 2026.

**Implementation notes**:

- Styled the top-banner Shop/Plan tabs, selected/focus-visible states, workflow
  panel spacing, and sticky basket column in `frontend/src/styles.css`.
- Added a `Proposal ready` Plan tab badge that appears only when a reviewable
  planner proposal becomes ready while the customer is viewing Shop. The badge
  clears when the customer opens Plan, while the proposal remains in the Planner
  workflow for review.
- Surfaced only a boolean reviewable-proposal signal from `PlannerWorkspace` to
  `HomePage`; the Planner still owns proposal state and loading/error/accepted
  states remain inside the Planner workflow.
- Added App/component coverage for the proposal-ready badge and clear-on-open
  behavior.

**Completed validation**:

- `cd frontend && npm test`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Browser approval check at `http://127.0.0.1:5173/`: verified Shop default,
  Plan unavailable/error state, empty and populated Basket, sticky side panel,
  catalog add success, tab layout, and no console errors. Live planner proposal
  success/loading could not be verified in browser because the local backend
  reported Planner disabled; the ready-proposal badge path is covered by App
  tests with a mocked ready planner session.

**Goal**: Make the new tabbed layout feel calmer and less crammed at the
supported desktop viewport.

**Demo/Validation**:

- Run `cd frontend && npm test`.
- Run `cd frontend && npm run lint`.
- Run the browser approval check at `http://localhost:5173`.
- Verify Shop, Plan empty/loading/error/success, and Basket states remain
  readable without overlapping content.

### Task 2.1: Style the Top-Banner Workflow Tabs

- **Location**: `frontend/src/styles.css`
- **Description**: Add styles for the top-banner workflow tabs and main tab
  panels using the existing Tavola visual system.
- **Dependencies**: Sprint 1
- **Acceptance Criteria**:
  - Tab controls are compact, scannable, and clearly selected in the top banner.
  - Header spacing leaves the Tavola brand and Shop/Plan navigation readable.
  - The main workflow panels do not become large nested cards.
  - Catalog and Planner headings remain appropriately sized inside their panels.
  - Focus-visible states are obvious for keyboard users.
  - The palette stays aligned with existing Tavola colors without adding a new
    one-note theme.
- **Validation**:
  - Visual browser check confirms no overlapping text or controls at the
    supported desktop viewport.

### Task 2.2: Tune Main and Basket Column Heights

- **Location**: `frontend/src/styles.css`
- **Description**: Ensure the basket remains sticky on the right and usable when
  planner proposals are long, while the active main workflow panel scrolls
  naturally with the page.
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - `.storefront-main__side-panel` remains sticky with the current max-height and
    overflow behavior unless a smaller adjustment is needed.
  - Long planner proposals do not push the basket below the fold.
  - Catalog add controls remain reachable after reviewing a proposal by using
    the top-banner Shop tab, not by scrolling through planner content.
- **Validation**:
  - Browser approval check covers a populated proposal and a populated basket.

### Task 2.3: Add Proposal-Ready Tab Badging

- **Location**: `frontend/src/pages/HomePage.tsx`,
  `frontend/src/features/planner/PlannerWorkspace.tsx` only if planner state must
  be surfaced upward
- **Description**: Add a lightweight proposal-ready indicator to the Plan tab
  when a reviewable proposal exists while the customer is viewing Shop.
- **Dependencies**: Sprint 1
- **Acceptance Criteria**:
  - The badge is customer-readable, concise, and driven by planner state rather
    than duplicated state.
  - Only proposal-ready state appears in the top banner; loading, error, and
    accepted states remain inside the Planner workflow.
  - Planning in progress does not show a top-banner loading indicator while the
    customer is viewing Shop.
  - The badge clears when the customer opens Plan, while the proposal remains
    available for review.
  - If state lifting would make the planner materially more complex, extract a
    small planner state owner rather than adding parallel state.
- **Validation**:
  - Add an App-level test for the Plan tab indicator after a proposal is
    returned while Shop is active.

## Sprint 3: End-to-End UX Verification

**Goal**: Confirm the tabbed flow solves the cramming problem without regressing
catalog, basket, planner, or checkout workflows.

**Demo/Validation**:

- Run frontend tests and lint.
- Start frontend and backend together when verifying real API-backed flows.
- Complete the checklist in `docs/frontend-browser-approval-check.md`.

### Task 3.1: Update App Integration Tests

- **Location**: `frontend/src/App.test.tsx`
- **Description**: Update tests that assumed Planner and Catalog were both
  simultaneously visible in the primary column.
- **Dependencies**: Sprint 1
- **Acceptance Criteria**:
  - Test Shop default selection in the top banner.
  - Test a fresh render starts on Shop and the Tavola brand switches back to
    Shop without clearing Basket or Planner state.
  - Test the Shop workflow page heading is `Shop`.
  - Test switching to Planner, submitting a prompt, receiving a proposal, and
    accepting it into the visible basket.
  - Test switching back to Catalog after a proposal and adding/browsing remains
    available.
  - Test Catalog search/filter context survives workflow switching while product
    detail closes.
  - Existing checkout synchronization coverage remains intact.
- **Validation**:
  - `cd frontend && npm test -- App.test.tsx`

### Task 3.2: Browser Approval Check

- **Location**: `docs/frontend-browser-approval-check.md` for checklist reference
- **Description**: Manually verify the changed desktop workflow in the Codex
  in-app Browser.
- **Dependencies**: Sprint 2 and Task 3.1
- **Acceptance Criteria**:
  - Loading: catalog loading and planner status/loading states remain visible in
    the relevant tab.
  - Empty: empty basket remains visible on the right.
  - Error: catalog or planner errors remain visible when their tab is selected.
  - Success: accepted planner proposal updates the basket without leaving the
    customer stranded in a long stacked page.
  - Keyboard: tab controls and key actions can be reached and operated.
  - Console: no unexpected errors appear during the changed flow.
- **Validation**:
  - Report the browser checks run and any unchecked items in handoff.

## Testing Strategy

- Unit/integration tests:
  - `cd frontend && npm test -- App.test.tsx`
  - `cd frontend && npm test -- PlannerWorkspace.test.tsx` if planner mounting or
    state exposure changes
  - `cd frontend && npm test`
- Static checks:
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build` if styling or composition changes touch the
    production bundle shape
- Browser checks:
  - Run the checklist in `docs/frontend-browser-approval-check.md`.
  - Use the Codex in-app Browser against the Vite URL.
  - Include backend only if verifying live planner/catalog/basket requests
    through the Vite proxy.

## Potential Risks & Gotchas

- If hidden panels are unmounted, planner proposals and in-progress prompts may
  reset. Keep both panels mounted.
- If hidden panels are only visually hidden, screen readers may still encounter
  inactive content. Use correct hidden semantics for inactive main tab panels.
- If Catalog is kept mounted, open product details may also stay mounted unless
  explicitly closed on workflow switch.
- If custom tab semantics interfere with native keyboard behavior, the new
  navigation may be worse for keyboard users. Prefer ordinary buttons with clear
  selected state and focus styling.
- If Shop remains the default, customers who primarily want planning need one
  extra click. This is currently preferable because Tavola's demonstrator proves
  ordinary commerce first, but it should be confirmed.
- If Planner readiness is hidden while Catalog is active, the customer may miss
  that a proposal returned. Use a simple Plan tab badge in the top banner,
  while avoiding a broader status dashboard.
- Removing service status from the header may leave unused health-check props or
  tests. Remove customer-visible health-check plumbing from `App` and `HomePage`;
  keep only lower-level health client tests if they still serve API coverage.
- If the browser approval check uses mocked or disabled planner behavior, the
  proposal-ready state may need a controlled test fixture or existing API mock to
  verify visually.

## Rollback Plan

- Revert the top-banner tab changes in `frontend/src/pages/HomePage.tsx`.
- Remove tab-specific CSS from `frontend/src/styles.css`.
- Restore App tests to assert the stacked Planner + Catalog primary column.
- No backend, API, database, or domain rollback should be needed.
