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
- Backend application: use cases, meaning focused workflow entry points that
  coordinate domain objects and repository/agent ports.
- Backend domain: business rules and invariants owned by entities and value
  objects, independent of FastAPI and infrastructure.
- Backend infrastructure: persistence, seed/static data, external adapters,
  background work, generated resources, or tool boundaries that implement the
  application/domain ports.
- Frontend API clients: transport calls and response shape guards.
- Frontend features/pages: current page composition and feature areas.

## Key Backend Concepts

Group concepts by the current workflows and domain modules. Use concrete names
from the domain/application files and avoid implying missing capabilities.

When every backend concept shares the same fields, prefer a Markdown table over
repeated named bullets:

| Concept | Domain | Application | Infrastructure | Boundary rule |
| --- | --- | --- | --- | --- |
| Concept name | Entities, value objects, and invariants | Use cases and ports that coordinate the workflow | Repositories, seed data, adapters, or external tools | What must stay in this layer or source of truth |

Keep cells concise. If any cell needs several sentences or multiple subpoints,
fall back to named bullets for readability.

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

When every flow shares the same fields, prefer a Markdown table over repeated
named bullets:

| Flow | Starts | Frontend | Backend | Rule/source of truth |
| --- | --- | --- | --- | --- |
| Workflow name | Page/component/hook entry point | API client or state transition | Route and application use case | Domain rule, repository, adapter, or validation owner |

Keep cells concise. If any cell needs several sentences or multiple subpoints,
fall back to named bullets for readability.

## Tests And Scripts

Summarize backend pytest areas, frontend Vitest/component areas, and commands
from `AGENTS.md`, `backend/pyproject.toml`, and `frontend/package.json`.

## Mermaid Diagram

Use a single Mermaid `flowchart LR` diagram. Keep node labels short enough to
render cleanly. Prefer grouped subgraphs for frontend, API, application, domain,
and infrastructure. Avoid long labels, forced line breaks, or repeated edge
labels that make the rendered diagram busy.
Do not copy a generated scan into this section; design the diagram from the
source inspection and the flows described above.

Diagram rules:

- Split application and domain into separate layers.
- Explain the direction of dependency: API calls application use cases; use
  cases call domain rules and depend on ports; infrastructure adapters implement
  those ports and are wired in by dependency providers.
- Show schemas and dependency providers as API-layer collaborators, not as the
  next downstream business flow after routers.
- Put concrete seed data, in-memory repositories, databases, or external tools
  behind named infrastructure adapters/repositories.
- Avoid all-to-all arrows from use cases into infrastructure. Prefer one ports
  node such as "Repository and agent ports" when that makes dependency inversion
  clearer than many individual infrastructure arrows.
- Collapse repeated adapter arrows when they do not add meaning. Prefer a
  grouped "Infrastructure adapters" subgraph with one implement/wire arrow over
  several parallel arrows with the same label.
- Prefer this backend relationship shape when the current source supports it:
  `Routers -> Use cases -> Ports`, `Use cases -> Domain rules`,
  `Dependency providers -. choose adapters .-> Concrete adapters`, and
  `Concrete adapters -. implement .-> Ports`.
- Put `Concrete adapters` inside the infrastructure subgraph and point arrows to
  that node, not to the subgraph id. Include child nodes only for meaningful
  boundaries such as static seed data, in-memory repositories, databases,
  external services, Codex, or MCP tools.
- Show Planner/Codex/MCP boundaries only when they exist in the inspected source.

## Where To Start

Give practical edit entry points:

- API contract change: router + schema + frontend API client + tests.
- Domain rule change: domain tests first, then application/API wiring.
- UI workflow change: feature component/hook tests, then browser approval check.
- External adapter/tooling change: application boundary plus concrete
  infrastructure adapter and tests.
