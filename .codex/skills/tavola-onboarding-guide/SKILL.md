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
   composition, frontend API clients, and current feature areas.

3. Produce an onboarding guide using `references/guide-template.md` as the
   section contract. Keep it readable for a new agent or engineer who needs to
   orient in minutes.

4. Include one Mermaid diagram. Prefer a single `flowchart LR` diagram based on
   the discovered current repo shape: frontend composition and feature areas,
   frontend API client boundary, backend routers/schemas, application use cases,
   domain rules, infrastructure adapters, and any external boundaries that are
   actually present.

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
- Call out persistence and external-system boundaries explicitly, whether they
  are static, in-memory, database-backed, generated, or adapter-driven.
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

For a full section checklist, read `references/guide-template.md`.
