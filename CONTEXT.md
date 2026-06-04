# Tavola Product Context

Tavola is a small e-commerce platform for an independent Italian deli. It exists
to demonstrate a focused, understandable commerce flow with a clear
domain-driven architecture rather than to become a fully fledged marketplace or
enterprise commerce system.

Customers can browse deli products, build a basket, and complete a mock checkout.
The product experience should feel practical, local, and trustworthy: a customer
should be able to move from "what should I serve?" to a validated basket of real
deli products without needing to understand the internal architecture.

## Product Purpose

Tavola demonstrates how a lightweight retail application can combine ordinary
commerce workflows with controlled AI assistance.

The core user promise is:

- Customers can discover and select products from a real catalog.
- Customers can build and revise a basket before checkout.
- Customers can complete a mock checkout flow without real payment processing.
- Customers can ask for help planning food for an occasion, meal, or gathering.
- AI-generated suggestions are mapped back to real deli SKUs before reaching the
  basket.

The first demonstrator slice should prove ordinary commerce before AI planning:
catalog browsing, backend-owned basket editing, and mock pickup checkout. The
planner should build on that trusted path rather than introduce a parallel cart
flow.

Initial build order:

1. Catalog browsing.
2. Basket creation and editing.
3. Mock pickup checkout.
4. Menu-to-basket planner.
5. Planner proposal review and basket acceptance.

## Main AI Feature

The main AI feature is a Codex-powered menu-to-basket planner. In product and
domain language, this feature is the **Planner**; Codex is the implementation
technology behind it. The UI may include a small "powered by Codex" attribution,
but customer workflows should still be framed around Tavola's Planner and menu
proposals rather than Codex-specific operations. The attribution belongs in the
Planner surface only; accepted basket and order summaries should return to
Tavola meal-plan language without repeating Codex branding.

A customer describes an occasion or meal need, such as a small dinner party,
picnic, antipasti board, or family lunch. Codex works inside a bounded planning
session using catalog search and validation tools. It proposes a menu, maps that
menu to real deli SKUs, repairs invalid plans when needed, and returns a
validated basket.

The application performs deterministic checks before anything reaches the cart.
The planner may assist with ideas, substitutions, and composition, but it does
not bypass product availability, SKU validity, quantity rules, or basket
validation. The flow is AI-assisted, but still safe, controlled, and inspectable.

The planner should return an actionable proposal for the customer to review, not
mutate the basket directly. A proposal can include a customer-readable menu
explanation, course sections, SKU lines, quantities, server-priced totals, and
concise per-line rationale. The customer can remove lines or adjust quantities
before accepting the proposal into the basket.

Planner proposals should include customer-facing explainability that helps the
customer trust the suggestion. This should describe planning evidence in Tavola
language, such as party size used, template chosen, dietary constraints applied,
excluded non-matching options, catalog validation, and server-calculated pricing.
It should not expose low-level Codex runtime metadata such as model names, tool
counts, retries, thread IDs, or raw transcripts.

Planner rationale may explain why SKUs work together for a course or occasion,
but the planner should not provide recipe instructions, cooking timings, or
exact serving guarantees.

When a request cannot be honestly satisfied from the current catalog, the
planner should either produce the closest valid menu proposal with clear
assumptions or explain that Tavola cannot build that proposal from current SKUs.
It must not invent SKUs or ignore explicit dietary constraints.

Explicit supported dietary constraints are hard constraints for planner
proposals. In the first catalog, Tavola can verify vegetarian, vegan,
gluten-free, and no-alcohol requests through structured facets. If the customer
asks for one of these, every proposed product must satisfy that constraint.
Style preferences such as lighter, richer, cozy, or special are softer planning
preferences.

The planner must not guarantee constraints that Tavola does not track. If a
customer asks for an unsupported constraint, such as dairy-free when no
dairy-free facet exists, the planner should explain the limitation rather than
claiming compliance.

Unsupported safety or allergy-like constraints should stop the planner from
returning a menu proposal that claims to satisfy them. Lower-stakes preferences
may be handled as best-effort only when the limitation is made clear.

Budget language depends on phrasing. Approximate budget requests, such as
"around £50", are soft targets that should be approached transparently with the
server-calculated total shown. Firm budget caps, such as "under £50", are hard
constraints unless the planner explains that no suitable menu proposal can be
built within the cap.

The planner should ask a follow-up question only when required planning
information is missing. Party size is the main required input because quantities
cannot be responsibly suggested without it. Other preferences, such as budget,
dietary needs, and style, may be inferred or treated as optional unless the
customer mentions them. The customer experience remains free-text-first, but
known party size should be preserved as structured planner session context.

Planner composition should use simple package templates rather than arbitrary
recipe generation. Initial templates are:

- Antipasto + Primo + Dessert.
- Antipasto + Primo.
- Primo + Dessert.
- Primo only.
- Aperitivo.

These templates are planning scaffolds, not purchasable products. The basket and
checkout remain based on real SKUs. A course such as Primo may contain one SKU
for a prepared dish or multiple SKUs for a simple pairing, such as fresh pasta
plus sauce.

Drinks are contextual add-ons for planner proposals, not automatic parts of meal
packages. The planner should include drinks only when the customer asks for them
or the occasion clearly implies them, such as an aperitivo, picnic drinks, or a
wine pairing.

Accepted planner proposals may later carry lightweight meal-plan grouping
metadata in the basket and order summary so the customer can still see the shape
of the meal plan after accepting it. This metadata should preserve only
customer-readable context and organization, such as proposal title, party size,
package template, course names, and which basket lines belong to each course.
It should not preserve planner rationale, AI transcript, Codex run metadata, or
alternative suggestions in the basket or order domain. SKU lines remain the
source of pricing and checkout truth.

Checkout should allow future order summaries to preserve optional meal-plan
grouping metadata copied from a basket, while order lines remain the source of
pricing truth. The mock checkout slice does not need to introduce grouping data
before the planner exists.

## Scope

Tavola should stay intentionally small.

In scope:

- Product browsing.
- Product detail information.
- Basket creation and editing.
- Mock checkout.
- Catalog search for planner support.
- Planner sessions that produce validated basket proposals.
- Deterministic validation before cart mutation.
- Static generated catalog imagery for the seed inventory.
- Desktop browser experience for the demonstrator.

Out of scope unless explicitly requested:

- Mobile-specific layout and interaction design.
- Real payment processing.
- Real shipping, fulfillment, or delivery integrations.
- Customer accounts and loyalty systems.
- Promotions, coupons, gift cards, or complex pricing rules.
- Inventory reservation systems.
- Marketplace, multi-vendor, or multi-store features.
- Advanced order management.
- Recipe database, recipe instructions, or exact serving guarantees.
- Runtime image generation.

## Domain Language

Use these terms consistently when shaping the codebase:

- Product: A sellable deli item as shown to customers. In the first catalog,
  each product has exactly one SKU.
- SKU: The concrete catalog identity that can be added to a basket and validated
  for availability, quantity, and pricing.
  _Avoid in customer-facing copy_: SKU; use Product or item instead.
- Unit label: The required free-text customer-facing sellable unit for a SKU,
  such as `250g`, `serves 2`, `single portion`, `750ml`, or `jar 180g`.
- Short description: A compact customer-facing product sentence used for catalog
  cards, scanning, and search.
- Detail description: Richer customer-facing product copy used on the product
  detail surface; it is not searched in the first version.
- Catalog: The customer-facing set of available products and SKUs that can be
  browsed or searched.
- Seed catalog: The real static demonstrator catalog data used by Tavola's first
  commerce flow.
- Category: A customer-facing catalog navigation group, such as Antipasti,
  Primi, Desserts, Drinks, or Pantry. Each product has exactly one primary
  category.
- Basket: The customer's current collection of intended purchases.
- Basket line: A single SKU entry in a basket with a customer-selected quantity.
- Basket quantity: A positive integer count of sellable SKU units on a basket
  line.
- Checkout: The mock process that finalizes a basket into a demonstration order.
- Contact details: The name and email submitted during checkout for one order;
  they are not a customer account or reusable customer profile.
- Order: A pickup-only demonstration record created by checkout from a basket;
  it is not payment or fulfillment state.
- Order ID: A generated customer-facing confirmation reference for one order;
  it does not imply order lookup or order management.
- Order line: A checkout-time snapshot of one SKU line on an order, including
  quantity and customer-facing price details.
- Pickup window: A backend-defined customer-facing pickup choice for mock
  checkout; it is not a capacity reservation or live schedule.
- Planner: Tavola's customer-facing assistant for turning a meal request into a
  menu proposal.
- Planner session: A bounded AI-assisted workflow for turning a meal request
  into a menu proposal.
- Menu proposal: The planner's suggested meal or occasion plan while it is being
  reviewed, including after deterministic validation and before basket
  acceptance.
- Planner note: Customer-facing explainability on a menu proposal that describes
  the planning evidence, constraints, validation, and assumptions behind the
  suggestion.
- Party size: The number of people the customer wants the menu proposal to
  serve, extracted from the meal request or a follow-up answer.
- Course: A planner or menu structure role, such as Antipasto, Primo, Dessert,
  or Aperitivo; courses are not the same as catalog categories.
- Package template: A planner-only course structure such as Antipasto + Primo +
  Dessert, used to shape a proposal without becoming a purchasable product.
- Meal-plan grouping: Optional basket or order metadata that preserves an
  accepted menu proposal's title, party size, package template, course names,
  and line grouping while SKU lines remain authoritative.
- Validated menu proposal: A menu proposal that has passed deterministic
  application checks and is safe to present for basket acceptance.
  _Avoid_: Validated basket, basket proposal.

Initial product/SKU relationship:

- Customers browse products.
- Each initial product has exactly one SKU.
- Basket, checkout, and planner validation reference SKUs, not products.
- A basket has at most one basket line per SKU; adding the same SKU again merges
  into the existing line by increasing its quantity.
- Basket lines store SKU identity and quantity; customer-facing SKU details and
  prices are resolved from the current backend catalog when a basket is
  displayed or validated.
- Planner output remains a **Menu proposal** until the customer accepts it into a
  **Basket**; validation alone does not make planner output a basket.
- A **Planner session** has at most one current **Menu proposal** in the first
  version. Follow-ups can fill missing information before proposal creation, and
  customer edits can revalidate the current proposal, but comparison between
  multiple simultaneous proposals is out of scope.
- Follow-up questions happen before a menu proposal exists. After a menu
  proposal is ready, the first version supports deterministic product removal,
  quantity editing, revalidation, and acceptance rather than conversational
  refinement such as "make it cheaper" or "swap dessert."
- Planning is independent of the customer's current **Basket** until
  acceptance. The existing basket does not shape the first version's menu
  proposal; basket merge or replacement happens only when the customer accepts
  the proposal.
- Accepting a **Menu proposal** marks that proposal as accepted for its
  **Planner session**. The accepted proposal should not be accepted again; the
  customer can start a new planner session or edit the basket after acceptance.
- A **Planner session** should keep only the minimum customer text needed for
  the demonstrator, such as the original meal request and latest follow-up
  answer. Normalized planning context, such as party size, constraints, current
  menu proposal, and accepted status, is the primary session state; full AI or
  tool transcripts are not part of the domain record.
- **Planner notes** should be structured customer-facing messages with a note
  type, such as constraint applied, catalog checked, pricing checked,
  quantity assumption, assumption, or substitution, rather than one
  undifferentiated prose block.
- **Planner notes** belong to the current **Menu proposal**, not the surrounding
  session status. Revalidating an edited menu proposal should refresh its notes.
- **Planner notes** should record whether their source is Tavola's deterministic
  validation or the planner's composition reasoning. Dietary exclusions, catalog
  checks, and pricing checks are Tavola-sourced; taste and pairing explanations
  may be planner-sourced.
- Planner notes should explain quantity assumptions when party size or unit
  labels materially shape the suggested quantities, without implying exact
  serving guarantees.
- The UI should show a small set of proposal-level planner notes for trust
  evidence, while per-line rationale explains why each product belongs in the
  menu proposal.
- Customers can edit a menu proposal's product quantities or remove product
  lines before acceptance, but they cannot directly edit course names or move
  products between courses in the first version.
- Revalidating an edited menu proposal should remove empty courses rather than
  showing course sections with no products.
- Removing or adjusting products in a menu proposal should trigger
  deterministic revalidation and price recalculation only. The planner should
  not automatically generate replacement products in the first version.
- Accepting a **Menu proposal** into a **Basket** can add proposal lines to the
  existing basket or replace all current basket lines. Replace means all current
  basket lines are removed regardless of whether they came from catalog browsing
  or an earlier planner proposal.
- Adding a **Menu proposal** to an existing **Basket** follows the normal basket
  merge rule: matching SKU lines are combined by increasing quantity rather than
  creating duplicate grouped lines.
- The first version does not need a pre-accept merge preview. After **Add to
  basket**, the updated basket is the confirmation of merged quantities.
- **Replace basket** should require lightweight confirmation when the current
  basket is non-empty because it removes existing basket lines. No confirmation
  is needed when the basket is empty.
- **Meal-plan grouping** should survive ordinary basket edits only while it
  remains coherent. Removing all products from a grouped course removes that
  course; removing all grouped products removes the grouping. Quantity edits keep
  the grouping attached to the same product lines, and later catalog-browsed
  additions are ungrouped.
- Catalog APIs may expose customer-facing product data with a `sku_id` because
  the SKU is the stable basket identity.
- Customer-facing UI, planner notes, checkout copy, and error messages should
  call sellable things **Products** or items, never SKUs. SKU remains an
  internal/API identity term, so API fields such as `sku_id` do not need to be
  renamed as long as user-facing text translates them.
- Customer-facing validation errors should describe product problems in
  action-oriented language. Internal error codes may mention SKU, but visible UI
  copy should not.
- Basket quantities count SKU units. For example, quantity `2` of Fresh
  Tagliatelle with unit label `250g` means two 250g packs.
- Unit labels are not parsed as structured measurement data in the first
  version; exact serving guarantees and nutritional measurement logic remain out
  of scope.
- The planner may use unit labels as human-readable hints when suggesting
  practical quantities, especially obvious labels such as `serves 2`, but unit
  labels do not create exact serving guarantees.
- Codex may propose product quantities using party size, catalog context, and
  unit labels. Tavola validates that those quantities are allowed and
  recalculates prices, but it does not independently certify that quantities
  exactly serve the party size.
- Customer-facing catalog browsing, search, and detail endpoints expose only
  products that can be bought in the demonstrator. Unavailable SKUs are not a
  planned customer-facing state for Tavola; existing availability checks are
  defensive validation only.

Category/course relationship:

- Customers browse by category.
- Planner proposals are organized by course.
- A product's category does not always determine its planner course. For
  example, a Pantry product such as sugo may support a Primo course when paired
  with fresh pasta.
- Cross-category meaning belongs in tags rather than multiple categories. For
  example, pesto remains in Pantry but may carry tags such as `pasta`, `primo`,
  and `sauce`.

## Initial Commerce Model

The first version should use a small static seed catalog served by the backend.
Catalog items should be single sellable SKUs rather than a separate product and
variant hierarchy. A starting catalog of 20 SKUs is enough to demonstrate
browsing, basket editing, checkout, and later planner composition.

The seed catalog is product data for the demonstrator, not incidental mock data.
Missing unit labels, unclear descriptions, invalid image IDs, or weak tags
should be treated as catalog data-quality issues.

All 20 seed catalog SKUs are available in the first catalog slice so the
customer-facing browseable catalog remains complete. Unavailable-SKU behavior is
not part of the product experience and should appear only in defensive tests
unless real catalog availability is explicitly brought into scope.

Each seed catalog product should meet a minimum content bar: real deli-style
name, stable SKU slug, primary category, required unit label, GBP price, one
sentence short description, one to two sentence detail description, at least two
tags, dietary facet booleans, image ID, and explicit display order.

Customer-facing categories should initially be:

- Antipasti.
- Primi.
- Desserts.
- Drinks.
- Pantry.

These labels are canonical customer-facing category names for the first catalog.
Do not rename them to alternatives such as Starters, Mains, Pasta, Beverages, or
Pantry Staples unless the product language is explicitly revisited. Search can
use tags and descriptions to catch related words without changing category
labels.

Catalog browsing has no user-facing sort control in the first version. Results
use backend-owned display order: categories appear as Antipasti, Primi,
Desserts, Drinks, Pantry, and products within each category use explicit display
order. Search preserves this curated order after filtering.

Category IDs are stable lowercase URL-safe identifiers: `antipasti`, `primi`,
`desserts`, `drinks`, and `pantry`. Category labels remain the canonical
customer-facing names.

SKU IDs use stable human-readable slugs, such as `fresh-tagliatelle-250g` or
`pesto-genovese-180g`. They are stable identities, not values regenerated from
display names.

The seed catalog should contain exactly 5 Antipasti, 6 Primi, 3 Desserts, 3
Drinks, and 3 Pantry items. Primi may include prepared dishes such as lasagne or
parmigiana di melanzane as well as simple composed options such as fresh pasta
and sauce.

Prices are owned by the backend and represented as integer minor units with a
currency, such as `unit_price_minor` and `currency`. The first seed catalog uses
GBP and displays prices in pounds sterling. The frontend may display prices, but
basket and order totals must be recalculated server-side. Prices are
tax-inclusive for the demonstrator; no VAT breakdown is needed.

The first basket model should be backend-owned, anonymous, and in memory. The
frontend can store a generated basket ID in localStorage. If the backend loses
the basket during a restart, the frontend should create a new basket.

Basket validation should start with these rules:

- SKU must exist in the catalog.
- SKU must pass any defensive availability guard in the catalog.
- Quantity must be a positive integer.
- Quantity must not exceed a simple per-line maximum of 10 units per SKU.
- Totals are calculated by the backend from catalog prices.

The per-line maximum is a basket validation rule, not catalog browsing copy. The
first catalog UI should not display quantity limits before basket editing exists.

Checkout should create an in-memory demonstration order for pickup only. It
should require contact details and a backend-defined pickup window. Payment,
shipping, delivery, and customer accounts remain out of scope.

Contact detail validation is intentionally lightweight: require a non-blank name
and an email value with text before and after `@`. Do not add deliverability
checks, strict email parsing, phone numbers, addresses, or marketing consent in
the first version.

Pickup windows are static demonstrator choices with stable IDs and
customer-facing labels. They do not use calendar logic, capacity checks, opening
hours, or inventory reservation.

The frontend displays pickup windows provided by the backend and submits the
selected pickup window ID during checkout. The backend validates the ID and
stores the selected pickup window label on the order snapshot.

After a successful checkout, the checkout creates an order snapshot and leaves
the customer's current basket empty. The first version does not model a separate
checked-out basket lifecycle.

An order may keep the originating basket ID as provenance, but the basket remains
the customer's current editable basket rather than becoming order state.

An order ID may be shown on the checkout confirmation as a receipt-like
reference. The first version does not let customers retrieve, manage, or update
orders by order ID after the confirmation flow.

Checkout validates basket line SKU identities against the current backend
catalog before creating an order. The seed catalog prices are static for the
demonstrator, but order lines still store customer-facing SKU and price snapshots
from checkout time.

The first checkout API is a checkout workflow, not an order-management surface.
It creates an order for confirmation but does not expose order history, order
status changes, or customer order lookup.

Customer-facing checkout copy should present a practical pickup order flow. Do
not ask the customer to handle payment, and do not foreground implementation
scope with phrases such as "mock payment" or "continue without payment."

## Catalog Metadata

Use structured facets for objective attributes and tags for fuzzy planning and
search meaning.

Initial hard-checkable facets should include:

- `is_vegetarian`.
- `is_vegan`.
- `is_gluten_free`.
- `contains_alcohol`.

Customer-facing labels for these facets are Vegetarian, Vegan, Gluten-free, and
Contains alcohol.

Dietary constraints declared by the customer should be enforced as deterministic
validation rules when the required facets exist. The `is_gluten_free` facet may
be displayed as Gluten-free, but the first version must avoid broader allergen
or food-safety claims such as Coeliac-safe, allergen-free, or suitable for
specific medical needs unless the catalog later gains explicit allergen metadata
and the product intentionally accepts that responsibility.

Tags should support catalog search and planner composition as controlled
discovery and planning descriptors, not as customer-facing taxonomy or hard
validation facts. They can describe roles, occasions, meal moments, pairings,
and uses, such as `pasta`, `sauce`, `dinner-party`, `starter`, `picnic`,
`comfort-food`, or `pairs-with-wine`. Keep tags lower-case and constrained;
thoughtful tagging is part of the planner's product quality.

Tags may hint at a course or use, such as `primo` for a Pantry sauce that pairs
with pasta, but deterministic dietary checks must use structured facets rather
than tags.

Catalog tags and structured dietary facets should not contradict each other.
If they ever do, hard constraint validation trusts the structured facets and the
catalog data should be treated as needing correction.

Raw tags are not rendered directly as customer-facing labels. If the UI needs
visible descriptors beyond facets, use curated customer copy such as "Good for"
phrases rather than title-casing tag values.

Customer-facing catalog API responses should not expose raw tags or availability
fields in the first catalog slice. Tags remain backend metadata for search and
future planner support. Availability is a defensive backend guard, not a normal
catalog state shown to customers.

Customer-facing catalog search should be deterministic and match only product
name, primary category label, short description, tags, and positive structured
facets such as `vegetarian`, `vegan`, `gluten-free`, and `contains-alcohol`.
Long detail copy is not searched in the first version.

Search query normalization is intentionally simple: trim leading and trailing
whitespace, collapse internal whitespace for matching, match case-insensitively,
and treat empty or whitespace-only queries as no query. Do not add stemming,
fuzzy matching, typo correction, or ranking in the first version.

When a search query has multiple tokens, every token must match somewhere in the
product's combined searchable text. Token OR search is too noisy for the first
version.

The first catalog UI should show dietary facets as product badges and allow them
to be found through text search, but it should not include dedicated dietary
facet filter controls.

Product detail should add richer product context beyond the card: detail
description, larger image, unit label, price, and visible facets. Curated
"good for" descriptors can be added later if detail panels need more
customer-facing guidance. Availability is not presented as a normal
customer-facing detail state in the first catalog slice.

Catalog browsing is inspect-only until the basket slice exists. Product cards
and detail surfaces should not include add-to-basket buttons, disabled basket
placeholders, or other dead purchase controls.

Catalog products expose an `image_id` rather than frontend asset paths or
backend-served image URLs. The frontend maps `image_id` values to committed
static catalog image assets.

The first customer-facing catalog API exposes products with `sku_id`, `name`,
`category_id`, `category_label`, `unit_label`, `unit_price_minor`, `currency`,
`short_description`, dietary facet booleans, and `image_id`. Product detail adds
`detail_description`.

Customer-facing catalog UI should use ordinary shopping language such as
"products", "items", or "picks" rather than exposing "SKU" terminology in normal
browsing copy.

## Architectural Implications

Tavola should be shaped around domain-driven boundaries:

- The API layer handles HTTP transport, request validation, response models, and
  routing.
- The application layer coordinates use cases such as browsing, basket updates,
  checkout, and planner sessions.
- The domain layer owns business rules and invariants for products, SKUs,
  baskets, validation, and checkout state.
- The infrastructure layer provides concrete catalog storage, AI tool adapters,
  persistence, and other external integrations.

AI behavior should be treated as an application workflow with explicit tool
boundaries, not as hidden domain logic. Deterministic validation remains part of
the application's trusted path.

The planner should access the catalog through explicit search and validation
tools, even while the catalog is small. Search can start as deterministic lookup
over product name, primary category label, short description, structured facets,
and tags. Embeddings, personalization, and advanced ranking are future
enhancements.

## Design Principles

- Keep the commerce model small and legible.
- Prefer vertical slices that demonstrate the current user flow.
- Design desktop-first for the demonstrator. Do not add mobile-specific layouts,
  breakpoints, or interactions unless explicitly requested.
- Make invalid planner output repairable rather than silently accepted.
- Keep AI suggestions explainable enough for the customer to review.
- Preserve a clear boundary between generated ideas and validated cart changes.
- Optimize for demonstration clarity over platform completeness.
- Keep package context visible after planner acceptance where it helps the
  customer understand the basket, without making packages the pricing authority.
- Keep the **Basket** visible as supporting context during desktop **Catalog
  browsing** so the customer can see the browse-to-basket loop without changing
  screens. Future planner entry points should sit near this basket decision
  surface rather than displacing the catalog.
- Keep future **Menu proposal** review visually distinct from actual **Basket
  lines** until the customer accepts the proposal into the basket.
- On the desktop opening screen, avoid a separate masthead between the top bar
  and the commerce flow. Let **Catalog browsing** be the first meaningful content.
- The opening catalog header should be compact and action-oriented; prefer copy
  like "Catalog", "Fresh from the counter", and "Browse real deli products, then
  add your picks to the basket."
- Catalog product counts are useful metadata, not primary content. Present counts
  inline or compactly rather than as a large summary card on the opening screen.
- At a `1366x768` desktop viewport, the opening screen should show the catalog
  heading, browsing controls, and at least the top half of the first row of
  product cards without scrolling.
- Customer-facing **Category** filters should remain visible on the desktop
  catalog surface rather than being hidden behind a menu. They may be made denser
  to preserve first-viewport product visibility.
- Catalog search should remain visible in the opening desktop catalog controls,
  but it should be compact enough that it does not push product cards out of the
  first viewport.
- Basket empty-state copy should use customer-facing shopping language rather
  than implementation language such as "backend-owned basket."

## Flagged Ambiguities

- "SKU" is a valid internal/API identity term, but it should not appear in
  customer-facing UI, planner notes, checkout copy, or visible error messages.
  Use **Product** or item in user-facing text.
- "Storefront workspace" was used in early UI copy for the opening screen, but it
  is not canonical customer-facing language. The opening screen should be framed
  around **Catalog browsing**, with the **Basket** visible as supporting context.
- "Backend connected" describes implementation health, not customer-facing
  commerce language. When the UI exposes this demonstrator affordance, prefer
  quiet **service status** language such as "Service ready" or "Service
  unavailable."
