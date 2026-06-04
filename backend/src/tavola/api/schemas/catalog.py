from pydantic import BaseModel

from tavola.domain.catalog import CatalogCategory, CatalogSku


class CatalogCategoryResponse(BaseModel):
    category_id: str
    label: str

    @classmethod
    def from_domain(cls, category: CatalogCategory) -> "CatalogCategoryResponse":
        return cls(category_id=category.category_id, label=category.label)


class CatalogProductSummaryResponse(BaseModel):
    sku_id: str
    name: str
    category_id: str
    category_label: str
    unit_label: str
    unit_price_minor: int
    currency: str
    short_description: str
    is_vegetarian: bool
    is_vegan: bool
    is_gluten_free: bool
    contains_alcohol: bool
    image_id: str

    @classmethod
    def from_domain(cls, sku: CatalogSku) -> "CatalogProductSummaryResponse":
        return cls(
            sku_id=sku.sku_id,
            name=sku.name,
            category_id=sku.category.category_id,
            category_label=sku.category.label,
            unit_label=sku.unit_label,
            unit_price_minor=sku.price.amount_minor,
            currency=sku.price.currency,
            short_description=sku.short_description,
            is_vegetarian=sku.facets.is_vegetarian,
            is_vegan=sku.facets.is_vegan,
            is_gluten_free=sku.facets.is_gluten_free,
            contains_alcohol=sku.facets.contains_alcohol,
            image_id=sku.image_id,
        )


class CatalogProductDetailResponse(CatalogProductSummaryResponse):
    detail_description: str

    @classmethod
    def from_domain(cls, sku: CatalogSku) -> "CatalogProductDetailResponse":
        summary = CatalogProductSummaryResponse.from_domain(sku)
        return cls(
            **summary.model_dump(),
            detail_description=sku.detail_description,
        )


class CatalogListResponse(BaseModel):
    categories: list[CatalogCategoryResponse]
    products: list[CatalogProductSummaryResponse]
