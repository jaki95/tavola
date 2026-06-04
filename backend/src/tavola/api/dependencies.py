from tavola.application.basket import BasketRepository
from tavola.application.catalog import CatalogRepository
from tavola.application.checkout import OrderRepository, PickupWindowRepository
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.checkout_repository import (
    InMemoryOrderRepository,
    StaticPickupWindowRepository,
)

_basket_repository = InMemoryBasketRepository()
_pickup_window_repository = StaticPickupWindowRepository.from_seed()
_order_repository = InMemoryOrderRepository()


def get_basket_repository() -> BasketRepository:
    return _basket_repository


def get_catalog_repository() -> CatalogRepository:
    return StaticCatalogRepository.from_seed()


def get_pickup_window_repository() -> PickupWindowRepository:
    return _pickup_window_repository


def get_order_repository() -> OrderRepository:
    return _order_repository
