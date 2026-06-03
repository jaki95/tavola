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

Out of scope unless explicitly requested:

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

- Product: A sellable deli item as shown to customers.
- SKU: A concrete catalog item that can be added to a basket.
- Catalog: The set of products and SKUs available to browse or search.
- Basket: The customer's current collection of intended purchases.
- Checkout: The mock process that finalizes a basket into a demonstration order.
- Planner session: A bounded AI-assisted workflow for turning a meal request
  into a proposed basket.
- Menu proposal: The planner's suggested meal or occasion plan before final SKU
  validation.
- Package template: A planner-only course structure such as Antipasto + Primo +
  Dessert, used to shape a proposal without becoming a purchasable product.
- Meal-plan grouping: Optional basket or order metadata that preserves the
  accepted proposal's course structure while SKU lines remain authoritative.
- Validated basket: A basket proposal that has passed deterministic application
  checks and is safe to present for cart creation or update.

## Initial Commerce Model

The first version should use a small static seed catalog served by the backend.
Catalog items should be single sellable SKUs rather than a separate product and
variant hierarchy. A starting catalog of 20 SKUs is enough to demonstrate
browsing, basket editing, checkout, and later planner composition.

Customer-facing categories should initially be:

- Antipasti.
- Primi.
- Desserts.
- Drinks.
- Pantry.

The seed catalog should roughly contain 5 Antipasti, 6 Primi, 3 Desserts, 3
Drinks, and 3 Pantry items. Primi may include prepared dishes such as lasagne or
parmigiana di melanzane as well as simple composed options such as fresh pasta
and sauce. Drinks are contextual add-ons for planner proposals, not automatic
parts of meal packages unless the customer asks or the occasion clearly implies
them.

Prices are owned by the backend and represented as integer minor units with a
currency, such as `unit_price_cents` and `currency`. The frontend may display
prices, but basket and order totals must be recalculated server-side. Prices are
tax-inclusive for the demonstrator; no VAT breakdown is needed.

The first basket model should be backend-owned, anonymous, and in memory. The
frontend can store a generated basket ID in localStorage. If the backend loses
the basket during a restart, the frontend should create a new basket.

Basket validation should start with these rules:

- SKU must exist in the catalog.
- SKU must be available.
- Quantity must be a positive integer.
- Quantity must not exceed a simple per-line maximum.
- Totals are calculated by the backend from catalog prices.

Checkout should create an in-memory demonstration order for pickup only. It
should require customer name, email, and a backend-defined pickup window. Payment,
shipping, delivery, and customer accounts remain out of scope.

## Catalog Metadata

Use structured facets for objective attributes and tags for fuzzy planning and
search meaning.

Initial hard-checkable facets should include:

- Vegetarian.
- Vegan.
- Gluten-free.
- Contains alcohol.

Dietary constraints declared by the customer should be enforced as deterministic
validation rules when the required facets exist. Avoid serious allergen safety
claims in the first version unless the catalog later gains explicit allergen
metadata and the product intentionally accepts that responsibility.

Tags should support catalog search and planner composition. They can describe
roles, occasions, meal moments, pairings, and uses, such as `antipasti`,
`dinner-party`, `starter`, `picnic`, `comfort-food`, or `pairs-with-wine`. Keep
tags lower-case and constrained; thoughtful tagging is part of the planner's
product quality.

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
over name, category, description, structured facets, and tags. Embeddings,
personalization, and advanced ranking are future enhancements.

## Design Principles

- Keep the commerce model small and legible.
- Prefer vertical slices that demonstrate the current user flow.
- Make invalid planner output repairable rather than silently accepted.
- Keep AI suggestions explainable enough for the customer to review.
- Preserve a clear boundary between generated ideas and validated cart changes.
- Optimize for demonstration clarity over platform completeness.
- Keep package context visible after planner acceptance where it helps the
  customer understand the basket, without making packages the pricing authority.
