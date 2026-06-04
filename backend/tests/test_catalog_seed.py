import re
from collections import Counter, defaultdict

from tavola.infrastructure.catalog_seed import SEED_CATALOG

EXPECTED_CATEGORY_COUNTS = {
    "antipasti": 5,
    "primi": 6,
    "desserts": 3,
    "drinks": 3,
    "pantry": 3,
}

EXPECTED_CATEGORY_ORDER = {
    "antipasti": 1,
    "primi": 2,
    "desserts": 3,
    "drinks": 4,
    "pantry": 5,
}

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def test_seed_catalog_contains_twenty_unique_available_skus() -> None:
    sku_ids = [sku.sku_id for sku in SEED_CATALOG]

    assert len(SEED_CATALOG) == 20
    assert len(set(sku_ids)) == 20
    assert all(sku.is_available for sku in SEED_CATALOG)
    assert all(SLUG_PATTERN.fullmatch(sku_id) for sku_id in sku_ids)


def test_seed_catalog_has_expected_category_distribution() -> None:
    category_counts = Counter(sku.category.category_id for sku in SEED_CATALOG)

    assert category_counts == EXPECTED_CATEGORY_COUNTS


def test_seed_catalog_uses_backend_owned_display_order() -> None:
    ordered_keys = [
        (sku.category.display_order, sku.display_order, sku.sku_id)
        for sku in SEED_CATALOG
    ]
    display_orders_by_category: dict[str, list[int]] = defaultdict(list)

    for sku in SEED_CATALOG:
        assert (
            sku.category.display_order
            == EXPECTED_CATEGORY_ORDER[sku.category.category_id]
        )
        display_orders_by_category[sku.category.category_id].append(sku.display_order)

    assert ordered_keys == sorted(ordered_keys)
    assert display_orders_by_category == {
        "antipasti": [1, 2, 3, 4, 5],
        "primi": [1, 2, 3, 4, 5, 6],
        "desserts": [1, 2, 3],
        "drinks": [1, 2, 3],
        "pantry": [1, 2, 3],
    }


def test_seed_catalog_has_valid_price_and_tag_shape() -> None:
    for sku in SEED_CATALOG:
        assert sku.unit_label.strip()
        assert sku.price.currency == "GBP"
        assert sku.price.amount_minor > 0
        assert len(sku.tags) >= 2
        assert len(set(sku.tags)) == len(sku.tags)
        assert all(SLUG_PATTERN.fullmatch(tag) for tag in sku.tags)


def test_seed_catalog_has_customer_ready_copy() -> None:
    for sku in SEED_CATALOG:
        assert sku.name.strip()
        assert len(sku.short_description.split()) >= 5
        assert sku.short_description.endswith(".")
        assert sku.short_description.count(".") == 1
        assert 1 <= sku.detail_description.count(".") <= 2
        assert len(sku.detail_description.split()) >= 10
        assert "sample" not in sku.short_description.lower()
        assert "sample" not in sku.detail_description.lower()


def test_seed_catalog_has_useful_dietary_facets_in_each_category() -> None:
    categories_with_vegetarian_sku = {
        sku.category.category_id for sku in SEED_CATALOG if sku.facets.is_vegetarian
    }
    categories_with_gluten_free_sku = {
        sku.category.category_id for sku in SEED_CATALOG if sku.facets.is_gluten_free
    }

    assert categories_with_vegetarian_sku == set(EXPECTED_CATEGORY_COUNTS)
    assert {"antipasti", "desserts", "drinks", "pantry"}.issubset(
        categories_with_gluten_free_sku
    )
    assert any(sku.facets.is_vegan for sku in SEED_CATALOG)
    assert any(sku.facets.contains_alcohol for sku in SEED_CATALOG)


def test_seed_catalog_image_ids_match_stable_sku_id() -> None:
    image_ids = [sku.image_id for sku in SEED_CATALOG]

    assert len(set(image_ids)) == 20
    assert image_ids == [sku.sku_id for sku in SEED_CATALOG]
