from fastapi.testclient import TestClient

from tavola.api.dependencies import get_catalog_repository
from tavola.api.main import app
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.infrastructure.catalog_repository import StaticCatalogRepository


def make_sku(
    sku_id: str,
    name: str,
    category: CatalogCategory,
    display_order: int,
    *,
    is_available: bool = True,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name=name,
        category=category,
        unit_label="single portion",
        price=Money(amount_minor=500, currency="GBP"),
        short_description="A useful customer-facing catalog sentence.",
        detail_description="A richer product note for the customer detail view.",
        tags=("deli", "sample"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id=sku_id,
        display_order=display_order,
        is_available=is_available,
    )


def test_catalog_route_returns_seed_catalog_with_ordered_categories() -> None:
    client = TestClient(app)

    response = client.get("/api/catalog")

    assert response.status_code == 200
    body = response.json()
    assert body["categories"] == [
        {"category_id": "antipasti", "label": "Antipasti"},
        {"category_id": "primi", "label": "Primi"},
        {"category_id": "desserts", "label": "Desserts"},
        {"category_id": "drinks", "label": "Drinks"},
        {"category_id": "pantry", "label": "Pantry"},
    ]
    assert len(body["products"]) == 20
    assert body["products"][0] == {
        "sku_id": "burrata-pugliese-125g",
        "name": "Burrata Pugliese",
        "category_id": "antipasti",
        "category_label": "Antipasti",
        "unit_label": "125g",
        "unit_price_minor": 495,
        "currency": "GBP",
        "short_description": (
            "Fresh burrata with a creamy centre and delicate milk sweetness."
        ),
        "is_vegetarian": True,
        "is_vegan": False,
        "is_gluten_free": True,
        "contains_alcohol": False,
        "image_id": "burrata-pugliese-125g",
    }
    assert "tags" not in body["products"][0]
    assert "is_available" not in body["products"][0]


def test_catalog_route_filters_by_case_insensitive_category_and_query() -> None:
    client = TestClient(app)

    response = client.get("/api/catalog", params={"category": "PrImI", "q": "pasta"})

    assert response.status_code == 200
    body = response.json()
    assert [product["sku_id"] for product in body["products"]] == [
        "fresh-tagliatelle-250g",
        "ricotta-spinach-ravioli-300g",
        "beef-ragu-lasagne-serves-2",
        "potato-gnocchi-500g",
    ]


def test_catalog_route_returns_empty_products_for_valid_filters_with_no_match() -> None:
    client = TestClient(app)

    response = client.get("/api/catalog", params={"category": "desserts", "q": "pasta"})

    assert response.status_code == 200
    assert response.json()["products"] == []


def test_catalog_route_returns_422_for_invalid_category() -> None:
    client = TestClient(app)

    response = client.get("/api/catalog", params={"category": "starters"})

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["query", "category"],
                "msg": "Unsupported catalog category.",
                "type": "value_error",
            }
        ]
    }


def test_catalog_product_detail_route_returns_known_sku_detail() -> None:
    client = TestClient(app)

    response = client.get("/api/catalog/products/fresh-tagliatelle-250g")

    assert response.status_code == 200
    body = response.json()
    assert body["sku_id"] == "fresh-tagliatelle-250g"
    assert body["detail_description"] == (
        "Silky tagliatelle made with durum wheat flour and free-range egg."
        " Toss with ragu, mushrooms, or a simple butter and sage sauce."
    )
    assert "tags" not in body
    assert "is_available" not in body


def test_catalog_product_detail_route_returns_404_for_missing_or_unavailable_sku() -> (
    None
):
    antipasti = CatalogCategory("antipasti", "Antipasti", 1)
    repository = StaticCatalogRepository(
        [
            make_sku(
                "unavailable-artichokes",
                "Unavailable Artichokes",
                antipasti,
                1,
                is_available=False,
            )
        ]
    )
    app.dependency_overrides[get_catalog_repository] = lambda: repository
    client = TestClient(app)

    try:
        missing_response = client.get("/api/catalog/products/missing-sku")
        unavailable_response = client.get(
            "/api/catalog/products/unavailable-artichokes"
        )
    finally:
        app.dependency_overrides.clear()

    assert missing_response.status_code == 404
    assert unavailable_response.status_code == 404
