# Tavola Onboarding Guide Template

Use this template when producing the final guide. Keep headings concise and
omit sections that are not supported by current source inspection.

When saving a guide artifact, use `docs/onboarding/architecture-guide.md` unless
the user requested a different path.

## Product Summary

Explain Tavola's purpose in one paragraph using `CONTEXT.md` as the authority.
Name the current customer or operator workflows found in the source tree.

## Architecture At A Glance

Summarize the layer split found in the current repo. Include only layers and
boundaries that are present:

- Backend API: FastAPI routing, request/response schemas, dependency wiring.
- Backend application: use cases and workflow orchestration.
- Backend domain: business rules and invariants.
- Backend infrastructure: persistence, seed/static data, external adapters,
  background work, generated resources, or tool boundaries that exist now.
- Frontend API clients: transport calls and response shape guards.
- Frontend features/pages: current page composition and feature areas.

## Key Backend Concepts

Group concepts by the current workflows and domain modules. Use concrete names
from the domain/application files and avoid implying missing capabilities.

## API Routes

List routes as method/path plus purpose. Mention that `Settings.api_prefix`
defaults to `/api`.

## Frontend Boundaries

Explain how the current frontend entry points compose pages, feature areas,
components, hooks, API clients, and types. Map feature folders to workflows only
when the source supports that mapping.

## Data Flow

Trace the major flows discovered from routes, frontend API clients, feature
hooks/components, and application use cases. Prefer 2-5 flows with concrete
file references over an exhaustive list.

## Tests And Scripts

Summarize backend pytest areas, frontend Vitest/component areas, and commands
from `AGENTS.md`, `backend/pyproject.toml`, and `frontend/package.json`.

## Mermaid Diagram

Use a single Mermaid `flowchart LR` diagram. Keep node labels short enough to
render cleanly. Prefer grouped subgraphs for frontend, API, application/domain,
and infrastructure.

## Where To Start

Give practical edit entry points:

- API contract change: router + schema + frontend API client + tests.
- Domain rule change: domain tests first, then application/API wiring.
- UI workflow change: feature component/hook tests, then browser approval check.
- External adapter/tooling change: application boundary plus concrete
  infrastructure adapter and tests.
