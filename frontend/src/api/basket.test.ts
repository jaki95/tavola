import { afterEach, describe, expect, test, vi } from "vitest";

import type { BasketResponse } from "../types/basket";

const basketResponse: BasketResponse = {
  basket_id: "basket-123",
  lines: [
    {
      sku_id: "fresh-tagliatelle-250g",
      name: "Fresh Tagliatelle",
      category_id: "primi",
      category_label: "Primi",
      unit_label: "250g",
      quantity: 2,
      unit_price_minor: 425,
      line_total_minor: 850,
      currency: "GBP",
      image_id: "fresh-tagliatelle-250g"
    }
  ],
  total_minor: 850,
  currency: "GBP",
  item_count: 2,
  line_count: 1
};

describe("basket API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
    vi.unstubAllEnvs();
  });

  test("maps a valid basket response", async () => {
    const { createBasket } = await loadBasketClient();
    stubJsonResponse(basketResponse);

    const result = await createBasket();

    expect(result).toEqual({ ok: true, data: basketResponse });
  });

  test("creates a basket with the expected POST request", async () => {
    const { createBasket } = await loadBasketClient();
    const fetchMock = stubJsonResponse({ ...basketResponse, lines: [] });

    await createBasket();

    expect(fetchMock).toHaveBeenCalledWith("/api/baskets", {
      method: "POST",
      headers: { Accept: "application/json" }
    });
  });

  test("gets a basket by encoded basket ID", async () => {
    const { getBasket } = await loadBasketClient();
    const fetchMock = stubJsonResponse(basketResponse);

    const result = await getBasket("basket one/two");

    expect(result).toEqual({ ok: true, data: basketResponse });
    expect(fetchMock).toHaveBeenCalledWith("/api/baskets/basket%20one%2Ftwo", {
      headers: { Accept: "application/json" }
    });
  });

  test("adds a basket line with an encoded basket ID and JSON body", async () => {
    const { addBasketLine } = await loadBasketClient();
    const fetchMock = stubJsonResponse(basketResponse);

    const result = await addBasketLine("basket one/two", "fresh pasta/250g", 2);

    expect(result).toEqual({ ok: true, data: basketResponse });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/baskets/basket%20one%2Ftwo/lines",
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          sku_id: "fresh pasta/250g",
          quantity: 2
        })
      }
    );
  });

  test("sets a line quantity with encoded basket and SKU IDs", async () => {
    const { setBasketLineQuantity } = await loadBasketClient();
    const fetchMock = stubJsonResponse({
      ...basketResponse,
      lines: [{ ...basketResponse.lines[0], quantity: 3, line_total_minor: 1275 }],
      total_minor: 1275,
      item_count: 3
    });

    const result = await setBasketLineQuantity(
      "basket one/two",
      "fresh pasta/250g",
      3
    );

    expect(result.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/baskets/basket%20one%2Ftwo/lines/fresh%20pasta%2F250g",
      {
        method: "PATCH",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          quantity: 3
        })
      }
    );
  });

  test("removes a basket line with encoded basket and SKU IDs", async () => {
    const { removeBasketLine } = await loadBasketClient();
    const fetchMock = stubJsonResponse({
      ...basketResponse,
      lines: [],
      total_minor: 0,
      item_count: 0,
      line_count: 0
    });

    const result = await removeBasketLine("basket one/two", "fresh pasta/250g");

    expect(result.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/baskets/basket%20one%2Ftwo/lines/fresh%20pasta%2F250g",
      {
        method: "DELETE",
        headers: { Accept: "application/json" }
      }
    );
  });

  test.each([
    ["missing basket ID", { ...basketResponse, basket_id: undefined }],
    ["missing lines", { ...basketResponse, lines: undefined }],
    [
      "malformed line",
      {
        ...basketResponse,
        lines: [{ ...basketResponse.lines[0], quantity: 0 }]
      }
    ],
    [
      "unknown category ID",
      {
        ...basketResponse,
        lines: [{ ...basketResponse.lines[0], category_id: "mains" }]
      }
    ],
    ["fractional total", { ...basketResponse, total_minor: 850.5 }],
    ["negative item count", { ...basketResponse, item_count: -1 }]
  ])("rejects a malformed basket response with a basket-specific error: %s", async (
    _caseName,
    malformedResponse
  ) => {
    const { createBasket } = await loadBasketClient();
    stubJsonResponse(malformedResponse);

    const result = await createBasket();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid basket response."
      }
    });
  });

  test("passes through HTTP errors from basket fetches", async () => {
    const { getBasket } = await loadBasketClient();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("Not found", { status: 404 }))
    );

    const result = await getBasket("missing-basket");

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Request failed with status 404.",
        status: 404
      }
    });
  });

  test("passes through HTTP errors from basket mutations", async () => {
    const { addBasketLine } = await loadBasketClient();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("Invalid quantity", { status: 422 }))
    );

    const result = await addBasketLine("basket-123", "fresh-tagliatelle-250g", 11);

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Request failed with status 422.",
        status: 422
      }
    });
  });
});

async function loadBasketClient() {
  return await import("./basket");
}

function stubJsonResponse(body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  return fetchMock;
}
