---
name: "Tavola"
description: "A compact desktop storefront for an independent Italian deli with Shop, Plan, Basket, and pickup checkout workflows."
colors:
  ink: "#201a16"
  muted: "#66584c"
  paper: "#fffdf7"
  porcelain: "#f8f3ea"
  flour: "#efe1c8"
  tomato: "#b22017"
  tomato-dark: "#87180f"
  basil: "#2d6544"
  basil-soft: "#e2eddc"
  enamel: "#21566d"
  saffron: "#c98f1f"
  border: "#cdb991"
  hairline: "#4a311c29"
typography:
  display:
    fontFamily: "Fraunces, Iowan Old Style, Palatino Linotype, Georgia, serif"
    fontSize: "2rem"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "0"
  headline:
    fontFamily: "Fraunces, Iowan Old Style, Palatino Linotype, Georgia, serif"
    fontSize: "1.7rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0"
  title:
    fontFamily: "Fraunces, Iowan Old Style, Palatino Linotype, Georgia, serif"
    fontSize: "1.24rem"
    fontWeight: 800
    lineHeight: 1.08
    letterSpacing: "0"
  body:
    fontFamily: "Avenir Next, Gill Sans, Trebuchet MS, ui-sans-serif, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Avenir Next, Gill Sans, Trebuchet MS, ui-sans-serif, sans-serif"
    fontSize: "0.76rem"
    fontWeight: 900
    lineHeight: 1.2
    letterSpacing: "0"
rounded:
  xs: "6px"
  sm: "7px"
  md: "8px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.tomato}"
    textColor: "{colors.paper}"
    rounded: "{rounded.sm}"
    padding: "8px 14px"
    height: "40px"
    typography: "{typography.label}"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.tomato}"
    rounded: "{rounded.sm}"
    padding: "8px 14px"
    height: "40px"
    typography: "{typography.label}"
  workflow-tab:
    backgroundColor: "{colors.porcelain}"
    textColor: "{colors.muted}"
    rounded: "{rounded.md}"
    padding: "5px 12px"
    height: "32px"
    typography: "{typography.label}"
  product-card:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "13px 14px 14px"
  field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "0 0.8rem"
    height: "40px"
---

# Design System: Tavola

## 1. Overview

**Creative North Star: "The Working Deli Counter"**

Product UI, not campaign. Polished deli counter: food-close, price-clear,
compact, trustworthy. Warmth from food imagery, serif brand, hairlines,
tomato/basil/saffron/enamel accents.

Reject enterprise/marketplace/SaaS/landing-page/terminal/metric/noisy-AI feel.
No customer-facing SKU or Codex runtime detail.

**Key Characteristics:** desktop; catalog + Basket visible; food-led cards;
tomato for real actions; serif for brand/names; sans for controls/data/state.

## 2. Colors

Restrained deli palette. Paper/Porcelain = surfaces. Tomato = commerce action.
Basil = selected/success/dietary. Enamel = system/Planner/focus. Saffron =
pending/warning.

### Primary

- **Counter Tomato:** Add, checkout, submit, rare commerce emphasis.
- **Dark Tomato:** hover, pressed, critical copy, strong action border.

### Secondary

- **Fresh Basil:** selected, success, dietary, metadata.
- **Basil Soft:** badges, validated fills, proposal totals.

### Tertiary

- **Service Enamel:** focus, system status, Planner validation.
- **Pickup Saffron:** pending, warning.

### Neutral

- **Ink:** text/prices.
- **Counter Muted:** prose, units, helper copy.
- **Paper:** cards/panels/fields/active tabs.
- **Porcelain:** page/toolbar canvas.
- **Flour:** image fallback.
- **Deli Border/Hairline:** dividers/structure.

### Named Rules

**Tomato Means Action.** Use only for action/active commerce/rare alert.
**Warmth Through Product.** Food/copy/accent carry warmth, not beige wash.

## 3. Typography

**Display Font:** Fraunces -> Iowan Old Style -> Palatino Linotype -> Georgia -> serif.
**Body Font:** Avenir Next -> Gill Sans -> Trebuchet MS -> ui-sans-serif -> sans-serif.
**Label/Mono Font:** none.

**Character:** Serif = identity/named objects. Sans = controls/labels/state/data.

### Hierarchy

- **Display** (800, 2rem-5.2rem, lh 0.92-0.95): brand, rare screen title.
- **Headline** (800, 1.65rem-2rem, lh 1): Planner/checkout/Basket/detail.
- **Title** (800, 1.08rem-1.35rem): product, basket line, course.
- **Body** (400-800, 0.88rem-1rem, lh 1.35-1.5): prose/status/rationale.
  Long prose 65-75ch.
- **Label** (800-900, 0.68rem-0.9rem, tracking 0): tabs/badges/fields/buttons.
  Uppercase only compact metadata.

### Named Rules

**Serif Is for Meaning.** No serif on dense UI.
**No Tracked Kicker.** Uppercase ok; tracking 0; no marketing eyebrow stacks.

## 4. Elevation

Hairlines + tonal fills + inset controls + small hover lift. Flat at rest.
Shadows only for hover/containment/modal separation.

### Shadow Vocabulary

- **Soft Panel** (`0 18px 46px rgb(54 36 20 / 11%)`): modal/major overlay.
- **Card Lift** (`0 12px 26px rgb(54 36 20 / 10%)`): hover/framed card.
- **Control Press** (`inset 0 -2px 0 rgb(32 26 22 / 10%)`): tactile button.
- **Status Halo** (`0 0 0 4px rgb(...)`): tiny status dot only.

### Named Rules

**Flat Until Touched.** Lift only hover/active, except modal/sticky commerce.
**One Depth Cue.** Strong border or shadow, not both.

## 5. Components

### Buttons

7px radius, 40px min height. Primary = tomato fill/white/dark tomato border.
Secondary = paper/transparent + tomato/hairline. Focus = enamel 3px outline.
Strongest button only Basket/order/Planner submit.

### Chips

Basil Soft + Basil text + pill + compact uppercase. Selected filter = Paper +
tomato + inset underline. Inactive = muted/transparent.

### Cards / Containers

8px cards/panels/notes/review/confirmation; 7px fields. Paper surfaces,
Porcelain canvas, Flour fallback. Hairline rest; lift hover only. No side
stripes. Dense padding 12-18px; product cards `13px 14px 14px`.

### Inputs / Fields

Paper bg, Hairline border, 7px radius, ink text, inset shade, 40px min height.
Focus enamel. Disabled lower opacity/no hover. Error = tinted full panel +
action copy.

### Navigation

Shop/Plan = in-page tabs. Active = Paper, tomato-dark, hairline, inset tomato
underline. Proposal-ready = restrained basil badge.

### Product Card

Image first. Fixed image band, category, serif name, price/unit, 2-line desc,
badges, bottom actions. Hover lift <=1px. No reflow.

### Basket Rail

Sticky right rail, visible with Shop/Plan. Clear total, thumbnails, steppers,
strong checkout. Empty state teaches add-product next action.

### Checkout Modal

Focused finalization. Trap focus, restore focus, show Basket review +
contact/pickup fields, keep Back to basket.

### Planner Workspace

Compact input; expand for Menu proposal review. Free-text first. Notes/totals/
courses/rationales = validated commerce info, not chat transcript.

## 6. Do's and Don'ts

### Do:

- **Do** keep Basket visible beside Shop/Plan desktop.
- **Do** use tomato for add/checkout/submit/destructive confirm.
- **Do** reserve basil/enamel/saffron for distinct states.
- **Do** use Tavola terms: Products, Basket, Checkout, Planner, Plan a menu,
  Menu proposal, Pickup.
- **Do** show Planner evidence: party size, constraints, catalog, pricing,
  assumptions, validation.
- **Do** keep controls familiar, keyboard-accessible, consistent.
- **Do** verify contrast for muted text/placeholders/badges/disabled.

### Don't:

- **Don't** feel enterprise, marketplace, generic SaaS, landing page.
- **Don't** use oversized hero, metrics, noisy AI, terminal styling,
  mobile-first decisions.
- **Don't** expose SKU, Codex metadata, tool counts, transcripts, retries,
  backend plumbing.
- **Don't** make Planner separate cart flow.
- **Don't** claim unsupported diet guarantees or invent products.
- **Don't** use side stripes, gradient text, glass cards, stripe decoration,
  decorative motion.
