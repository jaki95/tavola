---
target: frontend/src/pages/HomePage.tsx
total_score: 28
p0_count: 0
p1_count: 2
timestamp: 2026-06-06T17-00-30Z
slug: frontend-src-pages-homepage-tsx
---
# Tavola HomePage Critique

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Loading and error states exist, Basket status is clear, Planner readiness is quiet before a proposal exists. |
| 2 | Match System / Real World | 3 | Strong deli language, but early "powered by Codex" emphasis points at implementation before customer value. |
| 3 | User Control and Freedom | 3 | Shop/Plan switching, Basket editing, and checkout escape paths work; invalid quantity correction can be silent. |
| 4 | Consistency and Standards | 3 | Cohesive visual system; tomato action styling is applied too broadly across different action weights. |
| 5 | Error Prevention | 3 | Disabled checkout, validation, and replace confirmation help; some filter and quantity states need clearer prevention. |
| 6 | Recognition Rather Than Recall | 3 | Basket persists and product cards are scannable; Planner needs more visible expectation-setting. |
| 7 | Flexibility and Efficiency | 2 | Search and category filters help, but repeat shopping has limited accelerators and basket review tools. |
| 8 | Aesthetic and Minimalist Design | 3 | Attractive, compact, and on-brand; first viewport still has too many equally weighted controls. |
| 9 | Error Recovery | 3 | Reload and retry paths exist; some recovery copy is generic and not always tied to the source of the problem. |
| 10 | Help and Documentation | 2 | Planner examples and empty states help, but Planner and checkout trust moments need more contextual guidance. |
| **Total** | | **28/40** | **Good: solid foundation, meaningful issues before it feels effortless.** |

## Anti-Patterns Verdict

**LLM assessment:** The HomePage does not read as obvious AI slop. It has a coherent product point of view: food-led cards, compact desktop storefront layout, persistent Basket, restrained deli palette, and a clear Shop/Plan split. The remaining risk is not generic slop, but over-polished demonstrator energy: heavy labels, many framed areas, and tomato buttons appearing at too many action levels.

**Deterministic scan:** `detect.mjs --json frontend/src/pages/HomePage.tsx` returned no findings. A broader check including `frontend/src/styles.css` also returned no findings after the prior polish pass.

**Visual overlays:** Overlay injection was attempted but did not succeed. The browser evaluation surface is read-only and failed on the preflight title mutation, so no reliable user-visible `[Human]` overlay is available. Fallback signal: live browser inspection of Shop, Basket, Plan, and checkout states, plus clean console logs.

## Overall Impression

This is a strong demonstrator storefront with the right architecture showing through the interface. The biggest opportunity is action hierarchy: Tavola already knows what matters, but the UI still asks too many things to speak with equal force.

## What's Working

- The core IA is right: Shop and Plan remain anchored to the same visible Basket, so Planner does not become a parallel cart.
- The catalog is genuinely food-led. Product image, name, unit, price, and Add action are visible without a marketing wrapper.
- Checkout has the right basic shape: Basket review, contact fields, pickup window, focus management, and a visible Back to basket path.

## Priority Issues

**[P1] Tomato action hierarchy is diluted**

**Why it matters:** Tomato should mean commerce commitment in Tavola: Add, checkout, create order, or destructive confirmation. Today Search, retry, planner submit, catalog actions, checkout, and several hover states share similar tomato emphasis. That slows scanning and weakens the Basket-moving actions.

**Fix:** Reserve filled tomato for actions that change Basket, create an order, or submit a Planner request. Make Search, Reset filters, View details, retry, and low-risk utility actions quieter. Disable or visually mute Reset filters when no filters are active.

**Suggested command:** `$impeccable quieter frontend/src/styles.css`

**[P1] Planner empty state does not earn enough trust**

**Why it matters:** The Plan view gives a text area, examples, and "powered by Codex," but it does not lead with the customer reassurance that makes AI-assisted commerce trustworthy: real products, price validation, review before Basket.

**Fix:** Add a compact trust strip or inline note beside the Planner composer: Tavola checks real catalog products, recalculates prices, and shows a Menu proposal for review before Basket changes. Keep Codex attribution smaller than the validation promise.

**Suggested command:** `$impeccable onboard frontend/src/features/planner/PlannerWorkspace.tsx`

**[P2] First-viewport cognitive load is high**

**Why it matters:** On Shop, the customer sees brand, tabs, title, lede, six category choices, search, reset, count, product cards, Add, View details, Basket totals, quantity controls, Remove, and checkout. The structure is correct, but the number of similarly visible decisions pushes working memory.

**Fix:** Calm the filter row, reduce repeated metadata on cards, and let product image/name/price/action dominate. Keep visible choices grouped under a single browsing decision instead of making search, reset, categories, product actions, and Basket all compete.

**Suggested command:** `$impeccable layout frontend/src/pages/HomePage.tsx`

**[P2] Checkout feels competent but emotionally thin**

**Why it matters:** Checkout works as a form, but the moment is high-stakes even in a mock demonstrator. The customer needs reassurance about payment, pickup, and editability before creating the order.

**Fix:** Add small, specific reassurance near the submit area: mock pickup order, no payment collected, selected pickup window, and Basket can still be changed with Back to basket. Tune the confirmation state toward "your deli pickup is arranged."

**Suggested command:** `$impeccable clarify frontend/src/features/checkout/CheckoutPanel.tsx`

**[P3] Some interactions fail softly but silently**

**Why it matters:** Invalid Basket quantity input can remain as a draft value without a visible explanation. Disabled states rely mainly on opacity. Careful shoppers and stress testers get less confidence from these edge states.

**Fix:** Add inline quantity validation or restore-and-explain behavior, strengthen disabled affordances, and make proposal quantity updates visibly confirm or fail.

**Suggested command:** `$impeccable harden frontend/src/features/basket/BasketLineItem.tsx`

## Persona Red Flags

**Alex, efficient repeat shopper:** Search, Reset filters, Add, View details, Remove, and checkout compete visually. The primary path works, but the interface does not yet reward speed because too many controls carry similar weight.

**Jordan, Planner-curious first-timer:** "Powered by Codex" appears before the product promise. Jordan may not know whether the Planner changes the Basket directly, uses real products, checks prices, or invents items.

**Sam, keyboard and assistive tech user:** Semantic structure is mostly strong, but the critique browser pass could not conclusively verify full Tab traversal with the available tooling. Quantity correction and disabled states should be clearer without relying on visual inference.

**Riley, deliberate stress tester:** Quantity edge cases and recovery states need sharper explanations. If a value cannot be accepted, the UI should say why and preserve trust rather than quietly sitting in an unresolved draft state.

## Minor Observations

- The brand mark is strong, but repeated uppercase labels across filters, badges, totals, and form labels create visual grit.
- The Basket rail is structurally excellent, but sparse states can feel oversized relative to one product line.
- The checkout backdrop feels slightly heavier than the interaction needs.
- The Plan view has a large empty lower canvas before a proposal exists. Compact is good, but the empty area currently reads unfinished.

## Questions to Consider

- What if tomato were allowed to mean only "changes my Basket or creates my order"?
- Should the Planner lead with Codex, or with "Tavola checks catalog products, quantities, and prices before anything reaches Basket"?
- Can the first viewport answer one question first: "What should I buy?" or "What am I checking out?"
