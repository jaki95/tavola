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
    ) -> CodexSdkRunResult:
        self.prompt = prompt
        self.model = model
        self.sandbox_mode = sandbox_mode
        self.mcp_servers = mcp_servers
        self.timeout_seconds = timeout_seconds
        if self.should_timeout:
            raise TimeoutError
        assert self.result is not None
        return self.result


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
                "get_sku_detail",
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
    assert "Use only Tavola MCP tools" in client.prompt
    assert "SKU validity, availability, quantities, and totals" in client.prompt
    assert "Vegetarian dinner for 2" in client.prompt


def test_python_codex_sdk_client_starts_thread_with_mcp_server_config() -> None:
    created_clients: list[FakeCodex] = []

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
    assert fake_codex.thread.ran_prompt == "Plan dinner"


def test_codex_adapter_maps_malformed_json_to_typed_failure() -> None:
    result = _run_agent(
        CodexSdkRunResult(
            final_output="not json",
            tool_names=(
                "list_package_templates",
                "search_catalog",
                "get_sku_detail",
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
                "get_sku_detail",
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


class FakeCodex:
    def __init__(self, config) -> None:
        self.config = config
        self.thread = FakeThread()
        self.started_model = None
        self.started_sandbox = None

    def thread_start(self, **kwargs):
        self.started_model = kwargs["model"]
        self.started_sandbox = kwargs["sandbox"]
        return self.thread


class FakeThread:
    def __init__(self) -> None:
        self.ran_prompt = None

    def run(self, prompt, **kwargs):
        del kwargs
        self.ran_prompt = prompt
        return FakeTurnResult()


class FakeTurnResult:
    final_response = '{"title": "Dinner"}'
    items = [
        {"name": "list_package_templates"},
        {"tool_name": "search_catalog"},
        {"name": "get_sku_detail"},
        {"name": "validate_menu_proposal"},
    ]
    error = None
