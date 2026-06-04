import {
  apiGetJson,
  apiSendJson,
  type ApiError,
  type ApiResult
} from "./client";
import {
  catalogCategoryIds,
  type CatalogCategoryId
} from "../types/catalog";
import type {
  AddBasketLineRequest,
  BasketLine,
  BasketResponse,
  SetBasketLineQuantityRequest
} from "../types/basket";

const catalogCategoryIdSet = new Set<string>(catalogCategoryIds);

type BasketMutationOptions = {
  method: "POST" | "PATCH" | "DELETE";
  body?: unknown;
};

export async function createBasket(): Promise<ApiResult<BasketResponse>> {
  return await sendBasketRequest("/baskets", { method: "POST" });
}

export async function getBasket(
  basketId: string
): Promise<ApiResult<BasketResponse>> {
  const result = await apiGetJson<unknown>(basketPath(basketId));

  return mapBasketResult(result);
}

export async function addBasketLine(
  basketId: string,
  request: AddBasketLineRequest
): Promise<ApiResult<BasketResponse>>;
export async function addBasketLine(
  basketId: string,
  skuId: string,
  quantity: number
): Promise<ApiResult<BasketResponse>>;
export async function addBasketLine(
  basketId: string,
  skuIdOrRequest: string | AddBasketLineRequest,
  quantity?: number
): Promise<ApiResult<BasketResponse>> {
  const request =
    typeof skuIdOrRequest === "string"
      ? {
          sku_id: skuIdOrRequest,
          quantity
        }
      : skuIdOrRequest;

  return await sendBasketRequest(`${basketPath(basketId)}/lines`, {
    method: "POST",
    body: request
  });
}

export async function setBasketLineQuantity(
  basketId: string,
  skuId: string,
  request: SetBasketLineQuantityRequest
): Promise<ApiResult<BasketResponse>>;
export async function setBasketLineQuantity(
  basketId: string,
  skuId: string,
  quantity: number
): Promise<ApiResult<BasketResponse>>;
export async function setBasketLineQuantity(
  basketId: string,
  skuId: string,
  quantityOrRequest: number | SetBasketLineQuantityRequest
): Promise<ApiResult<BasketResponse>> {
  const request =
    typeof quantityOrRequest === "number"
      ? {
          quantity: quantityOrRequest
        }
      : quantityOrRequest;

  return await sendBasketRequest(basketLinePath(basketId, skuId), {
    method: "PATCH",
    body: request
  });
}

export async function removeBasketLine(
  basketId: string,
  skuId: string
): Promise<ApiResult<BasketResponse>> {
  return await sendBasketRequest(basketLinePath(basketId, skuId), {
    method: "DELETE"
  });
}

async function sendBasketRequest(
  path: string,
  options: BasketMutationOptions
): Promise<ApiResult<BasketResponse>> {
  const result = await apiSendJson<unknown>(path, options);

  return mapBasketResult(result);
}

function mapBasketResult(
  result: ApiResult<unknown>
): ApiResult<BasketResponse> {
  if (!result.ok) {
    return result;
  }

  if (isBasketResponse(result.data)) {
    return {
      ok: true,
      data: result.data
    };
  }

  return {
    ok: false,
    error: invalidBasketResponseError
  };
}

function basketPath(basketId: string): string {
  return `/baskets/${encodeURIComponent(basketId)}`;
}

function basketLinePath(basketId: string, skuId: string): string {
  return `${basketPath(basketId)}/lines/${encodeURIComponent(skuId)}`;
}

function isBasketResponse(value: unknown): value is BasketResponse {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value["basket_id"] === "string" &&
    Array.isArray(value["lines"]) &&
    value["lines"].every(isBasketLine) &&
    isMinorUnitAmount(value["total_minor"]) &&
    typeof value["currency"] === "string" &&
    isNonNegativeInteger(value["item_count"]) &&
    isNonNegativeInteger(value["line_count"])
  );
}

function isBasketLine(value: unknown): value is BasketLine {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value["sku_id"] === "string" &&
    typeof value["name"] === "string" &&
    isCatalogCategoryId(value["category_id"]) &&
    typeof value["category_label"] === "string" &&
    typeof value["unit_label"] === "string" &&
    isPositiveInteger(value["quantity"]) &&
    isMinorUnitAmount(value["unit_price_minor"]) &&
    isMinorUnitAmount(value["line_total_minor"]) &&
    typeof value["currency"] === "string" &&
    typeof value["image_id"] === "string"
  );
}

function isCatalogCategoryId(value: unknown): value is CatalogCategoryId {
  return typeof value === "string" && catalogCategoryIdSet.has(value);
}

function isMinorUnitAmount(value: unknown): value is number {
  return isNonNegativeInteger(value);
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value > 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

const invalidBasketResponseError: ApiError = {
  kind: "invalid_response",
  message: "The Tavola API returned an invalid basket response."
};
