from dataclasses import dataclass
from typing import Literal, Protocol

from tavola.domain.catalog import (
    CatalogSku,
    catalog_category_ids,
    catalog_dietary_facet_ids,
)

CatalogTagMatch = Literal["any", "all"]
CatalogAlcoholFilter = Literal["include", "exclude", "only"]
DEFAULT_CATALOG_CANDIDATE_LIMIT = 8
MAX_CATALOG_CANDIDATE_LIMIT = 20


class CatalogRepository(Protocol):
    def list_skus(self) -> tuple[CatalogSku, ...]:
        """Return catalog SKUs in customer-facing display order."""

    def get_sku(self, sku_id: str) -> CatalogSku | None:
        """Return one SKU, or None when the catalog identity is unknown."""


@dataclass(frozen=True, slots=True)
class CatalogBrowseResult:
    products: tuple[CatalogSku, ...]


@dataclass(frozen=True, slots=True)
class CatalogTagVocabularyResult:
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FindCatalogCandidatesInput:
    category_ids: tuple[str, ...] = ()
    dietary_facets: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    tag_match: CatalogTagMatch = "any"
    alcohol: CatalogAlcoholFilter = "include"
    max_results: int = DEFAULT_CATALOG_CANDIDATE_LIMIT


@dataclass(frozen=True, slots=True)
class CatalogCandidatesResult:
    products: tuple[CatalogSku, ...]
    result_count: int


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


class ListAvailableCatalogTags:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    def __call__(self) -> CatalogTagVocabularyResult:
        tags = {
            tag
            for sku in self._repository.list_skus()
            if sku.is_available
            for tag in sku.tags
        }
        return CatalogTagVocabularyResult(tuple(sorted(tags)))


class FindCatalogCandidates:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    def __call__(
        self,
        filters: FindCatalogCandidatesInput | None = None,
    ) -> CatalogCandidatesResult:
        resolved_filters = filters or FindCatalogCandidatesInput()
        _validate_candidate_filters(resolved_filters)
        matches = tuple(
            sku
            for sku in self._repository.list_skus()
            if sku.is_available
            and _matches_candidate_categories(sku, resolved_filters.category_ids)
            and _matches_candidate_dietary_facets(sku, resolved_filters.dietary_facets)
            and _matches_candidate_tags(
                sku,
                resolved_filters.tags,
                resolved_filters.tag_match,
            )
            and _matches_candidate_alcohol(sku, resolved_filters.alcohol)
        )
        max_results = _clamp_candidate_limit(resolved_filters.max_results)
        return CatalogCandidatesResult(
            products=matches[:max_results],
            result_count=len(matches),
        )


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


def _validate_candidate_filters(filters: FindCatalogCandidatesInput) -> None:
    unknown_categories = set(filters.category_ids) - set(catalog_category_ids())
    if unknown_categories:
        raise ValueError(f"unsupported category_ids: {sorted(unknown_categories)}")

    unknown_facets = set(filters.dietary_facets) - set(catalog_dietary_facet_ids())
    if unknown_facets:
        raise ValueError(f"unsupported dietary_facets: {sorted(unknown_facets)}")

    if filters.tag_match not in ("any", "all"):
        raise ValueError("tag_match must be any or all")
    if filters.alcohol not in ("include", "exclude", "only"):
        raise ValueError("alcohol must be include, exclude, or only")


def _matches_candidate_categories(
    sku: CatalogSku,
    category_ids: tuple[str, ...],
) -> bool:
    if not category_ids:
        return True
    return sku.category.category_id in category_ids


def _matches_candidate_dietary_facets(
    sku: CatalogSku,
    dietary_facets: tuple[str, ...],
) -> bool:
    return all(
        _has_dietary_facet(sku, dietary_facet) for dietary_facet in dietary_facets
    )


def _has_dietary_facet(sku: CatalogSku, dietary_facet: str) -> bool:
    if dietary_facet == "vegetarian":
        return sku.facets.is_vegetarian
    if dietary_facet == "vegan":
        return sku.facets.is_vegan
    if dietary_facet == "gluten_free":
        return sku.facets.is_gluten_free
    return False


def _matches_candidate_tags(
    sku: CatalogSku,
    tags: tuple[str, ...],
    tag_match: CatalogTagMatch,
) -> bool:
    if not tags:
        return True

    sku_tags = set(sku.tags)
    if tag_match == "all":
        return set(tags).issubset(sku_tags)
    return any(tag in sku_tags for tag in tags)


def _matches_candidate_alcohol(
    sku: CatalogSku,
    alcohol: CatalogAlcoholFilter,
) -> bool:
    if alcohol == "exclude":
        return not sku.facets.contains_alcohol
    if alcohol == "only":
        return sku.facets.contains_alcohol
    return True


def _clamp_candidate_limit(max_results: int) -> int:
    return min(max(max_results, 1), MAX_CATALOG_CANDIDATE_LIMIT)
