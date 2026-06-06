from tavola.application.catalog import CatalogRepository
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.infrastructure.catalog_repository import StaticCatalogRepository


def make_sku(
    sku_id: str,
    category: CatalogCategory,
    display_order: int,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name=sku_id.replace("-", " ").title(),
        category=category,
        unit_label="single portion",
        price=Money(amount_minor=500, currency="GBP"),
        short_description="A compact customer-facing deli description.",
        detail_description="A richer product note for the customer detail view.",
        tags=("deli", "sample"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id=sku_id,
        display_order=display_order,
        is_available=True,
    )


def test_static_catalog_repository_lists_skus_in_catalog_display_order() -> None:
    desserts = CatalogCategory("desserts", "Desserts", 3)
    antipasti = CatalogCategory("antipasti", "Antipasti", 1)
    repository = StaticCatalogRepository(
        [
            make_sku("tiramisu-cup", desserts, 1),
            make_sku("marinated-olives", antipasti, 2),
            make_sku("burrata-pugliese", antipasti, 1),
        ]
    )

    skus = repository.list_skus()

    assert [sku.sku_id for sku in skus] == [
        "burrata-pugliese",
        "marinated-olives",
        "tiramisu-cup",
    ]


def test_static_catalog_repository_fetches_sku_by_id() -> None:
    primi = CatalogCategory("primi", "Primi", 2)
    tagliatelle = make_sku("fresh-tagliatelle-250g", primi, 1)
    repository = StaticCatalogRepository([tagliatelle])

    assert repository.get_sku("fresh-tagliatelle-250g") == tagliatelle


def test_static_catalog_repository_returns_none_for_missing_sku() -> None:
    repository = StaticCatalogRepository([])

    assert repository.get_sku("missing-sku") is None


def test_static_catalog_repository_can_be_backed_by_seed_catalog() -> None:
    repository = StaticCatalogRepository.from_seed()

    skus = repository.list_skus()

    assert skus
    assert repository.get_sku("fresh-tagliatelle-250g") is not None
    assert repository.get_sku("pinot-grigio-delle-venezie-750ml") is not None


def test_static_catalog_repository_satisfies_application_protocol() -> None:
    repository: CatalogRepository = StaticCatalogRepository([])

    assert repository.list_skus() == ()
