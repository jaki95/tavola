import json
from dataclasses import dataclass

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
    mcp_servers: tuple[CodexMcpServerConfig, ...] = ()
    timeout_seconds: float | None = None

    def run(
        self,
        *,
        prompt: str,
        model: str,
        sandbox_mode: str,
        mcp_servers: tuple[CodexMcpServerConfig, ...],
        timeout_seconds: float,
        timing_sink=None,
    ) -> CodexSdkRunResult:
        del timing_sink
        self.prompt = prompt
        self.model = model
        self.sandbox_mode = sandbox_mode
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
        mcp_servers: tuple[CodexMcpServerConfig, ...],
        timeout_seconds: float,
        timing_sink=None,
    ) -> CodexSdkRunResult:
        del model, sandbox_mode, mcp_servers, timeout_seconds, timing_sink
        assert self.prompts is not None
        self.prompts.append(prompt)
        return self.results.pop(0)


def test_codex_adapter_configures_bounded_tools_and_validates_final_json() -> None:
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
            tool_names=(
                "list_package_templates",
                "search_catalog",
                "validate_menu_proposal",
            ),
        )
    )
    agent = CodexMenuPlannerAgent(
        client=client,
        model="codex-test-model",
        timeout_seconds=12,
        mcp_server_command=("python", "-m", "tavola.infrastructure.planner_mcp_server"),
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
    assert client.timeout_seconds == 12
    assert client.mcp_servers == (
        CodexMcpServerConfig(
            name="tavola-planner-tools",
            command=("python", "-m", "tavola.infrastructure.planner_mcp_server"),
        ),
    )
    assert client.prompt is not None
    assert "You MUST use Tavola MCP tools" in client.prompt
    assert "Do not rely on memory, visible page data, or guessed catalog data" in (
        client.prompt
    )
    assert "list_package_templates before choosing a package template" in client.prompt
    assert "search_catalog for candidate products" in client.prompt
    assert "validate_menu_proposal for the completed proposal" in client.prompt
    assert "After list_package_templates, your next action must be search_catalog" in (
        client.prompt
    )
    assert "Do not call get_sku_detail during the first pass" in client.prompt
    assert "Your final response is invalid unless this turn used all three" in (
        client.prompt
    )
    assert "SKU validity, availability, quantities, and totals" in client.prompt
    assert "Final JSON contract" in client.prompt
    assert '"courses"' in client.prompt
    assert '"sku_id"' in client.prompt
    assert "Return JSON only, without Markdown" in client.prompt
    assert "Vegetarian dinner for 2" in client.prompt


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
        mcp_servers=(
            CodexMcpServerConfig(
                name="tavola-planner-tools",
                command=("python", "-m", "tavola.infrastructure.planner_mcp_server"),
            ),
        ),
        timeout_seconds=10,
        timing_sink=events.append,
    )

    assert result.final_output == '{"title": "Dinner"}'
    assert result.tool_names == (
        "list_package_templates",
        "search_catalog",
        "get_sku_detail",
        "validate_menu_proposal",
    )
    fake_codex = created_clients[0]
    assert fake_codex.config.config_overrides == (
        'mcp_servers.tavola-planner-tools.command="python"',
        'mcp_servers.tavola-planner-tools.args=["-m", '
        '"tavola.infrastructure.planner_mcp_server"]',
    )
    assert fake_codex.started_model == "codex-test-model"
    assert fake_codex.started_sandbox == "read-only"
    assert fake_codex.started_approval_mode == "auto_review"
    assert fake_codex.thread.ran_approval_mode == "auto_review"
    assert fake_codex.thread.ran_prompt == "Plan dinner"
    assert fake_codex.was_closed is True
    assert [event.name for event in events] == [
        "sdk_client_create",
        "sdk_thread_start",
        "sdk_turn_run",
        "tool_names_detected",
    ]
    assert events[0].attributes == {"mcp_server_count": 1}
    assert events[3].attributes == {
        "tool_names": (
            "list_package_templates",
            "search_catalog",
            "get_sku_detail",
            "validate_menu_proposal",
        )
    }


def test_codex_adapter_maps_malformed_json_to_typed_failure() -> None:
    result = _run_agent(
        CodexSdkRunResult(
            final_output="not json",
            tool_names=(
                "list_package_templates",
                "search_catalog",
                "validate_menu_proposal",
            ),
        )
    )

    assert result.status == ProposalStatus.FAILED
    assert result.agent_error is not None
    assert result.agent_error.code == PlannerAgentErrorCode.MALFORMED_OUTPUT


def test_codex_adapter_requires_tavola_tool_use_before_final_output() -> None:
    result = _run_agent(
        CodexSdkRunResult(
            final_output=json.dumps({"title": "Skipped tools"}),
            tool_names=("search_catalog",),
        )
    )

    assert result.status == ProposalStatus.FAILED
    assert result.agent_error is not None
    assert result.agent_error.code == PlannerAgentErrorCode.MISSING_TOOL_USE


def test_codex_adapter_maps_tool_failure_to_typed_failure() -> None:
    result = _run_agent(
        CodexSdkRunResult(
            final_output="{}",
            tool_names=(
                "list_package_templates",
                "search_catalog",
                "validate_menu_proposal",
            ),
            tool_error="validate_menu_proposal failed",
        )
    )

    assert result.status == ProposalStatus.FAILED
    assert result.agent_error is not None
    assert result.agent_error.code == PlannerAgentErrorCode.TOOL_FAILURE


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
    return (
        "list_package_templates",
        "search_catalog",
        "validate_menu_proposal",
    )


def valid_raw_proposal() -> dict[str, object]:
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
                        "sku_id": "fresh-tagliatelle-250g",
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

    def run(self, prompt, **kwargs):
        self.ran_prompt = prompt
        self.ran_approval_mode = kwargs["approval_mode"].value
        return FakeTurnResult()


@dataclass(frozen=True)
class FakeThreadItem:
    root: object


@dataclass(frozen=True)
class FakeMcpToolCall:
    tool: str


class FakeTurnResult:
    final_response = '{"title": "Dinner"}'
    items = [
        {"name": "list_package_templates"},
        FakeThreadItem(root=FakeMcpToolCall("search_catalog")),
        {"name": "get_sku_detail"},
        FakeMcpToolCall("validate_menu_proposal"),
    ]
    error = None
