import re
from dataclasses import dataclass

SUPPORTED_CURRENCY = "GBP"
_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CATEGORY_DEFINITIONS = {
    "antipasti": ("Antipasti", 1),
    "primi": ("Primi", 2),
    "desserts": ("Desserts", 3),
    "drinks": ("Drinks", 4),
    "pantry": ("Pantry", 5),
}


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _require_slug(value: str, field_name: str) -> None:
    _require_text(value, field_name)
    if not _SLUG_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable slug")


@dataclass(frozen=True, slots=True)
class Money:
    amount_minor: int
    currency: str

    def __post_init__(self) -> None:
        if self.amount_minor < 0:
            raise ValueError("amount_minor must be non-negative")
        if self.currency != SUPPORTED_CURRENCY:
            raise ValueError(f"currency must be {SUPPORTED_CURRENCY}")


@dataclass(frozen=True, slots=True)
class CatalogCategory:
    category_id: str
    label: str
    display_order: int

    def __post_init__(self) -> None:
        _require_text(self.category_id, "category_id")
        _require_text(self.label, "label")

        if self.category_id not in _CATEGORY_DEFINITIONS:
            raise ValueError(f"unsupported category_id: {self.category_id}")

        expected_label, expected_order = _CATEGORY_DEFINITIONS[self.category_id]
        if self.label != expected_label:
            raise ValueError(f"label must be {expected_label}")
        if self.display_order != expected_order:
            raise ValueError(f"display_order must be {expected_order}")


def catalog_categories() -> tuple[CatalogCategory, ...]:
    return tuple(
        CatalogCategory(category_id, label, display_order)
        for category_id, (label, display_order) in sorted(
            _CATEGORY_DEFINITIONS.items(),
            key=lambda item: item[1][1],
        )
    )


@dataclass(frozen=True, slots=True)
class DietaryFacets:
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_gluten_free: bool = False
    contains_alcohol: bool = False

    def __post_init__(self) -> None:
        if self.is_vegan and not self.is_vegetarian:
            raise ValueError("vegan SKUs must also be vegetarian")


@dataclass(frozen=True, slots=True)
class CatalogSku:
    sku_id: str
    name: str
    category: CatalogCategory
    unit_label: str
    price: Money
    short_description: str
    detail_description: str
    tags: tuple[str, ...]
    facets: DietaryFacets
    image_id: str
    display_order: int
    is_available: bool

    def __post_init__(self) -> None:
        _require_slug(self.sku_id, "sku_id")
        _require_text(self.name, "name")
        _require_text(self.unit_label, "unit_label")
        _require_text(self.short_description, "short_description")
        _require_text(self.detail_description, "detail_description")
        _require_slug(self.image_id, "image_id")

        if self.display_order <= 0:
            raise ValueError("display_order must be positive")
        if len(self.tags) < 2:
            raise ValueError("at least two tags are required")
        if any(not _SLUG_PATTERN.fullmatch(tag) for tag in self.tags):
            raise ValueError("tags must be lower-case slugs")
