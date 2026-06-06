# Plan: Tavola Visual Style Refresh

**Generated**: 2026-06-04
**Estimated Complexity**: Medium

## Overview

Adapt Tavola's existing storefront visual design toward the generated compact
planner-band mockup style while preserving the current commerce behavior. This
plan is a visual refresh only: it should improve the app shell, catalog,
product cards, basket, and checkout presentation, but it should not implement
the Codex-powered planner feature or change the AI planner plan.

The visual target is a warmer, more polished desktop deli storefront: compact
first-viewport composition, paper-like surfaces, restrained tomato/basil/saffron
accents, clearer product cards, a calmer basket panel, and denser operational
layout. The app should feel more like the mockup's trustworthy commerce tool
than a landing page.

Reference mockup:

- `docs/plans/assets/tavola-planner-band-visual-reference.png`

Implementation agents must open and visually inspect this reference image before
editing frontend files. Do not treat the mockup as a vague mood board; extract
concrete styling decisions from it and compare the implemented browser view
against those decisions before handoff.

Reference style cues to replicate where they fit the existing app:

- Large red serif Tavola brand treatment with smaller deli sublabel.
- Warm ivory page canvas with subtle paper texture and thin gold/hairline
  dividers.
- Compact planner-style band proportions for future compatibility, without
  implementing planner behavior in this refresh.
- Main content split with catalog on the left and a calm right-side basket rail.
- Product cards with large food photography, slim borders, restrained shadows,
  serif product names, unit labels, GBP prices, and red outline add buttons.
- Basket panel with generous line spacing, product thumbnails, quantity steppers,
  clear subtotal/total hierarchy, and a strong red checkout button.
- Trust/support strips using small line icons and concise product/customer copy.

## Clarifying Decisions

- Keep the Codex planner implementation plan separate and continue it against
  the current working UI style for now.
- Do not add a functional planner band in this visual refresh.
- Use the mockup as visual direction for density, palette, surface treatment,
  and future planner compatibility.
- Preserve existing desktop-first support; do not introduce mobile-specific
  layout work.
- Preserve current catalog, basket, and checkout behavior.
- Use product/item language in any visible copy; do not introduce customer-
  facing SKU language.
- Keep cards at 8px radius or less and avoid nested cards.
- After any frontend change, run the frontend browser approval check.

## Prerequisites

- Current catalog, basket, and checkout tests are passing or known.
- Frontend dependencies are installed with `cd frontend && npm install`.
- The visual reference image exists at
  `docs/plans/assets/tavola-planner-band-visual-reference.png`.
- No new frontend framework, icon system, state library, or routing change is
  expected.

## Sprint 1: Visual Baseline And Design Tokens

**Goal**: Establish the visual refresh foundation without changing app
structure or behavior.

**Demo/Validation**:

- `cd frontend && npm test`
- `cd frontend && npm run lint`
- Existing storefront still renders and behaves the same.

### Task 1.1: Capture Current UI Baseline

- **Location**: `docs/frontend-browser-approval-check.md`,
  `frontend/src/styles.css`
- **Description**: Before visual edits, run the app and capture desktop
  screenshots of catalog, product detail, basket states, and checkout modal for
  comparison. Open the reference mockup and write a short style checklist from
  the screenshot before editing.
- **Dependencies**: None.
- **Acceptance Criteria**:
  - Baseline screenshots or notes cover catalog loaded state, basket empty,
    basket with lines, product detail, and checkout.
  - Style checklist explicitly references the mockup's brand/header, planner
    band proportions, catalog cards, basket rail, buttons, borders, typography,
    and trust strips.
  - Any pre-existing visual or test issues are recorded before changes.
- **Validation**: Browser inspection at the supported desktop viewport.

### Task 1.2: Refine Global Tokens

- **Location**: `frontend/src/styles.css`
- **Description**: Adjust CSS custom properties and global surface rules to
  better match the mockup: warmer paper backgrounds, quieter borders, clearer
  accent contrast, consistent shadows, and tighter spacing scale.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - Existing color names remain understandable and domain-appropriate.
  - Palette does not become one-note beige, dark blue, or tomato-only.
  - Focus states remain visible.
  - Typography remains readable and desktop-oriented.
  - No functional component changes are required.
- **Validation**: Visual browser check plus `cd frontend && npm run lint`.

### Task 1.3: Normalize Button And Form Styling

- **Location**: `frontend/src/styles.css`
- **Description**: Create more consistent button, input, select, and textarea
  treatments using existing selectors/classes where possible.
- **Dependencies**: Task 1.2.
- **Acceptance Criteria**:
  - Primary actions use the same visual language across catalog, basket, and
    checkout.
  - Disabled and pending states remain clear.
  - Text fits inside buttons at the supported desktop viewport.
  - Controls remain keyboard accessible.
- **Validation**: Component tests where available and browser keyboard check.

### Sprint 1 Implementation Notes

- Captured the pre-edit browser baseline at the supported desktop viewport:
  catalog loaded with first product row visible, empty basket, populated basket,
  product detail modal, and checkout modal. No console errors were observed in
  those baseline states.
- Reference checklist from the mockup: tomato-red serif brand treatment, warm
  ivory paper canvas, thin tan/gold hairlines, compact first-viewport commerce
  proportions, large food-led product cards, outline add buttons, calm basket
  rail, filled tomato checkout actions, readable serif headings, and concise
  trust/support metadata.
- Sprint 1 CSS changes keep the current storefront structure and behavior while
  refreshing global tokens, page texture, focus states, shared form controls,
  primary buttons, secondary buttons, and catalog-card add actions.
- Pre-existing visual/content concerns for later sprints: basket lines do not
  yet include thumbnails, trust/support strips are not yet present, and product
  detail loading/error copy can expose internal product identifiers.

## Sprint 2: App Shell And Storefront Layout

**Goal**: Make the overall storefront composition match the mockup's compact,
polished desktop structure.

**Demo/Validation**:

- Storefront opens with top bar, catalog, and basket visible without feeling
  like a marketing hero.
- At least the first catalog row remains visible at the supported desktop
  viewport.

### Task 2.1: Tighten Top Bar And Brand Area

- **Location**: `frontend/src/pages/HomePage.tsx`,
  `frontend/src/styles.css`, `frontend/src/App.test.tsx`
- **Description**: Refine top-bar spacing, brand mark presentation, and service
  status sizing to match the mockup's quieter header.
- **Dependencies**: Sprint 1.
- **Acceptance Criteria**:
  - Brand remains clearly Tavola and first-viewport visible.
  - Service status stays secondary and compact.
  - Header does not consume unnecessary vertical space.
  - Existing status loading/success/error states still render.
- **Validation**: App tests and browser approval for status states.

### Task 2.2: Refine Commerce Grid

- **Location**: `frontend/src/pages/HomePage.tsx`,
  `frontend/src/styles.css`
- **Description**: Adjust the main catalog/basket grid to feel denser and more
  balanced, with a stable side panel and catalog width that matches the mockup.
- **Dependencies**: Task 2.1.
- **Acceptance Criteria**:
  - Basket panel remains visible beside catalog on the supported desktop
    viewport.
  - Catalog is not pushed below the fold by decorative or oversized header
    content.
  - Layout avoids nested card sections.
  - Existing checkout opening behavior is unchanged.
- **Validation**: Browser check with empty and populated basket.

### Task 2.3: Remove Or Reduce Distracting Decorative Elements

- **Location**: `frontend/src/styles.css`
- **Description**: Reduce background flourishes that compete with the compact
  commerce UI, keeping only subtle texture or hairline treatment where it helps.
- **Dependencies**: Task 2.2.
- **Acceptance Criteria**:
  - Background supports scanning product cards and basket details.
  - No orb/blob-like decoration is introduced.
  - Page still feels warm and branded.
- **Validation**: Visual comparison against the mockup and current app.

### Sprint 2 Implementation Notes

- Tightened the storefront banner into a compact Tavola brand area with a
  secondary service status readout, preserving loading, success, and error
  status behavior in App tests.
- Widened the desktop commerce workspace, stabilized the right-side basket rail,
  and kept catalog and basket visible together at the supported desktop browser
  viewport.
- Reduced decorative page/background treatment to a warmer paper canvas with
  subtle hairlines, and softened the catalog control and basket panel surfaces
  so product browsing remains the primary focus.
- Browser approval covered the loaded storefront, empty basket, populated basket,
  checkout modal, service/API error state through the Vite proxy, keyboard focus,
  and console-error checks.

## Sprint 3: Catalog Browser And Product Cards

**Goal**: Bring the main product browsing surface closer to the mockup's
polished commerce feel.

**Demo/Validation**:

- Catalog controls, product cards, loading, empty, error, and detail states all
  feel visually consistent.
- Product imagery remains the primary card signal.

### Task 3.1: Compact Catalog Header And Filters

- **Location**: `frontend/src/features/catalog/CatalogBrowser.tsx`,
  `frontend/src/features/catalog/CatalogFilters.tsx`,
  `frontend/src/features/catalog/*.test.tsx`,
  `frontend/src/styles.css`
- **Description**: Reduce the current catalog hero/header feeling and make
  search/category controls more compact and tool-like.
- **Dependencies**: Sprint 2.
- **Acceptance Criteria**:
  - Catalog title and lede are scan-friendly, not hero-scale.
  - Category and search controls stay accessible.
  - Loading and error states still fit the refreshed layout.
  - Existing filter behavior and tests remain valid.
- **Validation**: Catalog component tests and browser check for filters/search.

### Task 3.2: Refresh Product Card Layout

- **Location**: `frontend/src/features/catalog/CatalogCard.tsx`,
  `frontend/src/features/catalog/CatalogGrid.tsx`,
  `frontend/src/features/catalog/*.test.tsx`,
  `frontend/src/styles.css`
- **Description**: Adjust card density, image ratio, price/unit placement,
  facets, and add controls to match the mockup's deli product grid.
- **Dependencies**: Task 3.1.
- **Acceptance Criteria**:
  - Product image, name, unit label, and price are easy to scan.
  - Add action is visible but not visually noisy.
  - Basket quantity state remains visible when a product is already in the
    basket.
  - Cards do not resize unexpectedly on hover, loading, or pending states.
  - No visible text says SKU.
- **Validation**: Product grid tests and browser check with products added.

### Task 3.3: Refresh Product Detail Surface

- **Location**: `frontend/src/features/catalog/CatalogDetail.tsx`,
  `frontend/src/features/catalog/CatalogDetail.test.tsx`,
  `frontend/src/styles.css`
- **Description**: Align the product detail panel/modal styling with refreshed
  product cards and the mockup's calmer surfaces.
- **Dependencies**: Task 3.2.
- **Acceptance Criteria**:
  - Detail image and description feel connected to the product card style.
  - Add-to-basket state still works.
  - Close and keyboard behavior remain accessible.
  - No customer-facing SKU language appears.
- **Validation**: Detail tests and browser keyboard/mouse check.

### Sprint 3 Implementation Notes

- Compact catalog controls now read as a tool strip rather than a hero panel,
  with category radios and search preserving their accessible labels and
  existing filter behavior.
- Product cards now lead with stable food imagery, slimmer paper surfaces,
  tighter serif product hierarchy, clearer price/unit placement, quieter
  dietary badges, and compact red outline add actions that still show in-basket
  quantity state.
- Product detail now shares the refreshed card language with a calmer modal,
  larger product image, clearer price/unit hierarchy, working add-to-basket
  state, and loading/error copy that does not expose raw product identifiers.
- Browser approval covered the loaded catalog at a desktop viewport,
  category filtering, search/no-results/reset, populated basket card state,
  product detail open/add/keyboard close/mouse close, backend-driven detail and
  catalog error states through the Vite proxy, keyboard focus on catalog search,
  and console-error checks.

## Sprint 4: Basket And Checkout Polish

**Goal**: Make basket and checkout feel like first-class parts of the polished
commerce workspace.

**Demo/Validation**:

- Basket empty, loading, error, populated, and checkout states all match the
  refreshed visual style.

### Task 4.1: Refresh Basket Panel

- **Location**: `frontend/src/features/basket/BasketPanel.tsx`,
  `frontend/src/features/basket/BasketLineItem.tsx`,
  `frontend/src/features/basket/*.test.tsx`,
  `frontend/src/styles.css`
- **Description**: Update the basket panel to match the mockup's compact side
  panel: clearer totals, calmer empty state, denser line items, and stronger
  checkout action hierarchy.
- **Dependencies**: Sprint 3.
- **Acceptance Criteria**:
  - Basket remains readable with multiple lines.
  - Quantity controls and remove actions remain keyboard accessible.
  - Empty basket state is helpful but compact.
  - Error messages use product/item language, not SKU.
- **Validation**: Basket tests and browser check for all basket states.

### Task 4.2: Refresh Checkout Panel

- **Location**: `frontend/src/features/checkout/CheckoutPanel.tsx`,
  `frontend/src/features/checkout/*.test.tsx`,
  `frontend/src/styles.css`
- **Description**: Bring checkout modal/panel styling into alignment with the
  refreshed basket and card surfaces.
- **Dependencies**: Task 4.1.
- **Acceptance Criteria**:
  - Contact details and pickup window controls are clear.
  - Checkout success state feels consistent with the new visual language.
  - Validation and API errors remain user-friendly.
  - Mock checkout scope remains unchanged.
- **Validation**: Checkout tests and browser check for success/error paths.

### Sprint 4 Implementation Notes

- Basket rail now uses the refreshed paper/hairline treatment with a compact
  red serif Basket title, product thumbnails from the existing catalog image
  map, denser line-item controls, clearer total/count hierarchy, compact empty
  and error states, and a stronger checkout action.
- Checkout now shares the refreshed basket/card surface language with a clearer
  review/form split, aligned success confirmation, visible validation/API
  alerts, and unchanged mock pickup checkout behavior.
- Generic 5xx API fallbacks now use customer-friendly Tavola copy while
  preserving FastAPI validation detail messages for basket and checkout errors.
- Browser approval covered empty basket, populated basket, basket quantity
  validation error, checkout form, checkout success, checkout API error with
  backend outage, Vite proxy-backed requests, keyboard focus visibility in the
  modal, and console-error checks.

## Sprint 5: Browser Approval And Style Handoff

**Goal**: Verify the refreshed visual system end to end and document how it
should guide future planner UI work.

**Demo/Validation**:

- `cd frontend && npm test`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Frontend browser approval check completed at the supported desktop viewport.

### Task 5.1: Run Full Frontend Verification

- **Location**: `docs/frontend-browser-approval-check.md`
- **Description**: Run the required checks for frontend changes and manually
  verify changed states in the browser. Re-open the reference mockup and compare
  the implemented desktop screenshot against the style checklist from Task 1.1.
- **Dependencies**: Sprints 1-4.
- **Acceptance Criteria**:
  - Catalog loading, empty/no-results, error, and success states checked.
  - Basket empty, populated, mutation pending, and error states checked.
  - Product detail and checkout success/error states checked.
  - Supported desktop viewport shows a polished, non-overlapping layout.
  - Final browser screenshot intentionally matches the reference mockup's
    density, surface treatment, typography hierarchy, product card feel, and
    basket rail composition where those elements exist in the current app.
  - Any unchecked states are explicitly reported.
- **Validation**: Test/lint/build commands and in-app browser approval notes.

### Task 5.2: Add Visual Style Notes For Future Planner Work

- **Location**: `docs/plans/completed/codex-menu-to-basket-planner-plan.md`,
  `docs/plans/completed/tavola-visual-style-refresh-plan.md`
- **Description**: Add or preserve a short note that the Codex planner can later
  use the refreshed visual language, but the planner implementation remains a
  separate feature slice.
- **Dependencies**: Task 5.1.
- **Acceptance Criteria**:
  - Future planner work has a clear reference to the compact planner-band visual
    direction.
  - The current visual refresh does not imply that the AI feature has been
    implemented.
- **Validation**: Documentation review.

### Sprint 5 Implementation Notes

- Frontend verification passed with `cd frontend && npm test`,
  `cd frontend && npm run lint`, and `cd frontend && npm run build`.
- Browser approval used the Codex in-app Browser at the supported desktop
  viewport (`1280x720`) against the Vite proxy-backed app. Verified catalog
  success and no-results states, empty and populated basket states, basket
  quantity validation error, product detail success and API error, checkout
  success and API error, service/catalog/basket API-down states, accessible
  controls, visible basket rail beside catalog, first catalog row visibility,
  and no unexpected console errors.
- The final desktop screenshot was compared against
  `docs/plans/assets/tavola-planner-band-visual-reference.png`: the implemented
  storefront preserves the compact planner band, warm paper surfaces, red serif
  hierarchy, food-led product cards, and calm right-side basket rail without
  claiming new planner behavior beyond the separate planner feature slice.
- Loading and mutation-pending states were covered by the existing frontend
  component tests but were too brief to capture manually in-browser on the local
  dev server; no unchecked functional state remains outside that browser timing
  limitation.
- `docs/plans/completed/codex-menu-to-basket-planner-plan.md` now references this visual
  direction for future planner composition while keeping the planner
  implementation separate from this visual refresh.

## Testing Strategy

- Existing frontend unit/component tests should continue to cover behavior.
- Browser approval is required because this is primarily visual and
  user-facing.
- Use screenshot comparison by eye against the reference mockup and the
  pre-refresh baseline.
- Run production build to catch CSS/module issues.
- Backend tests are not required unless frontend changes reveal API contract
  assumptions or copy changes require backend error mapping.

## Potential Risks & Gotchas

- The mockup includes a planner band, but this plan should not implement the AI
  feature. Mitigation: treat the mockup as visual direction and leave planner
  behavior to the existing Codex planner plan.
- The current app already has warm deli styling; over-editing could churn stable
  components. Mitigation: work in small CSS/component slices and preserve tests.
- Compacting the catalog header could hide useful controls. Mitigation: verify
  search/category controls in browser approval.
- Product cards can become too dense if images, prices, and controls compete.
  Mitigation: keep stable card dimensions and inspect real catalog imagery.
- Basket side panel can become cramped with several lines. Mitigation: test with
  populated basket and long product names.
- Visual changes may accidentally introduce customer-facing SKU language while
  touching error states. Mitigation: scan visible copy and add focused frontend
  assertions where practical.

## Rollback Plan

- Revert visual changes by sprint because each sprint should be behaviorally
  independent.
- If catalog card changes regress usability, keep token/shell updates and revert
  only card-specific CSS/component edits.
- If basket or checkout polish creates interaction regressions, revert those
  components while preserving earlier catalog/shell refreshes.
- Because this plan does not alter backend behavior or AI planner architecture,
  rollback should not affect catalog, basket, checkout, or future planner API
  contracts.
