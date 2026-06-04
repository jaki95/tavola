from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from tavola.api.dependencies import get_catalog_repository
from tavola.api.schemas.catalog import (
    CatalogCategoryResponse,
    CatalogListResponse,
    CatalogProductDetailResponse,
    CatalogProductSummaryResponse,
)
from tavola.application.catalog import (
    BrowseCatalog,
    CatalogRepository,
    GetCatalogSkuDetail,
)
from tavola.domain.catalog import catalog_categories

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=CatalogListResponse)
def browse_catalog(
    repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
    category: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
) -> CatalogListResponse:
    category_id = _normalize_category_query(category)
    result = BrowseCatalog(repository)(category_id=category_id, query=q)
    return CatalogListResponse(
        categories=[
            CatalogCategoryResponse.from_domain(category)
            for category in catalog_categories()
        ],
        products=[
            CatalogProductSummaryResponse.from_domain(product)
            for product in result.products
        ],
    )


@router.get("/products/{sku_id}", response_model=CatalogProductDetailResponse)
def get_catalog_product(
    sku_id: str,
    repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
) -> CatalogProductDetailResponse:
    sku = GetCatalogSkuDetail(repository)(sku_id)
    if sku is None:
        raise HTTPException(status_code=404, detail="Catalog product not found.")
    return CatalogProductDetailResponse.from_domain(sku)


def _normalize_category_query(category: str | None) -> str | None:
    if category is None:
        return None

    normalized = category.strip().casefold()
    category_ids = {category.category_id for category in catalog_categories()}
    if normalized not in category_ids:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "category"],
                    "msg": "Unsupported catalog category.",
                    "type": "value_error",
                }
            ],
        )
    return normalized
