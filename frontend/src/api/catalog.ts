import { apiGetJson, type ApiError, type ApiResult } from "./client";
import {
  catalogCategoryIds,
  type CatalogCategory,
  type CatalogCategoryId,
  type CatalogFilters,
  type CatalogListResponse,
  type CatalogProductDetail,
  type CatalogProductSummary
} from "../types/catalog";

type CatalogRequestFilters = Partial<CatalogFilters>;

const catalogCategoryIdSet = new Set<string>(catalogCategoryIds);

export async function getCatalog(
  filters: CatalogRequestFilters = {}
): Promise<ApiResult<CatalogListResponse>> {
  const result = await apiGetJson<unknown>(buildCatalogPath(filters));

  if (!result.ok) {
    return result;
  }

  if (isCatalogListResponse(result.data)) {
    return {
      ok: true,
      data: result.data
    };
  }

  return {
    ok: false,
    error: invalidCatalogResponseError
  };
}

export async function getCatalogProduct(
  skuId: string
): Promise<ApiResult<CatalogProductDetail>> {
  const result = await apiGetJson<unknown>(
    `/catalog/products/${encodeURIComponent(skuId)}`
  );

  if (!result.ok) {
    return result;
  }

  if (isCatalogProductDetail(result.data)) {
    return {
      ok: true,
      data: result.data
    };
  }

  return {
    ok: false,
    error: invalidCatalogProductResponseError
  };
}

function buildCatalogPath(filters: CatalogRequestFilters): string {
  const params = new URLSearchParams();

  if (filters.category_id !== null && filters.category_id !== undefined) {
    params.set("category", filters.category_id);
  }

  const query = filters.query?.trim();
  if (query) {
    params.set("q", query);
  }

  const queryString = params.toString();
  return queryString ? `/catalog?${queryString}` : "/catalog";
}

function isCatalogListResponse(value: unknown): value is CatalogListResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    Array.isArray(value["categories"]) &&
    value["categories"].every(isCatalogCategory) &&
    Array.isArray(value["products"]) &&
    value["products"].every(isCatalogProductSummary)
  );
}

function isCatalogCategory(value: unknown): value is CatalogCategory {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isCatalogCategoryId(value["category_id"]) && typeof value["label"] === "string"
  );
}

function isCatalogProductDetail(value: unknown): value is CatalogProductDetail {
  if (!isRecord(value)) {
    return false;
  }

  const detailDescription = value["detail_description"];

  return isCatalogProductSummary(value) && typeof detailDescription === "string";
}

function isCatalogProductSummary(value: unknown): value is CatalogProductSummary {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value["sku_id"] === "string" &&
    typeof value["name"] === "string" &&
    isCatalogCategoryId(value["category_id"]) &&
    typeof value["category_label"] === "string" &&
    typeof value["unit_label"] === "string" &&
    isMinorUnitAmount(value["unit_price_minor"]) &&
    typeof value["currency"] === "string" &&
    typeof value["short_description"] === "string" &&
    typeof value["is_vegetarian"] === "boolean" &&
    typeof value["is_vegan"] === "boolean" &&
    typeof value["is_gluten_free"] === "boolean" &&
    typeof value["contains_alcohol"] === "boolean" &&
    typeof value["image_id"] === "string"
  );
}

function isCatalogCategoryId(value: unknown): value is CatalogCategoryId {
  return typeof value === "string" && catalogCategoryIdSet.has(value);
}

function isMinorUnitAmount(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

const invalidCatalogResponseError: ApiError = {
  kind: "invalid_response",
  message: "The Tavola API returned an invalid catalog response."
};

const invalidCatalogProductResponseError: ApiError = {
  kind: "invalid_response",
  message: "The Tavola API returned an invalid catalog product response."
};
