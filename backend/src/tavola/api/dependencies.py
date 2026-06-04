from tavola.application.basket import BasketRepository
from tavola.application.catalog import CatalogRepository
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository

_basket_repository = InMemoryBasketRepository()


def get_basket_repository() -> BasketRepository:
    return _basket_repository


def get_catalog_repository() -> CatalogRepository:
    return StaticCatalogRepository.from_seed()
