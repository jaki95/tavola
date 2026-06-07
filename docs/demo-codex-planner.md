# Codex Planner Demo Guide

This guide helps demo Tavola's Codex-powered Planner as a customer-facing
menu-to-basket workflow. Keep the story focused on Tavola: a customer asks for
help planning food, reviews a menu proposal made from real deli products, then
chooses whether to add it to the basket or replace the basket.

Do not include interview-specific context, local credentials, token values, raw
Codex transcripts, SDK traces, stack traces, or secret-bearing command output in
the demo.

## Demo Setup

Run the backend and frontend together so the Vite app can call the FastAPI API
through the local proxy.

Backend:

```sh
cd backend
uv run uvicorn tavola.api.main:app --reload
```

Frontend:

```sh
cd frontend
npm run dev
```

For real Codex-backed planner runs, configure credentials only in the local
shell or a local secret manager. Use `backend/README.md` for the current planner
environment settings and opt-in smoke command. Do not commit real credential
values or paste them into demo notes.

Current live-demo defaults are `gpt-5.5`, `low` reasoning effort, a 60-second
technical timeout, and zero malformed-output repair retries. Tavola validation
failure repair is separate and can send one invalid proposal back to Codex once
before failing safely. Model strings are accepted or rejected by the installed
Codex SDK and the active local credential path, so do not treat public API model
documentation as a guarantee of demo availability. Use the benchmark smoke in
`backend/README.md` to compare `low` against `sdk-default` reasoning effort or
to test candidate model strings. Record only model name, reasoning effort, retry
count, timeout, status, benchmark class, and sanitized timing totals.

## Latency Benchmark Checklist

Tavola's live Planner benchmark target is below 10 seconds for an ideal run and
below 30 seconds for an acceptable demo run. Runs above 30 seconds are benchmark
misses even when the Planning UX remains customer-safe and the backend continues
until the 60-second technical timeout.

These benchmarks are historical/operator evidence only. They must not define
customer-facing progress copy. During Planning, the UI should show backend-owned
Planning updates emitted by Tavola's session lifecycle, and should not invent
elapsed-time phases or later steps from a timer.

Use only the Codex SDK runtime path for benchmark decisions. Do not benchmark or
select a fake runtime planner, direct Responses API fallback, or alternate model
route outside the SDK.

Primary benchmark persona:

```text
Vegetarian dinner for 4 around GBP 50
```

Recommended comparison personas:

- `Dinner for 10 with one vegetarian guest`
- `Antipasti and pasta for 4 around GBP 50`
- `Aperitivo for 6 with drinks`
- `Help me plan Sunday lunch`, followed by a party-size answer in the browser
- An unsupported safety or allergy-like constraint request that Tavola cannot
  honestly satisfy from current catalog facets

For the primary persona, run at least three real Codex benchmark repeats:

```sh
cd backend
TAVOLA_PLANNER_CODEX_ENABLED=true \
TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED=true \
uv run python -m tavola.infrastructure.codex_planner_smoke \
  --benchmark --repeat 3 \
  "Vegetarian dinner for 4 around GBP 50"
```

Record this paste-safe handoff shape:

```text
model: <model>
reasoning_effort: <low|sdk-default|...>
timeout_seconds: <seconds>
max_retries: <count>
primary_persona_totals_ms: min <n>, median <n>, max <n>
primary_persona_classes: <ideal|acceptable|slow|failed>
decision: <below 10s achieved|below 30s accepted|above 30s demo slow-path>
notes: <proposal validity, timeout/failure count, browser-observed wait>
```

Do not record prompts beyond the approved persona labels, raw Codex transcripts,
tool arguments, final proposal JSON, customer personal details, credential
paths, token values, stack traces, or SDK trace output.

Historical benchmark evidence from the 2026-06-04 real Codex SDK run showed
Tavola MCP handlers were effectively instant: the live
`Vegetarian dinner for 4 around GBP 50` trace spent about 2 ms in MCP tool
handlers and about 50 seconds outside those handlers. Treat new benchmark work
as Codex SDK/model/config and UX evidence unless timing data proves a different
backend bottleneck.

Historical benchmark decision from the 2026-06-04 real Codex SDK run:

```text
model: gpt-5.5
reasoning_effort: low
timeout_seconds: 60
max_retries: 0
primary_persona_totals_ms: min 36493, median 50090, max 60007
primary_persona_classes: slow, slow, slow
decision: above 30s demo slow-path
notes: 2 valid proposals, 1 technical timeout; browser-observed proposal
  readiness was about 65 seconds for one successful live run
```

Live planner prompts send Tavola planner context and a catalog-only MCP tool
through the configured Codex credential path. Tavola validates the proposal after
Codex responds. Get explicit operator approval before running live smoke prompts
or browser flows that submit planner requests.

During proposal runs, Codex should narrow Tavola's real products with
catalog-native filters such as category, dietary needs, tags, and alcohol mode.
Tavola then validates the returned menu before anything can reach the basket. In
demo narration, describe this as Tavola checking the catalog and prices rather
than as generic search.

The planner surface should show the small `powered by Codex` attribution. Basket
and checkout copy should return to Tavola meal-plan language after the proposal
is accepted.

While a session is Planning, the planner surface should show only backend-owned
Planning updates returned by the session API. Suitable narration is Tavola
checking the catalog, composing the menu, validating products, and calculating
prices. Do not describe timer-based progress, elapsed thresholds, SDK internals,
or Codex trace events as customer-visible Planner UX.

## Language Rules

Customer-facing copy should say `product`, `item`, or the product name. Do not
say `SKU` in UI messages, planner notes, or demo narration aimed at the
customer.

Internally, Tavola validates concrete catalog identities before a proposal can
reach the basket. That is an implementation detail: describe it to customers as
checking products against Tavola's catalog, confirming availability, and using
Tavola's server-calculated pricing.

Planner notes should be customer-readable evidence, such as:

- Party size used for quantity planning.
- Package template chosen, such as Antipasto + Primo + Dessert or Aperitivo.
- Dietary constraints applied.
- Products checked against Tavola's catalog.
- Prices and totals calculated by Tavola.
- Assumptions, substitutions, or limits where the catalog cannot guarantee a
  request.

Planner notes should not expose model names, tool counts, retry details,
transcripts, thread IDs, tokens, credentials, stack traces, or raw validation
payloads.

## Demo Personas

Use these prompts as the primary demo script. Exact products and totals may vary
as the catalog or planner hardening changes, but the follow-up behavior, proposal
shape, and trust notes should stay consistent.

### Vegetarian Dinner Host

Prompt:

```text
Vegetarian dinner for 4 around £50
```

Expected follow-up behavior:

- No follow-up should be needed because the prompt includes party size,
  dietary constraint, and approximate budget.
- The planner should treat `around £50` as a soft target, not a strict cap.

Expected proposal shape:

- A vegetarian dinner proposal for 4 people.
- Usually an Antipasto + Primo + Dessert shape.
- Course sections might include vegetarian antipasti, a vegetarian primo such as
  filled pasta, gnocchi, or parmigiana, and a dessert.
- Each line should show product name, unit label, quantity, unit price, line
  total, and a short rationale.
- The proposal total should be calculated by Tavola and shown clearly, with any
  budget variance explained as an assumption or warning.

Expected planner notes:

- Party size of 4 was used.
- Vegetarian was applied as a hard dietary constraint.
- A dinner-style package template was selected.
- Proposed products were checked against Tavola's catalog.
- Pricing and totals were calculated by Tavola.
- The budget was approximate, so the final total may be near but not exactly
  £50.

### Aperitivo Organiser

Prompt:

```text
Aperitivo for 6 with drinks
```

Expected follow-up behavior:

- No follow-up should be needed because the prompt includes party size and the
  occasion implies the Aperitivo package template.
- Drinks should be included because the customer explicitly asked for them.

Expected proposal shape:

- An Aperitivo proposal for 6 people.
- A compact sharing spread, typically olives, vegetables or other antipasti,
  and drinks.
- Drink lines may include soft drinks, wine, or both depending on the planner's
  catalog-backed choice and any explicit constraints.
- The proposal should stay reviewable: product lines can be removed or adjusted
  before choosing Add to basket or Replace basket.

Expected planner notes:

- Party size of 6 was used.
- Aperitivo was selected as the package template.
- Drinks were included because the request asked for them.
- Proposed products were checked against Tavola's catalog.
- Prices and totals were calculated by Tavola.
- Any alcohol assumption should be clear if the proposal includes wine.

### Under-Specified Family Lunch

Prompt:

```text
Help me plan Sunday lunch
```

Expected follow-up behavior:

- The planner should ask a follow-up before producing a menu proposal because
  party size is missing.
- The follow-up should ask how many people the lunch is for.
- After answering with a party size, the planner should continue to a proposal.

Expected proposal shape:

- A lunch proposal shaped by the follow-up answer.
- Usually Antipasto + Primo, Primo + Dessert, or Antipasto + Primo + Dessert
  depending on the planner's assumptions and catalog fit.
- The proposal should remain made only from real Tavola products, with editable
  quantities and removal controls before basket acceptance.

Expected planner notes:

- Party size came from the follow-up answer.
- The selected package template is named in customer-friendly terms.
- The planner states any assumptions, such as no dietary restriction or no
  fixed budget supplied.
- Products were checked against Tavola's catalog.
- Prices and totals were calculated by Tavola.

## Demo Flow Checklist

1. Start with an empty planner composer and visible catalog context.
2. Submit one of the persona prompts.
3. For the family lunch prompt, answer the party-size follow-up.
4. Review the menu proposal title, explanation, course sections, line
   rationales, planner notes, warnings, item count, and total.
5. Adjust a quantity or remove a line to show customer review control.
6. Use Add to basket for the first acceptance path.
7. Use Replace basket in a second run when the basket is non-empty and confirm
   the lightweight replacement warning.
8. Confirm the basket updates without exposing internal product identifiers,
   Codex runtime details, or secret-bearing output.

## Safe Troubleshooting Talk Track

If real Codex is unavailable, say that the Planner is disabled until the
operator configures local access. Do not show credential values, token
diagnostics, stack traces, or raw SDK errors.

If a proposal cannot be built, frame the failure in Tavola terms: the current
catalog cannot honestly satisfy the request, or the planner needs more
information before suggesting quantities.
