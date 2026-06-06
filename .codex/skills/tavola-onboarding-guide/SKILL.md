---
name: tavola-onboarding-guide
description: Create a quick Tavola repository onboarding and architecture guide with a Mermaid diagram. Use when someone asks to explain the repo, map backend/frontend boundaries, summarize domain concepts, describe API routes, trace data flow, inventory tests and scripts, create or update docs/onboarding/architecture-guide.md, or produce onboarding documentation for Tavola maintainers or agents.
---

# Tavola Onboarding Guide

## Start Here

Read `AGENTS.md` and `CONTEXT.md` first. Treat `CONTEXT.md` as the authority for
product language, scope, and customer workflow names.

Use this skill to produce an accurate, compact architecture guide from the
current source tree. Do not rely on stale memory or a fixed architecture shape;
inspect the repo and adapt to what exists now.

## Workflow

1. Run the scanner from the repository root:

```bash
cd backend && uv run python ../.codex/skills/tavola-onboarding-guide/scripts/generate_onboarding_scan.py
```

2. Read the scanner output, then manually inspect the key files and directories
   it points to. At minimum, inspect the backend entry points, router/schema
   files, current application/domain/infrastructure directories, frontend page
   composition, frontend API clients, and current feature areas. Treat the scan
   as facts for orientation; draw the diagram yourself after inspection.

3. Produce an onboarding guide using `references/guide-template.md` as the
   section contract. Keep it readable for a new agent or engineer who needs to
   orient in minutes.

4. Include one Mermaid diagram. Prefer a single `flowchart LR` diagram based on
   the discovered current repo shape. Make the layer story explicit:
   frontend clients call API routers; routers invoke application use cases;
   use cases coordinate workflows, call domain objects for rules, and depend on
   repository/agent ports; infrastructure provides concrete adapters that
   implement those ports. Keep schemas and dependency providers as API
   collaborators, not as business-flow steps. Keep node labels short and avoid
   making dependency-provider wiring visually dominant.

## Delivery Target

- If the user asks for an explanation, overview, tour, or quick orientation,
  return the guide in the response.
- If the user asks to create, save, write, update, or maintain an onboarding
  guide/doc/artifact, write it to `docs/onboarding/architecture-guide.md`.
- If `docs/onboarding/architecture-guide.md` already exists and the user asks
  for a saved guide, update that file rather than creating a second guide.
- If the user gives a different path, use the requested path.

## Inspection Rules

- Explain Tavola using the product language in `CONTEXT.md`, not generic store
  language.
- Preserve the layer boundaries from `AGENTS.md` where the current repo still
  uses them. If the source tree has changed, describe the changed boundary
  clearly instead of forcing the old model.
- Name the current major workflows and feature areas in Tavola language.
- Distinguish source-of-truth behavior from transport or UI mapping. For
  example, basket pricing and validation are backend/domain concerns; frontend
  clients validate response shape at the transport boundary.
- Explain "application use case" in plain language: a focused workflow entry
  point such as creating checkout, adding a basket line, or validating a
  planner proposal. It coordinates domain objects and ports, but it should not
  own HTTP details, React state, or concrete persistence/tool implementations.
- Call out persistence and external-system boundaries explicitly, whether they
  are static, in-memory, database-backed, generated, or adapter-driven.
- In diagrams, do not merge application, domain, and infrastructure into one
  layer. Show application use cases, domain invariants, ports/interfaces, and
  infrastructure adapters as distinct nodes or subgraphs. Avoid arrows that
  imply every use case talks to every infrastructure component equally.
- Prefer grouped infrastructure arrows when individual adapter wiring makes the
  diagram noisy. One "infrastructure adapters implement ports" arrow is often
  clearer than several repeated dotted arrows.
- For the infrastructure side of the diagram, prefer one summary node such as
  `Concrete adapters` inside the infrastructure subgraph, with optional child
  nodes for important data/tool boundaries like static seed data or MCP tools.
  Point arrows at that summary node rather than at the subgraph itself; Mermaid
  renderers vary in how they display arrows to subgraph ids.
- Avoid repeated edge labels such as three separate "choose concrete" or
  "implements" arrows. Use one `choose adapters` arrow from dependency providers
  to infrastructure adapters and one `implement` arrow from adapters to ports.
- Mention tests by behavior area and layer rather than dumping every filename.
- Mark any uncertainty as "Inspect further" with concrete files to read.

## Output Style

Use concise prose and concrete file references. A good guide is usually:

- one short product summary
- one architecture overview
- one backend section
- one frontend section
- one data-flow section
- one testing/scripts section
- one Mermaid diagram
- a short "where to start changing things" section

Avoid long undifferentiated prose blocks. For dense sections, prefer compact
named bullets or tables with consistent labels. For backend concepts, use a
table when every concept shares labels such as `Domain`, `Application`,
`Infrastructure`, and `Boundary rule`. For data flow, use a table when every
flow shares labels such as `Starts`, `Frontend`, `Backend`, and
`Rule/source of truth`. Keep table cells concise; if cells need several
sentences, use named bullets instead.

For a full section checklist, read `references/guide-template.md`.
