from tavola.application.catalog import BrowseCatalog, GetCatalogSkuDetail
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
    short_description: str = "A useful customer-facing catalog sentence.",
    tags: tuple[str, ...] = ("deli", "sample"),
    facets: DietaryFacets | None = None,
    is_available: bool = True,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name=name,
        category=category,
        unit_label="single portion",
        price=Money(amount_minor=500, currency="GBP"),
        short_description=short_description,
        detail_description="A richer product note for the customer detail view.",
        tags=tags,
        facets=facets or DietaryFacets(is_vegetarian=True),
        image_id=sku_id,
        display_order=display_order,
        is_available=is_available,
    )


def test_browse_catalog_returns_available_seed_skus_in_display_order() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())()

    assert len(result.products) == 20
    assert result.products[0].sku_id == "burrata-pugliese-125g"
    assert result.products[-1].sku_id == "extra-virgin-olive-oil-500ml"
    assert all(sku.is_available for sku in result.products)


def test_browse_catalog_filters_by_category_id() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())(category_id="primi")

    assert [sku.category.category_id for sku in result.products] == ["primi"] * 6
    assert result.products[0].sku_id == "fresh-tagliatelle-250g"


def test_browse_catalog_searches_customer_catalog_text_and_positive_facets() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())(query="vegan")

    assert {sku.sku_id for sku in result.products} >= {
        "marinated-nocellara-olives-250g",
        "caponata-siciliana-300g",
        "potato-gnocchi-500g",
    }
    assert all(sku.facets.is_vegan or "vegan" in sku.tags for sku in result.products)


def test_browse_catalog_normalizes_search_query() -> None:
    repository = StaticCatalogRepository.from_seed()
    browse = BrowseCatalog(repository)

    expected = browse(query="fresh pasta").products

    assert browse(query="  FRESH   PASTA  ").products == expected
    assert browse(query="   ").products == browse().products


def test_browse_catalog_requires_all_search_tokens_to_match() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())(
        query="fresh tagliatelle"
    )

    assert [sku.sku_id for sku in result.products] == ["fresh-tagliatelle-250g"]


def test_browse_catalog_combines_category_and_search_filters() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())(
        category_id="pantry",
        query="sauce",
    )

    assert [sku.sku_id for sku in result.products] == [
        "sugo-pomodoro-500g",
        "pesto-genovese-180g",
    ]


def test_browse_catalog_returns_empty_result_when_no_products_match() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())(query="pizza")

    assert result.products == ()


def test_browse_catalog_excludes_unavailable_skus() -> None:
    antipasti = CatalogCategory("antipasti", "Antipasti", 1)
    repository = StaticCatalogRepository(
        [
            make_sku("available-olives", "Available Olives", antipasti, 1),
            make_sku(
                "unavailable-artichokes",
                "Unavailable Artichokes",
                antipasti,
                2,
                is_available=False,
            ),
        ]
    )

    result = BrowseCatalog(repository)()

    assert [sku.sku_id for sku in result.products] == ["available-olives"]


def test_get_catalog_sku_detail_returns_known_available_sku() -> None:
    detail = GetCatalogSkuDetail(StaticCatalogRepository.from_seed())(
        "fresh-tagliatelle-250g"
    )

    assert detail is not None
    assert detail.sku_id == "fresh-tagliatelle-250g"
    assert detail.detail_description


def test_get_catalog_sku_detail_returns_none_for_missing_or_unavailable_sku() -> None:
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
    get_detail = GetCatalogSkuDetail(repository)

    assert get_detail("missing-sku") is None
    assert get_detail("unavailable-artichokes") is None
