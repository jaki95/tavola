import re
from dataclasses import dataclass

from tavola.domain.basket import BasketId
from tavola.domain.catalog import CatalogSku, Money

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _require_slug(value: str, field_name: str) -> None:
    _require_text(value, field_name)
    if not _SLUG_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable slug")


def _validate_quantity(quantity: int) -> None:
    if type(quantity) is not int:
        raise ValueError("quantity must be an integer")
    if quantity <= 0:
        raise ValueError("quantity must be positive")


@dataclass(frozen=True, slots=True)
class OrderId:
    value: str

    def __post_init__(self) -> None:
        _require_text(self.value, "order_id")


@dataclass(frozen=True, slots=True)
class PickupWindow:
    pickup_window_id: str
    label: str
    display_order: int

    def __post_init__(self) -> None:
        _require_slug(self.pickup_window_id, "pickup_window_id")
        _require_text(self.label, "label")
        if self.display_order <= 0:
            raise ValueError("display_order must be positive")


@dataclass(frozen=True, slots=True)
class ContactDetails:
    name: str
    email: str

    def __post_init__(self) -> None:
        _require_text(self.name, "contact_name")
        _require_text(self.email, "contact_email")
        if not _has_basic_email_separator(self.email):
            raise ValueError("contact_email must contain text before and after @")


@dataclass(frozen=True, slots=True)
class OrderLine:
    sku_id: str
    name: str
    category_id: str
    category_label: str
    unit_label: str
    quantity: int
    unit_price: Money
    line_total: Money
    image_id: str

    @classmethod
    def from_sku(
        cls,
        sku: CatalogSku,
        *,
        quantity: int,
        line_total: Money | None = None,
    ) -> "OrderLine":
        _validate_quantity(quantity)
        return cls(
            sku_id=sku.sku_id,
            name=sku.name,
            category_id=sku.category.category_id,
            category_label=sku.category.label,
            unit_label=sku.unit_label,
            quantity=quantity,
            unit_price=sku.price,
            line_total=line_total
            or Money(
                amount_minor=sku.price.amount_minor * quantity,
                currency=sku.price.currency,
            ),
            image_id=sku.image_id,
        )

    @property
    def currency(self) -> str:
        return self.unit_price.currency

    def __post_init__(self) -> None:
        _require_text(self.sku_id, "sku_id")
        _require_text(self.name, "name")
        _require_text(self.category_id, "category_id")
        _require_text(self.category_label, "category_label")
        _require_text(self.unit_label, "unit_label")
        _require_text(self.image_id, "image_id")
        _validate_quantity(self.quantity)

        expected_total = self.unit_price.amount_minor * self.quantity
        if self.line_total.currency != self.unit_price.currency:
            raise ValueError("line_total currency must match unit_price currency")
        if self.line_total.amount_minor != expected_total:
            raise ValueError("line_total must match unit price and quantity")


@dataclass(frozen=True, slots=True)
class Order:
    order_id: OrderId
    basket_id: BasketId
    contact: ContactDetails
    pickup_window: PickupWindow
    lines: tuple[OrderLine, ...]

    def __post_init__(self) -> None:
        if not self.lines:
            raise ValueError("order lines are required")

    @property
    def total(self) -> Money:
        return Money(
            amount_minor=sum(line.line_total.amount_minor for line in self.lines),
            currency=self.currency,
        )

    @property
    def currency(self) -> str:
        return self.lines[0].currency

    @property
    def item_count(self) -> int:
        return sum(line.quantity for line in self.lines)

    @property
    def line_count(self) -> int:
        return len(self.lines)


def _has_basic_email_separator(email: str) -> bool:
    local, separator, domain = email.strip().partition("@")
    return bool(local and separator and domain)
