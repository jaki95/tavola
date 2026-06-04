import { afterEach, describe, expect, test, vi } from "vitest";

import { apiSendJson } from "./client";

describe("apiSendJson", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  test("sends JSON bodies with the requested method", async () => {
    const fetchMock = stubJsonResponse({ basket_id: "basket-1" });

    const result = await apiSendJson("/baskets/basket-1/lines", {
      method: "POST",
      body: { sku_id: "fresh-tagliatelle-250g", quantity: 1 }
    });

    expect(result).toEqual({ ok: true, data: { basket_id: "basket-1" } });
    expect(fetchMock).toHaveBeenCalledWith("/api/baskets/basket-1/lines", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        sku_id: "fresh-tagliatelle-250g",
        quantity: 1
      })
    });
  });

  test("omits content type and body when no JSON body is provided", async () => {
    const fetchMock = stubJsonResponse({ basket_id: "basket-1", lines: [] });

    const result = await apiSendJson("/baskets/basket-1/lines/missing", {
      method: "DELETE"
    });

    expect(result).toEqual({
      ok: true,
      data: { basket_id: "basket-1", lines: [] }
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/baskets/basket-1/lines/missing",
      {
        method: "DELETE",
        headers: {
          Accept: "application/json"
        }
      }
    );
  });

  test("preserves HTTP errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("Not found", { status: 404 }))
    );

    const result = await apiSendJson("/baskets/missing", { method: "PATCH" });

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Request failed with status 404.",
        status: 404
      }
    });
  });

  test("uses FastAPI detail strings as HTTP error messages", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "basket not found" }), {
          status: 404
        })
      )
    );

    const result = await apiSendJson("/baskets/missing", { method: "PATCH" });

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "basket not found",
        status: 404
      }
    });
  });

  test("uses FastAPI validation messages as HTTP error messages", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: [
              {
                loc: ["body", "quantity"],
                msg: "Quantity cannot exceed 10.",
                type: "quantity_exceeded"
              }
            ]
          }),
          {
            status: 422
          }
        )
      )
    );

    const result = await apiSendJson("/baskets/basket-1/lines", {
      method: "POST",
      body: { sku_id: "fresh-tagliatelle-250g", quantity: 11 }
    });

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Quantity cannot exceed 10.",
        status: 422
      }
    });
  });

  test("preserves network errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch"))
    );

    const result = await apiSendJson("/baskets", { method: "POST" });

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "network",
        message: "Could not reach the Tavola API."
      }
    });
  });

  test("preserves invalid JSON response errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("not json", { status: 200 }))
    );

    const result = await apiSendJson("/baskets", { method: "POST" });

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid response."
      }
    });
  });
});

function stubJsonResponse(body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  return fetchMock;
}
