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
import type { BasketLine, BasketResponse } from "../types/basket";
import type {
  CheckoutRequest,
  CheckoutResponse,
  Order,
  OrderLine,
  PickupWindow,
  PickupWindowsResponse
} from "../types/checkout";

const catalogCategoryIdSet = new Set<string>(catalogCategoryIds);

export async function listPickupWindows(): Promise<
  ApiResult<PickupWindowsResponse>
> {
  const result = await apiGetJson<unknown>("/checkout/pickup-windows");

  if (!result.ok) {
    return result;
  }

  if (isPickupWindowsResponse(result.data)) {
    return {
      ok: true,
      data: result.data
    };
  }

  return {
    ok: false,
    error: invalidPickupWindowsResponseError
  };
}

export async function createCheckout(
  request: CheckoutRequest
): Promise<ApiResult<CheckoutResponse>> {
  const result = await apiSendJson<unknown>("/checkout", {
    method: "POST",
    body: request
  });

  if (!result.ok) {
    return result;
  }

  if (isCheckoutResponse(result.data)) {
    return {
      ok: true,
      data: result.data
    };
  }

  return {
    ok: false,
    error: invalidCheckoutResponseError
  };
}

function isPickupWindowsResponse(
  value: unknown
): value is PickupWindowsResponse {
  return (
    isRecord(value) &&
    Array.isArray(value["pickup_windows"]) &&
    value["pickup_windows"].every(isPickupWindow)
  );
}

function isPickupWindow(value: unknown): value is PickupWindow {
  return (
    isRecord(value) &&
    typeof value["pickup_window_id"] === "string" &&
    typeof value["label"] === "string" &&
    isPositiveInteger(value["display_order"])
  );
}

function isCheckoutResponse(value: unknown): value is CheckoutResponse {
  return (
    isRecord(value) &&
    isOrder(value["order"]) &&
    isBasketResponse(value["basket"])
  );
}

function isOrder(value: unknown): value is Order {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value["order_id"] === "string" &&
    typeof value["basket_id"] === "string" &&
    typeof value["contact_name"] === "string" &&
    typeof value["contact_email"] === "string" &&
    isPickupWindow(value["pickup_window"]) &&
    Array.isArray(value["lines"]) &&
    value["lines"].every(isOrderLine) &&
    isMinorUnitAmount(value["total_minor"]) &&
    typeof value["currency"] === "string" &&
    isNonNegativeInteger(value["item_count"]) &&
    isNonNegativeInteger(value["line_count"])
  );
}

function isOrderLine(value: unknown): value is OrderLine {
  return isBasketLine(value);
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

const invalidPickupWindowsResponseError: ApiError = {
  kind: "invalid_response",
  message: "The Tavola API returned an invalid pickup windows response."
};

const invalidCheckoutResponseError: ApiError = {
  kind: "invalid_response",
  message: "The Tavola API returned an invalid checkout response."
};
