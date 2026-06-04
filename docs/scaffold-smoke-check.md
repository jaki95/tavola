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
