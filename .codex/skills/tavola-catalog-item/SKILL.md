---
name: tavola-catalog-item
description: Add, replace, or revise Tavola catalog SKUs through a reviewed product-entry workflow that drafts catalog data, gets user approval, generates a static product image, updates seed data and frontend image mapping, and runs Tavola validation.
---

# Tavola Catalog Item

Use this skill when adding, replacing, or revising a Tavola catalog SKU. It is a
reviewed product-entry workflow, not a background automation.

## Start Here

Read `AGENTS.md` and `CONTEXT.md` before making scope, category, pricing, or
catalog-size decisions. Use the project-local `$tdd` skill for implementation
work.

Current Tavola constraints to check before drafting:

- The first seed catalog is intentionally small and currently has exactly 20
  SKUs.
- Each product has exactly one SKU in the first catalog.
- Customer-facing categories are `Antipasti`, `Primi`, `Desserts`, `Drinks`,
  and `Pantry`.
- Prices are backend-owned integer minor units in GBP.
- Basket, checkout, and planner validation use SKU IDs, not product names.

## Workflow

1. Clarify the catalog operation.
   - If the user did not say, ask whether this is replacing an existing SKU,
     revising an existing SKU, or intentionally expanding the catalog.
   - If expanding beyond 20 SKUs, call out the `CONTEXT.md` seed-catalog
     constraint and ask whether to update that product constraint too.

2. Draft a complete SKU proposal from the user's intent.
   Include:
   - `sku_id`.
   - name.
   - category.
   - unit label.
   - price in GBP minor units.
   - short description.
   - detail description.
   - tags.
   - dietary facets.
   - image ID.
   - display order.
   - image subject prompt idea.

3. Pause for user review.
   - Present the proposal concisely.
   - Do not edit catalog files or generate the product image until the user
     approves the SKU proposal.
   - Incorporate feedback and re-present the proposal as needed.

4. After approval, generate the static image.
   - Use `.codex/skills/tavola-catalog-image-style/SKILL.md`.
   - Generate a project-bound bitmap image for the approved SKU.
   - Inspect the output for product correctness, cohesive Tavola style, no text,
     no logos, no readable labels, no hands, and no unrelated props.
   - Retry once with a tighter prompt if the image fails those checks.
   - Save the accepted asset under `frontend/src/assets/catalog/` using the
     approved `image_id` as the filename stem.

5. Implement the catalog change test-first.
   - Update backend seed catalog data in
     `backend/src/tavola/infrastructure/data/catalog.json`.
   - Keep `backend/src/tavola/infrastructure/catalog_seed.py` as loader/mapping
     code unless the JSON shape changes.
   - Update backend seed tests for counts, category distribution, ordering,
     pricing, tags, descriptions, facets, and image IDs.
   - Update `frontend/src/features/catalog/catalogImages.ts`.
   - Update frontend image-map tests so missing mappings fail.
   - Keep API response contracts unchanged unless the user explicitly requested
     a product model change.

6. Validate.
   Run the narrowest relevant tests first, then broaden as needed:
   - `cd backend && uv run pytest tests/test_catalog_seed.py`
   - `cd frontend && npm test -- src/features/catalog/catalogImages.test.ts`
   - Broader backend/frontend tests when the change affects ordering, filters,
     search, or UI rendering.

7. Finish.
   Report:
   - The SKU added, replaced, or revised.
   - Whether the catalog remains at 20 SKUs or the product constraint changed.
   - Image asset path.
   - Backend and frontend files touched.
   - Tests run and any unchecked browser/image review gaps.
   - Do not commit unless the user explicitly asked for a commit or PR flow.

## SKU Drafting Rules

- Prefer stable, human-readable lowercase SKU slugs.
- Keep unit labels free text; do not invent structured measurement parsing.
- Keep tags lowercase and useful for deterministic search/planner meaning.
- Use category labels and IDs exactly as defined in `CONTEXT.md`.
- Use `is_available=True` unless the user is intentionally modelling an
  unavailable SKU for validation.
- Preserve backend-owned display order. When replacing a SKU, usually reuse the
  replaced SKU's display order.
- Avoid advanced commerce features such as promotions, variants, inventory
  reservation, shipping, or customer account behavior.

## Image Review

The image is generated only after the SKU proposal is approved. It is still a
static reviewed asset:

- Do not leave app-referenced images under `$CODEX_HOME/generated_images`.
- Copy or convert the accepted image into the workspace.
- Prefer web-friendly dimensions and size while preserving the 4:3 catalog
  frame.
- Keep the original generated file in place unless the user explicitly asks to
  delete it.
