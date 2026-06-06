import json
import re
from collections import Counter, defaultdict
from collections.abc import Callable
from importlib.resources import files

import pytest

from tavola.domain.catalog import CatalogSku
from tavola.infrastructure.catalog_seed import SEED_CATALOG, _catalog_sku_from_row

EXPECTED_CATEGORY_IDS = {"antipasti", "primi", "desserts", "drinks", "pantry"}

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


def test_seed_catalog_contains_unique_available_skus() -> None:
    sku_ids = [sku.sku_id for sku in SEED_CATALOG]

    assert SEED_CATALOG
    assert len(set(sku_ids)) == len(SEED_CATALOG)
    assert all(sku.is_available for sku in SEED_CATALOG)
    assert all(SLUG_PATTERN.fullmatch(sku_id) for sku_id in sku_ids)


def test_seed_catalog_uses_only_canonical_populated_categories() -> None:
    category_counts = Counter(sku.category.category_id for sku in SEED_CATALOG)

    assert set(category_counts) == EXPECTED_CATEGORY_IDS
    assert all(count > 0 for count in category_counts.values())


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
    for display_orders in display_orders_by_category.values():
        assert display_orders == list(range(1, len(display_orders) + 1))


def test_seed_catalog_includes_pinot_grigio_delle_venezie() -> None:
    sku = next(
        (
            sku
            for sku in SEED_CATALOG
            if sku.sku_id == "pinot-grigio-delle-venezie-750ml"
        ),
        None,
    )

    assert sku is not None
    assert sku.name == "Pinot Grigio delle Venezie"
    assert sku.category.category_id == "drinks"
    assert sku.unit_label == "750ml"
    assert sku.price.amount_minor == 1395
    assert sku.short_description == (
        "Crisp white wine with pear, citrus, and a clean mineral finish."
    )
    assert sku.tags == ("wine", "pinot-grigio", "white", "veneto", "aperitivo")
    assert sku.facets.is_vegetarian
    assert not sku.facets.is_vegan
    assert sku.facets.is_gluten_free
    assert sku.facets.contains_alcohol
    assert sku.image_id == sku.sku_id
    assert sku.display_order == 4


def test_seed_catalog_uses_house_made_aranciata_and_limonata_names() -> None:
    sku_ids = {sku.sku_id for sku in SEED_CATALOG}
    aranciata = next(
        (sku for sku in SEED_CATALOG if sku.sku_id == "aranciata-sparkling-330ml"),
        None,
    )
    limonata = next(
        (sku for sku in SEED_CATALOG if sku.sku_id == "limonata-sparkling-330ml"),
        None,
    )

    assert "san-pellegrino-aranciata-330ml" not in sku_ids
    assert aranciata is not None
    assert aranciata.name == "Homemade Aranciata"
    assert aranciata.category.category_id == "drinks"
    assert aranciata.unit_label == "330ml"
    assert aranciata.price.amount_minor == 225
    assert aranciata.short_description == (
        "Homemade sparkling aranciata with a gently bitter citrus finish."
    )
    assert aranciata.tags == (
        "aranciata",
        "orange",
        "soft-drink",
        "homemade",
        "vegan",
        "aperitivo",
    )
    assert aranciata.facets.is_vegetarian
    assert aranciata.facets.is_vegan
    assert aranciata.facets.is_gluten_free
    assert not aranciata.facets.contains_alcohol
    assert aranciata.image_id == aranciata.sku_id
    assert aranciata.display_order == 1

    assert limonata is not None
    assert limonata.name == "Homemade Limonata"
    assert "lemonade" not in limonata.short_description.casefold()
    assert "lemonade" not in limonata.detail_description.casefold()


def test_seed_catalog_replaces_polenta_cake_with_torta_della_nonna() -> None:
    sku_ids = {sku.sku_id for sku in SEED_CATALOG}
    sku = next(
        (sku for sku in SEED_CATALOG if sku.sku_id == "torta-della-nonna-slice"),
        None,
    )

    assert "lemon-polenta-cake-slice" not in sku_ids
    assert sku is not None
    assert sku.name == "Torta della Nonna"
    assert sku.category.category_id == "desserts"
    assert sku.unit_label == "slice"
    assert sku.price.amount_minor == 475
    assert sku.short_description == (
        "Tuscan custard tart slice with pine nuts and a crisp pastry shell."
    )
    assert sku.tags == ("tart", "custard", "pine-nuts", "dessert", "tuscan")
    assert sku.facets.is_vegetarian
    assert not sku.facets.is_vegan
    assert not sku.facets.is_gluten_free
    assert not sku.facets.contains_alcohol
    assert sku.image_id == sku.sku_id
    assert sku.display_order == 3


def test_seed_catalog_includes_ribollita_toscana() -> None:
    sku = next(
        (sku for sku in SEED_CATALOG if sku.sku_id == "ribollita-toscana-500g"),
        None,
    )

    assert sku is not None
    assert sku.name == "Ribollita Toscana"
    assert sku.category.category_id == "primi"
    assert sku.unit_label == "500g"
    assert sku.price.amount_minor == 795
    assert sku.short_description == (
        "Hearty Tuscan vegetable and bread soup with cavolo nero and beans."
    )
    assert sku.tags == (
        "soup",
        "ribollita",
        "tuscan",
        "beans",
        "vegetarian",
        "vegan",
        "primo",
    )
    assert sku.facets.is_vegetarian
    assert sku.facets.is_vegan
    assert not sku.facets.is_gluten_free
    assert not sku.facets.contains_alcohol
    assert sku.image_id == sku.sku_id
    assert sku.display_order == 7


def test_seed_catalog_includes_focaccia_pecorino_finocchiona_and_cantucci() -> None:
    skus = {sku.sku_id: sku for sku in SEED_CATALOG}

    focaccia = skus.get("rosemary-focaccia-piece")
    pecorino = skus.get("pecorino-toscano-200g")
    finocchiona = skus.get("finocchiona-salami-100g")
    cantucci = skus.get("cantucci-biscotti-200g")

    assert focaccia is not None
    assert focaccia.name == "Rosemary Focaccia"
    assert focaccia.category.category_id == "antipasti"
    assert focaccia.unit_label == "piece"
    assert focaccia.price.amount_minor == 495
    assert focaccia.short_description == (
        "Olive oil focaccia with rosemary, sea salt, and a soft open crumb."
    )
    assert focaccia.tags == (
        "focaccia",
        "bread",
        "rosemary",
        "sharing",
        "vegan",
        "antipasti",
    )
    assert focaccia.facets.is_vegetarian
    assert focaccia.facets.is_vegan
    assert not focaccia.facets.is_gluten_free
    assert not focaccia.facets.contains_alcohol
    assert focaccia.image_id == focaccia.sku_id
    assert focaccia.display_order == 6

    assert pecorino is not None
    assert pecorino.name == "Pecorino Toscano"
    assert pecorino.category.category_id == "pantry"
    assert pecorino.unit_label == "200g"
    assert pecorino.price.amount_minor == 750
    assert pecorino.short_description == (
        "Firm Tuscan sheep's cheese with a nutty savoury finish."
    )
    assert pecorino.tags == (
        "cheese",
        "pecorino",
        "tuscan",
        "pantry",
        "pairing",
    )
    assert not pecorino.facets.is_vegetarian
    assert not pecorino.facets.is_vegan
    assert pecorino.facets.is_gluten_free
    assert not pecorino.facets.contains_alcohol
    assert pecorino.image_id == pecorino.sku_id
    assert pecorino.display_order == 4

    assert finocchiona is not None
    assert finocchiona.name == "Finocchiona Salami"
    assert finocchiona.category.category_id == "antipasti"
    assert finocchiona.unit_label == "100g"
    assert finocchiona.price.amount_minor == 695
    assert finocchiona.short_description == (
        "Tuscan fennel salami sliced for antipasti boards and aperitivo."
    )
    assert finocchiona.tags == (
        "salami",
        "fennel",
        "tuscan",
        "cured-meat",
        "antipasti",
        "aperitivo",
    )
    assert not finocchiona.facets.is_vegetarian
    assert not finocchiona.facets.is_vegan
    assert finocchiona.facets.is_gluten_free
    assert not finocchiona.facets.contains_alcohol
    assert finocchiona.image_id == finocchiona.sku_id
    assert finocchiona.display_order == 7

    assert cantucci is not None
    assert cantucci.name == "Cantucci Biscotti"
    assert cantucci.category.category_id == "desserts"
    assert cantucci.unit_label == "200g"
    assert cantucci.price.amount_minor == 525
    assert cantucci.short_description == (
        "Crunchy almond biscotti for coffee, dessert plates, and gifting."
    )
    assert cantucci.tags == (
        "biscotti",
        "cantucci",
        "almond",
        "dessert",
        "tuscan",
        "coffee",
    )
    assert cantucci.facets.is_vegetarian
    assert not cantucci.facets.is_vegan
    assert not cantucci.facets.is_gluten_free
    assert not cantucci.facets.contains_alcohol
    assert cantucci.image_id == cantucci.sku_id
    assert cantucci.display_order == 4


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


def test_seed_catalog_has_useful_dietary_facets() -> None:
    categories_with_vegetarian_sku = {
        sku.category.category_id for sku in SEED_CATALOG if sku.facets.is_vegetarian
    }
    categories_with_gluten_free_sku = {
        sku.category.category_id for sku in SEED_CATALOG if sku.facets.is_gluten_free
    }

    assert categories_with_vegetarian_sku == EXPECTED_CATEGORY_IDS
    assert {"antipasti", "drinks", "pantry"}.issubset(categories_with_gluten_free_sku)
    assert any(sku.facets.is_vegan for sku in SEED_CATALOG)
    assert any(sku.facets.contains_alcohol for sku in SEED_CATALOG)


def test_seed_catalog_image_ids_match_stable_sku_id() -> None:
    image_ids = [sku.image_id for sku in SEED_CATALOG]

    assert len(set(image_ids)) == len(SEED_CATALOG)
    assert image_ids == [sku.sku_id for sku in SEED_CATALOG]
