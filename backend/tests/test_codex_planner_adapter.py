import json
from dataclasses import dataclass
from pathlib import Path

from tavola.application.planner import PlanMenuFromRequest, PlannerAgentErrorCode
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.domain.planner import ProposalStatus
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.codex_planner import (
    CodexMcpServerConfig,
    CodexMenuPlannerAgent,
    CodexSdkRunResult,
    PlannerTimingEvent,
    PythonCodexSdkClient,
)


def make_sku(
    sku_id: str = "fresh-tagliatelle-250g",
    *,
    amount_minor: int = 425,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name="Fresh Tagliatelle",
        category=CatalogCategory("primi", "Primi", 2),
        unit_label="250g",
        price=Money(amount_minor=amount_minor, currency="GBP"),
        short_description="Egg pasta cut fresh each morning.",
        detail_description="Silky ribbons of egg pasta for a quick supper.",
        tags=("pasta", "fresh"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id=sku_id,
        display_order=1,
        is_available=True,
    )


@dataclass
class CapturingCodexClient:
    result: CodexSdkRunResult | None = None
    should_timeout: bool = False
    prompt: str | None = None
    model: str | None = None
    sandbox_mode: str | None = None
    reasoning_effort: str | None = None
    mcp_servers: tuple[CodexMcpServerConfig, ...] = ()
    timeout_seconds: float | None = None

    def run(
        self,
        *,
        prompt: str,
        model: str,
        sandbox_mode: str,
        reasoning_effort: str | None,
        mcp_servers: tuple[CodexMcpServerConfig, ...],
        timeout_seconds: float,
        timing_sink=None,
    ) -> CodexSdkRunResult:
        del timing_sink
        self.prompt = prompt
        self.model = model
        self.sandbox_mode = sandbox_mode
        self.reasoning_effort = reasoning_effort
        self.mcp_servers = mcp_servers
        self.timeout_seconds = timeout_seconds
        if self.should_timeout:
            raise TimeoutError
        assert self.result is not None
        return self.result


@dataclass
class SequencedCodexClient:
    results: list[CodexSdkRunResult]
    prompts: list[str] | None = None

    def __post_init__(self) -> None:
        self.prompts = []

    def run(
        self,
        *,
        prompt: str,
        model: str,
        sandbox_mode: str,
        reasoning_effort: str | None,
        mcp_servers: tuple[CodexMcpServerConfig, ...],
        timeout_seconds: float,
        timing_sink=None,
    ) -> CodexSdkRunResult:
        del model, sandbox_mode, reasoning_effort, mcp_servers, timeout_seconds
        del timing_sink
        assert self.prompts is not None
        self.prompts.append(prompt)
        return self.results.pop(0)


def test_codex_adapter_configures_catalog_tool_and_tavola_validates_final_json() -> (
    None
):
    client = CapturingCodexClient(
        result=CodexSdkRunResult(
            final_output=json.dumps(
                {
                    "title": "Weeknight Pasta",
                    "explanation": "A compact pasta proposal.",
                    "planner_notes": ["Catalog identities checked."],
                    "party_size": 2,
                    "package_template_id": "primo-only",
                    "courses": [
                        {
                            "course": "primo",
                            "lines": [
                                {
                                    "sku_id": "fresh-tagliatelle-250g",
                                    "quantity": 2,
                                    "rationale": "A flexible pasta course.",
                                }
                            ],
                        }
                    ],
                }
            ),
            tool_names=required_tool_names(),
        )
    )
    agent = CodexMenuPlannerAgent(
        client=client,
        model="codex-test-model",
        reasoning_effort="low",
        timeout_seconds=12,
    )
    planner = PlanMenuFromRequest(
        agent=agent,
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    result = planner(customer_request="Vegetarian dinner for 2")

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert result.menu_proposal is not None
    assert result.menu_proposal.total.amount_minor == 850
    assert client.model == "codex-test-model"
    assert client.sandbox_mode == "read-only"
    assert client.reasoning_effort == "low"
    assert client.timeout_seconds == 12
    assert client.mcp_servers == (
        CodexMcpServerConfig(
            name="tavola-planner-tools",
            command=(
                "python",
                "-m",
                "tavola.infrastructure.planner_catalog_mcp_server",
            ),
        ),
    )
    assert client.prompt is not None
    assert len(client.prompt) < 3200
    assert "Proposal flow" in client.prompt
    assert "antipasto-primo-dessert" in client.prompt
    assert "antipasto-primo" in client.prompt
    assert "primo-dessert" in client.prompt
    assert "primo-only" in client.prompt
    assert "aperitivo" in client.prompt
    assert "do not mention templates" in client.prompt
    assert "find_catalog_candidates" in client.prompt
    assert "tag_match" in client.prompt
    assert "alcohol" in client.prompt
    assert "validate_menu_proposal" not in client.prompt
    normalized_prompt = " ".join(client.prompt.split())
    assert (
        "Tavola validates the returned proposal after your response"
        in normalized_prompt
    )
    assert "Do not pass party size, budget, occasion" in client.prompt
    assert "chosen course set" in client.prompt
    assert "Drinks course" in client.prompt
    assert "ask one follow-up question" in client.prompt
    assert "If party size is already present, do not ask a follow-up" in client.prompt
    assert "'Vegetarian dinner for 4 around GBP 50' has party_size 4" in client.prompt
    assert "must call find_catalog_candidates" in normalized_prompt
    assert "party size" in client.prompt
    assert "Use exact course values only" in client.prompt
    assert "antipasto, primo, dessert" in client.prompt
    assert "Do not use category labels like Antipasti" in normalized_prompt
    assert "Do not invent products or prices" in client.prompt
    assert "vegetarian, vegan, gluten-free, and no-alcohol" in client.prompt
    assert "whole-menu vegetarian request" in client.prompt
    assert "2 vegetarian guests" in client.prompt
    assert "do not force every line to be vegetarian" in client.prompt
    assert "Final JSON contract" in client.prompt
    assert '"follow_up_question"' in client.prompt
    assert '"courses"' in client.prompt
    assert '"sku_id"' in client.prompt
    assert "Return one JSON object only" in client.prompt
    assert "Vegetarian dinner for 2" in client.prompt
    assert "search_catalog" not in client.prompt
    assert "list_package_templates" not in client.prompt
    assert "get_sku_detail" not in client.prompt


def test_codex_adapter_loads_prompt_template_from_markdown_file() -> None:
    client = CapturingCodexClient(
        result=CodexSdkRunResult(
            final_output=json.dumps(valid_raw_proposal()),
            tool_names=required_tool_names(),
        )
    )
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(client=client, model="codex-test-model"),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )
    prompt_file = (
        Path(__file__).parents[1]
        / "src"
        / "tavola"
        / "infrastructure"
        / "codex_planner"
        / "codex_planner_prompt.md"
    )

    result = planner(customer_request="Vegetarian dinner for 2")

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert client.prompt is not None
    assert prompt_file.read_text(encoding="utf-8").strip() in client.prompt
    assert "Customer request:\nVegetarian dinner for 2" in client.prompt


def test_codex_adapter_repairs_malformed_json_once() -> None:
    client = SequencedCodexClient(
        results=[
            CodexSdkRunResult(
                final_output="not json",
                tool_names=required_tool_names(),
            ),
            CodexSdkRunResult(
                final_output=json.dumps(valid_raw_proposal()),
                tool_names=required_tool_names(),
            ),
        ]
    )
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=client,
            model="codex-test-model",
            max_retries=1,
        ),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    result = planner(customer_request="Vegetarian dinner for 2")

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert result.menu_proposal is not None
    assert result.menu_proposal.total.amount_minor == 850
    assert client.prompts is not None
    assert len(client.prompts) == 2
    assert "Repair your previous planner output" in client.prompts[1]
    assert "not json" not in client.prompts[1]


def test_codex_adapter_does_not_repair_malformed_json_by_default() -> None:
    client = SequencedCodexClient(
        results=[
            CodexSdkRunResult(
                final_output="not json",
                tool_names=required_tool_names(),
            ),
        ]
    )
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=client,
            model="codex-test-model",
        ),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )

    result = planner(customer_request="Vegetarian dinner for 2")

    assert result.status == ProposalStatus.FAILED
    assert result.agent_error is not None
    assert result.agent_error.code == PlannerAgentErrorCode.MALFORMED_OUTPUT
    assert client.prompts is not None
    assert len(client.prompts) == 1


def test_codex_adapter_maps_follow_up_without_tools_to_needs_input() -> None:
    result = _run_agent(
        CodexSdkRunResult(
            final_output=json.dumps(
                {"follow_up_question": "How many people should Tavola plan for?"}
            ),
            tool_names=(),
        )
    )

    assert result.status == ProposalStatus.NEEDS_INPUT
    assert result.follow_up_question is not None
    assert result.follow_up_question.message == (
        "How many people should Tavola plan for?"
    )


def test_codex_adapter_emits_sanitized_timing_events_for_success() -> None:
    events: list[PlannerTimingEvent] = []
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=CapturingCodexClient(
                result=CodexSdkRunResult(
                    final_output=json.dumps(valid_raw_proposal()),
                    tool_names=required_tool_names(),
                )
            ),
            model="codex-test-model",
            timing_sink=events.append,
        ),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    result = planner(customer_request="Vegetarian dinner for 2")

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert [event.name for event in events] == [
        "parse_result",
        "total_elapsed",
    ]
    assert events[0].attributes == {"result": "proposal_ready"}
    assert events[1].attributes == {
        "status": "proposal_ready",
        "repair_attempts": 0,
    }


def test_codex_adapter_emits_repair_attempt_timing_without_raw_output() -> None:
    events: list[PlannerTimingEvent] = []
    client = SequencedCodexClient(
        results=[
            CodexSdkRunResult(
                final_output="not json",
                tool_names=required_tool_names(),
            ),
            CodexSdkRunResult(
                final_output=json.dumps(valid_raw_proposal()),
                tool_names=required_tool_names(),
            ),
        ]
    )
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=client,
            model="codex-test-model",
            max_retries=1,
            timing_sink=events.append,
        ),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    result = planner(customer_request="Vegetarian dinner for 2")

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert [(event.name, event.attributes) for event in events] == [
        ("parse_result", {"result": "malformed_output"}),
        ("repair_attempt", {"repair_attempts": 1}),
        ("parse_result", {"result": "proposal_ready"}),
        ("total_elapsed", {"status": "proposal_ready", "repair_attempts": 1}),
    ]
    assert all("not json" not in str(event.attributes) for event in events)


def test_codex_adapter_repairs_output_contract_failure_once() -> None:
    client = SequencedCodexClient(
        results=[
            CodexSdkRunResult(
                final_output=json.dumps({"title": "Missing proposal fields"}),
                tool_names=required_tool_names(),
            ),
            CodexSdkRunResult(
                final_output=json.dumps(valid_raw_proposal()),
                tool_names=required_tool_names(),
            ),
        ]
    )
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=client,
            model="codex-test-model",
            max_retries=1,
        ),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    result = planner(customer_request="Vegetarian dinner for 2")

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert client.prompts is not None
    assert len(client.prompts) == 2
    assert "Final output did not match Tavola's JSON contract" in client.prompts[1]


def test_codex_adapter_repairs_after_tavola_validation_failure() -> None:
    client = SequencedCodexClient(
        results=[
            CodexSdkRunResult(
                final_output=json.dumps(valid_raw_proposal(sku_id="missing-product")),
                tool_names=required_tool_names(),
            ),
            CodexSdkRunResult(
                final_output=json.dumps(valid_raw_proposal()),
                tool_names=required_tool_names(),
            ),
        ]
    )
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=client,
            model="codex-test-model",
        ),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    result = planner(customer_request="Vegetarian dinner for 2")

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert result.menu_proposal is not None
    assert result.menu_proposal.total.amount_minor == 850
    assert client.prompts is not None
    assert len(client.prompts) == 2
    repair_prompt = client.prompts[1]
    assert "Repair your previous menu proposal" in repair_prompt
    assert "Tavola validation errors" in repair_prompt
    assert "unknown_sku" in repair_prompt
    assert "missing-product" in repair_prompt
    assert "Return one corrected JSON object" in repair_prompt


def test_codex_adapter_stops_after_configured_repair_attempts() -> None:
    client = SequencedCodexClient(
        results=[
            CodexSdkRunResult(
                final_output="not json",
                tool_names=required_tool_names(),
            ),
            CodexSdkRunResult(
                final_output="still not json",
                tool_names=required_tool_names(),
            ),
        ]
    )
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=client,
            model="codex-test-model",
            max_retries=1,
        ),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )

    result = planner(customer_request="Dinner for two")

    assert result.status == ProposalStatus.FAILED
    assert result.agent_error is not None
    assert result.agent_error.code == PlannerAgentErrorCode.MALFORMED_OUTPUT
    assert client.prompts is not None
    assert len(client.prompts) == 2


def test_python_codex_sdk_client_starts_thread_with_mcp_server_config() -> None:
    created_clients: list[FakeCodex] = []
    events: list[PlannerTimingEvent] = []

    def codex_factory(config):
        client = FakeCodex(config)
        created_clients.append(client)
        return client

    client = PythonCodexSdkClient(codex_factory=codex_factory)

    result = client.run(
        prompt="Plan dinner",
        model="codex-test-model",
        sandbox_mode="read-only",
        reasoning_effort="low",
        mcp_servers=(
            CodexMcpServerConfig(
                name="tavola-planner-tools",
                command=(
                    "python",
                    "-m",
                    "tavola.infrastructure.planner_catalog_mcp_server",
                ),
            ),
        ),
        timeout_seconds=10,
        timing_sink=events.append,
    )

    assert result.final_output == '{"title": "Dinner"}'
    assert result.tool_names == ("find_catalog_candidates",)
    fake_codex = created_clients[0]
    assert fake_codex.config.config_overrides == (
        'mcp_servers.tavola-planner-tools.command="python"',
        'mcp_servers.tavola-planner-tools.args=["-m", '
        '"tavola.infrastructure.planner_catalog_mcp_server"]',
    )
    assert fake_codex.started_model == "codex-test-model"
    assert fake_codex.started_sandbox == "read-only"
    assert fake_codex.started_approval_mode == "auto_review"
    assert fake_codex.thread.ran_approval_mode == "auto_review"
    assert fake_codex.thread.ran_effort == "low"
    assert fake_codex.thread.ran_prompt == "Plan dinner"
    assert fake_codex.was_closed is True
    assert [event.name for event in events] == [
        "sdk_client_create",
        "sdk_thread_start",
        "sdk_turn_run",
        "tool_names_detected",
    ]
    assert events[0].attributes == {"mcp_server_count": 1}
    assert events[3].attributes == {"tool_names": ("find_catalog_candidates",)}


def test_codex_adapter_maps_malformed_json_to_typed_failure() -> None:
    result = _run_agent(
        CodexSdkRunResult(
            final_output="not json",
            tool_names=required_tool_names(),
        )
    )

    assert result.status == ProposalStatus.FAILED
    assert result.agent_error is not None
    assert result.agent_error.code == PlannerAgentErrorCode.MALFORMED_OUTPUT


def test_codex_adapter_accepts_catalog_only_tool_use_before_final_output() -> None:
    result = _run_agent(
        CodexSdkRunResult(
            final_output=json.dumps(valid_raw_proposal()),
            tool_names=("find_catalog_candidates",),
        )
    )

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert result.agent_error is None
    assert result.menu_proposal is not None


def test_codex_adapter_allows_server_validation_when_tool_use_is_not_reported() -> None:
    result = _run_agent(
        CodexSdkRunResult(
            final_output=json.dumps(valid_raw_proposal()),
            tool_names=(),
        )
    )

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert result.agent_error is None
    assert result.menu_proposal is not None


def test_codex_adapter_maps_tool_failure_to_typed_failure() -> None:
    result = _run_agent(
        CodexSdkRunResult(
            final_output="{}",
            tool_names=required_tool_names(),
            tool_error="find_catalog_candidates failed",
        )
    )

    assert result.status == ProposalStatus.FAILED
    assert result.agent_error is not None
    assert result.agent_error.code == PlannerAgentErrorCode.TOOL_FAILURE
    assert result.agent_error.message == (
        "Planner checks failed before Tavola could validate a proposal."
    )


def test_codex_adapter_maps_timeout_to_typed_failure() -> None:
    client = CapturingCodexClient(should_timeout=True)
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(client=client, model="codex-test-model"),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )

    result = planner(customer_request="Dinner for two")

    assert result.status == ProposalStatus.FAILED
    assert result.agent_error is not None
    assert result.agent_error.code == PlannerAgentErrorCode.TIMEOUT


def _run_agent(run_result: CodexSdkRunResult):
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=CapturingCodexClient(result=run_result),
            model="codex-test-model",
        ),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )
    return planner(customer_request="Dinner for two")


def required_tool_names() -> tuple[str, ...]:
    return ("find_catalog_candidates",)


def valid_raw_proposal(sku_id: str = "fresh-tagliatelle-250g") -> dict[str, object]:
    return {
        "title": "Weeknight Pasta",
        "explanation": "A compact pasta proposal.",
        "planner_notes": ["Catalog identities checked."],
        "party_size": 2,
        "package_template_id": "primo-only",
        "courses": [
            {
                "course": "primo",
                "lines": [
                    {
                        "sku_id": sku_id,
                        "quantity": 2,
                        "rationale": "A flexible pasta course.",
                    }
                ],
            }
        ],
    }


class FakeCodex:
    def __init__(self, config) -> None:
        self.config = config
        self.thread = FakeThread()
        self.started_model = None
        self.started_sandbox = None
        self.started_approval_mode = None
        self.was_closed = False

    def thread_start(self, **kwargs):
        self.started_model = kwargs["model"]
        self.started_sandbox = kwargs["sandbox"]
        self.started_approval_mode = kwargs["approval_mode"].value
        return self.thread

    def close(self) -> None:
        self.was_closed = True


class FakeThread:
    def __init__(self) -> None:
        self.ran_prompt = None
        self.ran_approval_mode = None
        self.ran_effort = None

    def run(self, prompt, **kwargs):
        self.ran_prompt = prompt
        self.ran_approval_mode = kwargs["approval_mode"].value
        self.ran_effort = kwargs["effort"].value if kwargs["effort"] else None
        return FakeTurnResult()


@dataclass(frozen=True)
class FakeThreadItem:
    root: object


@dataclass(frozen=True)
class FakeMcpToolCall:
    tool: str


class FakeTurnResult:
    final_response = '{"title": "Dinner"}'
    items = [FakeThreadItem(root=FakeMcpToolCall("find_catalog_candidates"))]
    error = None
