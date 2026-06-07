from collections.abc import Iterator
from dataclasses import dataclass
from threading import Event
from time import monotonic, sleep

import pytest
from fastapi.testclient import TestClient

from tavola.api.dependencies import (
    get_basket_repository,
    get_catalog_repository,
    get_menu_planner_agent,
    get_planner_background_runner,
    get_planner_runtime_status,
    get_planner_session_repository,
)
from tavola.api.main import app
from tavola.application.planner import MenuPlannerAgentResponse, ValidateMenuProposal
from tavola.config.settings import PlannerRuntimeStatus
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.domain.planner import (
    Course,
    CourseProposal,
    FollowUpQuestion,
    MenuProposal,
    PlannerSessionId,
    ProposalLine,
    ProposalStatus,
)
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.codex_planner import FakeMenuPlannerAgent
from tavola.infrastructure.planner_background import InProcessPlannerBackgroundRunner
from tavola.infrastructure.planner_repository import InMemoryPlannerSessionRepository


@dataclass(frozen=True, slots=True)
class PlannerApiHarness:
    client: TestClient
    basket_repository: InMemoryBasketRepository
    planner_repository: InMemoryPlannerSessionRepository
    background_runner: InProcessPlannerBackgroundRunner

    def use_agent(self, agent: FakeMenuPlannerAgent) -> None:
        app.dependency_overrides[get_menu_planner_agent] = lambda: agent

    def save_ready_session(
        self,
        *,
        customer_request: str = "Dinner for two",
        quantity: int = 2,
    ) -> None:
        validation_result = ValidateMenuProposal(
            make_complete_pasta_catalog(pasta_amount_minor=425)
        )(
            MenuProposal(
                title="Weeknight Pasta",
                explanation="A compact pasta proposal.",
                planner_notes=("Catalog identities checked.",),
                party_size=2,
                package_template_id="primo-only",
                courses=(
                    CourseProposal(
                        course=Course.PRIMO,
                        lines=(
                            ProposalLine(
                                sku_id="fresh-tagliatelle-250g",
                                quantity=quantity,
                                rationale="A flexible pasta course.",
                            ),
                            ProposalLine(
                                sku_id="sugo-pomodoro-500g",
                                quantity=1,
                                rationale="Tomato sauce completes the pasta course.",
                            ),
                        ),
                    ),
                ),
            )
        )
        assert validation_result.menu_proposal is not None
        self.planner_repository.save_session(
            self.planner_repository.create_session(
                customer_request=customer_request,
                status=ProposalStatus.PROPOSAL_READY,
                menu_proposal=validation_result.menu_proposal,
            )
        )


def make_sku(
    sku_id: str = "fresh-tagliatelle-250g",
    *,
    name: str = "Fresh Tagliatelle",
    category: CatalogCategory | None = None,
    amount_minor: int = 425,
    unit_label: str = "250g",
    is_available: bool = True,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name=name,
        category=category or CatalogCategory("primi", "Primi", 2),
        unit_label=unit_label,
        price=Money(amount_minor=amount_minor, currency="GBP"),
        short_description="Egg pasta cut fresh each morning.",
        detail_description="Silky ribbons of egg pasta for a quick supper.",
        tags=("pasta", "fresh"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id=sku_id,
        display_order=1,
        is_available=is_available,
    )


def make_sauce_sku(amount_minor: int = 0) -> CatalogSku:
    return CatalogSku(
        sku_id="sugo-pomodoro-500g",
        name="Sugo al Pomodoro",
        category=CatalogCategory("pantry", "Pantry", 5),
        unit_label="jar 500g",
        price=Money(amount_minor=amount_minor, currency="GBP"),
        short_description="Slow tomato sugo with basil for pasta.",
        detail_description="A jar of tomato sauce for fresh pasta.",
        tags=("sugo", "sauce", "pasta", "primo"),
        facets=DietaryFacets(is_vegetarian=True, is_vegan=True),
        image_id="sugo-pomodoro-500g",
        display_order=1,
        is_available=True,
    )


def make_complete_pasta_catalog(
    *,
    pasta_amount_minor: int = 425,
    sauce_amount_minor: int = 0,
) -> StaticCatalogRepository:
    return StaticCatalogRepository(
        [
            make_sku(amount_minor=pasta_amount_minor),
            make_sauce_sku(amount_minor=sauce_amount_minor),
        ]
    )


def raw_proposal(
    *,
    sku_id: str = "fresh-tagliatelle-250g",
    quantity: int = 2,
    rationale: str = "A flexible pasta course.",
) -> dict[str, object]:
    lines: list[dict[str, object]] = [
        {
            "sku_id": sku_id,
            "quantity": quantity,
            "rationale": rationale,
        }
    ]
    if sku_id == "fresh-tagliatelle-250g":
        lines.append(
            {
                "sku_id": "sugo-pomodoro-500g",
                "quantity": 1,
                "rationale": "Tomato sauce completes the pasta course.",
            }
        )
    return {
        "title": "Weeknight Pasta",
        "explanation": "A compact pasta proposal.",
        "planner_notes": ("Catalog identities checked.",),
        "party_size": 2,
        "package_template_id": "primo-only",
        "courses": (
            {
                "course": "primo",
                "lines": tuple(lines),
            },
        ),
    }


def proposal_request(
    *,
    sku_id: str = "fresh-tagliatelle-250g",
    quantity: int = 2,
    rationale: str = "A flexible pasta course.",
) -> dict[str, object]:
    lines: list[dict[str, object]] = [
        {
            "sku_id": sku_id,
            "quantity": quantity,
            "rationale": rationale,
        }
    ]
    if sku_id == "fresh-tagliatelle-250g":
        lines.append(
            {
                "sku_id": "sugo-pomodoro-500g",
                "quantity": 1,
                "rationale": "Tomato sauce completes the pasta course.",
            }
        )
    return {
        "title": "Weeknight Pasta",
        "explanation": "A compact pasta proposal.",
        "planner_notes": [
            {
                "note_type": "evidence",
                "source": "tavola",
                "message": "Catalog identities checked.",
            }
        ],
        "party_size": 2,
        "package_template_id": "primo-only",
        "courses": [
            {
                "course": "primo",
                "lines": lines,
            }
        ],
        "warnings": [],
    }


def expected_menu_proposal_response(quantity: int = 2) -> dict[str, object]:
    return {
        "title": "Weeknight Pasta",
        "explanation": "A compact pasta proposal.",
        "planner_notes": [
            {
                "note_type": "evidence",
                "source": "tavola",
                "message": "Catalog identities checked.",
            }
        ],
        "party_size": 2,
        "package_template_id": "primo-only",
        "courses": [
            {
                "course": "primo",
                "course_label": "Primo",
                "lines": [
                    {
                        "sku_id": "fresh-tagliatelle-250g",
                        "name": "Fresh Tagliatelle",
                        "category_id": "primi",
                        "category_label": "Primi",
                        "unit_label": "250g",
                        "quantity": quantity,
                        "unit_price_minor": 425,
                        "line_total_minor": 425 * quantity,
                        "currency": "GBP",
                        "image_id": "fresh-tagliatelle-250g",
                        "rationale": "A flexible pasta course.",
                    },
                    {
                        "sku_id": "sugo-pomodoro-500g",
                        "name": "Sugo al Pomodoro",
                        "category_id": "pantry",
                        "category_label": "Pantry",
                        "unit_label": "jar 500g",
                        "quantity": 1,
                        "unit_price_minor": 0,
                        "line_total_minor": 0,
                        "currency": "GBP",
                        "image_id": "sugo-pomodoro-500g",
                        "rationale": "Tomato sauce completes the pasta course.",
                    },
                ],
            }
        ],
        "total_minor": 425 * quantity,
        "currency": "GBP",
        "item_count": quantity + 1,
        "line_count": 2,
        "warnings": [],
    }


def expected_session_response(quantity: int = 2) -> dict[str, object]:
    return {
        "planner_session_id": "planner-1",
        "status": "proposal_ready",
        "customer_request": "Dinner for two",
        "follow_up_answers": [],
        "follow_up_question": None,
        "menu_proposal": expected_menu_proposal_response(quantity),
        "validation_errors": [],
        "planning_updates": [
            {
                "stage": "queued",
                "message": "Sending request",
            },
            {"stage": "started", "message": "Sending request"},
            {
                "stage": "validating",
                "message": "Reviewing products and prices",
            },
            {
                "stage": "ready",
                "message": "Your menu proposal is ready to review.",
            },
        ],
    }


def install_test_dependencies(
    *,
    agent: FakeMenuPlannerAgent | None = None,
    basket_repository: InMemoryBasketRepository | None = None,
    planner_repository: InMemoryPlannerSessionRepository | None = None,
    catalog_repository: StaticCatalogRepository | None = None,
) -> PlannerApiHarness:
    resolved_basket_repository = basket_repository or InMemoryBasketRepository(
        id_generator=lambda: "basket-1"
    )
    resolved_planner_repository = (
        planner_repository
        or InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    )
    resolved_catalog_repository = catalog_repository or make_complete_pasta_catalog()
    resolved_agent = agent or FakeMenuPlannerAgent.with_proposal(raw_proposal())
    background_runner = InProcessPlannerBackgroundRunner()
    runtime_status = PlannerRuntimeStatus(
        enabled=True,
        mode="real_codex",
        message="Planner is running with live Codex assistance.",
    )

    app.dependency_overrides[get_basket_repository] = lambda: resolved_basket_repository
    app.dependency_overrides[get_catalog_repository] = lambda: (
        resolved_catalog_repository
    )
    app.dependency_overrides[get_planner_session_repository] = lambda: (
        resolved_planner_repository
    )
    app.dependency_overrides[get_menu_planner_agent] = lambda: resolved_agent
    app.dependency_overrides[get_planner_background_runner] = lambda: background_runner
    app.dependency_overrides[get_planner_runtime_status] = lambda: runtime_status

    return PlannerApiHarness(
        client=TestClient(app),
        basket_repository=resolved_basket_repository,
        planner_repository=resolved_planner_repository,
        background_runner=background_runner,
    )


@pytest.fixture
def client() -> Iterator[PlannerApiHarness]:
    harness = install_test_dependencies()
    try:
        yield harness
    finally:
        harness.background_runner.shutdown()
        app.dependency_overrides.clear()


def wait_for_session_status(
    harness: PlannerApiHarness,
    planner_session_id: str,
    status: str,
    *,
    timeout_seconds: float = 1.0,
) -> dict[str, object]:
    deadline = monotonic() + timeout_seconds
    while monotonic() < deadline:
        response = harness.client.get(f"/api/planner/sessions/{planner_session_id}")
        body = response.json()
        if body["status"] == status:
            return body
        sleep(0.01)
    pytest.fail(f"planner session did not reach {status}")


class BlockingProposalAgent:
    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()

    def plan_menu(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
    ) -> MenuPlannerAgentResponse:
        self.started.set()
        self.release.wait(timeout=2)
        return MenuPlannerAgentResponse(raw_proposal=raw_proposal())


def test_start_planner_session_returns_planning_then_polling_observes_proposal(
    client: PlannerApiHarness,
) -> None:
    response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Dinner for two"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "planner_session_id": "planner-1",
        "status": "planning",
        "customer_request": "Dinner for two",
        "follow_up_answers": [],
        "follow_up_question": None,
        "menu_proposal": None,
        "validation_errors": [],
        "planning_updates": [
            {
                "stage": "queued",
                "message": "Sending request",
            }
        ],
    }

    assert (
        wait_for_session_status(client, body["planner_session_id"], "proposal_ready")
        == expected_session_response()
    )


def test_start_planner_session_returns_quickly_while_agent_keeps_running(
    client: PlannerApiHarness,
) -> None:
    agent = BlockingProposalAgent()
    app.dependency_overrides[get_menu_planner_agent] = lambda: agent

    started_at = monotonic()
    response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Dinner for two"},
    )
    elapsed = monotonic() - started_at

    assert response.status_code == 201
    assert response.json()["status"] == "planning"
    assert elapsed < 1
    assert agent.started.wait(timeout=1)
    planning_response = client.client.get("/api/planner/sessions/planner-1")
    assert planning_response.json()["planning_updates"] == [
        {
            "stage": "queued",
            "message": "Sending request",
        },
        {"stage": "started", "message": "Sending request"},
    ]

    busy_response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Dinner for four"},
    )

    assert busy_response.status_code == 503
    assert "already planning" in busy_response.json()["detail"]
    agent.release.set()
    wait_for_session_status(client, "planner-1", "proposal_ready")


def test_planner_status_reports_demo_mode(client: PlannerApiHarness) -> None:
    app.dependency_overrides[get_planner_runtime_status] = lambda: PlannerRuntimeStatus(
        enabled=False,
        mode="disabled",
        message="Planner is not enabled for this environment.",
    )

    response = client.client.get("/api/planner/status")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "mode": "disabled",
        "message": "Planner is not enabled for this environment.",
    }


def test_start_planner_session_returns_unavailable_when_planner_is_disabled(
    client: PlannerApiHarness,
) -> None:
    app.dependency_overrides[get_planner_runtime_status] = lambda: PlannerRuntimeStatus(
        enabled=False,
        mode="disabled",
        message="Planner is not enabled for this environment.",
    )

    response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Dinner for two"},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Planner is not enabled for this environment."}
    assert client.planner_repository.get_session(PlannerSessionId("planner-1")) is None


def test_follow_up_answer_completes_session(client: PlannerApiHarness) -> None:
    client.use_agent(
        FakeMenuPlannerAgent.with_follow_up(
            FollowUpQuestion(message="How many people should this serve?")
        )
    )
    start_response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Help me plan Sunday lunch"},
    )
    planner_session_id = start_response.json()["planner_session_id"]
    assert (
        wait_for_session_status(client, planner_session_id, "needs_input")[
            "follow_up_question"
        ]
        == "How many people should this serve?"
    )
    client.use_agent(FakeMenuPlannerAgent.with_proposal(raw_proposal(quantity=4)))

    response = client.client.post(
        f"/api/planner/sessions/{planner_session_id}/follow-up-answer",
        json={"message": "Four people"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "planning"
    assert body["customer_request"] == "Help me plan Sunday lunch"
    assert body["follow_up_answers"] == ["Four people"]
    final_body = wait_for_session_status(client, planner_session_id, "proposal_ready")
    assert final_body["menu_proposal"]["total_minor"] == 1700


def test_validate_edited_quantity_recalculates_proposal(
    client: PlannerApiHarness,
) -> None:
    client.save_ready_session()
    planner_session_id = "planner-1"

    response = client.client.post(
        f"/api/planner/sessions/{planner_session_id}/proposal/validate",
        json={"menu_proposal": proposal_request(quantity=3)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "proposal_ready"
    assert body["menu_proposal"]["total_minor"] == 1275
    assert body["menu_proposal"]["item_count"] == 4
    assert body["menu_proposal"]["courses"][0]["lines"][0]["quantity"] == 3
    assert body["menu_proposal"]["planner_notes"][-1] == {
        "note_type": "evidence",
        "source": "tavola",
        "message": "Revalidated by Tavola.",
    }


def test_accept_append_returns_basket_and_meal_plan_grouping(
    client: PlannerApiHarness,
) -> None:
    client.basket_repository.create_basket()
    client.save_ready_session()
    planner_session_id = "planner-1"

    response = client.client.post(
        f"/api/planner/sessions/{planner_session_id}/accept",
        json={
            "basket_id": "basket-1",
            "mode": "append",
            "menu_proposal": proposal_request(quantity=2),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "basket": {
            "basket_id": "basket-1",
            "lines": [
                {
                    "sku_id": "fresh-tagliatelle-250g",
                    "name": "Fresh Tagliatelle",
                    "category_id": "primi",
                    "category_label": "Primi",
                    "unit_label": "250g",
                    "quantity": 2,
                    "unit_price_minor": 425,
                    "line_total_minor": 850,
                    "currency": "GBP",
                    "image_id": "fresh-tagliatelle-250g",
                },
                {
                    "sku_id": "sugo-pomodoro-500g",
                    "name": "Sugo al Pomodoro",
                    "category_id": "pantry",
                    "category_label": "Pantry",
                    "unit_label": "jar 500g",
                    "quantity": 1,
                    "unit_price_minor": 0,
                    "line_total_minor": 0,
                    "currency": "GBP",
                    "image_id": "sugo-pomodoro-500g",
                },
            ],
            "total_minor": 850,
            "currency": "GBP",
            "item_count": 3,
            "line_count": 2,
        },
        "meal_plan_grouping": {
            "title": "Weeknight Pasta",
            "party_size": 2,
            "package_template_id": "primo-only",
            "courses": [
                {
                    "course": "primo",
                    "course_label": "Primo",
                    "line_sku_ids": [
                        "fresh-tagliatelle-250g",
                        "sugo-pomodoro-500g",
                    ],
                }
            ],
        },
    }


def test_get_planner_session_returns_404_for_missing_session(
    client: PlannerApiHarness,
) -> None:
    response = client.client.get("/api/planner/sessions/missing-session")

    assert response.status_code == 404
    assert response.json() == {"detail": "planner session not found"}


def test_accept_returns_404_for_missing_basket(client: PlannerApiHarness) -> None:
    client.save_ready_session()
    planner_session_id = "planner-1"

    response = client.client.post(
        f"/api/planner/sessions/{planner_session_id}/accept",
        json={
            "basket_id": "missing-basket",
            "mode": "append",
            "menu_proposal": proposal_request(),
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "basket not found"}


def test_validate_proposal_returns_422_for_validation_errors(
    client: PlannerApiHarness,
) -> None:
    client.save_ready_session()
    planner_session_id = "planner-1"

    response = client.client.post(
        f"/api/planner/sessions/{planner_session_id}/proposal/validate",
        json={"menu_proposal": proposal_request(quantity=0)},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["type"] == "invalid_quantity"
    assert detail[0]["loc"][:2] == ["body", "menu_proposal"]
