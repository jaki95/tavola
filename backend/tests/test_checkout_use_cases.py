from dataclasses import dataclass

import pytest

from tavola.application.checkout import (
    CheckoutBasketNotFound,
    CheckoutBasketQuantityInvalid,
    CheckoutContactInvalid,
    CheckoutEmptyBasket,
    CheckoutPickupWindowNotFound,
    CheckoutSkuNotFound,
    CheckoutSkuUnavailable,
    CreateCheckoutOrder,
    ListPickupWindows,
)
from tavola.domain.basket import Basket, BasketId
from tavola.domain.catalog import CatalogCategory, CatalogSku, DietaryFacets, Money
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.checkout_repository import (
    InMemoryOrderRepository,
    StaticPickupWindowRepository,
)


def make_sku(
    sku_id: str = "fresh-tagliatelle-250g",
    *,
    name: str = "Fresh Tagliatelle",
    amount_minor: int = 425,
    is_available: bool = True,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name=name,
        category=CatalogCategory("primi", "Primi", 2),
        unit_label="250g",
        price=Money(amount_minor=amount_minor, currency="GBP"),
        short_description="Egg pasta cut fresh each morning.",
        detail_description="Silky ribbons of egg pasta for a quick supper.",
        tags=("pasta", "fresh"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id=sku_id,
        display_order=1,
        is_available=is_available,
    )


def make_checkout_use_case(
    *,
    basket_repository: InMemoryBasketRepository | None = None,
    catalog_repository: StaticCatalogRepository | None = None,
    pickup_window_repository: StaticPickupWindowRepository | None = None,
    order_repository: InMemoryOrderRepository | None = None,
) -> CreateCheckoutOrder:
    return CreateCheckoutOrder(
        basket_repository=basket_repository
        or InMemoryBasketRepository(id_generator=lambda: "basket-1"),
        catalog_repository=catalog_repository or StaticCatalogRepository([make_sku()]),
        pickup_window_repository=pickup_window_repository
        or StaticPickupWindowRepository.from_seed(),
        order_repository=order_repository
        or InMemoryOrderRepository(id_generator=lambda: "order-1"),
    )


def test_list_pickup_windows_returns_backend_defined_display_order() -> None:
    repository = StaticPickupWindowRepository.from_seed()

    result = ListPickupWindows(repository)()

    assert [window.display_order for window in result] == sorted(
        window.display_order for window in result
    )
    assert [window.pickup_window_id for window in result] == [
        "friday-afternoon",
        "saturday-midday",
        "sunday-morning",
    ]


def test_checkout_creates_order_from_current_catalog_and_clears_basket() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    stale_catalog = StaticCatalogRepository([make_sku(amount_minor=425)])
    current_catalog = StaticCatalogRepository([make_sku(amount_minor=500)])
    order_repository = InMemoryOrderRepository(id_generator=lambda: "order-1")
    basket = basket_repository.create_basket()
    stale_sku = stale_catalog.get_sku("fresh-tagliatelle-250g")
    assert stale_sku is not None
    basket_repository.save_basket(basket.add_line(stale_sku, quantity=2))

    result = CreateCheckoutOrder(
        basket_repository=basket_repository,
        catalog_repository=current_catalog,
        pickup_window_repository=StaticPickupWindowRepository.from_seed(),
        order_repository=order_repository,
    )(
        "basket-1",
        contact_name="Giulia Rossi",
        contact_email="giulia@example.com",
        pickup_window_id="friday-afternoon",
    )

    assert result.order.order_id.value == "order-1"
    assert result.order.basket_id == BasketId("basket-1")
    assert result.order.contact.name == "Giulia Rossi"
    assert result.order.pickup_window.pickup_window_id == "friday-afternoon"
    assert result.order.total.amount_minor == 1000
    assert result.order.item_count == 2
    assert result.order.lines[0].unit_price.amount_minor == 500
    assert result.order.lines[0].line_total.amount_minor == 1000
    assert order_repository.get_order(result.order.order_id) == result.order
    assert result.basket == Basket.empty(BasketId("basket-1"))
    assert basket_repository.get_basket(BasketId("basket-1")) == result.basket


def test_checkout_rejects_missing_basket() -> None:
    checkout = make_checkout_use_case()

    with pytest.raises(CheckoutBasketNotFound) as error:
        checkout(
            "missing-basket",
            contact_name="Giulia Rossi",
            contact_email="giulia@example.com",
            pickup_window_id="friday-afternoon",
        )

    assert error.value.code == "basket_not_found"


def test_checkout_rejects_empty_basket() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()

    with pytest.raises(CheckoutEmptyBasket) as error:
        make_checkout_use_case(basket_repository=basket_repository)(
            "basket-1",
            contact_name="Giulia Rossi",
            contact_email="giulia@example.com",
            pickup_window_id="friday-afternoon",
        )

    assert error.value.code == "empty_basket"


def test_checkout_rejects_missing_pickup_window() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket = basket_repository.create_basket()
    sku = make_sku()
    basket_repository.save_basket(basket.add_line(sku, quantity=1))

    with pytest.raises(CheckoutPickupWindowNotFound) as error:
        make_checkout_use_case(
            basket_repository=basket_repository,
            catalog_repository=StaticCatalogRepository([sku]),
        )(
            "basket-1",
            contact_name="Giulia Rossi",
            contact_email="giulia@example.com",
            pickup_window_id="missing-window",
        )

    assert error.value.code == "pickup_window_not_found"
    assert error.value.pickup_window_id == "missing-window"


@pytest.mark.parametrize(
    ("contact_name", "contact_email", "field"),
    [
        (" ", "giulia@example.com", "contact_name"),
        ("Giulia Rossi", "giulia.example.com", "contact_email"),
    ],
)
def test_checkout_rejects_invalid_contact_details(
    contact_name: str,
    contact_email: str,
    field: str,
) -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket = basket_repository.create_basket()
    sku = make_sku()
    basket_repository.save_basket(basket.add_line(sku, quantity=1))

    with pytest.raises(CheckoutContactInvalid) as error:
        make_checkout_use_case(
            basket_repository=basket_repository,
            catalog_repository=StaticCatalogRepository([sku]),
        )(
            "basket-1",
            contact_name=contact_name,
            contact_email=contact_email,
            pickup_window_id="friday-afternoon",
        )

    assert error.value.code == "invalid_contact_details"
    assert error.value.field == field


def test_checkout_rejects_missing_current_catalog_sku() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket = basket_repository.create_basket()
    basket_repository.save_basket(basket.add_line(make_sku(), quantity=1))

    with pytest.raises(CheckoutSkuNotFound) as error:
        make_checkout_use_case(
            basket_repository=basket_repository,
            catalog_repository=StaticCatalogRepository([]),
        )(
            "basket-1",
            contact_name="Giulia Rossi",
            contact_email="giulia@example.com",
            pickup_window_id="friday-afternoon",
        )

    assert error.value.code == "sku_not_found"
    assert error.value.sku_id == "fresh-tagliatelle-250g"


def test_checkout_rejects_unavailable_current_catalog_sku() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket = basket_repository.create_basket()
    basket_repository.save_basket(basket.add_line(make_sku(), quantity=1))

    with pytest.raises(CheckoutSkuUnavailable) as error:
        make_checkout_use_case(
            basket_repository=basket_repository,
            catalog_repository=StaticCatalogRepository([make_sku(is_available=False)]),
        )(
            "basket-1",
            contact_name="Giulia Rossi",
            contact_email="giulia@example.com",
            pickup_window_id="friday-afternoon",
        )

    assert error.value.code == "sku_unavailable"
    assert error.value.sku_id == "fresh-tagliatelle-250g"


@dataclass(frozen=True, slots=True)
class CorruptBasketLine:
    sku: CatalogSku
    quantity: int


@dataclass(frozen=True, slots=True)
class CorruptBasket:
    basket_id: BasketId
    lines: tuple[CorruptBasketLine, ...]


class CorruptBasketRepository:
    def __init__(self, basket: CorruptBasket) -> None:
        self.saved_basket: Basket | None = None
        self._basket = basket

    def create_basket(self) -> Basket:
        raise NotImplementedError

    def get_basket(self, basket_id: BasketId) -> CorruptBasket | None:
        if basket_id == self._basket.basket_id:
            return self._basket
        return None

    def save_basket(self, basket: Basket) -> None:
        self.saved_basket = basket


def test_checkout_rejects_basket_quantity_problems() -> None:
    sku = make_sku()
    basket_repository = CorruptBasketRepository(
        CorruptBasket(
            basket_id=BasketId("basket-1"),
            lines=(CorruptBasketLine(sku=sku, quantity=0),),
        )
    )

    with pytest.raises(CheckoutBasketQuantityInvalid) as error:
        make_checkout_use_case(
            basket_repository=basket_repository,  # type: ignore[arg-type]
            catalog_repository=StaticCatalogRepository([sku]),
        )(
            "basket-1",
            contact_name="Giulia Rossi",
            contact_email="giulia@example.com",
            pickup_window_id="friday-afternoon",
        )

    assert error.value.code == "invalid_basket_quantity"
    assert error.value.sku_id == "fresh-tagliatelle-250g"
