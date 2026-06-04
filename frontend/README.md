# Tavola Frontend

Vite React TypeScript frontend scaffold for the Tavola demonstrator.

## Local Setup

Install dependencies:

```sh
npm install
```

Run the development server:

```sh
npm run dev
```

Vite serves the app on its local development URL, usually
`http://localhost:5173`, and proxies `/api/*` requests to the backend. The
default proxy target is `http://localhost:8000`; set
`VITE_BACKEND_PROXY_TARGET` to point at a different backend during local
development.

The storefront includes Tavola's Planner workspace. For the Codex Planner demo
script, supported persona prompts, expected follow-up behavior, and safe
customer-facing copy rules, see
[`docs/demo-codex-planner.md`](../docs/demo-codex-planner.md).

Run tests:

```sh
npm test
```

Run quality checks:

```sh
npm run lint
npm run build
```

Preview the production build locally:

```sh
npm run preview
```
