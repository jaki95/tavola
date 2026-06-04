from typing import Protocol

from tavola.domain.catalog import CatalogSku


class CatalogRepository(Protocol):
    def list_skus(self) -> tuple[CatalogSku, ...]:
        """Return catalog SKUs in customer-facing display order."""

    def get_sku(self, sku_id: str) -> CatalogSku | None:
        """Return one SKU, or None when the catalog identity is unknown."""
