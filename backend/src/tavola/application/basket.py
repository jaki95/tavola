from typing import Protocol

from tavola.application.catalog import CatalogRepository
from tavola.domain.basket import (
    Basket,
    BasketId,
    BasketLineNotFoundError,
    BasketQuantityExceededError,
    BasketQuantityNotPositiveError,
)


class BasketRepository(Protocol):
    def create_basket(self) -> Basket:
        """Create and persist an empty basket."""

    def get_basket(self, basket_id: BasketId) -> Basket | None:
        """Return one basket, or None when the basket is unknown."""

    def save_basket(self, basket: Basket) -> None:
        """Persist the latest basket state."""


class BasketApplicationError(Exception):
    code = "basket_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class BasketNotFound(BasketApplicationError):
    code = "basket_not_found"

    def __init__(self, basket_id: str) -> None:
        self.basket_id = basket_id
        super().__init__("basket not found")


class BasketLineNotFound(BasketApplicationError):
    code = "line_not_found"

    def __init__(self, sku_id: str) -> None:
        self.sku_id = sku_id
        super().__init__("basket line not found")


class BasketSkuNotFound(BasketApplicationError):
    code = "sku_not_found"

    def __init__(self, sku_id: str) -> None:
        self.sku_id = sku_id
        super().__init__("SKU not found")


class BasketSkuUnavailable(BasketApplicationError):
    code = "sku_unavailable"

    def __init__(self, sku_id: str) -> None:
        self.sku_id = sku_id
        super().__init__("SKU is unavailable")


class BasketQuantityInvalid(BasketApplicationError):
    code = "invalid_quantity"

    def __init__(self) -> None:
        super().__init__("quantity must be positive")


class BasketQuantityExceeded(BasketApplicationError):
    code = "quantity_exceeds_max"

    def __init__(self, max_quantity: int) -> None:
        self.max_quantity = max_quantity
        super().__init__(f"quantity cannot exceed {max_quantity}")


class CreateBasket:
    def __init__(self, repository: BasketRepository) -> None:
        self._repository = repository

    def __call__(self) -> Basket:
        return self._repository.create_basket()


class GetBasket:
    def __init__(self, repository: BasketRepository) -> None:
        self._repository = repository

    def __call__(self, basket_id: str) -> Basket:
        return _get_basket_or_raise(self._repository, basket_id)


class AddBasketLine:
    def __init__(
        self,
        basket_repository: BasketRepository,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._basket_repository = basket_repository
        self._catalog_repository = catalog_repository

    def __call__(self, basket_id: str, *, sku_id: str, quantity: int) -> Basket:
        basket = _get_basket_or_raise(self._basket_repository, basket_id)
        sku = self._catalog_repository.get_sku(sku_id)
        if sku is None:
            raise BasketSkuNotFound(sku_id)
        if not sku.is_available:
            raise BasketSkuUnavailable(sku_id)

        try:
            updated = basket.add_line(sku, quantity=quantity)
        except BasketQuantityNotPositiveError as error:
            raise BasketQuantityInvalid() from error
        except BasketQuantityExceededError as error:
            raise BasketQuantityExceeded(error.max_quantity) from error

        self._basket_repository.save_basket(updated)
        return updated


class SetBasketLineQuantity:
    def __init__(self, repository: BasketRepository) -> None:
        self._repository = repository

    def __call__(self, basket_id: str, *, sku_id: str, quantity: int) -> Basket:
        basket = _get_basket_or_raise(self._repository, basket_id)

        try:
            updated = basket.set_line_quantity(sku_id, quantity=quantity)
        except BasketQuantityNotPositiveError as error:
            raise BasketQuantityInvalid() from error
        except BasketQuantityExceededError as error:
            raise BasketQuantityExceeded(error.max_quantity) from error
        except BasketLineNotFoundError as error:
            raise BasketLineNotFound(sku_id) from error

        self._repository.save_basket(updated)
        return updated


class RemoveBasketLine:
    def __init__(self, repository: BasketRepository) -> None:
        self._repository = repository

    def __call__(self, basket_id: str, *, sku_id: str) -> Basket:
        basket = _get_basket_or_raise(self._repository, basket_id)

        try:
            updated = basket.remove_line(sku_id)
        except BasketLineNotFoundError as error:
            raise BasketLineNotFound(sku_id) from error

        self._repository.save_basket(updated)
        return updated


def _get_basket_or_raise(repository: BasketRepository, basket_id: str) -> Basket:
    basket = repository.get_basket(BasketId(basket_id))
    if basket is None:
        raise BasketNotFound(basket_id)
    return basket
