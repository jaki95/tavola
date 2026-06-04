import { afterEach, describe, expect, test, vi } from "vitest";

import type {
  CatalogListResponse,
  CatalogProductSummary,
  CatalogProductDetail
} from "../types/catalog";

const productSummary: CatalogProductSummary = {
  sku_id: "fresh-tagliatelle-250g",
  name: "Fresh Tagliatelle",
  category_id: "primi",
  category_label: "Primi",
  unit_label: "250g",
  unit_price_minor: 425,
  currency: "GBP",
  short_description: "Silky fresh pasta nests for a quick supper.",
  is_vegetarian: true,
  is_vegan: false,
  is_gluten_free: false,
  contains_alcohol: false,
  image_id: "fresh-tagliatelle-250g"
};

const catalogResponse: CatalogListResponse = {
  categories: [
    { category_id: "antipasti", label: "Antipasti" },
    { category_id: "primi", label: "Primi" }
  ],
  products: [productSummary]
};

const productDetail: CatalogProductDetail = {
  ...productSummary,
  detail_description:
    "Silky tagliatelle made with durum wheat flour and free-range egg."
};

describe("getCatalog", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
    vi.unstubAllEnvs();
  });

  test("requests the catalog list from the default API base URL", async () => {
    const { getCatalog } = await loadCatalogClient();
    const fetchMock = stubJsonResponse(catalogResponse);

    const result = await getCatalog();

    expect(result).toEqual({ ok: true, data: catalogResponse });
    expect(fetchMock).toHaveBeenCalledWith("/api/catalog", {
      headers: { Accept: "application/json" }
    });
  });

  test("builds safe query strings for category and search filters", async () => {
    const { getCatalog } = await loadCatalogClient();
    const fetchMock = stubJsonResponse({ ...catalogResponse, products: [] });

    const result = await getCatalog({
      category_id: "primi",
      query: " fresh pasta "
    });

    expect(result).toEqual({
      ok: true,
      data: { ...catalogResponse, products: [] }
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/catalog?category=primi&q=fresh+pasta",
      { headers: { Accept: "application/json" } }
    );
  });

  test("omits empty filters from catalog requests", async () => {
    const { getCatalog } = await loadCatalogClient();
    const fetchMock = stubJsonResponse(catalogResponse);

    await getCatalog({ category_id: null, query: "   " });

    expect(fetchMock).toHaveBeenCalledWith("/api/catalog", {
      headers: { Accept: "application/json" }
    });
  });

  test("passes through non-OK HTTP responses", async () => {
    const { getCatalog } = await loadCatalogClient();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("Unavailable", { status: 503 }))
    );

    const result = await getCatalog();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Request failed with status 503.",
        status: 503
      }
    });
  });

  test("passes through transport failures", async () => {
    const { getCatalog } = await loadCatalogClient();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch"))
    );

    const result = await getCatalog();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "network",
        message: "Could not reach the Tavola API."
      }
    });
  });

  test("returns a predictable error for invalid catalog list responses", async () => {
    const { getCatalog } = await loadCatalogClient();
    stubJsonResponse({ categories: catalogResponse.categories });

    const result = await getCatalog();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid catalog response."
      }
    });
  });
});

describe("getCatalogProduct", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
    vi.unstubAllEnvs();
  });

  test("requests product detail by SKU ID", async () => {
    const { getCatalogProduct } = await loadCatalogClient();
    const fetchMock = stubJsonResponse(productDetail);

    const result = await getCatalogProduct("fresh-tagliatelle-250g");

    expect(result).toEqual({ ok: true, data: productDetail });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/catalog/products/fresh-tagliatelle-250g",
      { headers: { Accept: "application/json" } }
    );
  });

  test("encodes SKU IDs before requesting product detail", async () => {
    const { getCatalogProduct } = await loadCatalogClient();
    const fetchMock = stubJsonResponse(productDetail);

    await getCatalogProduct("fresh pasta/250g");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/catalog/products/fresh%20pasta%2F250g",
      { headers: { Accept: "application/json" } }
    );
  });

  test("passes through detail HTTP errors", async () => {
    const { getCatalogProduct } = await loadCatalogClient();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("Not found", {
          status: 404
        })
      )
    );

    const result = await getCatalogProduct("missing-sku");

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Request failed with status 404.",
        status: 404
      }
    });
  });

  test("returns a predictable error for invalid product detail responses", async () => {
    const { getCatalogProduct } = await loadCatalogClient();
    stubJsonResponse({
      ...productDetail,
      detail_description: 42
    });

    const result = await getCatalogProduct("fresh-tagliatelle-250g");

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid catalog product response."
      }
    });
  });
});

async function loadCatalogClient() {
  return await import("./catalog");
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
