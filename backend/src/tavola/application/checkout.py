from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from tavola.application.basket import BasketRepository
from tavola.application.catalog import CatalogRepository
from tavola.domain.basket import Basket, BasketId
from tavola.domain.checkout import (
    ContactDetails,
    Order,
    OrderId,
    OrderLine,
    PickupWindow,
)


class PickupWindowRepository(Protocol):
    def list_pickup_windows(self) -> tuple[PickupWindow, ...]:
        """Return backend-defined pickup windows in display order."""

    def get_pickup_window(self, pickup_window_id: str) -> PickupWindow | None:
        """Return one pickup window, or None when the choice is unknown."""


class OrderRepository(Protocol):
    def create_order(
        self,
        *,
        basket_id: BasketId,
        contact_details: ContactDetails,
        pickup_window: PickupWindow,
        lines: Iterable[OrderLine],
    ) -> Order:
        """Create and persist an order with a repository-owned identifier."""

    def get_order(self, order_id: OrderId) -> Order | None:
        """Return one order, or None when the order is unknown."""

    def save_order(self, order: Order) -> None:
        """Persist the latest order state."""


@dataclass(frozen=True, slots=True)
class CheckoutResult:
    order: Order
    basket: Basket


class CheckoutApplicationError(Exception):
    code = "checkout_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CheckoutBasketNotFound(CheckoutApplicationError):
    code = "basket_not_found"

    def __init__(self, basket_id: str) -> None:
        self.basket_id = basket_id
        super().__init__("basket not found")


class CheckoutEmptyBasket(CheckoutApplicationError):
    code = "empty_basket"

    def __init__(self, basket_id: str) -> None:
        self.basket_id = basket_id
        super().__init__("basket is empty")


class CheckoutPickupWindowNotFound(CheckoutApplicationError):
    code = "pickup_window_not_found"

    def __init__(self, pickup_window_id: str) -> None:
        self.pickup_window_id = pickup_window_id
        super().__init__("pickup window not found")


class CheckoutContactInvalid(CheckoutApplicationError):
    code = "invalid_contact_details"

    def __init__(self, *, field: str) -> None:
        self.field = field
        super().__init__("contact details are invalid")


class CheckoutSkuNotFound(CheckoutApplicationError):
    code = "sku_not_found"

    def __init__(self, sku_id: str) -> None:
        self.sku_id = sku_id
        super().__init__("SKU not found")


class CheckoutSkuUnavailable(CheckoutApplicationError):
    code = "sku_unavailable"

    def __init__(self, sku_id: str) -> None:
        self.sku_id = sku_id
        super().__init__("SKU is unavailable")


class CheckoutBasketQuantityInvalid(CheckoutApplicationError):
    code = "invalid_basket_quantity"

    def __init__(self, sku_id: str) -> None:
        self.sku_id = sku_id
        super().__init__("basket quantity is invalid")


class ListPickupWindows:
    def __init__(self, repository: PickupWindowRepository) -> None:
        self._repository = repository

    def __call__(self) -> tuple[PickupWindow, ...]:
        return self._repository.list_pickup_windows()


class CreateCheckoutOrder:
    def __init__(
        self,
        *,
        basket_repository: BasketRepository,
        catalog_repository: CatalogRepository,
        pickup_window_repository: PickupWindowRepository,
        order_repository: OrderRepository,
    ) -> None:
        self._basket_repository = basket_repository
        self._catalog_repository = catalog_repository
        self._pickup_window_repository = pickup_window_repository
        self._order_repository = order_repository

    def __call__(
        self,
        basket_id: str,
        *,
        contact_name: str,
        contact_email: str,
        pickup_window_id: str,
    ) -> CheckoutResult:
        basket = self._get_basket(basket_id)
        if not basket.lines:
            raise CheckoutEmptyBasket(basket_id)

        pickup_window = self._pickup_window_repository.get_pickup_window(
            pickup_window_id
        )
        if pickup_window is None:
            raise CheckoutPickupWindowNotFound(pickup_window_id)

        try:
            contact_details = ContactDetails(name=contact_name, email=contact_email)
        except ValueError as error:
            raise CheckoutContactInvalid(field=_contact_error_field(error)) from error

        order_lines = tuple(self._create_order_line(line) for line in basket.lines)
        order = self._order_repository.create_order(
            basket_id=basket.basket_id,
            contact_details=contact_details,
            pickup_window=pickup_window,
            lines=order_lines,
        )
        empty_basket = Basket.empty(basket.basket_id)
        self._basket_repository.save_basket(empty_basket)
        return CheckoutResult(order=order, basket=empty_basket)

    def _get_basket(self, basket_id: str) -> Basket:
        try:
            parsed_basket_id = BasketId(basket_id)
        except ValueError as error:
            raise CheckoutBasketNotFound(basket_id) from error

        basket = self._basket_repository.get_basket(parsed_basket_id)
        if basket is None:
            raise CheckoutBasketNotFound(basket_id)
        return basket

    def _create_order_line(self, basket_line: object) -> OrderLine:
        sku_id = basket_line.sku.sku_id
        current_sku = self._catalog_repository.get_sku(sku_id)
        if current_sku is None:
            raise CheckoutSkuNotFound(sku_id)
        if not current_sku.is_available:
            raise CheckoutSkuUnavailable(sku_id)

        try:
            return OrderLine.from_sku(current_sku, quantity=basket_line.quantity)
        except ValueError as error:
            raise CheckoutBasketQuantityInvalid(sku_id) from error


def _contact_error_field(error: ValueError) -> str:
    message = str(error)
    if "contact_email" in message:
        return "contact_email"
    return "contact_name"
