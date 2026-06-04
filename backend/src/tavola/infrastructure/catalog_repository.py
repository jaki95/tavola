from collections.abc import Iterable

from tavola.domain.catalog import CatalogSku


class StaticCatalogRepository:
    def __init__(self, skus: Iterable[CatalogSku]) -> None:
        self._skus = tuple(
            sorted(
                skus,
                key=lambda sku: (sku.category.display_order, sku.display_order),
            )
        )
        self._skus_by_id = {sku.sku_id: sku for sku in self._skus}

    @classmethod
    def from_seed(cls) -> "StaticCatalogRepository":
        from tavola.infrastructure.catalog_seed import SEED_CATALOG

        return cls(SEED_CATALOG)

    def list_skus(self) -> tuple[CatalogSku, ...]:
        return self._skus

    def get_sku(self, sku_id: str) -> CatalogSku | None:
        return self._skus_by_id.get(sku_id)
