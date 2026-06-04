# Plan: Main View Storefront Refinement

**Generated**: 2026-06-04
**Last Updated**: 2026-06-04
**Estimated Complexity**: Medium
**Status**: Implemented

## Overview

Refine Tavola's main storefront view so the first desktop viewport leads with the
commerce workflow instead of structural explanation. The catalog and basket
components should remain behaviorally intact, but the page chrome around them
should become lighter: remove the catalog/basket/checkout workflow pills from the
top right, move backend connectivity into a quiet status treatment there, reduce
the large "Storefront workspace" intro card, preserve the bottom-right circle
motif as a subtle brand accent, and bring visible catalog products above the fold
on laptop-height screens.

Clarifying assumptions for this plan:

- The supported target remains desktop browser only, following
  `docs/adr/0001-desktop-first-demonstrator-ui.md`.
- Catalog browsing and basket editing behavior are not being redesigned in this
  slice.
- "Laptop screen" means a common desktop viewport such as `1366x768` or
  `1440x900`.
- Backend status should remain accessible and observable, but it should not read
  as a major content card when the connection is healthy.
- Sticky basket behavior is out of scope for this refinement; the basket should
  remain visible in the first viewport but does not need to follow catalog scroll.
- Product card structure, image sizing, and add/detail behavior are out of scope;
  the surrounding page chrome should absorb the layout refinement.
- Opening-view checkout promotion is out of scope; removing the workflow pills
  should not be replaced by new "mock checkout" copy in this slice.
- No external documentation lookup is needed because this is a local React/CSS
  layout refinement using existing dependencies.

## Implementation Summary

Implemented on 2026-06-04 as a frontend-only storefront refinement.

- Removed the Catalog/Basket/Checkout workflow pills from the top bar.
- Moved backend health into a compact `Service status` indicator in the top bar,
  preserving `role=status` for loading/success and `role=alert` for errors.
- Replaced the floating header treatment with a full-width, non-sticky top bar.
- Added a small circular Tavola brand mark to the header. The mark echoes the
  previous circular motif, uses a stronger tomato ring, and avoids badge-like
  red dot decoration.
- Removed the large "Storefront workspace" intro card and preserved the
  decorative circle only as a subtle page accent.
- Combined the catalog title copy and filters into one compact catalog controls
  surface instead of separate stacked cards.
- Moved product count metadata to the results edge above the product grid.
- Replaced implementation-facing empty basket copy with customer-facing shopping
  language.
- Kept API clients, basket use case wiring, catalog data flow, product card
  structure, and backend contracts unchanged.

Validation completed:

- `cd frontend && npm test`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Browser visual checks with the Codex in-app Browser at a `1280x720` viewport,
  which is stricter than the planned laptop-height check. Verified the full-width
  static header bar, compact service status, combined catalog controls, count
  above results, basket visibility, no workflow pills, no intro card, first-row
  product visibility, and error-state visibility during the implementation pass.

Known validation note:

- The Browser plugin's text-entry helper intermittently failed because its
  virtual clipboard was unavailable. Catalog search and basket behavior remained
  covered by the passing frontend tests; browser verification focused on the
  layout and visible states that this plan changed.

## Prerequisites

- Read `CONTEXT.md` and preserve Tavola's catalog-first demonstrator scope.
- Review current top-level composition in `frontend/src/pages/HomePage.tsx`.
- Review current visual system and layout rules in `frontend/src/styles.css`.
- Keep existing API clients, basket use case wiring, and catalog data flow
  unchanged.
- Remove implementation-facing "backend-owned" language from the affected
  customer-facing main view copy.
- Do not change backend health, catalog, or basket API contracts; service-status
  wording is a frontend presentation concern.

## Implementation Slice: Main View Refinement

**Goal**: Make the first desktop viewport feel like an active storefront: quiet
the header chrome, compact the backend status, reduce the intro treatment, and
bring catalog products into view immediately.

**Demo/Validation**:

- Run `cd frontend && npm test`.
- Run `cd frontend && npm run lint`.
- Complete the relevant parts of `docs/frontend-browser-approval-check.md`.
- In the browser, verify the top right no longer shows Catalog/Basket/Checkout
  pills.
- Verify loading, success, and error backend states remain visible and announced.
- At `1366x768` or equivalent desktop viewport, verify the catalog heading,
  browsing controls, and at least the top half of the first row of product cards
  are visible without scrolling.

### Task 1.1: Remove Workflow Pill Navigation From The Home Page

**Status**: Completed.

- **Location**: `frontend/src/pages/HomePage.tsx`
- **Description**: Remove `workflowItems` and the `primary-nav` rendering from
  the top bar. Point the brand link at `#catalog-title` so it returns the
  customer to the catalog top.
- **Dependencies**: None.
- **Acceptance Criteria**:
  - The top bar no longer renders Catalog, Basket, or Checkout controls.
  - Checkout is not shown as a disabled planned affordance in the opening view.
  - The brand link targets `#catalog-title`, not `#workspace`.
  - No catalog or basket behavior changes.
- **Validation**:
  - Update `frontend/src/App.test.tsx` expectations that currently assert the
    navigation links and disabled checkout button.
- **Implementation Notes**:
  - Removed `workflowItems` and `primary-nav`.
  - Brand link now targets `#catalog-title`.
  - Added a constrained `.top-bar__inner` inside a full-width `.top-bar`.

### Task 1.2: Convert Backend Status Into A Compact Top-Bar Indicator

**Status**: Completed.

- **Location**:
  - `frontend/src/pages/HomePage.tsx`
  - `frontend/src/components/BackendStatusPanel.tsx`
  - `frontend/src/styles.css`
- **Description**: Move `BackendStatusPanel` into the top bar and restyle it as
  a compact status indicator instead of a full content card. Preserve state copy
  for loading, success, and error, but shorten the healthy visual footprint.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - Healthy status reads as a small top-right indicator.
  - Loading and error states remain discoverable and accessible via `role=status`
    or `role=alert`.
  - Error status stays concise in the top bar, for example "Service unavailable";
    detailed recovery messages remain with catalog or basket error states.
  - The status component remains reusable and typed around `BackendStatus`.
- **Validation**:
  - Update backend status tests in `frontend/src/App.test.tsx`.
  - Manually verify mocked loading, success, and error states in the browser or
    through a focused component render.
- **Implementation Notes**:
  - Status copy now uses customer-facing service language: "Checking service",
    "Service ready", and "Service unavailable".
  - `BackendStatusPanel` remains typed around `BackendStatus` and remains
    accessible through the `Service status` label.

### Task 1.3: Remove The Storefront Workspace Card

**Status**: Completed.

- **Location**:
  - `frontend/src/pages/HomePage.tsx`
  - `frontend/src/styles.css`
- **Description**: Remove the current `workspace-intro` section entirely and let
  the catalog header carry the opening page identity. Preserve the decorative
  bottom-right circle motif only as a subtle pseudo-element attached to the page
  or catalog surface, not as a large card that consumes vertical space. Rename
  touched top-level `workspace` classes to catalog/storefront language, without
  doing a broad historical rename pass.
- **Dependencies**: Task 1.2.
- **Acceptance Criteria**:
  - The first viewport no longer spends most of its height on "Storefront
    workspace" copy.
  - No separate masthead or intro row sits between the top bar and the
    catalog/basket commerce layout.
  - Tavola remains clearly branded in the header and opening content.
  - The circular visual accent remains present but does not obscure content.
  - The circular visual accent does not require a separate masthead or increase
    first-viewport whitespace.
  - The main landmark still has a stable target for the brand link.
  - Touched top-level class names no longer preserve `workspace` terminology.
- **Validation**:
  - Update `frontend/src/App.test.tsx` if the `h1` location or accessible name
    changes.
  - Browser-check that no decorative element overlaps catalog or basket content.
- **Implementation Notes**:
  - Removed the `workspace-intro` section and renamed touched top-level
    storefront classes.
  - Catalog now owns the opening `h1`.
  - The decorative circle moved to a subtle non-interactive page pseudo-element.
  - A smaller circular brand mark was later added to the header.

### Task 1.4: Tighten The Catalog Browser Header

**Status**: Completed.

- **Location**:
  - `frontend/src/features/catalog/CatalogBrowser.tsx`
  - `frontend/src/styles.css`
- **Description**: Make the catalog header more useful and less tall. Prefer
  concise copy, a denser product-count treatment, and layout that leads directly
  into category controls and product cards.
- **Dependencies**: Task 1.3.
- **Acceptance Criteria**:
  - The header still exposes `catalog-title` for accessible section labelling.
  - Product count remains visible without becoming a large card.
  - Category filters appear high enough that the catalog feels immediately
    actionable.
  - Existing loading, error, search, empty, and success states remain explicit.
- **Validation**:
  - Run catalog feature tests under `frontend/src/features/catalog/`.
  - Browser-check catalog loading, successful product display, empty filter
    results, and catalog error state.
- **Implementation Notes**:
  - Catalog title copy and filters now share one compact controls surface.
  - Product count moved out of the heading area and into a results bar above the
    grid.
  - The count remains `aria-live="polite"`.

### Task 1.5: Rebalance The Commerce Grid Around Catalog And Basket

**Status**: Completed.

- **Location**: `frontend/src/styles.css`
- **Description**: Adjust spacing, top margins, grid columns, and sticky/visual
  treatment as needed so the catalog remains the primary left-side workflow and
  the basket remains visible without feeling like a nested card inside another
  card.
- **Dependencies**: Task 1.4.
- **Acceptance Criteria**:
  - Catalog and basket retain the existing two-column desktop arrangement.
  - At `1366x768`, the catalog heading, browsing controls, and at least the top
    half of the first row of product cards are visible without scrolling.
  - Basket header and empty/success states remain readable.
  - No nested-card effect is introduced around existing catalog and basket
    surfaces.
  - Basket positioning does not introduce sticky-scroll behavior in this slice.
  - Product cards keep their existing structure, image sizing, and actions.
- **Validation**:
  - Browser-check `1366x768` or equivalent desktop viewport.
  - Add or update component tests only if markup or accessibility names change.
- **Implementation Notes**:
  - Reduced top spacing and column gap while preserving the existing two-column
    catalog/basket relationship.
  - Existing basket sticky behavior was already present before this plan; no new
    sticky-scroll behavior was introduced during this slice.
  - Browser validation used `1280x720`, where the catalog heading, controls,
    basket, and a substantial portion of the first product row were visible.

### Task 1.6: Remove Backend Language From Basket Empty Copy

**Status**: Completed.

- **Location**: `frontend/src/features/basket/BasketPanel.tsx`
- **Description**: Replace implementation-facing empty basket copy with customer
  shopping language, such as "Add products from the catalog to start your
  basket."
- **Dependencies**: Task 1.2.
- **Acceptance Criteria**:
  - Empty basket copy does not say "backend-owned".
  - The empty state still clearly points the customer back to catalog products.
  - Basket behavior and mutation state handling are unchanged.
- **Validation**:
  - Run `frontend/src/features/basket/BasketPanel.test.tsx`.
  - Browser-check the empty basket state in the first viewport.
- **Implementation Notes**:
  - Empty basket copy now reads: "Add products from the catalog to start your
    basket."

## Testing Strategy

- Update `frontend/src/App.test.tsx` for top-bar/status markup changes.
- Keep existing catalog and basket tests as regression coverage for untouched
  behavior.
- Add focused tests only where accessible names, landmarks, or state text change.
- Use browser approval as the primary layout verification because the key risk is
  first-viewport composition, not domain behavior.
- Do not add brittle unit tests for pixel/fold layout; assert layout acceptance
  through browser approval at the named desktop viewport.
- Browser-check loading, success, empty, and error states touched by the layout
  change.
- Report exact commands run and any unchecked browser approval items in handoff.

## Potential Risks & Gotchas

- The backend status indicator can become too quiet in error states. Mitigation:
  keep `role=alert`, visible error copy, and enough width for actionable text.
- Removing the workflow navigation may remove useful anchor jumps. Mitigation:
  keep brand or skip-style linking to the main catalog area if needed.
- Reducing intro copy could make the demonstrator less self-explanatory.
  Mitigation: keep concise catalog-adjacent copy that says customers can browse
  real deli products and add picks to the basket.
- The first viewport target can vary by browser chrome and dev tools. Mitigation:
  validate at a named desktop viewport and report the exact size used.
- CSS spacing changes may accidentally affect catalog detail modal, empty state,
  or basket line controls. Mitigation: verify all touched catalog/basket states
  during browser approval.

## Rollback Plan

- Revert the `HomePage.tsx`, `BackendStatusPanel.tsx`, `CatalogBrowser.tsx`, and
  `styles.css` changes from this slice.
- Restore the previous `App.test.tsx` expectations for top navigation and large
  backend status card.
- Keep API, catalog data, basket behavior, and backend code untouched throughout
  the work so rollback remains limited to frontend composition and tests.
