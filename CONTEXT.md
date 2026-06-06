# Tavola Product Context

Tavola is small e-commerce app for independent Italian deli. Goal: demonstrate
focused commerce flow + clear domain-driven architecture, not full marketplace or
enterprise commerce.

Customer promise: browse real deli products, build basket, complete mock pickup
checkout, optionally ask Planner for occasion/meal help. AI suggestions must map
to real SKUs before basket.

## Build Order

1. Catalog browsing.
2. Basket creation/editing.
3. Mock pickup checkout.
4. Menu-to-basket Planner.
5. Proposal review + basket acceptance.

Prove ordinary commerce before AI. Planner builds on trusted catalog/basket path;
it never creates parallel cart flow.

## Core Scope

In:

- Product browsing + detail.
- Basket creation/editing.
- Mock pickup checkout.
- Catalog search for planner support.
- Planner sessions -> validated menu proposals.
- Deterministic validation before basket mutation.
- Static generated catalog imagery for seed inventory.
- Desktop browser demonstrator.

Out unless explicit:

- Mobile-specific layout/interaction.
- Real payments, shipping, fulfillment, delivery.
- Accounts, loyalty, promos, coupons, gift cards, complex pricing.
- Inventory reservation.
- Marketplace/multi-vendor/multi-store.
- Advanced order management.
- Recipe DB, recipe instructions, exact serving guarantees.
- Runtime image generation.

## Storefront UX

- Workflows: customer nav labels **Shop** and **Plan**; domain terms
  **Catalog** and **Planner** stay valid in code/docs.
- Catalog/Shop default on fresh load. Tavola brand click returns to Shop without
  clearing Basket/Planner state.
- Shop heading: **Shop**. Plan heading: **Plan a menu**.
- Top banner prioritizes Tavola brand + Shop/Plan tabs. No backend status in
  primary storefront header.
- Shop/Plan are in-page workflow tabs, not routes/deep links.
- Basket remains visible on Shop and Plan, including empty state.
- Switching workflows preserves catalog category/search and planner proposal
  edits. It does not preserve open product detail across workflows.
- Switching away from Plan during Planning does not cancel session.
- Proposal-ready indicator may appear on Plan tab when proposal becomes ready
  while user is in Shop. It clears when Plan opens. Banner must not become status
  dashboard.
- Planning updates may appear inside the Planner surface only. They must come
  from Tavola's backend lifecycle, not elapsed-time guesses, and must not turn
  the top banner into a status dashboard.
- Planner input state stays compact; proposal review may expand.
- After proposal acceptance, stay in Planner and visibly update Basket.
- Opening desktop screen: no separate masthead between top bar and commerce flow.
  First meaningful content is Shop.
- Opening Shop copy should be compact/action-oriented, e.g. "Fresh from the
  counter" + "Browse Tavola's catalog, then add your picks to the basket."
- At 1366x768: show Shop heading, controls, and at least top half first product
  row without scrolling.
- Category filters and search remain visible on desktop catalog; make dense
  enough to preserve product visibility.
- Product counts are compact metadata, not large summary cards.
- Basket empty copy uses shopping language, not implementation language.

## Domain Language

- **Product**: sellable deli item shown to customers. First catalog: one SKU per
  product.
- **SKU**: concrete catalog identity for basket validation/pricing. Internal/API
  term only; visible UI says Product/item.
- **Unit label**: free-text sellable unit, e.g. `250g`, `serves 2`, `750ml`.
- **Short description**: compact catalog-card/search sentence.
- **Detail description**: richer product-detail copy; not searched initially.
- **Catalog**: browsable/searchable available products/SKUs.
- **Seed catalog**: static demonstrator catalog data.
- **Category**: customer navigation group. One primary category per product.
- **Basket**: current intended purchases.
- **Basket line**: one SKU + quantity.
- **Basket quantity**: positive integer count of SKU units.
- **Checkout**: mock flow finalizing basket into demo order.
- **Contact details**: name/email for one order; not account/profile.
- **Order**: pickup-only demo record; not payment/fulfillment state.
- **Order ID**: customer-facing confirmation ref; no lookup/management implied.
- **Order line**: checkout-time snapshot of SKU line + price details.
- **Pickup window**: backend-defined choice; no capacity/live schedule.
- **Planner**: Tavola assistant for meal request -> menu proposal. Codex is impl
  tech; "powered by Codex" only inside Planner surface.
- **Planner session**: bounded AI-assisted workflow.
- **Planning**: in-progress live session. Avoid "processing", "job", "run",
  "Codex run" in customer/domain language.
- **Planning update**: customer-visible progress entry emitted during Planning.
  Distinct from session status and runtime availability; avoid "status update",
  "progress phase", "Codex step".
- **Menu proposal**: suggested meal plan under review, after validation and
  before basket acceptance.
- **Planner note**: customer-facing explainability: evidence, constraints,
  validation, assumptions.
- **Party size**: people served; required for responsible quantities.
- **Course**: proposal role, e.g. Antipasto, Primo, Dessert, Drinks, Aperitivo.
  Not same as category.
- **Package template**: planner-only required course structure. Not purchasable.
- **Meal-plan grouping**: optional accepted-proposal metadata in basket/order:
  title, party size, template, course names, line grouping. SKU lines stay price
  authority.
- **Validated menu proposal**: proposal that passed deterministic checks. Avoid
  "validated basket" / "basket proposal".
- **Catalog candidate**: implementation term for products returned to Planner;
  not customer-facing/domain term.

## Product, SKU, Basket

- Customers browse Products; Basket/checkout/planner validation reference SKUs.
- Each initial Product has exactly one SKU.
- Basket has max one line per SKU. Adding same SKU merges by increasing qty.
- Basket lines store SKU identity + qty. Display resolves product details/prices
  from current backend catalog.
- Basket qty counts SKU units. Qty `2` of `250g` tagliatelle = two packs.
- Unit labels are not parsed as measurements. They can guide planner quantities
  but never exact serving guarantees.
- Catalog browsing/search/detail expose only buyable products. Unavailable SKU is
  defensive validation state, not product experience.
- API may expose `sku_id`; visible UI/errors/planner notes/checkout copy must say
  Product/item.
- Customer-facing validation errors: action-oriented product problems. Internal
  error codes may mention SKU.

## Seed Catalog

- Backend serves small static seed catalog. It is product data, not throwaway
  mock data.
- Exactly 20 SKUs: 5 Antipasti, 6 Primi, 3 Desserts, 3 Drinks, 3 Pantry.
- All 20 available in first catalog slice.
- Each item needs: deli-style name, stable SKU slug, primary category, unit
  label, GBP price, one-sentence short desc, one/two-sentence detail desc, at
  least two tags, dietary facets, image ID, display order.
- Categories are canonical labels: Antipasti, Primi, Desserts, Drinks, Pantry.
  Do not rename to Starters/Mains/Pasta/Beverages/Pantry Staples unless product
  language revisited.
- Category IDs: `antipasti`, `primi`, `desserts`, `drinks`, `pantry`.
- SKU IDs: stable human-readable slugs, e.g. `fresh-tagliatelle-250g`.
- Primi may include prepared dishes plus composed options like pasta + sauce.
- Prices: backend-owned integer minor units + currency
  (`unit_price_minor`, `currency`). First catalog GBP. Totals recalculated
  server-side. Tax-inclusive; no VAT breakdown.
- Catalog results use backend-owned display order:
  Antipasti -> Primi -> Desserts -> Drinks -> Pantry; products by explicit order.
  Search preserves curated order. No user-facing sort control first version.
- Catalog products expose `image_id`; frontend maps to committed static assets.

## Catalog Metadata + Search

Use structured facets for objective hard checks; tags for fuzzy search/planning.

Facets:

- `is_vegetarian` -> Vegetarian.
- `is_vegan` -> Vegan.
- `is_gluten_free` -> Gluten-free.
- `contains_alcohol` -> Contains alcohol.

Rules:

- Dietary constraints use facets, not tags.
- Gluten-free must not imply Coeliac-safe/allergen-free/medical suitability
  without explicit future allergen metadata.
- Tags support search/planner discovery: roles, occasions, meal moments,
  pairings, uses (`pasta`, `sauce`, `dinner-party`, `picnic`, etc.).
- Tags are lower-case, constrained, non-customer taxonomy. Raw tags not rendered.
- Tags may hint course/use, e.g. Pantry sugo tagged `primo`, but facets win hard
  validation.
- Facet/tag contradictions mean catalog data-quality bug; hard validation trusts
  facets.
- Catalog API first slice does not expose raw tags or availability.
- Search matches product name, category label, short desc, tags, positive facets.
  Detail desc excluded.
- Search normalization: trim, collapse whitespace, case-insensitive. Empty query
  = no query. No stemming/fuzzy/typo/ranking.
- Multi-token search = AND; every token must match combined searchable text.
- First catalog search matches dietary facets, but browse cards may omit facet
  badges to keep product scanning calm. No dedicated facet filters.
- Product detail adds detail desc, larger image, unit label, price, visible
  facets. No add-to-basket controls before basket slice.

## Basket Validation

First basket model: backend-owned, anonymous, in-memory. Frontend stores basket
ID in localStorage. If backend loses basket on restart, frontend creates new one.

Rules:

- SKU exists.
- Defensive availability guard passes.
- Qty is positive integer.
- Qty <= 10 per SKU line.
- Totals calculated backend-side from catalog prices.

Per-line max is validation rule, not catalog browsing copy.

## Checkout

- In-memory demo order, pickup only.
- Requires contact details + backend-defined pickup window.
- No payment, shipping, delivery, account, marketing consent, phone, address,
  deliverability checks, strict email parsing.
- Contact validation: non-blank name; email has text before/after `@`.
- Pickup windows: static stable IDs + labels. No calendar/capacity/opening hours.
- Frontend displays backend pickup windows and submits selected ID.
- Backend validates ID and stores selected label on order snapshot.
- Successful checkout creates order snapshot and empties current basket.
- Basket remains current editable basket; no separate checked-out basket
  lifecycle.
- Order may store originating basket ID as provenance.
- Order ID shown on confirmation only; no retrieve/manage/update flow.
- Checkout validates SKU identities against current catalog before order.
- Order lines snapshot customer-facing SKU/price details at checkout.
- Checkout API creates confirmation order; no order history/status/lookup.
- Customer copy frames practical pickup order. Avoid "mock payment" /
  "continue without payment."

## Planner Product Rules

- Planner = Tavola customer workflow; Codex = implementation technology.
- Catalog and Planner are sibling storefront workflows with Basket companion.
- Customer describes occasion/meal (dinner party, picnic, antipasti board,
  family lunch).
- Planner uses bounded session + catalog search/validation tools.
- It proposes menu, maps to real SKUs, repairs invalid plans if needed, returns
  validated proposal.
- AI may assist ideas/substitutions/composition, but cannot bypass availability,
  SKU validity, qty rules, dietary/budget constraints, or basket validation.
- Planner returns actionable proposal for review; it does not mutate Basket.
- Proposal contains readable explanation, courses, SKU lines, quantities,
  server-priced totals, per-line rationale.
- Customer can remove lines or adjust qty before accepting.
- Planner rationale can explain why SKUs fit course/occasion; no recipe
  instructions, cooking timings, exact serving guarantees.
- If current catalog cannot satisfy request, return closest valid proposal with
  clear assumptions or explain impossible. Never invent SKUs.
- Unsupported allergy/safety constraints must not produce claimed-compliant menu.
  Lower-stakes preferences can be best effort with limitation explained.

## Planner Constraints

- Party size is main required input; ask follow-up only when required info
  missing. Budget/diet/style optional unless mentioned.
- Preserve known party size as structured session context.
- Supported hard constraints: vegetarian, vegan, gluten-free, no-alcohol.
- If user asks one supported constraint for whole menu, every proposed product
  must satisfy it.
- Partial guest constraints (e.g. "6 people, 2 vegetarian") apply to named
  guests. Provide safe coverage; do not claim whole menu vegetarian unless true.
- Soft style prefs: lighter, richer, cozy, special.
- Unsupported constraints (e.g. dairy-free without facet): explain limitation;
  do not claim compliance.
- Approx budget ("around GBP50") = soft target with server total shown.
- Firm cap ("under GBP50") = hard constraint unless no suitable proposal exists.

## Planner Templates + Drinks

Initial package templates:

- Antipasto + Primo + Dessert.
- Antipasto + Primo.
- Primo + Dessert.
- Primo only.
- Aperitivo.

Rules:

- Templates are scaffolds, not purchasable products.
- Basket/checkout always use real SKUs.
- Primo may be one prepared dish or multiple SKUs, e.g. pasta + sauce.
- Drinks are contextual add-ons, not automatic.
- Include drinks only when requested or clearly implied (aperitivo, picnic
  drinks, wine pairing).
- Drinks appear as optional Drinks course appended to template.
- If user asks drinks without specifying alcohol, Planner may include alcoholic
  or non-alcoholic drinks and must explain alcohol assumption.
- No-alcohol requests/signals are hard constraints.
- If requested drinks unavailable, Planner may return closest valid food menu
  with warning unless drinks are main/firm requirement.

## Planner Session Lifecycle

- Session has at most one current Menu proposal first version.
- Live session starts Planning, then becomes follow-up question, menu proposal,
  or failure.
- Answering follow-up returns session to Planning.
- Planning only when live Planner available; disabled Planner creates no session.
- If Planning lasts >30s, show calm slow-state copy; demo run may continue until
  backend timeout.
- Follow-ups happen before proposal exists.
- After proposal ready, first version supports deterministic line removal, qty
  editing, revalidation, acceptance. No conversational refinement like "make it
  cheaper" or "swap dessert."
- Planning independent of current Basket until acceptance. Existing basket does
  not shape first proposal.
- Accepting proposal marks it accepted for session; cannot accept again.
- Customer can start new session or edit basket after acceptance.
- Session stores minimal customer text: original request + latest follow-up.
  Domain record stores normalized context, current proposal, accepted status.
  No full AI/tool transcripts.

## Planner Notes + Proposal Review

- Proposal-level notes: structured customer-facing messages with type:
  constraint applied, catalog checked, pricing checked, quantity assumption,
  assumption, substitution, etc.
- Notes belong to current proposal, not session status.
- Revalidating edited proposal refreshes notes.
- Notes record source: Tavola deterministic validation or planner composition.
  Dietary exclusions/catalog/pricing = Tavola-sourced. Taste/pairing can be
  planner-sourced.
- Notes explain quantity assumptions when party size/unit labels matter, without
  serving guarantees.
- UI shows small proposal-level trust evidence; per-line rationale explains why
  each product belongs.
- Customer may edit quantities/remove lines before acceptance.
- Customer cannot edit course names or move products between courses first
  version.
- Revalidation removes empty courses.
- Editing triggers deterministic revalidation + price recalculation only; no auto
  replacement products.
- Proposal review edits persist across Shop/Plan switches.

## Proposal Acceptance + Meal-Plan Grouping

- Accepting proposal can add to existing Basket or replace all Basket lines.
- Replace removes all current lines, whether catalog-added or earlier planner.
- Add follows normal basket merge: same SKU quantities combine.
- No pre-accept merge preview first version; updated Basket is confirmation.
- Replace basket needs lightweight confirmation when Basket non-empty. No confirm
  when empty.
- Accepted proposal may later carry lightweight meal-plan grouping in basket/order
  summary: proposal title, party size, template, course names, line-course links.
- Grouping stores customer-readable context only. No rationale, transcript, Codex
  metadata, alternatives.
- SKU/order lines remain pricing + checkout truth.
- Grouping survives basket edits only while coherent. Remove all products from a
  grouped course -> remove course. Remove all grouped products -> remove
  grouping. Qty edits keep grouping. Later catalog additions are ungrouped.
- Checkout may preserve grouping metadata from basket to order summary, but mock
  checkout need not add grouping before Planner exists.

## Category vs Course

- Customers browse by Category.
- Planner proposals organize by Course.
- Package templates define required courses; Drinks may append.
- Aperitivo template: food/snacks in Aperitivo; beverages in Drinks when
  requested/implied.
- Product category does not always determine course. Pantry sugo may support
  Primo when paired with pasta.
- Cross-category meaning belongs in tags, not multiple categories.
- Planner may use implementation filtering before choosing lines; intermediate
  matches are not customer-facing meal-plan model.

## Architecture

Tavola uses DDD boundaries:

- API: HTTP transport, request validation, response models, routing.
- Application: use cases/workflows for browsing, basket updates, checkout,
  planner sessions.
- Domain: business rules/invariants for products, SKUs, baskets, validation,
  checkout state.
- Infrastructure: concrete catalog storage, AI adapters/tools, persistence,
  external integrations.

AI is application workflow with explicit tools, not hidden domain logic.
Deterministic validation remains trusted path. Planner accesses catalog via
explicit search/validation tools. Search starts deterministic; embeddings,
personalization, advanced ranking are future.

## Design Principles

- Keep commerce model small/legible.
- Prefer vertical slices for current flow.
- Desktop-first demonstrator; no mobile-specific work unless explicit.
- Invalid planner output must be repairable, not silently accepted.
- AI suggestions must be explainable/reviewable.
- Keep generated ideas separate from validated cart changes.
- Optimize demonstration clarity over platform completeness.
- Keep package context visible after acceptance when useful; packages never own
  pricing.
- Basket remains supporting context during desktop Catalog browsing and future
  Planner entry points.
- Menu proposal review remains visually distinct from actual Basket lines until
  accepted.

## Flagged Ambiguities

- "SKU" OK internal/API; never in customer UI, planner notes, checkout copy,
  visible errors. Use Product/item.
- "Storefront workspace" not canonical. Opening screen = Shop with Basket
  companion.
- "Backend connected"/service status is implementation health, not storefront
  nav/header content.
