from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from tavola.api.dependencies import (
    get_basket_repository,
    get_catalog_repository,
    get_menu_planner_agent,
    get_planner_session_repository,
)
from tavola.api.main import app
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.domain.planner import FollowUpQuestion
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.codex_planner import FakeMenuPlannerAgent
from tavola.infrastructure.planner_repository import InMemoryPlannerSessionRepository


@dataclass(frozen=True, slots=True)
class PlannerApiHarness:
    client: TestClient
    basket_repository: InMemoryBasketRepository
    planner_repository: InMemoryPlannerSessionRepository

    def use_agent(self, agent: FakeMenuPlannerAgent) -> None:
        app.dependency_overrides[get_menu_planner_agent] = lambda: agent


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


def raw_proposal(
    *,
    sku_id: str = "fresh-tagliatelle-250g",
    quantity: int = 2,
    rationale: str = "A flexible pasta course.",
) -> dict[str, object]:
    return {
        "title": "Weeknight Pasta",
        "explanation": "A compact pasta proposal.",
        "planner_notes": ("Catalog identities checked.",),
        "party_size": 2,
        "package_template_id": "primo-only",
        "courses": (
            {
                "course": "primo",
                "lines": (
                    {
                        "sku_id": sku_id,
                        "quantity": quantity,
                        "rationale": rationale,
                    },
                ),
            },
        ),
    }


def proposal_request(
    *,
    sku_id: str = "fresh-tagliatelle-250g",
    quantity: int = 2,
    rationale: str = "A flexible pasta course.",
) -> dict[str, object]:
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
                "lines": [
                    {
                        "sku_id": sku_id,
                        "quantity": quantity,
                        "rationale": rationale,
                    }
                ],
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
                    }
                ],
            }
        ],
        "total_minor": 425 * quantity,
        "currency": "GBP",
        "item_count": quantity,
        "line_count": 1,
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
    resolved_catalog_repository = catalog_repository or StaticCatalogRepository(
        [make_sku()]
    )
    resolved_agent = agent or FakeMenuPlannerAgent.with_proposal(raw_proposal())

    app.dependency_overrides[get_basket_repository] = lambda: resolved_basket_repository
    app.dependency_overrides[get_catalog_repository] = lambda: (
        resolved_catalog_repository
    )
    app.dependency_overrides[get_planner_session_repository] = lambda: (
        resolved_planner_repository
    )
    app.dependency_overrides[get_menu_planner_agent] = lambda: resolved_agent

    return PlannerApiHarness(
        client=TestClient(app),
        basket_repository=resolved_basket_repository,
        planner_repository=resolved_planner_repository,
    )


@pytest.fixture
def client() -> Iterator[PlannerApiHarness]:
    harness = install_test_dependencies()
    try:
        yield harness
    finally:
        app.dependency_overrides.clear()


def test_start_planner_session_returns_proposal_response_shape(
    client: PlannerApiHarness,
) -> None:
    response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Dinner for two"},
    )

    assert response.status_code == 201
    assert response.json() == expected_session_response()


def test_planner_status_reports_demo_mode(client: PlannerApiHarness) -> None:
    response = client.client.get("/api/planner/status")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "mode": "disabled",
        "message": "Planner is not enabled for this environment.",
    }


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
    client.use_agent(FakeMenuPlannerAgent.with_proposal(raw_proposal(quantity=4)))

    response = client.client.post(
        f"/api/planner/sessions/{planner_session_id}/follow-up-answer",
        json={"message": "Four people"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "proposal_ready"
    assert body["customer_request"] == "Help me plan Sunday lunch"
    assert body["follow_up_answers"] == ["Four people"]
    assert body["menu_proposal"]["total_minor"] == 1700


def test_validate_edited_quantity_recalculates_proposal(
    client: PlannerApiHarness,
) -> None:
    start_response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Dinner for two"},
    )
    planner_session_id = start_response.json()["planner_session_id"]

    response = client.client.post(
        f"/api/planner/sessions/{planner_session_id}/proposal/validate",
        json={"menu_proposal": proposal_request(quantity=3)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "proposal_ready"
    assert body["menu_proposal"]["total_minor"] == 1275
    assert body["menu_proposal"]["item_count"] == 3
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
    start_response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Dinner for two"},
    )
    planner_session_id = start_response.json()["planner_session_id"]

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
                }
            ],
            "total_minor": 850,
            "currency": "GBP",
            "item_count": 2,
            "line_count": 1,
        },
        "meal_plan_grouping": {
            "title": "Weeknight Pasta",
            "party_size": 2,
            "package_template_id": "primo-only",
            "courses": [
                {
                    "course": "primo",
                    "course_label": "Primo",
                    "line_sku_ids": ["fresh-tagliatelle-250g"],
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
    start_response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Dinner for two"},
    )
    planner_session_id = start_response.json()["planner_session_id"]

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
    start_response = client.client.post(
        "/api/planner/sessions",
        json={"message": "Dinner for two"},
    )
    planner_session_id = start_response.json()["planner_session_id"]

    response = client.client.post(
        f"/api/planner/sessions/{planner_session_id}/proposal/validate",
        json={"menu_proposal": proposal_request(quantity=0)},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["type"] == "invalid_quantity"
    assert detail[0]["loc"][:2] == ["body", "menu_proposal"]
