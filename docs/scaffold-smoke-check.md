# Scaffold Smoke Check

Use this checklist after backend or frontend scaffold changes. It verifies that
the repository scaffold, documented commands, and local backend/frontend wiring
still work together. For changed frontend workflows, also complete
`docs/frontend-browser-approval-check.md`; that checklist is the source of truth
for browser approval on user-facing frontend changes.

Run commands from the repository root unless a checklist item changes directory.

## Automated Checks

- [ ] Install backend dependencies: `cd backend && uv sync`.
- [ ] Verify backend package imports:
  `cd backend && uv run python -c "import tavola.api, tavola.domain"`.
- [ ] Run backend tests: `cd backend && uv run pytest`.
- [ ] Run backend linting: `cd backend && uv run ruff check .`.
- [ ] Run backend format check: `cd backend && uv run ruff format --check .`.
- [ ] Install frontend dependencies: `cd frontend && npm install`.
- [ ] Run frontend tests: `cd frontend && npm test`.
- [ ] Run frontend linting: `cd frontend && npm run lint`.
- [ ] Run frontend build: `cd frontend && npm run build`.

## Cross-Service Live Proxy Checks

- [ ] Start the backend: `cd backend && uv run uvicorn tavola.api.main:app --reload`.
- [ ] In another shell, confirm backend health returns HTTP 200 JSON:
  `curl http://localhost:8000/api/health`.
- [ ] Start the frontend: `cd frontend && npm run dev`.
- [ ] Open the Vite URL, normally `http://localhost:5173`, in the Codex in-app
  Browser when available.
- [ ] Confirm the Tavola app shell renders with catalog, basket, and checkout
  navigation placeholders.
- [ ] Confirm the backend status panel changes from checking to connected.
- [ ] In the browser network panel, confirm the frontend requests
  `/api/health` from the Vite origin and receives the backend health response
  through the Vite proxy.
- [ ] If the scaffold change also changed a frontend workflow, complete
  `docs/frontend-browser-approval-check.md` and report any unchecked items.

## Basket Creation And Editing Browser Smoke Check

Use this script for the basket creation and editing workflow after the basket
slice changes or when validating the full backend/frontend scaffold. The basket
contents are backend-owned; the frontend must store only the opaque
`basket_id` in `localStorage`, under `tavola:basket_id`, and must not cache
basket lines, quantities, prices, or totals there.

- [ ] Start the backend:
  `cd backend && uv run uvicorn tavola.api.main:app --reload`.
- [ ] Start the frontend in another shell: `cd frontend && npm run dev`.
- [ ] Open the Vite URL, normally `http://localhost:5173`, in the Codex in-app
  Browser when available.
- [ ] Confirm the backend status is connected and the persistent `Current
  basket` panel renders.
- [ ] Clear existing browser state for this origin, reload the page, and confirm
  a fresh empty basket is created automatically before any product is added.
- [ ] Inspect `localStorage` for the Vite origin and confirm it contains
  `tavola:basket_id` with one basket ID value. Confirm no basket contents,
  line data, quantities, prices, or totals are stored in `localStorage`.
- [ ] From a catalog card, click `Add to basket` for `Fresh Tagliatelle` and
  confirm the `Current basket` panel shows one line with quantity `1`,
  backend-calculated line total, basket total, and item count.
- [ ] On the same catalog card, confirm the add button changes to show the SKU
  is already in the basket, such as `Add another` with `1 in basket`.
- [ ] Open `View details` for `Fresh Tagliatelle`, click the detail modal's add
  action, and confirm the existing basket line is merged to quantity `2`
  rather than duplicated.
- [ ] From the basket panel, edit `Fresh Tagliatelle` quantity to `4` using the
  quantity input or increment control, and confirm the line total, basket total,
  and item count update from the backend response.
- [ ] Attempt to set `Fresh Tagliatelle` quantity to `11` and confirm the
  basket rejects the change with the backend validation message
  `Quantity cannot exceed 10.` The basket item count and totals should remain at
  the last accepted quantity.
- [ ] Remove `Fresh Tagliatelle` from the basket and confirm removing the final
  line leaves the same basket visible as an empty backend-owned basket.
- [ ] Add a product again, copy the current `tavola:basket_id` value, refresh
  the browser, and confirm the basket reloads with the stored basket ID and the
  same backend-owned contents.
- [ ] Stop and restart the backend process. With the same browser
  `localStorage` still present, reload the frontend page and confirm the
  disappeared in-memory basket is recovered by creating a fresh empty basket.
- [ ] Inspect `localStorage` again and confirm `tavola:basket_id` was replaced
  with the new basket ID, with no basket contents stored client-side.
