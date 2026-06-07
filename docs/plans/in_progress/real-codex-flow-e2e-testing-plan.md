# Plan: Real Codex Flow End-To-End Testing

**Generated**: 2026-06-04
**Estimated Complexity**: Medium

## Overview

Run Tavola's Planner through the real Codex path end to end, without adding a
deterministic runtime planner. The test proves that a live Codex-backed backend
session can use Tavola's catalog-only MCP tool, return a customer-reviewable
menu proposal, pass deterministic Tavola validation, and let the customer accept
that proposal into the basket through the existing storefront.

A Platform API key is not strictly required. Tavola can use local Codex
credentials if the backend process can access a valid local Codex login. The
real-flow contract is:

- Local Codex auth available: run with
  `TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true`.
- Platform API key available: run with `OPENAI_API_KEY`.
- Neither available: Planner remains disabled.

Official Codex docs consulted on 2026-06-04:

- Codex authentication supports ChatGPT sign-in, API-key sign-in, cached local
  credentials, and enterprise Codex access tokens for trusted local automation.
- The Python Codex SDK controls a local Codex app-server over JSON-RPC and uses
  a pinned Codex runtime by default.
- Codex access tokens are intended for trusted local automation when ChatGPT
  workspace identity is required; Platform API keys remain suitable for
  usage-based automation.

## Prerequisites

- Sprint 5 real-or-disabled planner implementation is present.
- Backend dependencies are installed with `cd backend && uv sync`.
- Frontend dependencies are installed with `cd frontend && npm install`.
- One real Codex credential path is available:
  - Local Codex login already completed on this machine, or
  - `OPENAI_API_KEY` set in the shell, or
  - `CODEX_ACCESS_TOKEN` available and persisted with
    `codex login --with-access-token`.
- No credentials are committed, printed, pasted into docs, or captured in
  screenshots.
- The operator knows which Codex credential path is being tested and records
  only the path type, not secret values.

## Sprint 1: Real Codex E2E Run

**Goal**: Run the full real Codex planner workflow from credential preflight
through backend smoke, browser approval, regression checks, and safe handoff.

**Demo/Validation**:

- Backend status reports live Codex mode when credentials are available.
- Disabled mode still appears when credentials are absent or live Codex is not enabled.
- Smoke commands return validated menu proposals for known persona prompts.
- Browser approval covers live status, backend-owned Planning updates,
  follow-up, proposal, validation error, append acceptance, replace acceptance,
  and success states.
- Catalog, basket, and checkout remain usable.
- Automated backend and frontend checks still pass after the live run.

### Execution Findings: 2026-06-04 Live Local Codex Run

Credential path tested:

- Local Codex login declared with
  `TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true`.
- No credential values, auth files, raw transcripts, or stack traces were
  recorded in the handoff.

Live status and fallback findings:

- Live backend status returned `enabled: true` and `mode: "real_codex"`.
- Disabled fallback returned `enabled: false` and `mode: "disabled"` when live
  credentials were not declared.
- The frontend showed the live and disabled Planner states through the Vite
  `/api/planner/status` proxy.
- The catalog remained visible below the compact Planner band in both live and
  disabled states.

Model and SDK findings:

- The previous default model `gpt-5.2-codex` failed for the local ChatGPT-backed
  Codex account with an unsupported-model error.
- `gpt-5.1-codex`, `gpt-5.1-codex-max`, `gpt-5.1-codex-mini`,
  `gpt-5.5-codex`, `gpt-5.5-codex-max`, and `gpt-5.5-codex-mini` were also
  unsupported through this credential path.
- `gpt-5.5` was accepted by the local Codex SDK and is now the configured
  default model.
- The Python SDK was initially started with `ApprovalMode.deny_all`, which
  caused Tavola MCP tool calls to be rejected as user-denied. The adapter now
  uses `ApprovalMode.auto_review` while keeping the Codex sandbox at
  `read-only`.

MCP tool-use findings:

- These findings are historical evidence from the 2026-06-04 live run, not the
  current planner tool contract.
- The original prompt required `list_package_templates`, `search_catalog`,
  `get_sku_detail`, and `validate_menu_proposal`.
- `search_catalog` already returns product identity, name, category, unit label,
  price, short description, tags, dietary facets, availability, and image ID.
  Requiring `get_sku_detail` for every selected product caused avoidable tool
  calls for ordinary proposals.
- The happy-path required tool contract was later reduced to
  `list_package_templates`, `search_catalog`, and `validate_menu_proposal`, then
  superseded by the catalog-candidate MCP plan.
- Current live planner proposal runs should expose only Tavola's bounded catalog
  candidate finder to Codex. Tavola validates the returned proposal after Codex
  responds and may send one invalid proposal back to Codex for repair. Codex
  should not require `search_catalog`, `list_package_templates`,
  `get_sku_detail`, or `validate_menu_proposal`.

Historical timing findings from a sanitized 2026-06-04 live trace for
`Vegetarian dinner for 4 around £50`:

```text
total_run_ms 50481
list_package_templates 0ms
search_catalog 1ms
search_catalog 1ms
validate_menu_proposal 0ms
tool_total_ms 2
non_tool_elapsed_ms 50479
```

- MCP server execution was effectively instantaneous.
- The second search was model-selected refinement: first query
  `vegetarian dinner for 4 antipasto primo dessert around £50`, then broader
  query `vegetarian`.
- The measured latency came from the Codex model/app-server turn rather than
  Tavola MCP handlers.
- Treat the listed tool names as historical trace labels; new smoke output
  should show Codex using `find_catalog_candidates`, followed by Tavola
  validating the returned proposal outside the Codex tool surface.
- These timing findings are historical benchmark evidence, not intended Planner
  UX. Current browser checks should expect backend-owned Planning updates from
  Tavola's session lifecycle, not elapsed-time phases inferred by the frontend.

Browser findings:

- The browser reached a proposal-ready state for
  `Vegetarian dinner for 4 around £50` in about 55 seconds after reducing the
  required MCP tool contract.
- The proposal rendered title, explanation, courses, product lines, quantities,
  rationales, planner notes, item count, total, and Add/Replace actions.
- Customer-facing UI did not show `SKU` or `sku_id`.
- Editing a proposal quantity and using Add to basket succeeded; the basket and
  catalog basket badges updated without page reload.
- Browser console error logs were empty during the checked live status,
  disabled fallback, proposal, and append-success states.

Evidence screenshots were captured under `/private/tmp/` during the run and
were not committed to the repository.

### Latency Benchmark Addendum

The real-flow test now includes Tavola's Planner latency benchmark checklist.
The benchmark remains an opt-in real Codex SDK exercise, not a normal automated
test and not a reason to introduce a fake runtime planner or direct non-SDK
model path.

Benchmark classes are operator evidence only. They must not drive customer
progress copy; the Planner UI should render Planning updates returned by the
backend while the session status is `planning`.

Targets:

- Ideal: valid proposal below 10 seconds.
- Acceptable: valid proposal below 30 seconds.
- Slow path: valid proposal at or above 30 seconds, recorded as a benchmark
  miss even if the Planning UX remains usable until the technical timeout.

Primary benchmark command:

```sh
cd backend
TAVOLA_PLANNER_CODEX_ENABLED=true \
TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true \
uv run python -m tavola.infrastructure.codex_planner_smoke \
  --benchmark --repeat 3 \
  "Vegetarian dinner for 4 around GBP 50"
```

Record model, reasoning effort, timeout, retry count, per-run class, and
min/median/max totals. Do not record raw transcripts, prompts beyond approved
persona labels, tool arguments, proposal JSON, credentials, credential paths,
stack traces, or SDK traces.

Prior timing evidence showed the Tavola MCP server was not the bottleneck:
`Vegetarian dinner for 4 around GBP 50` spent about 2 ms in MCP handlers and
about 50 seconds in non-tool Codex SDK/model time. Future benchmark notes should
call out any material change to that split.

### Task 1.1: Verify Local Codex Auth Path

- **Location**: Local shell, `backend/README.md`
- **Description**: Confirm which real credential path will be used for the test:
  local Codex login, API key, or Codex access token.
- **Dependencies**: None.
- **Acceptance Criteria**:
  - The chosen credential path is known.
  - No credential value is echoed into terminal transcripts intended for
    handoff.
  - If local Codex login is used, the backend run is configured with
    `TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true`.
  - If API-key auth is used, the backend run is configured with `OPENAI_API_KEY`
    in the local shell only.
- **Validation**:
  - Run `codex login` or `codex login --with-access-token` only if local auth is
    missing.
  - Do not include secret output in the handoff.

### Task 1.2: Start Backend In Live Planner Mode

- **Location**: `backend/`
- **Description**: Start FastAPI with real Codex enabled and the selected
  credential path.
- **Dependencies**: Task 1.1.
- **Acceptance Criteria**:
  - Backend starts without exposing raw auth errors.
  - `GET /api/planner/status` returns `enabled: true` and
    `mode: "real_codex"`.
  - If credentials are absent, status returns disabled and no real-flow browser
    test begins.
- **Validation**:
  - Local Codex login path:
    ```sh
    cd backend
    TAVOLA_PLANNER_CODEX_ENABLED=true \
    TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true \
    uv run uvicorn tavola.api.main:app --reload
    ```
  - API-key path:
    ```sh
    cd backend
    TAVOLA_PLANNER_CODEX_ENABLED=true \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    uv run uvicorn tavola.api.main:app --reload
    ```
  - Status check:
    ```sh
    curl -s http://127.0.0.1:8000/api/planner/status
    ```

### Task 1.3: Reconfirm Disabled Fallback

- **Location**: `backend/src/tavola/config/settings.py`,
  `backend/tests/test_settings.py`
- **Description**: Before or after the live run, confirm that removing live
  credentials returns Tavola to disabled mode, not a fake planner.
- **Dependencies**: Task 1.2.
- **Acceptance Criteria**:
  - Disabled status says the Planner is unavailable.
  - No deterministic runtime proposal is produced.
- **Validation**:
  - `cd backend && uv run pytest tests/test_settings.py tests/test_planner_api.py`

### Task 1.4: Run Vegetarian Dinner Smoke

- **Location**: `backend/src/tavola/infrastructure/codex_planner_smoke.py`
- **Description**: Run one real Codex smoke with the primary demo prompt.
- **Dependencies**: Task 1.2.
- **Acceptance Criteria**:
  - Output status is proposal-ready.
  - Proposal contains only real catalog products.
  - Proposal includes customer-readable planner notes.
  - Totals are calculated by Tavola after validation.
  - No raw Codex transcript, token, credential, or stack trace is printed.
- **Validation**:
  ```sh
  cd backend
  TAVOLA_PLANNER_CODEX_ENABLED=true \
  TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true \
  uv run python -m tavola.infrastructure.codex_planner_smoke \
    "Vegetarian dinner for 4 around £50"
  ```

### Task 1.5: Run Follow-Up Smoke

- **Location**: `backend/src/tavola/application/planner.py`,
  `backend/src/tavola/infrastructure/codex_planner/`
- **Description**: Exercise an under-specified request that should ask for party
  size before returning a proposal.
- **Dependencies**: Task 1.4.
- **Acceptance Criteria**:
  - `Help me plan Sunday lunch` produces `needs_input` when party size is
    absent, or an equivalent honest limitation if Codex cannot proceed.
  - Supplying a party-size answer lets the session continue to proposal-ready.
  - Follow-up copy remains customer-safe.
- **Validation**:
  - Use the API route manually or a temporary smoke command extension if the
    existing smoke command only covers one-shot prompts.
  - Record whether the current smoke command needs a follow-up helper before
    browser testing.

### Task 1.6: Run Aperitivo Smoke

- **Location**: `backend/src/tavola/infrastructure/codex_planner_smoke.py`
- **Description**: Run the drinks persona to verify real Codex includes drinks
  only when the request supports them.
- **Dependencies**: Task 1.4.
- **Acceptance Criteria**:
  - Proposal uses an Aperitivo shape.
  - Drink lines are real catalog products.
  - Alcohol assumptions are clear if wine is included.
  - Proposal validates through Tavola.
- **Validation**:
  ```sh
  cd backend
  TAVOLA_PLANNER_CODEX_ENABLED=true \
  TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true \
  uv run python -m tavola.infrastructure.codex_planner_smoke \
    "Aperitivo for 6 with drinks"
  ```

### Task 1.7: Start Backend And Frontend Together

- **Location**: `backend/`, `frontend/`
- **Description**: Run the real backend and the Vite frontend so frontend API
  calls use the proxy.
- **Dependencies**: Tasks 1.4 to 1.6.
- **Acceptance Criteria**:
  - Frontend service status shows the backend is ready.
  - Planner mode shows live Codex mode.
  - The first catalog row remains visible under the compact planner band before
    a proposal is ready.
- **Validation**:
  ```sh
  cd backend
  TAVOLA_PLANNER_CODEX_ENABLED=true \
  TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true \
  uv run uvicorn tavola.api.main:app --reload
  ```
  ```sh
  cd frontend
  npm run dev
  ```

### Task 1.8: Verify Vegetarian Dinner Append Flow

- **Location**: `frontend/src/features/planner/PlannerWorkspace.tsx`
- **Description**: Submit the vegetarian dinner prompt, review the proposal,
  make a small edit, and append it to the basket.
- **Dependencies**: Task 1.7.
- **Acceptance Criteria**:
  - Backend-owned Planning updates are visible while the session is
    `planning`.
  - Proposal-ready state renders courses, products, quantities, rationale,
    planner notes, warnings, item count, and total.
  - Customer-facing UI does not say `SKU`.
  - Quantity edit updates local totals and server validation normalizes the
    proposal before acceptance.
  - Add to basket updates the basket without page reload.
- **Validation**:
  - Prompt: `Vegetarian dinner for 4 around £50`.
  - Capture screenshot of proposal-ready state.
  - Capture screenshot after Add to basket success.

### Task 1.9: Verify Follow-Up Flow

- **Location**: `frontend/src/features/planner/PlannerWorkspace.tsx`,
  `backend/src/tavola/api/routers/planner.py`
- **Description**: Submit an under-specified prompt and answer the required
  party-size follow-up.
- **Dependencies**: Task 1.7.
- **Acceptance Criteria**:
  - Follow-up state appears before proposal-ready when party size is missing.
  - Original customer request remains visible.
  - Answering with party size continues to a validated proposal.
  - Follow-up answer is not accepted after proposal-ready or accepted state.
- **Validation**:
  - Prompt: `Help me plan Sunday lunch`.
  - Follow-up answer: `Four people`.
  - Capture screenshot of follow-up state and final proposal state.

### Task 1.10: Verify Replace Basket Flow

- **Location**: `frontend/src/features/planner/PlannerWorkspace.tsx`,
  `backend/src/tavola/application/planner.py`
- **Description**: Start from a non-empty basket, submit the aperitivo prompt,
  and replace the basket with the accepted proposal.
- **Dependencies**: Task 1.7.
- **Acceptance Criteria**:
  - Existing basket contents are visible before replacement.
  - Replace action asks for confirmation when basket is non-empty.
  - Confirmed replace updates the basket to the planner proposal lines.
  - Meal-plan grouping metadata is returned by the API.
- **Validation**:
  - Prompt: `Aperitivo for 6 with drinks`.
  - Capture screenshot of replace confirmation and replacement success.

### Task 1.11: Verify Error And Validation States

- **Location**: `frontend/src/features/planner/usePlanner.ts`,
  `backend/src/tavola/application/planner.py`
- **Description**: Exercise an unsupported or hard-constraint prompt and a
  customer edit that server validation rejects.
- **Dependencies**: Task 1.7.
- **Acceptance Criteria**:
  - Unsupported request produces an honest limitation or safe failed state.
  - Validation errors use product/item language, not internal identity language.
  - The basket is unchanged after validation failure.
  - No raw Codex runtime details, stack traces, credentials, tool counts, or
    transcripts appear in the UI.
- **Validation**:
  - Example prompt: `Dairy-free dinner for 8 under £20`.
  - Edit a proposal quantity beyond the basket maximum if a proposal is ready.
  - Capture screenshot of visible error state.

### Task 1.12: Run Automated Regression Checks

- **Location**: `backend/`, `frontend/`
- **Description**: Re-run the standard Tavola checks after live Codex testing.
- **Dependencies**: Tasks 1.8 to 1.11.
- **Acceptance Criteria**:
  - Backend tests pass.
  - Backend lint and format checks pass.
  - Frontend tests, lint, and production build pass.
- **Validation**:
  ```sh
  cd backend && uv run pytest
  cd backend && uv run ruff check .
  cd backend && uv run ruff format --check .
  cd frontend && npm test
  cd frontend && npm run lint
  cd frontend && npm run build
  ```

### Task 1.13: Complete Browser Approval Checklist

- **Location**: `docs/frontend-browser-approval-check.md`
- **Description**: Record the browser states tested through the in-app Browser.
- **Dependencies**: Tasks 1.8 to 1.11.
- **Acceptance Criteria**:
  - Planning updates, empty, live status, follow-up, proposal, validation error,
    append success, replace success, and disabled fallback are either checked or
    explicitly marked unchecked with a reason.
  - Browser console is checked for unexpected errors.
  - Vite proxy path `/api/planner/status` is confirmed.
- **Validation**:
  - Use the in-app Browser at the supported desktop viewport.
  - Keep screenshots in a temporary location or attached handoff, not in source
    control unless explicitly requested.

### Task 1.14: Produce Safe Handoff

- **Location**: Final agent response, optional `docs/demo-codex-planner.md`
  update if the run reveals durable demo guidance.
- **Description**: Summarize the real-flow result in Tavola terms.
- **Dependencies**: Tasks 1.12 and 1.13.
- **Acceptance Criteria**:
  - Handoff states credential path type only, not secret values.
  - Handoff lists prompts tested, states verified, and screenshots captured.
  - Handoff notes any Codex output repair retries or typed failures without raw
    transcript dumps.
  - Handoff names remaining gaps.
- **Validation**:
  - Manual review for secret leakage before sharing.

## Testing Strategy

- Start narrow with backend status and smoke commands before launching the
  browser.
- Use live Codex only for the real-flow smoke and browser approval; keep normal
  automated tests deterministic through injected test doubles.
- Treat server-side Tavola validation as the acceptance source of truth.
- Capture enough browser evidence to prove the user workflow, but avoid raw
  transcripts or secret-bearing logs.
- Re-run the ordinary backend and frontend suites after live testing to prove
  the demonstrator remains stable.

## Potential Risks & Gotchas

- **Local login not visible to backend**: The backend process may run with a
  different `CODEX_HOME` or credential store. Mitigate by starting the backend
  from the same user/session and setting `CODEX_HOME` only when intentional.
- **API key vs local login policy mismatch**: ChatGPT login follows ChatGPT
  workspace policy; API keys follow Platform organization policy. Record which
  one is used because audit and billing behavior differ.
- **Codex output varies**: Product choices and totals may differ between runs.
  Validate shape, constraints, and Tavola-calculated totals rather than exact
  item names unless the prompt requires a product.
- **Latency**: Real Codex may be slow. Verify backend-owned Planning updates and
  avoid repeated browser submissions while one planner run is pending.
- **Repair behavior**: The live demo defaults to zero malformed-output repair
  retries to avoid doubling a slow customer wait after invalid JSON or a bad
  final contract. Tavola validation repair is separate: when Codex returns an
  invalid proposal, Tavola may send it back once for correction, then validates
  the repaired result. If repair still fails, the correct outcome is a safe
  failed state, not a fake proposal.
- **Credential leakage**: Do not paste tokens, `auth.json`, SDK traces, or raw
  transcripts into docs, tickets, screenshots, or handoff notes.
- **In-memory state reset**: Restarting the backend loses planner sessions and
  baskets. Keep browser runs within one backend process unless testing recovery.

## Rollback Plan

- Set `TAVOLA_PLANNER_CODEX_ENABLED=false` to return the Planner to disabled
  mode.
- Remove any local shell exports for `OPENAI_API_KEY`, `CODEX_ACCESS_TOKEN`, or
  `TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED`.
- If local Codex auth was created only for this test, run the appropriate Codex
  logout or revoke the access token from the workspace/admin console.
- Restart backend and frontend, then confirm `/api/planner/status` reports
  disabled and ordinary catalog/basket flows still work.
