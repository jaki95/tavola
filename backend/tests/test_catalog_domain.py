import pytest

from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)


def make_valid_sku(**overrides: object) -> CatalogSku:
    values: dict[str, object] = {
        "sku_id": "fresh-tagliatelle-250g",
        "name": "Fresh Tagliatelle",
        "category": CatalogCategory(
            category_id="primi",
            label="Primi",
            display_order=2,
        ),
        "unit_label": "250g",
        "price": Money(amount_minor=425, currency="GBP"),
        "short_description": "Egg pasta cut fresh each morning.",
        "detail_description": (
            "Silky ribbons of egg pasta made for a quick supper. Pair with a"
            " Tavola sugo or pesto."
        ),
        "tags": ("pasta", "fresh"),
        "facets": DietaryFacets(is_vegetarian=True),
        "image_id": "fresh-tagliatelle-250g",
        "display_order": 1,
        "is_available": True,
    }
    values.update(overrides)
    return CatalogSku(**values)


def test_catalog_sku_keeps_customer_facing_catalog_data() -> None:
    sku = make_valid_sku()

    assert sku.sku_id == "fresh-tagliatelle-250g"
    assert sku.price.amount_minor == 425
    assert sku.price.currency == "GBP"
    assert sku.category.category_id == "primi"
    assert sku.category.label == "Primi"
    assert sku.unit_label == "250g"
    assert sku.short_description == "Egg pasta cut fresh each morning."
    assert sku.detail_description.startswith("Silky ribbons")
    assert sku.tags == ("pasta", "fresh")
    assert sku.facets.is_vegetarian is True
    assert sku.facets.is_vegan is False
    assert sku.facets.is_gluten_free is False
    assert sku.facets.contains_alcohol is False
    assert sku.image_id == "fresh-tagliatelle-250g"
    assert sku.display_order == 1
    assert sku.is_available is True


@pytest.mark.parametrize(
    ("amount_minor", "currency", "message"),
    [
        (-1, "GBP", "amount_minor must be non-negative"),
        (100, "EUR", "currency must be GBP"),
        (100, "", "currency must be GBP"),
    ],
)
def test_money_rejects_invalid_values(
    amount_minor: int,
    currency: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        Money(amount_minor=amount_minor, currency=currency)


@pytest.mark.parametrize(
    ("category_id", "label", "display_order", "message"),
    [
        ("", "Primi", 2, "category_id is required"),
        ("primi", "", 2, "label is required"),
        ("starters", "Starters", 1, "unsupported category_id"),
        ("primi", "Pasta", 2, "label must be Primi"),
        ("primi", "Primi", 4, "display_order must be 2"),
    ],
)
def test_catalog_category_rejects_incoherent_values(
    category_id: str,
    label: str,
    display_order: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        CatalogCategory(
            category_id=category_id,
            label=label,
            display_order=display_order,
        )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        ("sku_id", "", "sku_id is required"),
        ("sku_id", "Fresh Tagliatelle", "sku_id must be a stable slug"),
        ("name", "", "name is required"),
        ("unit_label", "", "unit_label is required"),
        ("short_description", "", "short_description is required"),
        ("detail_description", "", "detail_description is required"),
        ("image_id", "", "image_id is required"),
        ("image_id", "Fresh Tagliatelle", "image_id must be a stable slug"),
        ("display_order", 0, "display_order must be positive"),
    ],
)
def test_catalog_sku_rejects_invalid_scalar_values(
    field_name: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        make_valid_sku(**{field_name: value})


@pytest.mark.parametrize(
    ("tags", "message"),
    [
        ((), "at least two tags are required"),
        (("pasta",), "at least two tags are required"),
        (("Fresh", "pasta"), "tags must be lower-case slugs"),
        (("fresh pasta", "egg"), "tags must be lower-case slugs"),
    ],
)
def test_catalog_sku_rejects_weak_tags(
    tags: tuple[str, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        make_valid_sku(tags=tags)
