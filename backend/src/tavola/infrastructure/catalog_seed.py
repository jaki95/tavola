import json
from importlib.resources import files
from typing import Any

from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
    catalog_categories,
)

_DATA_PACKAGE = "tavola.infrastructure.data"
_CATALOG_RESOURCE = "catalog.json"
_CATEGORIES_BY_ID = {
    category.category_id: category for category in catalog_categories()
}


def load_seed_catalog() -> tuple[CatalogSku, ...]:
    raw = json.loads(
        files(_DATA_PACKAGE).joinpath(_CATALOG_RESOURCE).read_text(encoding="utf-8")
    )
    if not isinstance(raw, list):
        raise ValueError("catalog seed must be a list")

    return tuple(_catalog_sku_from_row(row) for row in raw)


def _catalog_sku_from_row(row: object) -> CatalogSku:
    if not isinstance(row, dict):
        raise ValueError("catalog seed rows must be objects")

    category = _category_from_id(_string_field(row, "category_id"))
    return CatalogSku(
        sku_id=_string_field(row, "sku_id"),
        name=_string_field(row, "name"),
        category=category,
        unit_label=_string_field(row, "unit_label"),
        price=Money(
            amount_minor=_int_field(row, "unit_price_minor"),
            currency=_string_field(row, "currency"),
        ),
        short_description=_string_field(row, "short_description"),
        detail_description=_string_field(row, "detail_description"),
        tags=_string_tuple_field(row, "tags"),
        facets=_dietary_facets(row.get("facets")),
        image_id=_string_field(row, "image_id"),
        display_order=_int_field(row, "display_order"),
        is_available=_bool_field(row, "is_available"),
    )


def _category_from_id(category_id: str) -> CatalogCategory:
    try:
        return _CATEGORIES_BY_ID[category_id]
    except KeyError as exc:
        raise ValueError(f"unsupported seed category_id: {category_id}") from exc


def _dietary_facets(raw: object) -> DietaryFacets:
    if not isinstance(raw, dict):
        raise ValueError("catalog seed facets must be an object")

    return DietaryFacets(
        is_vegetarian=_optional_bool_field(raw, "is_vegetarian"),
        is_vegan=_optional_bool_field(raw, "is_vegan"),
        is_gluten_free=_optional_bool_field(raw, "is_gluten_free"),
        contains_alcohol=_optional_bool_field(raw, "contains_alcohol"),
    )


def _string_field(row: dict[str, Any], field_name: str) -> str:
    value = row.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"catalog seed field {field_name} must be a string")
    return value


def _int_field(row: dict[str, Any], field_name: str) -> int:
    value = row.get(field_name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"catalog seed field {field_name} must be an integer")
    return value


def _bool_field(row: dict[str, Any], field_name: str) -> bool:
    value = row.get(field_name)
    if not isinstance(value, bool):
        raise ValueError(f"catalog seed field {field_name} must be a boolean")
    return value


def _optional_bool_field(row: dict[str, Any], field_name: str) -> bool:
    value = row.get(field_name, False)
    if not isinstance(value, bool):
        raise ValueError(f"catalog seed field {field_name} must be a boolean")
    return value


def _string_tuple_field(row: dict[str, Any], field_name: str) -> tuple[str, ...]:
    value = row.get(field_name)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"catalog seed field {field_name} must be a string list")
    return tuple(value)


SEED_CATALOG: tuple[CatalogSku, ...] = load_seed_catalog()
