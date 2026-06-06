# Plan: Catalog Candidate MCP Tool

**Generated**: 2026-06-04
**Estimated Complexity**: Medium

## Overview

Replace Tavola's generic planner `search_catalog` MCP tool with a constrained
`find_catalog_candidates` tool that exposes catalog-native filters through
JSON Schema enums. The new contract should let Codex choose from known category,
dietary, alcohol, and tag vocabularies without using party size, budget,
occasion, or menu structure as fake semantic search text.

The implementation should keep domain and application boundaries intact:
catalog constants and SKU metadata stay in catalog/domain or catalog application
logic, while the MCP server remains an infrastructure adapter that exposes the
tool schema and calls the application behavior.

Assumptions for this plan:

- `find_catalog_candidates` replaces `search_catalog` in `tools/list` rather
  than being added as an alias.
- `list_package_templates` is removed from the MCP server because menu
  structures will be embedded in the planner prompt as a compact enum and
  domain validation remains the source of truth.
- `get_sku_detail` is removed from the Planner MCP server so Codex has only one
  catalog discovery tool and one validation tool. Candidate summaries should
  carry enough product information for proposal drafting without full product
  detail copy.
- The first version omits generic or product-name query fields; product
  narrowing is done with categories, dietary facets, tags, alcohol, and
  `max_results`.
- The candidate finder does not accept a course filter. Course placement remains
  Planner reasoning after catalog Products return; tags may carry course/use
  hints such as `primo`, `sauce`, or `aperitivo`.
- The candidate finder does not accept budget, party size, occasion, or menu
  structure fields. Budget is handled through Planner composition and
  server-calculated proposal totals, not product-level filtering.
- `dietary_facets` covers `vegetarian`, `vegan`, and `gluten_free`; alcohol is
  handled separately as `include`, `exclude`, or `only`.
- `tag_match` defaults to `any` so tags can broaden product discovery for
  pairings; callers use `all` only when intentionally narrowing.
- Package templates define required courses and can append an optional Drinks
  course without requiring a separate package template per drink combination.
- This slice enforces requested dietary constraints at candidate-filtering time
  and through planner prompt discipline. Deterministic final validation of
  customer-requested dietary constraints would require carrying structured
  requested constraints into `validate_menu_proposal`.
- Tags are derived from the available products in the active catalog repository
  used to create the MCP handlers, so buyable seed catalog changes update the
  schema automatically.
- Category and dietary facet enums are domain-owned stable vocabularies; tag
  enums are repository-derived catalog-data vocabulary.

## Prerequisites

- No new external dependency is required.
- Read and preserve `CONTEXT.md` planner constraints around hard dietary
  requirements, unsupported constraints, budget semantics, and real SKU
  validation.
- Existing backend tests should pass before and after the change.

## Sprint 1: Domain and Candidate Behavior

**Goal**: Make the domain and application layers understand optional Drinks
  courses and catalog-native candidate filtering before changing the MCP surface.

**Demo/Validation**:

- Domain tests accept required package-template courses plus one appended Drinks
  course.
- Application tests return available catalog products filtered by category,
  facets, tags, alcohol mode, and max result bounds.
- Stable category and dietary vocabularies are domain-owned; tag vocabulary is
  derived from available products.

**Implementation note**: Sprint 1 is implemented. Domain/application behavior
now supports catalog-native candidate filtering, repository-derived available
tags, stable category and dietary vocabularies, and optional appended Drinks
courses. Validation passed with the focused Sprint 1 backend tests and the full
backend pytest suite.

### Task 1.1: Add catalog vocabulary helpers

- **Location**: `backend/src/tavola/domain/catalog.py`
- **Description**: Add small helpers or constants for supported category ids and
  supported planner dietary facet ids. Reuse existing `_CATEGORY_DEFINITIONS`
  and `catalog_categories()` rather than duplicating category strings.
- **Dependencies**: None
- **Acceptance Criteria**:
  - Category ids are exposed in display order as
    `antipasti`, `primi`, `desserts`, `drinks`, `pantry`.
  - Dietary facet ids are exposed as `vegetarian`, `vegan`, `gluten_free`.
  - No FastAPI, Pydantic, MCP, or infrastructure imports enter the domain layer.
- **Validation**:
  - Add focused assertions in `backend/tests/test_catalog_domain.py`.

### Task 1.2: Add optional Drinks course semantics

- **Location**:
  - `backend/src/tavola/domain/planner.py`
  - `backend/tests/test_planner_domain.py`
  - `backend/src/tavola/application/planner.py`
  - `backend/tests/test_planner_use_cases.py`
- **Description**: Add `Course.DRINKS` and change package-template validation
  from exact course equality to "required template courses, optionally followed
  by Drinks." Keep drinks as a course, not a separate add-on model.
- **Dependencies**: None
- **Acceptance Criteria**:
  - Existing package templates still define their required courses.
  - A proposal for any package template may append one non-empty Drinks course
    after the required courses.
  - A Drinks course is never returned empty; if requested drinks cannot be
    satisfied from matching products, omit the course and include a warning or
    planner note.
  - A normal "with drinks" request can still return the closest valid food menu
    with a clear warning when no suitable drinks are available.
  - A drinks-primary or firm drinks requirement should not be silently satisfied
    by a food-only proposal.
  - For the Aperitivo template, beverage products belong in an appended Drinks
    course when drinks are requested or clearly implied.
  - Drinks cannot replace required courses, appear before required courses, or
    appear between required courses.
  - More than one Drinks course is rejected.
  - Planner validation still rejects unsupported course names and empty courses.
- **Validation**:
  - Domain tests cover valid required-only courses, valid required-plus-drinks
    courses, rejected missing required courses, rejected misplaced Drinks, and
    rejected duplicate Drinks.
  - Application validation tests prove a Drinks course can validate SKU lines and
    totals like any other course.

### Task 1.3: Derive available-product tag vocabulary

- **Location**:
  - `backend/src/tavola/application/catalog.py`
  - `backend/tests/test_catalog_use_cases.py`
- **Description**: Add an application-level helper or query object that returns
  the sorted unique tag set from available SKUs in `CatalogRepository.list_skus()`.
  Keep it repository-backed so tests and future non-seed catalogs stay in sync.
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - Duplicate tags collapse to one value.
  - Tags are stable and sorted for deterministic schemas.
  - Tags from unavailable SKUs are excluded because unavailable products are not
    part of the customer-facing product experience.
- **Validation**:
  - Unit test with repeated tags and an unavailable SKU whose unique tag is not
    returned.

### Task 1.4: Add an application candidate finder

- **Location**:
  - `backend/src/tavola/application/catalog.py`
  - `backend/tests/test_catalog_use_cases.py`
- **Description**: Add `FindCatalogCandidates` and a small input DTO or typed
  argument shape for:
  `category_ids`, `dietary_facets`, `tags`, `tag_match`, `alcohol`, and
  `max_results`.
- **Dependencies**: Tasks 1.1 and 1.3
- **Acceptance Criteria**:
  - Results always exclude unavailable SKUs.
  - `category_ids` uses OR semantics across allowed buckets.
  - `dietary_facets` uses AND semantics; vegan results must satisfy vegan, and
    gluten-free results must satisfy gluten-free.
  - `tags` uses `any` by default, or `all` when requested.
  - `alcohol="include"` does not filter by alcohol.
  - `alcohol="exclude"` removes SKUs where `contains_alcohol` is true.
  - `alcohol="only"` returns only SKUs where `contains_alcohol` is true.
  - Result order remains catalog display order.
  - `max_results` defaults to `8` and has a stable maximum of `20`. The cap is a
    bounded-payload limit, not a promise to return the whole catalog if the
    catalog later grows.
- **Validation**:
  - Add tests for category OR, dietary AND, tag any, tag all, alcohol exclude,
    alcohol only, result ordering, and max result clamping.

## Sprint 2: Minimal MCP and Codex Contract

**Goal**: Replace the broad Planner MCP tool surface with one candidate finder
  and one validator, then teach the Codex adapter to use that smaller contract.

**Demo/Validation**:

- MCP `tools/list` exposes only `find_catalog_candidates` and
  `validate_menu_proposal`.
- The `find_catalog_candidates` schema includes enums for category ids, dietary
  facets, available-product tags, tag match, and alcohol mode.
- Adapter guardrails require candidate finding and proposal validation only for
  proposal outputs; follow-up-only outputs can skip tool calls.

**Implementation note**: Sprint 2 is implemented. The Planner MCP server now
lists only `find_catalog_candidates` and `validate_menu_proposal`, builds
candidate schemas from the active catalog repository, validates invalid MCP
arguments with JSON-RPC `-32602`, and the Codex adapter prompt/required-tool
guardrails use the smaller candidate-plus-validation contract.

### Task 2.1: Generate tool descriptions from handlers

- **Location**:
  - `backend/src/tavola/infrastructure/planner_mcp_server.py`
  - `backend/tests/test_planner_mcp_tools.py`
- **Description**: Change `PlannerToolHandlers` so it carries both handlers and
  tool descriptions generated from the provided catalog repository. Update
  `handle_mcp_message(..., method="tools/list")` to return those descriptions
  instead of calling a repository-free `_tool_descriptions()`.
- **Dependencies**: Sprint 1
- **Acceptance Criteria**:
  - Tool schemas can include repository-derived tag enums.
  - Existing JSON-RPC initialize and tool call behavior remains unchanged.
  - Empty catalogs do not produce an invalid or surprising schema. If the tag
    enum would be empty, omit the enum for `tags.items` or expose an empty
    allowed list only with a test that documents the behavior.
- **Validation**:
  - Update `test_mcp_protocol_lists_and_calls_planner_tools`.
  - Add a test that a repository with tags `("pasta", "fresh")` lists both in
    the `tags.items.enum` schema.

### Task 2.2: Expose only `find_catalog_candidates` and validation

- **Location**:
  - `backend/src/tavola/infrastructure/planner_mcp_server.py`
  - `backend/tests/test_planner_mcp_tools.py`
- **Description**: Replace `search_catalog` with `find_catalog_candidates`, map
  MCP arguments into `FindCatalogCandidates`, and remove
  `list_package_templates` and `get_sku_detail` from handler registration, tool
  descriptions, tests, and recommended next actions.
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - `available_tool_names()` returns only `find_catalog_candidates` and
    `validate_menu_proposal`.
  - The input schema includes:
    - `category_ids`: array of category id enum strings.
    - `dietary_facets`: array enum of `vegetarian`, `vegan`, `gluten_free`.
    - `tags`: array enum derived from available products in the repository.
    - `tag_match`: enum `any`, `all`.
    - `alcohol`: enum `include`, `exclude`, `only`.
    - `max_results`: integer min `1`, max `20`.
  - The tool does not accept `query`, `name_query`, `product_name_query`,
    `course`, budget, price-cap, party-size, occasion, or menu-structure fields.
  - The response includes `result_count`, `returned_count`,
    `recommended_next_action`, and `products`.
  - Empty results recommend broadening catalog-native filters, not changing
    "request terms".
  - Candidate summaries include raw tags and `short_description`, but not
    `detail_description`.
  - Customer-facing catalog APIs continue to hide raw tags.
- **Validation**:
  - Rewrite current `search_catalog`, `list_package_templates`, and
    `get_sku_detail` MCP tests around the new two-tool surface.
  - Add MCP-level tests that schema enums include seed categories, seed tags,
    dietary facets, tag match values, and alcohol values.

### Task 2.3: Validate MCP arguments loudly

- **Location**:
  - `backend/src/tavola/infrastructure/planner_mcp_server.py`
  - `backend/tests/test_planner_mcp_tools.py`
- **Description**: Add narrow argument parsing for arrays and enums. Because MCP
  schemas guide clients but do not guarantee valid inputs, return a JSON-RPC
  `-32602` error for invalid enum strings when called through `tools/call`.
- **Dependencies**: Task 2.2
- **Acceptance Criteria**:
  - Unknown category, dietary facet, tag, `tag_match`, or alcohol value is
    reported as an invalid tool call.
  - Non-array values for array fields are invalid rather than silently ignored.
  - Missing optional fields still use defaults.
- **Validation**:
  - Add JSON-RPC tests for at least one invalid enum and one invalid array type.
  - Direct handler tests may assert `ValueError` if direct calls are used.

### Task 2.4: Update required tool names

- **Location**:
  - `backend/src/tavola/infrastructure/codex_planner.py`
  - `backend/tests/test_codex_planner_adapter.py`
- **Description**: Change `_REQUIRED_TOOL_NAMES` to require only
  `find_catalog_candidates` and `validate_menu_proposal` for proposal outputs.
  Parse final JSON before enforcing required tool use so follow-up-only outputs
  can be accepted without catalog calls.
- **Dependencies**: Task 2.2
- **Acceptance Criteria**:
  - A run that uses `find_catalog_candidates` and `validate_menu_proposal`
    passes tool-use validation.
  - A run that uses only `find_catalog_candidates` fails as missing validation.
  - A run that returns only `{"follow_up_question": "..."}` passes without any
    MCP tool names.
  - Tests no longer expect `search_catalog` in required tool sets.
- **Validation**:
  - Update `required_tool_names()` helper in adapter tests.
  - Update missing-tool and tool-failure tests.

### Task 2.5: Rewrite the planner prompt

- **Location**:
  - `backend/src/tavola/infrastructure/codex_planner.py`
  - `backend/tests/test_codex_planner_adapter.py`
- **Description**: Replace the generic search instructions with the constrained
  flow:
  1. Read the customer request.
  2. Pick one menu structure from:
     `antipasto-primo-dessert`, `antipasto-primo`, `primo-dessert`,
     `primo-only`, `aperitivo`.
  3. Call `find_catalog_candidates` using only category ids, dietary facets,
     tags, tag match, alcohol, and max results.
  4. Append a Drinks course only when drinks are requested or clearly implied.
  5. Choose products, quantities, course placement, and rationales.
  6. Call `validate_menu_proposal`.
  7. Return the final JSON object.
- **Dependencies**: Tasks 1.2 and 2.2
- **Acceptance Criteria**:
  - Prompt says party size, budget, occasion, and menu structure must not be
    passed as search text.
  - Prompt preserves hard constraints for vegetarian, vegan, gluten-free, and
    no-alcohol requests.
  - Prompt states that drinks are optional courses, not separate package
    templates.
  - Prompt states that generic drink requests do not automatically exclude
    alcohol, but no-alcohol signals must use the alcohol exclusion filter.
  - Prompt states that unavailable requested drinks should produce a warning
    unless drinks are the main or firm requirement.
  - Prompt preserves budget honesty and unsupported constraint language.
  - Prompt remains compact enough for current latency goals; update the existing
    prompt length assertion only if the new language justifies it.
- **Validation**:
  - Adapter prompt test asserts `find_catalog_candidates`, the menu structure
    ids, `tag_match`, `alcohol`, and the "do not pass party size/budget/occasion"
    instruction.
  - Adapter prompt test asserts `search_catalog` is absent.
  - Adapter prompt test asserts `list_package_templates` and `get_sku_detail`
    are absent.

### Task 2.6: Update SDK tool extraction expectations

- **Location**: `backend/tests/test_codex_planner_adapter.py`
- **Description**: Replace fake SDK tool-call fixtures and timing assertions
  that currently mention `search_catalog`.
- **Dependencies**: Task 2.4
- **Acceptance Criteria**:
  - Fake SDK item extraction still recognizes MCP tool names.
  - Sanitized timing still records tool names without transcripts.
  - Tests describe the new required flow.
- **Validation**:
  - Run `uv run pytest backend/tests/test_codex_planner_adapter.py` from
    `backend/`.

## Sprint 3: Documentation and Regression Checks

**Goal**: Keep demonstrator docs and smoke expectations aligned with the new
  bounded planner tool flow.

**Demo/Validation**:

- Backend tests pass.
- Demo docs no longer imply generic catalog search.
- Optional live smoke can prove the real Codex flow if credentials are available
  and the operator approves it.

**Implementation note**: Sprint 3 is implemented. Active demo and backend smoke
docs now describe bounded catalog candidate filtering in Tavola language, active
runbook references to the old generic catalog search flow are marked historical
or superseded, focused backend regressions passed, and the full backend pytest
suite passed. The optional live Codex smoke was not run because it requires
operator approval and live credentials.

### Task 3.1: Update planner docs and historical plan references

- **Location**:
  - `docs/demo-codex-planner.md`
  - `backend/README.md`
  - `docs/plans/in_progress/real-codex-flow-e2e-testing-plan.md` if it remains active
- **Description**: Update active docs that mention required `search_catalog`
  calls or old prompt flow. Avoid rewriting completed historical plans unless
  they are used as live runbooks.
- **Dependencies**: Sprint 2
- **Acceptance Criteria**:
  - Demo docs explain candidate filtering in Tavola language.
  - No active runbook says Codex must call `search_catalog`.
  - No customer-facing docs expose low-level MCP schema internals unless useful
    for a developer smoke test.
- **Validation**:
  - `rg -n "search_catalog|find_catalog_candidates" docs backend/README.md`
    shows only intended references.

### Task 3.2: Run backend regression suite

- **Location**: `backend/`
- **Description**: Run the focused MCP and adapter tests first, then the full
  backend suite.
- **Dependencies**: Sprints 1 and 2, plus Task 3.1
- **Acceptance Criteria**:
  - Focused tests pass:
    - `uv run pytest tests/test_planner_mcp_tools.py`
    - `uv run pytest tests/test_codex_planner_adapter.py`
    - `uv run pytest tests/test_catalog_use_cases.py tests/test_catalog_domain.py`
  - Full backend tests pass with `uv run pytest`.
- **Validation**:
  - Report any failures with exact test names and next fix.

### Task 3.3: Optional live planner smoke

- **Location**:
  - `backend/README.md`
  - `backend/src/tavola/infrastructure/codex_planner_smoke.py`
- **Description**: If credentials are available and operator approval is given,
  run the existing sanitized Codex planner smoke against prompts from
  `docs/demo-codex-planner.md`.
- **Dependencies**: Task 3.2
- **Acceptance Criteria**:
  - Smoke result uses `find_catalog_candidates`.
  - Proposal JSON validates through Tavola.
  - Sanitized timing output does not expose raw transcripts, credentials, or
    stack traces.
- **Validation**:
  - Record only status, model string, reasoning effort, retry count, timeout,
    tool names, and sanitized timings.

## Testing Strategy

- Domain tests prove vocabulary constants stay stable and framework-free.
- Application tests prove filtering semantics independent of MCP transport.
- MCP tests prove JSON-RPC schema, handler registration, argument validation,
  response shape, and error behavior.
- Adapter tests prove prompt contract and required tool-use guardrails.
- Tests should include the limitation that final proposal validation cannot
  independently reject a dietary mismatch unless requested constraints are
  passed into validation.
- Full backend `uv run pytest` catches cross-layer regressions.
- No frontend browser approval check is required unless implementation changes
  frontend planner UI or browser-visible behavior.

## Potential Risks & Gotchas

- The current `tools/list` function has no repository context, so dynamic tag
  enums require a small `PlannerToolHandlers` shape change before the schema can
  stay in sync.
- JSON Schema enums guide Codex but do not enforce inputs by themselves. The MCP
  handler should still validate invalid enum strings so unexpected callers fail
  clearly.
- Keeping `search_catalog` visible as an alias would undermine the goal of
  stopping fake semantic search. If backward compatibility is required later,
  expose it only outside the Codex planner server or behind an explicit
  compatibility path.
- `gluten-free` exists as a catalog tag, while the dietary facet id should be
  `gluten_free`. Tests should prove tag enum values and dietary facet enum
  values are independent and not normalized into each other.
- Alcohol appears both as a facet payload field (`contains_alcohol`) and as the
  requested `alcohol` filter mode. The tool input should avoid also accepting
  `contains_alcohol` in `dietary_facets` unless a future compatibility decision
  requires it.
- Candidate filtering alone cannot prove that the final proposal honored a
  dietary request if Codex later chooses a SKU from another source. End-to-end
  deterministic dietary enforcement needs structured requested constraints in
  the validation input.
- Removing `list_package_templates` entirely reduces one MCP call and one
  possible drift path, but the prompt must preserve the exact supported menu
  structures so Codex does not invent package template ids.

## Rollback Plan

- Revert the `find_catalog_candidates` handler registration and restore
  `search_catalog` in `PlannerToolHandlers`.
- Restore `_REQUIRED_TOOL_NAMES` and prompt references in
  `backend/src/tavola/infrastructure/codex_planner.py`.
- Re-register `list_package_templates` in
  `backend/src/tavola/infrastructure/planner_mcp_server.py` if the rollback
  needs the old prompt-discovery flow.
- Revert updated tests and docs that assert the new tool name.
- Keep application-level filtering helpers only if they are unused by no active
  path and have passing tests; otherwise remove them with the rollback.

## Resolved Decisions

- `Catalog candidate` remains implementation language only; domain and customer
  language should refer to Products or items.
- The Planner MCP server should expose only `find_catalog_candidates` and
  `validate_menu_proposal`.
- `search_catalog`, `list_package_templates`, and `get_sku_detail` should be
  removed from the Planner MCP surface.
- Candidate summaries should include raw tags and `short_description`, but not
  `detail_description`.
- `find_catalog_candidates` should not accept generic query, product-name query,
  course, budget, party size, occasion, or menu-structure fields.
- Category and dietary facet enums are domain-owned; tag enums are derived from
  available products in the active catalog repository.
- `tag_match` defaults to `any`; `all` is caller-selected only for intentional
  narrowing.
- `max_results` defaults to `8` and has a stable maximum of `20`.
- Package templates define required courses; Drinks may be appended as one
  non-empty optional course after required courses.
- For Aperitivo, food and snack items stay in Aperitivo while beverages belong
  in an appended Drinks course when requested or clearly implied.
- Normal "with drinks" requests may return the closest valid food menu with a
  warning if suitable drinks are unavailable; drinks-primary or firm drinks
  requirements should not silently become food-only proposals.
- Generic drink requests use `alcohol="include"` unless there is a no-alcohol
  signal; no-alcohol remains a hard constraint.
- Follow-up-only outputs do not require MCP tool calls; proposal outputs require
  `find_catalog_candidates` and `validate_menu_proposal`.
- Invalid enum values or field shapes should fail loudly with JSON-RPC `-32602`.
- No ADR is needed for this change; `CONTEXT.md` and this plan carry the
  relevant product and implementation decisions.
