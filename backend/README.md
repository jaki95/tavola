# Tavola Backend

FastAPI backend scaffold for the Tavola demonstrator.

## Local Setup

Install dependencies:

```sh
uv sync
```

Run the development API server:

```sh
uv run uvicorn tavola.api.main:app --reload
```

The API is available at `http://localhost:8000` by default. The scaffold health
endpoint is `GET /api/health`.

Validate the package layout:

```sh
uv run python -c "import tavola.api, tavola.domain"
```

Run tests:

```sh
uv run pytest
```

## Planner Codex Configuration

The menu-to-basket Planner is either live Codex-backed or disabled. Live Codex
runs are opt-in:

```sh
TAVOLA_PLANNER_CODEX_ENABLED=true
```

The backend includes the `openai-codex` Python SDK dependency for Codex-backed
planner runs. Because the current SDK beta depends on a prerelease runtime,
`pyproject.toml` allows prereleases and pins the test `httpx` dependency below
`1.0` so existing FastAPI test clients stay stable.

Configure real runs with:

- `TAVOLA_PLANNER_CODEX_MODEL`: Codex model name, default `gpt-5.5`.
- `TAVOLA_PLANNER_CODEX_SANDBOX_MODE`: default `read-only`. Use
  `workspace-write` only if a later adapter spike proves the MCP setup needs
  write access.
- `TAVOLA_PLANNER_CODEX_TIMEOUT_SECONDS`: planner run timeout, default `60`.
- `TAVOLA_PLANNER_CODEX_MAX_RETRIES`: adapter retry count, default `1`.
- `TAVOLA_PLANNER_CODEX_MISSING_CREDENTIALS`: `disable` reports the Planner as
  unavailable when credentials are missing; `error` raises during setup checks.
- `TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED`: set to `true` only when relying
  on an existing local Codex login rather than an API key.

For API-key authentication, set `OPENAI_API_KEY` in your local shell or secret
manager. Do not put real credentials in `.env.example`, source control, test
fixtures, or handoff notes.

Run an opt-in local smoke against the seed catalog:

```sh
TAVOLA_PLANNER_CODEX_ENABLED=true \
TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true \
uv run python -m tavola.infrastructure.codex_planner_smoke \
  "Vegetarian dinner for 4 around £50"
```

Use `OPENAI_API_KEY` instead of
`TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true` when authenticating with an
API key. The smoke command starts one Codex-backed planner run with Tavola's
bounded MCP tool server and prints the validated JSON proposal, or a structured
failure if Codex output cannot be validated.

Run an opt-in benchmark smoke to collect paste-safe timing evidence without
printing the proposal by default:

```sh
TAVOLA_PLANNER_CODEX_ENABLED=true \
TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true \
uv run python -m tavola.infrastructure.codex_planner_smoke \
  --benchmark --repeat 3 \
  "Vegetarian dinner for 4 around GBP 50"
```

Benchmark output includes the selected model, timeout, retry count, sanitized
timing events, per-run totals, and min/median/max elapsed milliseconds. It
classifies valid runs under 10 seconds as `ideal`, valid runs under 30 seconds
as `acceptable`, and valid runs at or above 30 seconds as `slow`. Slow valid
runs exit zero; planner failures, malformed output, missing required Tavola tool
use, technical timeout, and missing configuration exit nonzero. Do not paste
prompts, raw Codex transcripts, tool arguments, credentials, stack traces, or
proposal JSON into handoff notes.

For an operator-facing walkthrough of the browser demo, persona prompts, safe
planner notes, and customer-facing language rules, see
[`docs/demo-codex-planner.md`](../docs/demo-codex-planner.md).

Run quality checks:

```sh
uv run ruff check .
uv run ruff format --check .
```

Apply formatting:

```sh
uv run ruff format .
```
