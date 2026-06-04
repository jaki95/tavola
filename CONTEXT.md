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

The main AI feature is a Codex-powered menu-to-basket planner.

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

Accepted planner proposals may later carry lightweight meal-plan grouping
metadata in the basket and order summary so the customer can still see the shape
of the meal plan after accepting it. This metadata should preserve context such
as "Dinner for 4" with Antipasto, Primo, and Dessert sections, while SKU lines
remain the source of pricing and checkout truth.

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
- Planner session: A bounded AI-assisted workflow for turning a meal request
  into a proposed basket.
- Menu proposal: The planner's suggested meal or occasion plan before final SKU
  validation.
- Course: A planner or menu structure role, such as Antipasto, Primo, Dessert,
  or Aperitivo; courses are not the same as catalog categories.
- Package template: A planner-only course structure such as Antipasto + Primo +
  Dessert, used to shape a proposal without becoming a purchasable product.
- Meal-plan grouping: Optional basket or order metadata that preserves the
  accepted proposal's course structure while SKU lines remain authoritative.
- Validated basket: A basket proposal that has passed deterministic application
  checks and is safe to present for cart creation or update.

Initial product/SKU relationship:

- Customers browse products.
- Each initial product has exactly one SKU.
- Basket, checkout, and planner validation reference SKUs, not products.
- A basket has at most one basket line per SKU; adding the same SKU again merges
  into the existing line by increasing its quantity.
- Basket lines store SKU identity and quantity; customer-facing SKU details and
  prices are resolved from the current backend catalog when a basket is
  displayed or validated.
- Catalog APIs may expose customer-facing product data with a `sku_id` because
  the SKU is the stable basket identity.
- Basket quantities count SKU units. For example, quantity `2` of Fresh
  Tagliatelle with unit label `250g` means two 250g packs.
- Unit labels are not parsed as structured measurement data in the first
  version; exact serving guarantees and nutritional measurement logic remain out
  of scope.
- Customer-facing catalog browsing, search, and detail endpoints expose only
  available products; unavailable SKUs remain relevant to deterministic basket
  and planner validation but are not shown in the public catalog.

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
customer-facing browseable catalog remains complete. Unavailable-SKU behavior can
be tested with separate fixtures until real catalog availability changes are in
scope.

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
and sauce. Drinks are contextual add-ons for planner proposals, not automatic
parts of meal packages unless the customer asks or the occasion clearly implies
them.

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
- SKU must be available.
- Quantity must be a positive integer.
- Quantity must not exceed a simple per-line maximum of 10 units per SKU.
- Totals are calculated by the backend from catalog prices.

The per-line maximum is a basket validation rule, not catalog browsing copy. The
first catalog UI should not display quantity limits before basket editing exists.

Checkout should create an in-memory demonstration order for pickup only. It
should require customer name, email, and a backend-defined pickup window. Payment,
shipping, delivery, and customer accounts remain out of scope.

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
with pasta, but deterministic dietary or availability checks must use structured
facets and availability fields rather than tags.

Raw tags are not rendered directly as customer-facing labels. If the UI needs
visible descriptors beyond facets, use curated customer copy such as "Good for"
phrases rather than title-casing tag values.

Customer-facing catalog API responses should not expose raw tags or availability
fields in the first catalog slice. Tags remain backend metadata for search and
future planner support, and availability is enforced by excluding unavailable
products from customer-facing catalog responses.

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
customer-facing guidance. Because customer-facing catalog endpoints expose only
available products, availability is not presented as a normal customer-facing
detail state in the first catalog slice.

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
