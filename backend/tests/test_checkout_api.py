from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from tavola.api.dependencies import (
    get_basket_repository,
    get_catalog_repository,
    get_order_repository,
    get_pickup_window_repository,
)
from tavola.api.main import app
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.checkout_repository import (
    InMemoryOrderRepository,
    StaticPickupWindowRepository,
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


@pytest.fixture
def client() -> Iterator[TestClient]:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    catalog_repository = StaticCatalogRepository([make_sku()])
    pickup_window_repository = StaticPickupWindowRepository.from_seed()
    order_repository = InMemoryOrderRepository(id_generator=lambda: "order-1")

    app.dependency_overrides[get_basket_repository] = lambda: basket_repository
    app.dependency_overrides[get_catalog_repository] = lambda: catalog_repository
    app.dependency_overrides[get_pickup_window_repository] = lambda: (
        pickup_window_repository
    )
    app.dependency_overrides[get_order_repository] = lambda: order_repository

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def install_test_repositories(
    *,
    basket_repository: InMemoryBasketRepository | None = None,
    catalog_repository: StaticCatalogRepository | None = None,
    pickup_window_repository: StaticPickupWindowRepository | None = None,
    order_repository: InMemoryOrderRepository | None = None,
) -> tuple[InMemoryBasketRepository, StaticCatalogRepository]:
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
    app.dependency_overrides[get_pickup_window_repository] = lambda: (
        pickup_window_repository or StaticPickupWindowRepository.from_seed()
    )
    app.dependency_overrides[get_order_repository] = lambda: (
        order_repository or InMemoryOrderRepository(id_generator=lambda: "order-1")
    )
    return resolved_basket_repository, resolved_catalog_repository


def test_pickup_windows_route_returns_ordered_pickup_choices(
    client: TestClient,
) -> None:
    response = client.get("/api/checkout/pickup-windows")

    assert response.status_code == 200
    assert response.json() == {
        "pickup_windows": [
            {
                "pickup_window_id": "friday-afternoon",
                "label": "Friday afternoon collection",
                "display_order": 1,
            },
            {
                "pickup_window_id": "saturday-midday",
                "label": "Saturday midday collection",
                "display_order": 2,
            },
            {
                "pickup_window_id": "sunday-morning",
                "label": "Sunday morning collection",
                "display_order": 3,
            },
        ]
    }


def test_checkout_route_creates_order_and_returns_empty_basket(
    client: TestClient,
) -> None:
    client.post("/api/baskets")
    client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 2},
    )

    response = client.post(
        "/api/checkout",
        json={
            "basket_id": "basket-1",
            "contact_name": "Giulia Rossi",
            "contact_email": "giulia@example.com",
            "pickup_window_id": "friday-afternoon",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "order": {
            "order_id": "order-1",
            "basket_id": "basket-1",
            "contact_name": "Giulia Rossi",
            "contact_email": "giulia@example.com",
            "pickup_window": {
                "pickup_window_id": "friday-afternoon",
                "label": "Friday afternoon collection",
                "display_order": 1,
            },
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
        "basket": {
            "basket_id": "basket-1",
            "lines": [],
            "total_minor": 0,
            "currency": "GBP",
            "item_count": 0,
            "line_count": 0,
        },
    }
    assert client.get("/api/baskets/basket-1").json()["line_count"] == 0


def test_checkout_route_uses_fastapi_422_for_malformed_requests(
    client: TestClient,
) -> None:
    blank_basket_response = client.post(
        "/api/checkout",
        json={
            "basket_id": "   ",
            "contact_name": "Giulia Rossi",
            "contact_email": "giulia@example.com",
            "pickup_window_id": "friday-afternoon",
        },
    )
    blank_contact_response = client.post(
        "/api/checkout",
        json={
            "basket_id": "basket-1",
            "contact_name": " ",
            "contact_email": "giulia@example.com",
            "pickup_window_id": "friday-afternoon",
        },
    )

    assert blank_basket_response.status_code == 422
    assert blank_contact_response.status_code == 422
    assert blank_contact_response.json()["detail"][0]["loc"] == [
        "body",
        "contact_name",
    ]


def test_checkout_route_returns_404_for_missing_basket(client: TestClient) -> None:
    response = client.post(
        "/api/checkout",
        json={
            "basket_id": "missing-basket",
            "contact_name": "Giulia Rossi",
            "contact_email": "giulia@example.com",
            "pickup_window_id": "friday-afternoon",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "basket not found"}


def test_checkout_route_returns_422_for_empty_basket(client: TestClient) -> None:
    client.post("/api/baskets")

    response = client.post(
        "/api/checkout",
        json={
            "basket_id": "basket-1",
            "contact_name": "Giulia Rossi",
            "contact_email": "giulia@example.com",
            "pickup_window_id": "friday-afternoon",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "basket_id"],
                "msg": "Basket is empty.",
                "type": "empty_basket",
            }
        ]
    }


def test_checkout_route_returns_422_for_missing_pickup_window(
    client: TestClient,
) -> None:
    client.post("/api/baskets")
    client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 1},
    )

    response = client.post(
        "/api/checkout",
        json={
            "basket_id": "basket-1",
            "contact_name": "Giulia Rossi",
            "contact_email": "giulia@example.com",
            "pickup_window_id": "missing-window",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "pickup_window_id"],
                "msg": "Pickup window was not found.",
                "type": "pickup_window_not_found",
            }
        ]
    }


def test_checkout_route_returns_422_for_invalid_contact_email(
    client: TestClient,
) -> None:
    client.post("/api/baskets")
    client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 1},
    )

    response = client.post(
        "/api/checkout",
        json={
            "basket_id": "basket-1",
            "contact_name": "Giulia Rossi",
            "contact_email": "giulia.example.com",
            "pickup_window_id": "friday-afternoon",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "contact_email"],
                "msg": "Contact email must include text before and after @.",
                "type": "invalid_contact_details",
            }
        ]
    }


def test_checkout_route_returns_422_for_missing_or_unavailable_current_sku() -> None:
    unavailable_sku = make_sku(is_available=False)
    basket_repository, _ = install_test_repositories(
        catalog_repository=StaticCatalogRepository([])
    )
    basket = basket_repository.create_basket()
    basket_repository.save_basket(basket.add_line(make_sku(), quantity=1))
    client = TestClient(app)

    try:
        missing_response = client.post(
            "/api/checkout",
            json={
                "basket_id": "basket-1",
                "contact_name": "Giulia Rossi",
                "contact_email": "giulia@example.com",
                "pickup_window_id": "friday-afternoon",
            },
        )
        basket_repository.save_basket(basket.add_line(make_sku(), quantity=1))
        app.dependency_overrides[get_catalog_repository] = lambda: (
            StaticCatalogRepository([unavailable_sku])
        )
        unavailable_response = client.post(
            "/api/checkout",
            json={
                "basket_id": "basket-1",
                "contact_name": "Giulia Rossi",
                "contact_email": "giulia@example.com",
                "pickup_window_id": "friday-afternoon",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert missing_response.status_code == 422
    assert missing_response.json() == {
        "detail": [
            {
                "loc": ["body", "basket_id"],
                "msg": "Basket contains a SKU that is no longer available.",
                "type": "sku_not_found",
                "ctx": {"sku_id": "fresh-tagliatelle-250g"},
            }
        ]
    }
    assert unavailable_response.status_code == 422
    assert unavailable_response.json() == {
        "detail": [
            {
                "loc": ["body", "basket_id"],
                "msg": "Basket contains an unavailable SKU.",
                "type": "sku_unavailable",
                "ctx": {"sku_id": "fresh-tagliatelle-250g"},
            }
        ]
    }


def test_checkout_route_returns_empty_basket_error_for_second_attempt(
    client: TestClient,
) -> None:
    client.post("/api/baskets")
    client.post(
        "/api/baskets/basket-1/lines",
        json={"sku_id": "fresh-tagliatelle-250g", "quantity": 1},
    )
    client.post(
        "/api/checkout",
        json={
            "basket_id": "basket-1",
            "contact_name": "Giulia Rossi",
            "contact_email": "giulia@example.com",
            "pickup_window_id": "friday-afternoon",
        },
    )

    response = client.post(
        "/api/checkout",
        json={
            "basket_id": "basket-1",
            "contact_name": "Giulia Rossi",
            "contact_email": "giulia@example.com",
            "pickup_window_id": "friday-afternoon",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "empty_basket"
