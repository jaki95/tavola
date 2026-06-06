import json
import re
from collections import Counter, defaultdict
from collections.abc import Callable
from importlib.resources import files

import pytest

from tavola.domain.catalog import CatalogSku
from tavola.infrastructure.catalog_seed import SEED_CATALOG, _catalog_sku_from_row

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
ALCOHOL_RELATED_TERM_PATTERN = re.compile(
    r"\b(?:alcohol|alcoholic|amaro|beer|chianti|cider|grappa|limoncello|"
    r"marsala|prosecco|spritz|vermouth|wine)\b"
)


def _catalog_seed_rows() -> list[dict[str, object]]:
    raw = json.loads(
        files("tavola.infrastructure.data").joinpath("catalog.json").read_text()
    )

    assert isinstance(raw, list)
    return raw


def _planner_discovery_text(sku: CatalogSku) -> str:
    return " ".join(
        (
            sku.name,
            sku.short_description,
            sku.detail_description,
            *sku.tags,
        )
    ).casefold()


def _tagged_sku_ids(tag: str) -> set[str]:
    return {sku.sku_id for sku in SEED_CATALOG if tag in sku.tags}


def test_seed_catalog_is_backed_by_json_data_file() -> None:
    rows = _catalog_seed_rows()

    assert len(rows) == len(SEED_CATALOG)
    assert [row["sku_id"] for row in rows] == [sku.sku_id for sku in SEED_CATALOG]
    assert all("category_id" in row for row in rows)


def test_seed_catalog_loader_rejects_boolean_integer_fields() -> None:
    row = dict(_catalog_seed_rows()[0])
    row["unit_price_minor"] = True

    with pytest.raises(
        ValueError,
        match="catalog seed field unit_price_minor must be an integer",
    ):
        _catalog_sku_from_row(row)


def test_seed_catalog_dietary_tags_require_matching_structured_facets() -> None:
    dietary_tag_facets: dict[str, Callable[[CatalogSku], bool]] = {
        "vegan": lambda sku: sku.facets.is_vegan,
        "vegetarian": lambda sku: sku.facets.is_vegetarian,
        "gluten-free": lambda sku: sku.facets.is_gluten_free,
    }

    for tag, facet_matches in dietary_tag_facets.items():
        tagged_sku_ids = _tagged_sku_ids(tag)

        assert tagged_sku_ids
        assert tagged_sku_ids == {
            sku.sku_id for sku in SEED_CATALOG if tag in sku.tags and facet_matches(sku)
        }


def test_seed_catalog_alcohol_terms_match_contains_alcohol_facet() -> None:
    alcohol_term_sku_ids = {
        sku.sku_id
        for sku in SEED_CATALOG
        if ALCOHOL_RELATED_TERM_PATTERN.search(_planner_discovery_text(sku))
    }
    alcohol_facet_sku_ids = {
        sku.sku_id for sku in SEED_CATALOG if sku.facets.contains_alcohol
    }

    assert alcohol_term_sku_ids
    assert alcohol_term_sku_ids == alcohol_facet_sku_ids


def test_seed_catalog_hard_constraint_facets_are_validation_truth() -> None:
    vegan_facet_sku_ids = {sku.sku_id for sku in SEED_CATALOG if sku.facets.is_vegan}
    vegetarian_facet_sku_ids = {
        sku.sku_id for sku in SEED_CATALOG if sku.facets.is_vegetarian
    }
    gluten_free_facet_sku_ids = {
        sku.sku_id for sku in SEED_CATALOG if sku.facets.is_gluten_free
    }
    alcohol_facet_sku_ids = {
        sku.sku_id for sku in SEED_CATALOG if sku.facets.contains_alcohol
    }

    assert _tagged_sku_ids("vegan").issubset(vegan_facet_sku_ids)
    assert _tagged_sku_ids("vegetarian").issubset(vegetarian_facet_sku_ids)
    assert _tagged_sku_ids("gluten-free").issubset(gluten_free_facet_sku_ids)
    assert alcohol_facet_sku_ids
    assert vegetarian_facet_sku_ids - _tagged_sku_ids("vegetarian")
    assert gluten_free_facet_sku_ids - _tagged_sku_ids("gluten-free")


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
