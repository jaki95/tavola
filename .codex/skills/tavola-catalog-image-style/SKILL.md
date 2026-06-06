---
name: tavola-catalog-image-style
description: Generate cohesive static Tavola catalog product images for seed SKUs and future deli catalog additions.
---

# Tavola Catalog Image Style

Use this skill when generating static bitmap product images for Tavola catalog
SKUs. Generated files are committed under `frontend/src/assets/catalog/`; the app
does not perform runtime image generation.

## Shared Direction

- Use case: `product-mockup`.
- Format: 4:3 landscape product image, suitable for catalog cards and detail.
- Backdrop: warm off-white stone counter, subtle sage linen, muted terracotta
  accent, independent Italian deli mood.
- Lighting: soft north-window light, warm neutral color temperature, gentle
  natural shadows.
- Camera: 3/4 overhead angle with the product centered and generous padding.
- Texture: photorealistic, inspectable, crisp focus, appetizing but restrained.
- Scale: keep product size consistent across the catalog set.
- Avoid: text overlays, logos, watermarks, people, hands, price tags, readable
  labels, unrelated props, clutter, or dark atmospheric backgrounds.

## Reference Alignment

Before generating or accepting an image, inspect one or two existing committed
assets under `frontend/src/assets/catalog/` from the same category or nearest
visual family. Use those assets as the background/composition reference in the
prompt and review:

- Match the reference's counter color, plate/crockery shape, linen placement,
  terracotta prop scale, lighting direction, camera angle, product scale, and
  amount of negative space.
- Prefer replacing only the product subject while keeping the category set's
  background rhythm stable.
- If the generated image uses a noticeably different prop type, crop, texture,
  saturation, shadow weight, or background layout, reject it and retry with the
  reference background described explicitly.

For dessert slices, use `torta-della-nonna-slice.jpg`,
`cannoli-siciliani-two-pack.jpg`, and/or `tiramisu-cup-single.jpg` as the
primary reference: warm stone counter, sage linen entering from the
upper-left/left edge, shallow terracotta dish cropped in the upper-right,
off-white ceramic plate centered slightly low, and soft natural shadows.

## Prompt Shape

For one SKU:

```text
Use case: product-mockup
Asset type: Tavola catalog product card image, 4:3 landscape.
Primary request: Generate <SKU name>, <unit label>, <short product cue>.
Scene/backdrop: warm off-white stone counter, subtle sage linen, muted
terracotta accent, soft north-window light, independent Italian deli catalog
style.
Subject: <specific food styling that makes this SKU recognizable>.
Composition/style: 3/4 overhead, centered with generous padding,
photorealistic, crisp focus, realistic appetizing texture, same product scale as
a catalog set.
Negative constraints: no text overlays, logos, watermark, people, hands, price
tags, packaging labels, readable labels, unrelated props, messy background.
```

For batches, keep the shared scene/backdrop and negative constraints unchanged,
and vary only the subject line so each SKU remains distinct.
