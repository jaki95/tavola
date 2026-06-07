from tavola.application.catalog import (
    BrowseCatalog,
    FindCatalogCandidates,
    FindCatalogCandidatesInput,
    GetCatalogSkuDetail,
    ListAvailableCatalogTags,
)
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


ANTIPASTI = CatalogCategory("antipasti", "Antipasti", 1)
PRIMI = CatalogCategory("primi", "Primi", 2)
DESSERTS = CatalogCategory("desserts", "Desserts", 3)
DRINKS = CatalogCategory("drinks", "Drinks", 4)
PANTRY = CatalogCategory("pantry", "Pantry", 5)


def make_candidate_repository() -> StaticCatalogRepository:
    return StaticCatalogRepository(
        [
            make_sku(
                "red-wine",
                "Red Wine",
                DRINKS,
                1,
                tags=("wine", "red", "aperitivo"),
                facets=DietaryFacets(contains_alcohol=True),
            ),
            make_sku(
                "soft-drink",
                "Soft Drink",
                DRINKS,
                2,
                tags=("soft-drink", "aperitivo", "vegan"),
                facets=DietaryFacets(is_vegetarian=True, is_vegan=True),
            ),
            make_sku(
                "olive-oil",
                "Olive Oil",
                PANTRY,
                1,
                tags=("pantry", "vegan", "gluten-free"),
                facets=DietaryFacets(
                    is_vegetarian=True,
                    is_vegan=True,
                    is_gluten_free=True,
                ),
            ),
            make_sku(
                "caponata",
                "Caponata",
                ANTIPASTI,
                1,
                tags=("antipasti", "vegan", "gluten-free"),
                facets=DietaryFacets(
                    is_vegetarian=True,
                    is_vegan=True,
                    is_gluten_free=True,
                ),
            ),
            make_sku(
                "burrata",
                "Burrata",
                ANTIPASTI,
                2,
                tags=("antipasti", "cheese", "vegetarian"),
                facets=DietaryFacets(is_vegetarian=True, is_gluten_free=True),
            ),
            make_sku(
                "tagliatelle",
                "Tagliatelle",
                PRIMI,
                1,
                tags=("pasta", "fresh", "vegetarian"),
                facets=DietaryFacets(is_vegetarian=True),
            ),
            make_sku(
                "tiramisu",
                "Tiramisu",
                DESSERTS,
                1,
                tags=("dessert", "coffee", "vegetarian"),
                facets=DietaryFacets(
                    is_vegetarian=True,
                    contains_alcohol=True,
                ),
            ),
            make_sku(
                "hidden-artichokes",
                "Hidden Artichokes",
                ANTIPASTI,
                3,
                tags=("antipasti", "hidden", "vegan"),
                facets=DietaryFacets(is_vegetarian=True, is_vegan=True),
                is_available=False,
            ),
        ]
    )


def test_browse_catalog_returns_available_seed_skus_in_display_order() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())()

    assert result.products
    assert result.products[0].sku_id == "burrata-pugliese-125g"
    assert result.products[-1].sku_id == "pecorino-toscano-200g"
    assert "pinot-grigio-delle-venezie-750ml" in {sku.sku_id for sku in result.products}
    assert all(sku.is_available for sku in result.products)


def test_browse_catalog_filters_by_category_id() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())(category_id="primi")

    assert result.products
    assert {sku.category.category_id for sku in result.products} == {"primi"}
    assert result.products[0].sku_id == "fresh-tagliatelle-250g"


def test_browse_catalog_searches_customer_catalog_text_and_positive_facets() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())(query="vegan")

    assert {sku.sku_id for sku in result.products} >= {
        "marinated-nocellara-olives-250g",
        "caponata-siciliana-300g",
        "potato-gnocchi-500g",
    }
    assert all(sku.facets.is_vegan or "vegan" in sku.tags for sku in result.products)


def test_browse_catalog_finds_pantry_sauces_for_pasta_planning() -> None:
    result = BrowseCatalog(StaticCatalogRepository.from_seed())(query="pasta")

    assert {
        "sugo-pomodoro-500g",
        "pesto-genovese-180g",
    }.issubset({sku.sku_id for sku in result.products})


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


def test_list_available_catalog_tags_returns_sorted_unique_available_tags() -> None:
    antipasti = CatalogCategory("antipasti", "Antipasti", 1)
    repository = StaticCatalogRepository(
        [
            make_sku(
                "available-olives",
                "Available Olives",
                antipasti,
                1,
                tags=("olives", "aperitivo", "vegan"),
            ),
            make_sku(
                "available-caponata",
                "Available Caponata",
                antipasti,
                2,
                tags=("vegan", "sicilian", "aperitivo"),
            ),
            make_sku(
                "unavailable-artichokes",
                "Unavailable Artichokes",
                antipasti,
                3,
                tags=("artichoke", "hidden", "vegan"),
                is_available=False,
            ),
        ]
    )

    result = ListAvailableCatalogTags(repository)()

    assert result.tags == ("aperitivo", "olives", "sicilian", "vegan")


def test_find_catalog_candidates_excludes_unavailable_skus() -> None:
    result = FindCatalogCandidates(make_candidate_repository())(
        FindCatalogCandidatesInput(tags=("hidden",))
    )

    assert result.products == ()


def test_find_catalog_candidates_filters_category_ids_with_or_semantics() -> None:
    result = FindCatalogCandidates(make_candidate_repository())(
        FindCatalogCandidatesInput(category_ids=("desserts", "antipasti"))
    )

    assert [sku.sku_id for sku in result.products] == [
        "caponata",
        "burrata",
        "tiramisu",
    ]


def test_find_catalog_candidates_requires_all_dietary_facets() -> None:
    result = FindCatalogCandidates(make_candidate_repository())(
        FindCatalogCandidatesInput(dietary_facets=("vegan", "gluten_free"))
    )

    assert [sku.sku_id for sku in result.products] == ["caponata", "olive-oil"]


def test_find_catalog_candidates_matches_any_tag_by_default() -> None:
    result = FindCatalogCandidates(make_candidate_repository())(
        FindCatalogCandidatesInput(tags=("coffee", "fresh"))
    )

    assert [sku.sku_id for sku in result.products] == ["tagliatelle", "tiramisu"]


def test_find_catalog_candidates_can_require_all_tags() -> None:
    result = FindCatalogCandidates(make_candidate_repository())(
        FindCatalogCandidatesInput(
            tags=("vegan", "gluten-free"),
            tag_match="all",
        )
    )

    assert [sku.sku_id for sku in result.products] == ["caponata", "olive-oil"]


def test_find_catalog_candidates_filters_alcohol_modes() -> None:
    finder = FindCatalogCandidates(make_candidate_repository())

    with_alcohol_included = finder(FindCatalogCandidatesInput(alcohol="include"))
    without_alcohol = finder(FindCatalogCandidatesInput(alcohol="exclude"))
    only_alcohol = finder(FindCatalogCandidatesInput(alcohol="only"))

    assert [sku.sku_id for sku in with_alcohol_included.products] == [
        "caponata",
        "burrata",
        "tagliatelle",
        "tiramisu",
        "red-wine",
        "soft-drink",
        "olive-oil",
    ]
    assert [sku.sku_id for sku in without_alcohol.products] == [
        "caponata",
        "burrata",
        "tagliatelle",
        "soft-drink",
        "olive-oil",
    ]
    assert [sku.sku_id for sku in only_alcohol.products] == [
        "tiramisu",
        "red-wine",
    ]


def test_find_catalog_candidates_defaults_to_eight_results_and_caps_at_twenty() -> None:
    many_skus = [
        make_sku(
            f"pantry-item-{index}",
            f"Pantry Item {index}",
            PANTRY,
            index,
        )
        for index in range(1, 26)
    ]
    finder = FindCatalogCandidates(StaticCatalogRepository(many_skus))

    default_result = finder(FindCatalogCandidatesInput())
    capped_result = finder(FindCatalogCandidatesInput(max_results=50))

    assert len(default_result.products) == 8
    assert len(capped_result.products) == 20
    assert capped_result.result_count == 25


def test_find_catalog_candidates_clamps_tiny_max_results_to_one() -> None:
    result = FindCatalogCandidates(make_candidate_repository())(
        FindCatalogCandidatesInput(max_results=0)
    )

    assert [sku.sku_id for sku in result.products] == ["caponata"]


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
