import pytest

from tavola.domain.basket import (
    MAX_BASKET_LINE_QUANTITY,
    Basket,
    BasketId,
    BasketLineNotFoundError,
    BasketValidationError,
)
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)


def make_sku(
    sku_id: str = "fresh-tagliatelle-250g",
    *,
    name: str = "Fresh Tagliatelle",
    category: CatalogCategory | None = None,
    amount_minor: int = 425,
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
        image_id=sku_id,
        display_order=1,
        is_available=True,
    )


def test_empty_basket_has_stable_identity_and_zero_totals() -> None:
    basket = Basket.empty(BasketId("basket-1"))

    assert basket.basket_id.value == "basket-1"
    assert basket.lines == ()
    assert basket.total.amount_minor == 0
    assert basket.total.currency == "GBP"
    assert basket.item_count == 0
    assert basket.line_count == 0


def test_basket_id_rejects_blank_values() -> None:
    with pytest.raises(ValueError, match="basket_id is required"):
        BasketId(" ")


def test_add_line_records_catalog_sku_snapshot_and_totals() -> None:
    sku = make_sku()

    basket = Basket.empty(BasketId("basket-1")).add_line(sku, quantity=2)

    assert basket.lines[0].sku == sku
    assert basket.lines[0].quantity == 2
    assert basket.lines[0].line_total.amount_minor == 850
    assert basket.total.amount_minor == 850
    assert basket.item_count == 2
    assert basket.line_count == 1


def test_adding_existing_sku_merges_into_one_line() -> None:
    sku = make_sku()

    basket = (
        Basket.empty(BasketId("basket-1"))
        .add_line(sku, quantity=2)
        .add_line(sku, quantity=3)
    )

    assert len(basket.lines) == 1
    assert basket.lines[0].quantity == 5
    assert basket.total.amount_minor == 2125
    assert basket.item_count == 5


def test_merged_quantity_cannot_exceed_maximum() -> None:
    sku = make_sku()
    basket = Basket.empty(BasketId("basket-1")).add_line(
        sku,
        quantity=MAX_BASKET_LINE_QUANTITY,
    )

    with pytest.raises(BasketValidationError, match="cannot exceed 10"):
        basket.add_line(sku, quantity=1)


def test_setting_line_quantity_replaces_exact_quantity() -> None:
    sku = make_sku()
    basket = Basket.empty(BasketId("basket-1")).add_line(sku, quantity=2)

    updated = basket.set_line_quantity(sku.sku_id, quantity=4)

    assert updated.lines[0].quantity == 4
    assert updated.total.amount_minor == 1700
    assert updated.item_count == 4


def test_removing_final_line_keeps_valid_empty_basket() -> None:
    sku = make_sku()
    basket = Basket.empty(BasketId("basket-1")).add_line(sku, quantity=1)

    updated = basket.remove_line(sku.sku_id)

    assert updated.basket_id == basket.basket_id
    assert updated.lines == ()
    assert updated.total.amount_minor == 0
    assert updated.item_count == 0


@pytest.mark.parametrize("quantity", [0, -1])
def test_quantity_must_be_positive(quantity: int) -> None:
    with pytest.raises(BasketValidationError, match="quantity must be positive"):
        Basket.empty(BasketId("basket-1")).add_line(make_sku(), quantity=quantity)


@pytest.mark.parametrize("quantity", [1.5, "2", True])
def test_quantity_must_be_an_integer(quantity: object) -> None:
    with pytest.raises(BasketValidationError, match="quantity must be an integer"):
        Basket.empty(BasketId("basket-1")).add_line(make_sku(), quantity=quantity)  # type: ignore[arg-type]


def test_quantity_cannot_exceed_maximum() -> None:
    with pytest.raises(BasketValidationError, match="cannot exceed 10"):
        Basket.empty(BasketId("basket-1")).add_line(
            make_sku(),
            quantity=MAX_BASKET_LINE_QUANTITY + 1,
        )


def test_setting_or_removing_missing_line_raises_clear_error() -> None:
    basket = Basket.empty(BasketId("basket-1"))

    with pytest.raises(BasketLineNotFoundError, match="basket line not found"):
        basket.set_line_quantity("fresh-tagliatelle-250g", quantity=1)

    with pytest.raises(BasketLineNotFoundError, match="basket line not found"):
        basket.remove_line("fresh-tagliatelle-250g")
