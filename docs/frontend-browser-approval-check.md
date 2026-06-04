# Frontend Browser Approval Check

Use this checklist for every change under `frontend/` and every user-facing
browser workflow change. Tavola is desktop-first, so verify the changed flow at a
supported desktop viewport unless the user explicitly requested mobile behavior.

## Setup

- [ ] Start the frontend: `cd frontend && npm run dev`.
- [ ] If the changed flow depends on backend APIs, start the backend:
  `cd backend && uv run uvicorn tavola.api.main:app --reload`.
- [ ] Open the Vite URL, normally `http://localhost:5173`, in the Codex in-app
  Browser when available.

## Flow Verification

- [ ] Exercise the changed user workflow in the browser.
- [ ] Verify the loading, empty, error, and success states touched by the change.
- [ ] Verify critical user-facing state remains visible and understandable.
- [ ] Verify keyboard-accessible controls still work for the changed flow.
- [ ] Confirm there are no unexpected console errors during the changed flow.

## Backend-Backed Flows

- [ ] Confirm relevant frontend requests use the expected Vite proxy path.
- [ ] Confirm backend responses drive the visible UI state rather than hardcoded
  or stale client state.
- [ ] Confirm recoverable API failures surface a visible error state.

## Handoff

- [ ] Report the browser checks run.
- [ ] Report any unchecked items with the reason they could not be completed.
