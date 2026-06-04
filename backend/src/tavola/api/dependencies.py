from tavola.application.catalog import CatalogRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository


def get_catalog_repository() -> CatalogRepository:
    return StaticCatalogRepository.from_seed()
