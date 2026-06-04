# Plan: Catalog Browsing

**Generated**: 2026-06-04
**Estimated Complexity**: Medium

## Overview

Build Tavola's first product feature as a small vertical slice: customers can
browse a backend-owned deli catalog, filter by category, search by meaningful
catalog text, and inspect product detail without adding anything to a basket yet.
The implementation should establish the first real commerce domain concepts
while keeping storage static and in memory for the demonstrator.

This plan keeps catalog truth on the backend. The frontend can display products,
prices, categories, facets, and imagery, but it should not own price,
availability, or raw tag logic. Backend code should preserve the existing Tavola
boundaries: domain objects and invariants in `domain`, use-case orchestration in
`application`, static catalog storage in `infrastructure`, and transport schemas
and routes in `api`.

## Clarifying Assumptions

- The first catalog uses the static 20-SKU seed inventory described in
  `CONTEXT.md`.
- There is no database, admin UI, auth, inventory reservation, promotions, or
  basket mutation in this feature.
- Catalog item prices are integer minor units plus GBP currency, owned by the
  backend. Each SKU also has a required free-text customer-facing unit label
  such as `250g`, `serves 2`, or `jar 180g`; the first version does not parse
  unit labels as measurement data.
- Customer-facing categories are `Antipasti`, `Primi`, `Desserts`, `Drinks`, and
  `Pantry`, and each product has exactly one primary category.
- Category IDs are stable lowercase URL-safe identifiers: `antipasti`, `primi`,
  `desserts`, `drinks`, and `pantry`.
- SKU IDs use stable human-readable slugs and are not regenerated from display
  names.
- Catalog browsing has no user-facing sort control in the first version. Results
  use backend-owned display order by fixed category order and explicit per-SKU
  display order.
- Browsing includes category filters, a lightweight text search, product cards,
  visible facet badges, and a product detail surface. Dedicated dietary facet
  filter controls are out of scope for the first catalog slice.
- Search is deterministic over product name, primary category label, short
  description, tags, and positive structured facets; no long detail copy,
  embeddings, or AI planner tool integration yet.
- Search query normalization trims whitespace, collapses internal whitespace for
  matching, matches case-insensitively, and treats empty queries as no query. No
  stemming, fuzzy matching, typo correction, or ranking.
- Multi-token search uses token AND across the product's combined searchable
  text, not token OR.
- Catalog imagery is generated as one distinct static image per SKU, using a
  dedicated Tavola catalog image style skill for consistent background,
  lighting, framing, and mood.
- Backend catalog responses expose `image_id`; the frontend maps image IDs to
  committed static assets.
- Customer-facing catalog browsing, search, and detail endpoints expose only
  available SKUs. Availability still remains a backend field for later
  deterministic basket and planner validation.
- All 20 seed catalog SKUs are available in the first catalog slice; unavailable
  behavior is tested with separate test-only fixtures, not production seed data.
- Customer-facing catalog API responses do not expose raw tags or availability
  fields in the first catalog slice.
- Seed catalog products meet the content quality bar in `CONTEXT.md`: real
  deli-style name, stable SKU slug, primary category, required unit label, GBP
  price, one sentence short description, one to two sentence detail description,
  at least two tags, dietary facet booleans, image ID, and explicit display
  order.
- Accessibility and desktop-browser layout are part of the first slice. Mobile
  layouts and interactions are out of scope unless explicitly requested.

## Decisions

- Model the first catalog as single sellable SKUs rather than a separate
  product/variant hierarchy.
- Use immutable Python domain objects for SKU, category, money, facets, and
  catalog filtering.
- Expose API responses through Pydantic schemas even if internal domain objects
  use dataclasses.
- Application catalog use cases may return domain `CatalogSku` objects and
  simple result wrappers; the API maps them to Pydantic response schemas. Do not
  add a separate application DTO layer until response shapes genuinely diverge.
- Keep seed data as explicit Python data in infrastructure for type checking and
  simple tests.
- Add React feature code under `frontend/src/features/catalog/` and keep API
  transport under `frontend/src/api/`.
- Keep routing simple: the home page can become the catalog browsing screen, and
  product detail should use an in-page side panel for the desktop browser
  experience. This keeps browsing context visible without requiring React Router
  or a modal-first interaction.
- Frontend category, search, and selected-detail state stays local to the
  catalog browser in the first slice; it is not synchronized to the browser URL.
- Create a small reusable skill for Tavola catalog image generation before
  producing SKU images, so future catalog additions keep the same visual style.

## References Consulted

- FastAPI bigger applications and `APIRouter`:
  https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI testing with `TestClient`:
  https://fastapi.tiangolo.com/tutorial/testing/
- Vite development server proxy options:
  https://vite.dev/config/server-options
- React conditional rendering:
  https://react.dev/learn/conditional-rendering

## Prerequisites

- Existing backend and frontend scaffold from
  `docs/plans/backend-frontend-scaffold-plan.md`.
- Backend dependencies installed with `cd backend && uv sync`.
- Frontend dependencies installed with `cd frontend && npm install`.
- Existing local API proxy remains available for `/api/*` during Vite
  development.

## Sprint 1: Catalog Domain And Seed Inventory

**Goal**: Define the catalog's core domain vocabulary and provide a trustworthy
seed catalog that can be tested without HTTP or React.

**Demo/Validation**:

- `cd backend && uv run pytest tests/test_catalog_domain.py tests/test_catalog_seed.py`
- A developer can import the seed catalog and inspect 20 SKUs across the five
  customer-facing categories.
- Domain tests prove invalid price, category, SKU ID, and quantity-like values
  cannot enter the catalog model.

### Task 1.1: Add Catalog Domain Value Objects

- **Location**: `backend/src/tavola/domain/catalog.py`,
  `backend/tests/test_catalog_domain.py`
- **Description**: Add immutable domain types for `Money`, `CatalogCategory`,
  `DietaryFacets`, and `CatalogSku`. Keep them framework-free and enforce basic
  invariants such as non-empty stable SKU slug, non-empty name, non-negative
  price, supported currency, coherent category values, and positive display
  order.
- **Dependencies**: None
- **Acceptance Criteria**:
  - Domain module imports no FastAPI or Pydantic symbols.
  - `Money` stores amount in minor units and currency.
  - `CatalogSku` exposes availability, display order, unit label, short
    description, detail description, tags, facets, and image ID.
  - Dietary facet fields are `is_vegetarian`, `is_vegan`, `is_gluten_free`, and
    `contains_alcohol`.
  - Invalid domain objects raise clear `ValueError`s.
- **Validation**: Domain unit tests for valid and invalid objects.

### Task 1.2: Add Static Seed Catalog

- **Location**: `backend/src/tavola/infrastructure/catalog_seed.py`,
  `backend/tests/test_catalog_seed.py`
- **Description**: Create a 20-SKU seed catalog with exactly 5 Antipasti, 6
  Primi, 3 Desserts, 3 Drinks, and 3 Pantry items. Include realistic names,
  display order, short descriptions, detail descriptions, unit labels, prices,
  tags, dietary facets, availability, and image IDs.
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - Exactly 20 unique available SKU IDs are present.
  - SKU IDs are stable human-readable slugs.
  - Every SKU has exactly one customer-facing primary category, unit label, and
    backend-owned price.
  - Every SKU has an explicit display order within its category.
  - Every SKU has at least two lower-case constrained tags.
  - Every SKU has one sentence of short description and one to two sentences of
    detail description.
  - At least one useful dietary facet is represented in each category where it
    is plausible.
  - Missing unit labels, unclear descriptions, invalid image IDs, or weak tags
    are treated as seed catalog data-quality failures.
- **Validation**: Seed tests assert count, uniqueness, category distribution,
  price shape, tag format, and non-empty customer copy.

### Task 1.3: Add Catalog Repository Interface And Static Adapter

- **Location**: `backend/src/tavola/application/catalog.py`,
  `backend/src/tavola/infrastructure/catalog_repository.py`,
  `backend/tests/test_catalog_repository.py`
- **Description**: Define an application-facing catalog repository protocol and
  implement a static in-memory adapter backed by the seed catalog.
- **Dependencies**: Tasks 1.1, 1.2
- **Acceptance Criteria**:
  - Application code depends on a protocol, not the seed module directly.
  - Static repository can list all SKUs and fetch one SKU by ID.
  - Missing SKU lookup returns a predictable absence value rather than raising
    an infrastructure-specific error.
- **Validation**: Repository tests for list order, ID lookup, and missing lookup.

**Implementation note (2026-06-04)**: Sprint 1 is implemented. The catalog
domain value objects live in `tavola.domain.catalog`, the static 20-SKU seed
catalog lives in `tavola.infrastructure.catalog_seed`, and the application
repository protocol plus static adapter live in `tavola.application.catalog` and
`tavola.infrastructure.catalog_repository`.

## Sprint 2: Catalog Application Use Cases And API

**Goal**: Expose backend catalog browsing through stable HTTP endpoints while
keeping filtering and search behavior outside the API transport layer.

**Demo/Validation**:

- `cd backend && uv run pytest tests/test_catalog_api.py tests/test_catalog_use_cases.py`
- `GET /api/catalog` returns the seed catalog.
- `GET /api/catalog?category=primi&q=pasta` returns a filtered list.
- `GET /api/catalog/products/{sku_id}` returns detail for a known available SKU
  and 404 for a missing or unavailable SKU.

### Task 2.1: Add Catalog Query Use Case

- **Location**: `backend/src/tavola/application/catalog.py`,
  `backend/tests/test_catalog_use_cases.py`
- **Description**: Add a `BrowseCatalog` use case that accepts optional category
  and text query filters. Search should match name, category, short description,
  tags, and objective facets.
- **Dependencies**: Sprint 1
- **Acceptance Criteria**:
  - Empty filters return all 20 available seed catalog SKUs in backend-owned
    display order.
  - Category filters are case-insensitive at the API boundary but normalized
    to stable category IDs before application use.
  - Text search is deterministic and limited to product name, primary category
    label, short description, tags, and positive structured facets.
  - Search query normalization is covered for trimming, case-insensitivity,
    internal whitespace, and empty query behavior.
  - Multi-token search requires every token to match somewhere in the combined
    searchable text.
  - Filtering logic is covered outside API tests.
- **Validation**: Use-case tests for all products, category filter, text search,
  combined filters, no results, and unavailable item behavior using separate
  test-only fixtures.

### Task 2.2: Add Product Detail Use Case

- **Location**: `backend/src/tavola/application/catalog.py`,
  `backend/tests/test_catalog_use_cases.py`
- **Description**: Add a `GetCatalogSkuDetail` use case for fetching a single
  available SKU by ID with all customer-facing detail fields needed by the
  frontend.
- **Dependencies**: Sprint 1
- **Acceptance Criteria**:
  - Known available SKU returns detail data.
  - Unknown or unavailable SKU returns a not-found result that the API can map
    to 404.
  - Use case does not know about HTTP status codes.
- **Validation**: Use-case tests for known and unknown SKU IDs.

### Task 2.3: Add API Schemas And Catalog Router

- **Location**: `backend/src/tavola/api/schemas/catalog.py`,
  `backend/src/tavola/api/routers/catalog.py`,
  `backend/src/tavola/api/dependencies.py`,
  `backend/src/tavola/api/main.py`,
  `backend/tests/test_catalog_api.py`
- **Description**: Add Pydantic response models and FastAPI routes for catalog
  listing and SKU detail. Wire the static repository through a small dependency
  function so later persistence can replace it.
- **Dependencies**: Tasks 2.1, 2.2
- **Acceptance Criteria**:
  - `GET /api/catalog` returns a typed list response with categories and
    products.
  - Product response objects include `sku_id` as the stable basket identity.
  - Product summaries include `sku_id`, `name`, `category_id`,
    `category_label`, `unit_label`, `unit_price_minor`, `currency`,
    `short_description`, dietary facet booleans, and `image_id`.
  - Product detail responses add `detail_description`.
  - Customer-facing responses do not expose raw tags or availability fields.
  - The list response includes ordered category metadata for rendering filter
    controls.
  - `GET /api/catalog/products/{sku_id}` returns a typed detail response for
    available SKUs.
  - Invalid category query values return 422 with a predictable validation
    response.
  - Valid filters with no matching products return 200 with an empty products
    list.
  - Missing or unavailable SKU returns 404.
  - Static repository is provided through a small FastAPI dependency function
    that tests can override; no service container is introduced.
  - `main.py` remains a thin router registration point.
- **Validation**: API tests for happy path, filters, empty result, invalid
  category, and missing SKU.

### Task 2.4: Update Backend Package Layout Tests

- **Location**: `backend/tests/test_package_layout.py`
- **Description**: Extend package layout tests to include catalog modules and
  assert the domain layer remains importable without API infrastructure.
- **Dependencies**: Task 2.3
- **Acceptance Criteria**:
  - Package layout tests cover new catalog modules.
  - A simple import smoke test catches accidental layer cycles.
- **Validation**: `cd backend && uv run pytest tests/test_package_layout.py`

**Implementation note (2026-06-04)**: Sprint 2 is implemented. Catalog browsing
and detail use cases live in `tavola.application.catalog`, the public catalog
API uses Pydantic schemas under `tavola.api.schemas.catalog`, and the catalog
router is wired through `tavola.api.main` with a small overridable static
repository dependency.

## Sprint 3: Frontend Catalog Client And Types

**Goal**: Let React request catalog data through a typed client while preserving
explicit loading, error, empty, and success values for the UI.

**Demo/Validation**:

- `cd frontend && npm test -- src/api/catalog.test.ts`
- The frontend API client maps valid catalog responses into typed values.
- Invalid or failed responses become predictable errors, not thrown component
  failures.

### Task 3.1: Add Frontend Catalog Types

- **Location**: `frontend/src/types/catalog.ts`
- **Description**: Define TypeScript types for catalog category metadata, money,
  dietary facets, catalog product summary, catalog product detail, filter state,
  and catalog API result shapes.
- **Dependencies**: Sprint 2 API contract
- **Acceptance Criteria**:
  - Types mirror backend response names intentionally.
  - Catalog list response includes ordered category metadata and product
    summaries.
  - Product summary and detail types do not include raw tags or availability
    fields.
  - Money remains integer minor units plus currency until formatted for display,
    with the first seed catalog using GBP.
  - Category values are constrained to the five initial categories.
  - Dietary facet fields are `is_vegetarian`, `is_vegan`, `is_gluten_free`, and
    `contains_alcohol`.
- **Validation**: TypeScript build catches invalid category or missing required
  fields.

### Task 3.2: Add Catalog API Client

- **Location**: `frontend/src/api/catalog.ts`,
  `frontend/src/api/catalog.test.ts`
- **Description**: Add `getCatalog` and `getCatalogProduct` functions using the
  existing `apiGetJson` wrapper. Validate response shape with lightweight type
  guards before returning success.
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - Client builds query strings for category and search filters safely.
  - Client returns predictable `ApiResult` values for HTTP, network, and invalid
    response failures.
  - Components do not construct catalog URLs directly.
- **Validation**: API client tests with mocked `fetch` for list, filters, detail,
  HTTP error, transport error, and invalid response.

### Task 3.3: Add Price And Facet Formatting Helpers

- **Location**: `frontend/src/features/catalog/catalogFormat.ts`,
  `frontend/src/features/catalog/catalogFormat.test.ts`
- **Description**: Add focused formatting helpers for currency display, category
  labels, and dietary facet badges.
- **Dependencies**: Task 3.1
- **Acceptance Criteria**:
  - Price display uses backend minor units and currency, formatted for GBP with
    `Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" })` or an
    equivalent currency-aware helper.
  - Formatting helpers are pure and independent from React components.
  - Facet labels avoid unsupported allergen or medical safety claims; use
    Gluten-free, not Coeliac-safe or allergen-free.
- **Validation**: Helper unit tests for currency, categories, and facet labels.

**Implementation note (2026-06-04)**: Sprint 3 is implemented. Frontend catalog
types live in `frontend/src/types/catalog.ts`, the typed catalog API client lives
in `frontend/src/api/catalog.ts`, and pure category, money, and dietary facet
formatting helpers live under `frontend/src/features/catalog/catalogFormat.ts`.
The client keeps query-string construction and response validation out of React
components.

## Sprint 4: Browsing UI

**Goal**: Replace the placeholder storefront workspace with a usable catalog
browser that is practical, local, trustworthy, and ready for later basket work.

**Demo/Validation**:

- `cd frontend && npm test -- src/App.test.tsx src/features/catalog`
- With backend running, the first screen shows category controls, search, product
  cards, detail access, loading, empty, and error states.
- At the supported desktop width, filters, cards, and the detail side panel
  remain usable with no text overlap.

### Task 4.1: Add Catalog Feature State Hook

- **Location**: `frontend/src/features/catalog/useCatalogBrowser.ts`,
  `frontend/src/features/catalog/useCatalogBrowser.test.ts`
- **Description**: Add a hook that owns category selection, search text,
  selected SKU ID, catalog loading state, detail loading state, and reload
  behavior.
- **Dependencies**: Sprint 3
- **Acceptance Criteria**:
  - Hook exposes explicit `loading`, `success`, `empty`, and `error` states.
  - List request failure shows a catalog-level error state with reload.
  - Category changes trigger list refresh.
  - Search text is committed on submit/Enter or Search button, not on every
    keystroke.
  - Changing category or committed search closes any open product detail panel.
  - Reset clears category, draft search, committed search, and selected detail,
    then refetches the unfiltered catalog.
  - The hook does not expose user-facing sort state in the first version.
  - Browser URL is not mutated when filters or selected detail change.
  - Detail selection fetches a SKU detail without coupling cards to transport.
  - Detail request failure shows a detail-level error state that can be closed
    without replacing the whole catalog grid.
  - Reload can recover from failed list requests.
- **Validation**: Hook tests with mocked catalog client behavior.

### Task 4.2: Build Catalog Filter Controls

- **Location**: `frontend/src/features/catalog/CatalogFilters.tsx`,
  `frontend/src/features/catalog/CatalogFilters.test.tsx`
- **Description**: Add accessible category segmented controls and a search input
  for deterministic catalog browsing. Do not add dedicated dietary facet filter
  controls in this slice.
- **Dependencies**: Task 4.1
- **Acceptance Criteria**:
  - Category controls are keyboard accessible.
  - Category controls render from ordered API category metadata rather than a
    frontend-only category list.
  - An `All` control is frontend-only and omits the `category` query parameter
    while preserving any committed search term.
  - Search input has a visible label.
  - Search submits on Enter and via a Search button.
  - A reset control clears search, returns to All categories, closes detail, and
    reloads the unfiltered catalog.
  - Dietary facets are searchable through text input but are not separate filter
    controls.
  - Controls do not resize unpredictably across states.
- **Validation**: Component tests for selecting categories, entering search
  text, and clearing filters.

### Task 4.3: Build Product Card Grid

- **Location**: `frontend/src/features/catalog/CatalogGrid.tsx`,
  `frontend/src/features/catalog/CatalogCard.tsx`,
  `frontend/src/features/catalog/CatalogGrid.test.tsx`
- **Description**: Render desktop-first product cards with image, name, category,
  unit label, price, short description, dietary badges, and a detail action.
- **Dependencies**: Tasks 3.3, 4.1
- **Acceptance Criteria**:
  - Cards use semantic list markup.
  - Browse results render only available SKUs returned by the backend.
  - Empty results state explains that no products match the current filters and
    offers the reset action.
  - Price comes from backend data.
  - The detail action is accessible and does not imply basket add behavior.
- **Validation**: Component tests for product rendering, available-only browse
  results, and detail action callback.

### Task 4.4: Build Product Detail Surface

- **Location**: `frontend/src/features/catalog/CatalogDetail.tsx`,
  `frontend/src/features/catalog/CatalogDetail.test.tsx`
- **Description**: Add an in-page product detail side panel showing detail
  description, larger image, unit label, price, visible facets, and category. Do
  not include add-to-basket buttons, disabled basket placeholders, raw tag
  rendering, separate `good_for` fields, or other dead purchase controls in this
  slice.
- **Dependencies**: Tasks 4.1, 4.3
- **Acceptance Criteria**:
  - Detail surface can be opened and closed by mouse and keyboard.
  - Loading and error states are explicit.
  - Detail fetch errors stay scoped to the detail side panel.
  - Copy does not promise checkout or basket behavior yet.
  - No add-to-basket button or disabled basket placeholder is shown.
  - No frontend-only pricing calculations are introduced.
  - Desktop layout preserves nearby browsing context and keeps the panel readable
    without covering the catalog grid unnecessarily.
- **Validation**: Component tests for open, close, loading, error, and populated
  detail states, plus manual desktop browser checks.

### Task 4.5: Compose Catalog Browser On Home Page

- **Location**: `frontend/src/pages/HomePage.tsx`,
  `frontend/src/App.test.tsx`
- **Description**: Replace workflow placeholder content with the catalog browser
  as the first screen. Keep backend status available in a compact way if useful,
  but make catalog browsing the main experience.
- **Dependencies**: Tasks 4.1 through 4.4
- **Acceptance Criteria**:
  - The first viewport clearly signals Tavola and real deli products.
  - Placeholder navigation no longer disables the catalog path.
  - Basket and checkout remain visibly future or inactive without confusing the
    user.
  - Existing app tests are updated to assert catalog behavior instead of scaffold
    placeholder behavior.
- **Validation**: App tests for catalog first screen and backend status behavior.

**Implementation note (2026-06-04)**: Sprint 4 is implemented. The catalog
browser state hook lives in `frontend/src/features/catalog/useCatalogBrowser.ts`,
filter controls, card grid, and detail panel live under
`frontend/src/features/catalog/`, and the home page now presents catalog browsing
as Tavola's first screen while keeping basket and checkout visibly planned.

## Sprint 5: Static Imagery, Polish, And Smoke Checks

**Goal**: Make the catalog feel complete enough to demo and verify the
cross-service feature from backend seed data to frontend browsing.

**Demo/Validation**:

- Run the full scaffold smoke checklist in `docs/scaffold-smoke-check.md`.
- With both dev servers running, browse all five categories, search for at least
  three terms, open product detail, and verify prices, facets, and images match
  the backend response and frontend image map.
- Capture any unchecked smoke items in the implementation handoff.

### Task 5.1: Create Tavola Catalog Image Style Skill

- **Location**:
  `/Users/jaki/Projects/tavola/.codex/skills/tavola-catalog-image-style/SKILL.md`,
  optional `references/` or `assets/` under the same skill directory
- **Description**: Create a concise Codex skill for generating Tavola catalog
  product images with consistent style. The skill should specify shared
  background, lighting, camera angle, framing, color temperature, image size,
  and negative constraints such as no text overlays, no logos, and no unrelated
  props.
- **Dependencies**: Seed catalog names and descriptions from Sprint 1
- **Acceptance Criteria**:
  - Skill frontmatter clearly triggers on Tavola catalog product image
    generation.
  - Skill is repo-local so Tavola-specific product art direction travels with
    the project.
  - Skill body stays lean and gives reusable prompt structure for one SKU at a
    time or a batch of SKUs.
  - Style guidance produces cohesive images while leaving enough room for each
    SKU to look distinct.
  - Generated assets are still static committed files; the application performs
    no runtime image generation.
- **Validation**: Use the skill on one representative antipasti SKU and one
  primi SKU, inspect outputs for consistent style, then refine the skill before
  generating the full set.

### Task 5.2: Add Static Catalog Image Assets

- **Location**: `frontend/src/assets/catalog/`,
  `frontend/src/features/catalog/catalogImages.ts`,
  `backend/src/tavola/infrastructure/catalog_seed.py`
- **Description**: Generate and add one distinct static image file for each of
  the 20 seed SKUs using the Tavola catalog image style skill. Ensure backend
  `image_id` values map to frontend asset references predictably through an
  explicit imported asset map.
- **Dependencies**: Task 5.1, Sprint 4 UI can render image references
- **Acceptance Criteria**:
  - Every SKU card has its own relevant, inspectable product image.
  - Images share a consistent Tavola visual language for background, lighting,
    framing, and product scale.
  - Images live under `frontend/src/assets/catalog/`, not `frontend/public/`.
  - `catalogImages.ts` maps backend `image_id` values to imported assets.
  - Unknown image IDs render a designed fallback image at runtime.
  - Tests catch missing image mappings for the known seed catalog.
  - No runtime image generation is required.
- **Validation**: Browser check of catalog cards and detail images.

### Task 5.3: Tighten Desktop Styling

- **Location**: `frontend/src/styles.css`,
  catalog feature CSS colocated only if the project adopts that pattern
- **Description**: Update styling for catalog controls, cards, detail surface,
  empty state, error state, and desktop layout while respecting the existing
  restrained storefront visual direction.
- **Dependencies**: Sprint 4
- **Acceptance Criteria**:
  - Text does not overlap or overflow at the supported desktop width.
  - Category controls and product cards have stable dimensions.
  - The palette remains varied and deli-appropriate without becoming a one-note
    cream, red, or green theme.
  - Cards stay at 8px radius or less.
- **Validation**: Manual browser checks at the supported desktop viewport width.

### Task 5.4: Run Backend Quality Gates

- **Location**: `backend/`
- **Description**: Run backend install, tests, lint, and format checks for the
  catalog slice.
- **Dependencies**: Sprints 1 and 2
- **Acceptance Criteria**:
  - Backend dependencies sync successfully.
  - Backend tests pass.
  - Ruff lint and format checks pass.
- **Validation**:
  - `cd backend && uv sync`
  - `cd backend && uv run pytest`
  - `cd backend && uv run ruff check .`
  - `cd backend && uv run ruff format --check .`

### Task 5.5: Run Frontend Quality Gates

- **Location**: `frontend/`
- **Description**: Run frontend install, tests, lint, and production build for
  the catalog slice.
- **Dependencies**: Sprints 3 and 4
- **Acceptance Criteria**:
  - Frontend dependencies install successfully.
  - Frontend tests pass.
  - ESLint passes.
  - Production build passes.
- **Validation**:
  - `cd frontend && npm install`
  - `cd frontend && npm test`
  - `cd frontend && npm run lint`
  - `cd frontend && npm run build`

### Task 5.6: Run Cross-Service Browser Smoke Check

- **Location**: `docs/scaffold-smoke-check.md`
- **Description**: Start both services and manually verify the full catalog
  browsing flow through the Vite proxy.
- **Dependencies**: Tasks 5.4, 5.5
- **Acceptance Criteria**:
  - Backend health and catalog endpoints return HTTP 200 locally.
  - Frontend loads catalog data through `/api/catalog`.
  - Customer can filter, search, open detail, recover from an error by reload,
    and see empty states.
  - Any unchecked smoke checklist items are reported explicitly.
- **Validation**: Complete and report the scaffold smoke checklist.

## Testing Strategy

- Domain tests prove catalog invariants without network or framework imports.
- Application tests cover filtering, deterministic search, SKU detail lookup,
  unavailable behavior, and missing SKU results.
- API tests cover response shapes, query handling, validation errors, 404s, and
  route registration under the configured API prefix.
- Frontend API tests cover request URLs, query strings, response validation, and
  error mapping.
- Frontend component and hook tests cover browsing states, filter interactions,
  product cards, detail opening and closing, and failed/empty states.
- Frontend image-map tests catch missing static asset mappings for known seed
  catalog image IDs while components still render a fallback for unknown IDs.
- Manual browser checks verify desktop layout, image rendering, keyboard
  access, and the real backend-to-frontend flow.

## Potential Risks & Gotchas

- **Product/SKU naming drift**: The product context says initial catalog items
  should be single sellable SKUs, but customer copy may still say "products".
  Keep API/domain names SKU-aware and UI copy customer-friendly.
- **Search scope creep**: Search should stay deterministic and explainable. Do
  not add ranking engines, embeddings, fuzzy libraries, or planner-specific
  behavior in this slice.
- **Imagery cost and churn**: Static images will make the slice feel real, but
  creating 20 distinct assets may slow implementation. Mitigate by creating and
  validating the image style skill on two representative SKUs before generating
  the full set.
- **Unavailable SKU presentation**: Unavailable SKUs are excluded from all
  customer-facing catalog endpoints, but availability should remain explicit in
  backend data so later basket and planner validation can reject unavailable SKU
  IDs deterministically.
- **API contract churn**: Basket and planner slices will reuse catalog SKU data.
  Avoid frontend-only fields or response names that will be awkward for basket
  validation later.
- **Layout regression**: The current scaffold uses large placeholder sections.
  Replacing them with dense catalog controls needs desktop browser testing so
  text and actions do not collide.

## Rollback Plan

- Revert catalog router registration in `backend/src/tavola/api/main.py` to
  remove the public API surface.
- Remove or ignore the new catalog feature directory from
  `frontend/src/pages/HomePage.tsx` and restore the scaffold workspace shell.
- Keep domain and seed modules if they are useful for the next attempt; otherwise
  remove the `catalog` modules and associated tests in the same commit.
- Because no database or external service is introduced, rollback requires no
  migration or data cleanup.
