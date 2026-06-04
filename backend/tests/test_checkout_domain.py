import inspect

import pytest

import tavola.domain.checkout as checkout
from tavola.domain.basket import BasketId
from tavola.domain.catalog import CatalogCategory, CatalogSku, DietaryFacets, Money
from tavola.domain.checkout import (
    ContactDetails,
    Order,
    OrderId,
    OrderLine,
    PickupWindow,
)


def make_sku(
    sku_id: str = "fresh-tagliatelle-250g",
    *,
    name: str = "Fresh Tagliatelle",
    category: CatalogCategory | None = None,
    amount_minor: int = 425,
    image_id: str | None = None,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name=name,
        category=category or CatalogCategory("primi", "Primi", 2),
        unit_label="250g",
        price=Money(amount_minor=amount_minor, currency="GBP"),
        short_description="Egg pasta cut fresh each morning.",
        detail_description="Silky ribbons of egg pasta for a quick supper.",
        tags=("pasta", "fresh"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id=image_id or sku_id,
        display_order=1,
        is_available=True,
    )


def make_pickup_window(**overrides: object) -> PickupWindow:
    values: dict[str, object] = {
        "pickup_window_id": "friday-afternoon",
        "label": "Friday afternoon",
        "display_order": 1,
    }
    values.update(overrides)
    return PickupWindow(**values)


def make_order_line(
    sku: CatalogSku | None = None,
    *,
    quantity: int = 2,
    line_total: Money | None = None,
) -> OrderLine:
    sku = sku or make_sku()
    return OrderLine.from_sku(
        sku,
        quantity=quantity,
        line_total=line_total,
    )


def test_order_keeps_checkout_snapshot_and_calculated_totals() -> None:
    antipasti = CatalogCategory("antipasti", "Antipasti", 1)
    tagliatelle = make_sku()
    olives = make_sku(
        "nocellara-olives-250g",
        name="Nocellara Olives",
        category=antipasti,
        amount_minor=525,
    )

    order = Order(
        order_id=OrderId("TVL-1001"),
        basket_id=BasketId("basket-1"),
        contact=ContactDetails(name="Ada Lovelace", email="ada@example.com"),
        pickup_window=make_pickup_window(),
        lines=(
            make_order_line(tagliatelle, quantity=2),
            make_order_line(olives, quantity=1),
        ),
    )

    assert order.order_id.value == "TVL-1001"
    assert order.basket_id.value == "basket-1"
    assert order.contact.name == "Ada Lovelace"
    assert order.contact.email == "ada@example.com"
    assert order.pickup_window.label == "Friday afternoon"
    assert order.total.amount_minor == 1375
    assert order.total.currency == "GBP"
    assert order.item_count == 3
    assert order.line_count == 2

    first_line = order.lines[0]
    assert first_line.sku_id == "fresh-tagliatelle-250g"
    assert first_line.name == "Fresh Tagliatelle"
    assert first_line.category_id == "primi"
    assert first_line.category_label == "Primi"
    assert first_line.unit_label == "250g"
    assert first_line.quantity == 2
    assert first_line.unit_price.amount_minor == 425
    assert first_line.line_total.amount_minor == 850
    assert first_line.currency == "GBP"
    assert first_line.image_id == "fresh-tagliatelle-250g"


def test_checkout_domain_imports_no_transport_validation_frameworks() -> None:
    source = inspect.getsource(checkout)

    assert "fastapi" not in source.lower()
    assert "pydantic" not in source.lower()


@pytest.mark.parametrize(
    ("name", "email", "message"),
    [
        (" ", "ada@example.com", "contact_name is required"),
        ("Ada Lovelace", "", "contact_email is required"),
        ("Ada Lovelace", "ada.example.com", "contact_email must contain text"),
        ("Ada Lovelace", "@example.com", "contact_email must contain text"),
        ("Ada Lovelace", "ada@", "contact_email must contain text"),
    ],
)
def test_contact_details_reject_missing_or_weak_email_values(
    name: str,
    email: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ContactDetails(name=name, email=email)


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        ("pickup_window_id", "", "pickup_window_id is required"),
        (
            "pickup_window_id",
            "Friday Afternoon",
            "pickup_window_id must be a stable slug",
        ),
        ("label", "", "label is required"),
        ("display_order", 0, "display_order must be positive"),
    ],
)
def test_pickup_window_rejects_unstable_or_missing_values(
    field_name: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        make_pickup_window(**{field_name: value})


def test_order_id_rejects_blank_values() -> None:
    with pytest.raises(ValueError, match="order_id is required"):
        OrderId(" ")


def test_order_rejects_empty_line_lists() -> None:
    with pytest.raises(ValueError, match="order lines are required"):
        Order(
            order_id=OrderId("TVL-1001"),
            basket_id=BasketId("basket-1"),
            contact=ContactDetails(name="Ada Lovelace", email="ada@example.com"),
            pickup_window=make_pickup_window(),
            lines=(),
        )


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_line_quantity_must_be_positive(quantity: int) -> None:
    with pytest.raises(ValueError, match="quantity must be positive"):
        make_order_line(quantity=quantity)


def test_order_line_total_must_match_unit_price_and_quantity() -> None:
    with pytest.raises(
        ValueError, match="line_total must match unit price and quantity"
    ):
        make_order_line(
            quantity=2,
            line_total=Money(amount_minor=851, currency="GBP"),
        )
