from dataclasses import dataclass
from typing import Protocol

from tavola.domain.catalog import CatalogSku


class CatalogRepository(Protocol):
    def list_skus(self) -> tuple[CatalogSku, ...]:
        """Return catalog SKUs in customer-facing display order."""

    def get_sku(self, sku_id: str) -> CatalogSku | None:
        """Return one SKU, or None when the catalog identity is unknown."""


@dataclass(frozen=True, slots=True)
class CatalogBrowseResult:
    products: tuple[CatalogSku, ...]


class BrowseCatalog:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    def __call__(
        self,
        *,
        category_id: str | None = None,
        query: str | None = None,
    ) -> CatalogBrowseResult:
        search_tokens = _normalize_search_tokens(query)
        products = tuple(
            sku
            for sku in self._repository.list_skus()
            if sku.is_available
            and (category_id is None or sku.category.category_id == category_id)
            and _matches_search(sku, search_tokens)
        )
        return CatalogBrowseResult(products)


class GetCatalogSkuDetail:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    def __call__(self, sku_id: str) -> CatalogSku | None:
        sku = self._repository.get_sku(sku_id)
        if sku is None or not sku.is_available:
            return None
        return sku


def _normalize_search_tokens(query: str | None) -> tuple[str, ...]:
    if query is None:
        return ()
    return tuple(query.casefold().split())


def _matches_search(sku: CatalogSku, search_tokens: tuple[str, ...]) -> bool:
    if not search_tokens:
        return True

    searchable_text = " ".join(
        (
            sku.name,
            sku.category.label,
            sku.short_description,
            *sku.tags,
            *_positive_facet_terms(sku),
        )
    ).casefold()
    return all(token in searchable_text for token in search_tokens)


def _positive_facet_terms(sku: CatalogSku) -> tuple[str, ...]:
    terms = []
    if sku.facets.is_vegetarian:
        terms.append("vegetarian")
    if sku.facets.is_vegan:
        terms.append("vegan")
    if sku.facets.is_gluten_free:
        terms.extend(("gluten free", "gluten-free"))
    if sku.facets.contains_alcohol:
        terms.append("contains alcohol")
    return tuple(terms)
