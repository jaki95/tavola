from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from tavola.api.dependencies import get_basket_repository, get_catalog_repository
from tavola.api.main import app
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository


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


@pytest.fixture
def client() -> Iterator[TestClient]:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    catalog_repository = StaticCatalogRepository([make_sku()])
    app.dependency_overrides[get_basket_repository] = lambda: basket_repository
    app.dependency_overrides[get_catalog_repository] = lambda: catalog_repository

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def install_test_repositories(
    *,
    basket_repository: InMemoryBasketRepository | None = None,
    catalog_repository: StaticCatalogRepository | None = None,
) -> None:
    resolved_basket_repository = basket_repository or InMemoryBasketRepository(
        id_generator=lambda: "basket-1"
    )
    resolved_catalog_repository = catalog_repository or StaticCatalogRepository(
        [make_sku()]
    )
    app.dependency_overrides[get_basket_repository] = lambda: resolved_basket_repository
    app.dependency_overrides[get_catalog_repository] = lambda: (
        resolved_catalog_repository
    )


def test_create_basket_route_returns_empty_basket(client: TestClient) -> None:
    response = client.post("/api/baskets")

    assert response.status_code == 201
    assert response.json() == {
        "basket_id": "basket-1",
        "lines": [],
        "total_minor": 0,
        "currency": "GBP",
        "item_count": 0,
        "line_count": 0,
    }


def test_add_line_route_returns_one_line_basket(client: TestClient) -> None:
    client.post("/api/baskets")

    response = client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 2},
    )

    assert response.status_code == 200
    assert response.json() == {
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
    }


def test_get_basket_route_returns_persisted_basket(client: TestClient) -> None:
    client.post("/api/baskets")
    client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 2},
    )

    response = client.get("/api/baskets/basket-1")

    assert response.status_code == 200
    assert response.json()["item_count"] == 2
    assert response.json()["total_minor"] == 850


def test_add_line_route_merges_existing_sku_quantity(client: TestClient) -> None:
    client.post("/api/baskets")
    client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 2},
    )

    response = client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["line_count"] == 1
    assert body["item_count"] == 5
    assert body["lines"][0]["quantity"] == 5


def test_patch_line_route_sets_exact_quantity(client: TestClient) -> None:
    client.post("/api/baskets")
    client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 2},
    )

    response = client.patch(
        "/api/baskets/basket-1/lines/fresh-tagliatelle-250g",
        json={"quantity": 4},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["lines"][0]["quantity"] == 4
    assert body["total_minor"] == 1700


def test_delete_line_route_removes_final_line(client: TestClient) -> None:
    client.post("/api/baskets")
    client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 1},
    )

    response = client.delete("/api/baskets/basket-1/lines/fresh-tagliatelle-250g")

    assert response.status_code == 200
    assert response.json() == {
        "basket_id": "basket-1",
        "lines": [],
        "total_minor": 0,
        "currency": "GBP",
        "item_count": 0,
        "line_count": 0,
    }


def test_basket_routes_return_404_for_missing_basket_or_line(
    client: TestClient,
) -> None:
    missing_basket = client.get("/api/baskets/missing-basket")
    missing_add_basket = client.post(
        "/api/baskets/missing-basket/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 1},
    )
    client.post("/api/baskets")
    missing_patch_line = client.patch(
        "/api/baskets/basket-1/lines/missing-sku",
        json={"quantity": 1},
    )
    missing_delete_line = client.delete("/api/baskets/basket-1/lines/missing-sku")

    assert missing_basket.status_code == 404
    assert missing_basket.json() == {"detail": "basket not found"}
    assert missing_add_basket.status_code == 404
    assert missing_patch_line.status_code == 404
    assert missing_patch_line.json() == {"detail": "basket line not found"}
    assert missing_delete_line.status_code == 404


def test_add_line_route_returns_422_for_missing_or_unavailable_sku() -> None:
    catalog_repository = StaticCatalogRepository(
        [make_sku("unavailable-artichokes", is_available=False)]
    )
    install_test_repositories(catalog_repository=catalog_repository)
    client = TestClient(app)

    try:
        client.post("/api/baskets")
        missing_response = client.post(
            "/api/baskets/basket-1/lines",
            json={"sku_id": "missing-sku", "quantity": 1},
        )
        unavailable_response = client.post(
            "/api/baskets/basket-1/lines",
            json={"sku_id": "unavailable-artichokes", "quantity": 1},
        )
    finally:
        app.dependency_overrides.clear()

    assert missing_response.status_code == 422
    assert missing_response.json() == {
        "detail": [
            {
                "loc": ["body", "sku_id"],
                "msg": "SKU not found.",
                "type": "sku_not_found",
            }
        ]
    }
    assert unavailable_response.status_code == 422
    assert unavailable_response.json() == {
        "detail": [
            {
                "loc": ["body", "sku_id"],
                "msg": "SKU is unavailable.",
                "type": "sku_unavailable",
            }
        ]
    }


def test_basket_routes_return_422_for_quantity_errors(client: TestClient) -> None:
    client.post("/api/baskets")

    non_positive_response = client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 0},
    )
    over_max_response = client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 11},
    )
    malformed_response = client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "", "quantity": "2"},
    )

    assert non_positive_response.status_code == 422
    assert non_positive_response.json() == {
        "detail": [
            {
                "loc": ["body", "quantity"],
                "msg": "Quantity must be positive.",
                "type": "invalid_quantity",
            }
        ]
    }
    assert over_max_response.status_code == 422
    assert over_max_response.json() == {
        "detail": [
            {
                "loc": ["body", "quantity"],
                "msg": "Quantity cannot exceed 10.",
                "type": "quantity_exceeds_max",
                "ctx": {"max_quantity": 10},
            }
        ]
    }
    assert malformed_response.status_code == 422
