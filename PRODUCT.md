# Product

## Register

product

## Users

Desktop deli shoppers. Jobs: browse real products, build Basket, use Planner
for meal/menu help, complete mock pickup checkout.

Needs: scan catalog, trust price/qty, see Basket, switch Shop/Plan without
lost context.

## Product Purpose

Small DDD commerce demo: Catalog -> Basket -> mock pickup Checkout -> Planner
Menu proposals.

Planner maps free-text meal req to real products. AI suggests; Tavola validates
SKU, availability, qty, pricing, totals. User reviews Menu proposal before any
Basket change.

Success: "what should I serve?" -> validated Basket. No invented items, runtime
detail, or architecture leak.

## Brand Personality

Practical, local, trustworthy, quietly polished. Warmth via product copy, food
imagery, serif brand, restrained tomato/basil/saffron accents. UI compact,
task-first.

Voice: Tavola terms first: Products, Basket, Checkout, Planner, Plan a menu,
Menu proposal, Pickup. Hide implementation terms except the small
`powered by Codex` attribution inside the Planner surface.

## Anti-references

Avoid enterprise commerce, marketplace, generic SaaS dashboard, landing page,
oversized hero, decorative metrics, noisy AI branding, dark terminal styling,
mobile-first decisions.

Never expose SKU, Codex run metadata, tool counts, transcripts, retries,
backend plumbing, or raw planner internals. The Planner may show the restrained
`powered by Codex` badge, but progress/status copy must stay in Tavola language.
Planner must not invent products, claim unsupported dietary guarantees, or
become a separate cart.

## Design Principles

- Basket visible beside Shop/Plan.
- Catalog, Basket, Checkout work without Planner; Planner uses same flow.
- Explain validation: party size, constraints, catalog, pricing, assumptions.
  Hide machinery.
- Compact/scannable desktop UI. Prioritize image, name, price, qty, action.
- Warmth supports trust/clarity, not decoration.

## Accessibility & Inclusion

Semantic HTML, keyboard controls, visible focus, explicit loading/empty/error/
success states. WCAG AA contrast for text, placeholders, controls, state copy.
Motion = state feedback; respect reduced motion. Desktop supported unless
mobile requested.
