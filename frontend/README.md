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
