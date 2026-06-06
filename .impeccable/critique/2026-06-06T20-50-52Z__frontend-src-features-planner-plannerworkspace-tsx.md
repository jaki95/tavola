---
target: new planner view with live updates
total_score: 28
p0_count: 0
p1_count: 2
timestamp: 2026-06-06T20-50-52Z
slug: frontend-src-features-planner-plannerworkspace-tsx
---
#### Design Health Score

| # | Heuristic | Score | Key Issue |
|---|---|---:|---|
| 1 | Visibility of System Status | 3 | Live planning labels are clear, but no elapsed/ETA/cancel signal. |
| 2 | Match System / Real World | 3 | Uses Tavola language and real Products, but "powered by Codex" competes with deli trust. |
| 3 | User Control and Freedom | 2 | New request locks during planning; final Add/Replace actions sit below review content. |
| 4 | Consistency and Standards | 3 | Shared tabs/buttons mostly hold, but Planner quantity inputs differ from Basket steppers. |
| 5 | Error Prevention | 2 | Add vs Replace lacks basket-impact preview, especially with overlapping current Basket items. |
| 6 | Recognition Rather Than Recall | 3 | Examples, request summary, totals, course names help users stay oriented. |
| 7 | Flexibility and Efficiency | 2 | Review requires long scroll before primary action; no sticky proposal action bar. |
| 8 | Aesthetic and Minimalist Design | 3 | Compact, on-brand, food-led; repeated trust panel adds density in prime space. |
| 9 | Error Recovery | 2 | Alerts exist, but retry/cancel flow during long planning is thin. |
| 10 | Help and Documentation | 3 | Validation promise and notes explain why Planner is trustworthy. |
| **Total** | | **28/40** | **Good base, decision flow needs work.** |

#### Anti-Patterns Verdict

**LLM assessment**: Not obvious AI slop. Planner feels like Tavola commerce, not generic SaaS chat. Strong food imagery, tomato/basil/enamel roles, serif product naming, and Basket adjacency help. Biggest slop-adjacent pattern: repeated trust card plus mini metric tiles make the proposal feel more like a validation dashboard than a deli review.

**Deterministic scan**: `detect.mjs --json frontend/src/features/planner/PlannerWorkspace.tsx` returned `[]`. No detector hits.

**Visual overlays**: No reliable overlay available. Browser mutation preflight failed: `TypeError: Cannot set property title of [object Object] which has only a getter`. Fallback signal: manual browser inspection at `1366x768`, source read, and clean CLI detector.

#### Overall Impression

Planner is credible and on-brand. It earns trust by keeping Basket visible, showing real products, prices, and validation notes. Biggest opportunity: make proposal acceptance feel like a checkout-grade decision, not a hidden footer after a long generated review.

#### What's Working

- **Strong domain fit**: "Plan a menu", "Menu proposal", Products, Basket, prices, labels. No visible SKU/runtime leak in browser inspection.
- **Live planning feedback is calm**: Catalog, Menu shape, Prices, Review gives useful progress without showing backend machinery.
- **Proposal cards feel real**: Product images, units, per-line totals, and rationales make suggestions inspectable.

#### Priority Issues

**[P1] Primary decision is below fold**

Why it matters: At `1366x768`, proposal appears, but Add/Replace actions are offscreen after courses and notes. User reads validation, then must hunt for the actual Basket mutation.

Fix: Add a sticky proposal action strip inside the Planner column once proposal exists: total, item count, overlap note, Add to basket, Replace basket. Keep full footer too if useful.

Suggested command: `$impeccable layout planner view`

**[P1] Basket-impact preview missing**

Why it matters: Browser state had 13 Basket items and proposal contained items already in Basket. "Add to basket" does not explain merge/increase effects, and "Replace basket" is a quiet secondary button until clicked.

Fix: Before actions, show concise impact copy: "Adds 6 items, updates 3 already in Basket" or "Replace current Basket, removes 13 items." Make Replace require confirmation with summary.

Suggested command: `$impeccable clarify planner proposal actions`

**[P2] Trust panel repeats past its useful moment**

Why it matters: The validation promise is excellent at intake. During planning/proposal it consumes a large right-side box while the user needs current state and decision impact.

Fix: Collapse it after submission into a single inline line or badge: "Validated against catalog, labels, and prices." Move detailed trust proof into Validation notes.

Suggested command: `$impeccable distill planner trust panel`

**[P2] Live progress looks more certain than it is**

Why it matters: Steps advance by elapsed time, not real backend milestones. It reads like deterministic progress, but it is timer-based, so a slow run can over-promise "Prices" before real validation finishes.

Fix: Rename steps to softer status copy or tie steps to real events. Add "Still checking" state after 30s plus optional "Start new request after this finishes" or cancel if backend supports it.

Suggested command: `$impeccable harden planner live updates`

**[P3] Proposal edit controls diverge from Basket controls**

Why it matters: Basket uses minus/plus steppers. Planner proposal uses a bare number field plus Remove. Same commerce quantity concept, different affordance.

Fix: Reuse Basket-style stepper visual pattern for proposal quantities, with disabled/loading states aligned.

Suggested command: `$impeccable polish planner proposal controls`

#### Persona Red Flags

**Casey, decisive deli shopper**: Sees proposal, scans products, wants to add. Add action is below fold. Casey may assume Basket already changed because Basket rail is visible and contains overlapping items.

**Rina, cautious first-timer**: Trusts validation notes, but cannot tell what Add does to an existing Basket. Replace sounds risky, Add sounds safe, neither previews consequences.

**Morgan, keyboard-first user**: Can tab through controls, but long proposal means primary action arrives late in focus order. Quantity editing also changes interaction model from Basket steppers to raw number inputs.

#### Minor Observations

- "powered by Codex" is allowed inside Planner, but visually it competes with "Plan a menu." It could be smaller or moved into trust copy.
- Proposal totals are clear, but "Products 6" means item count, not line count. If quantities matter, "Items" may match Basket language better.
- Course rationale copy is useful, but multiple long rationales push actions lower. Consider one-line rationale clamp with expand.
- Planning animation respects reduced motion globally, good.

#### Questions to Consider

- Should proposal acceptance behave more like checkout review, with a sticky decision summary?
- Should Add to basket be disabled or warned when proposal overlaps current Basket items?
- Does the trust panel need to stay visible after validation notes exist?
