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

Runtime settings load the nearest discovered `.env` file before reading
environment variables. Values already present in the shell take precedence.

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
- `TAVOLA_PLANNER_CODEX_REASONING_EFFORT`: SDK turn reasoning effort, default
  `low` for the constrained live demo planner task. Set `sdk-default` to omit
  the effort argument when comparing against the SDK's implicit default in
  opt-in benchmarks. Other supported values are `none`, `minimal`, `medium`,
  `high`, and `xhigh`.
- `TAVOLA_PLANNER_CODEX_TIMEOUT_SECONDS`: planner run timeout, default `120`.
- `TAVOLA_PLANNER_CODEX_MAX_RETRIES`: malformed or contract-invalid Codex output
  retry count, default `0`. Repair retries are configurable for experiments,
  but the live demo default avoids doubling a slow customer wait after malformed
  output. Tavola validation failure repair is separate: the backend may send one
  invalid proposal back to Codex once, then Tavola validates the repaired result.
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
catalog-only MCP tool server and prints the validated JSON proposal, or a
structured failure if Codex output cannot be validated. Codex proposal runs
should use `find_catalog_candidates`; Tavola validates the returned proposal
after Codex responds and may send one invalid proposal back to Codex for repair.
The Codex-side tool surface should not expose the removed generic catalog search
tools or `validate_menu_proposal`.

Run an opt-in benchmark smoke to collect paste-safe timing evidence without
printing the proposal by default:

```sh
TAVOLA_PLANNER_CODEX_ENABLED=true \
TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true \
uv run python -m tavola.infrastructure.codex_planner_smoke \
  --benchmark --repeat 3 \
  "Vegetarian dinner for 4 around GBP 50"
```

Benchmark output includes the selected model, reasoning effort, timeout, retry
count, sanitized timing events, per-run totals, and min/median/max elapsed
milliseconds. It classifies valid runs under 10 seconds as `ideal`, valid runs
under 30 seconds as `acceptable`, and valid runs at or above 30 seconds as
`slow`. Slow valid runs exit zero; planner failures, malformed output,
technical timeout, and missing configuration exit nonzero. Do not paste prompts,
raw Codex transcripts, tool arguments, credentials, stack traces, or proposal
JSON into handoff notes.

Use this benchmark handoff format after at least three repeats of the primary
persona:

```text
model: <model>
reasoning_effort: <low|sdk-default|...>
timeout_seconds: <seconds>
max_retries: <count>
primary_persona_totals_ms: min <n>, median <n>, max <n>
primary_persona_classes: <ideal|acceptable|slow|failed>
decision: <below 10s achieved|below 30s accepted|above 30s demo slow-path>
```

The primary persona is `Vegetarian dinner for 4 around GBP 50`. Use
`docs/demo-codex-planner.md` for the broader browser demo personas and
customer-facing acceptance checks. Previous sanitized traces showed Tavola MCP
tool handlers taking about 2 ms during a roughly 50-second live run, so benchmark
decisions should focus on Codex SDK model/config behavior unless new timing
events show a different bottleneck.

The installed `openai-codex` SDK accepts model names as strings; public model
documentation is not proof that a model is available through the active local
credential path. Keep `gpt-5.5` as the documented default unless an opt-in
benchmark run proves another SDK-accepted model is faster and still returns
valid Tavola proposals.

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
