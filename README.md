# Tavola

Tavola is a lightweight e-commerce demonstrator for an independent Italian deli.
It has a FastAPI backend and a Vite React TypeScript frontend, shaped around the
domain boundaries described in `CONTEXT.md`.

The current scaffold proves the local developer workflow: the backend serves a
health API, the frontend renders the Tavola storefront shell, and Vite proxies
frontend `/api/*` requests to the backend during development.

## Project Layout

```text
backend/   FastAPI app, backend tests, uv project metadata
frontend/  Vite React TypeScript app, frontend tests, npm project metadata
docs/      Plans and scaffold verification notes
```

## Prerequisites

- Python 3.12+
- uv
- Node.js and npm

## Install

Install backend dependencies:

```sh
cd backend
uv sync
```

Install frontend dependencies:

```sh
cd frontend
npm install
```

## Run Locally

Start the backend API on `http://localhost:8000`:

```sh
cd backend
uv run uvicorn tavola.api.main:app --reload
```

In a second shell, start the frontend on Vite's local development URL, usually
`http://localhost:5173`:

```sh
cd frontend
npm run dev
```

The frontend calls `/api/health`. In development, Vite proxies `/api/*` to
`http://localhost:8000` by default. Override that target with
`VITE_BACKEND_PROXY_TARGET` if the backend is running elsewhere.

## Verify

Run backend checks:

```sh
cd backend
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Run frontend checks:

```sh
cd frontend
npm test
npm run lint
npm run build
```

For the full scaffold smoke flow, use `docs/scaffold-smoke-check.md`.
