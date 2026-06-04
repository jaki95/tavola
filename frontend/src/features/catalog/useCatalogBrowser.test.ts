import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import type { ApiResult } from "../../api/client";
import type {
  CatalogCategory,
  CatalogListResponse,
  CatalogProductDetail,
  CatalogProductSummary
} from "../../types/catalog";
import { useCatalogBrowser, type CatalogClient } from "./useCatalogBrowser";

const categories: CatalogCategory[] = [
  { category_id: "antipasti", label: "Antipasti" },
  { category_id: "primi", label: "Primi" }
];

const tagliatelle: CatalogProductSummary = {
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

const tagliatelleDetail: CatalogProductDetail = {
  ...tagliatelle,
  detail_description:
    "Silky tagliatelle made with durum wheat flour and free-range egg."
};

describe("useCatalogBrowser", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  test("loads the catalog into an explicit success state", async () => {
    const client = createCatalogClient({
      listResults: [catalogSuccess({ products: [tagliatelle] })]
    });

    const { result } = renderHook(() => useCatalogBrowser({ client }));

    expect(result.current.catalog.status).toBe("loading");

    await waitFor(() => {
      expect(result.current.catalog.status).toBe("success");
    });
    expect(result.current.catalog.products).toEqual([tagliatelle]);
    expect(result.current.catalog.categories).toEqual(categories);
    expect(client.getCatalog).toHaveBeenCalledWith({
      category_id: null,
      query: ""
    });
  });

  test("represents empty results separately from failed requests", async () => {
    const client = createCatalogClient({
      listResults: [catalogSuccess({ products: [] })]
    });

    const { result } = renderHook(() => useCatalogBrowser({ client }));

    await waitFor(() => {
      expect(result.current.catalog.status).toBe("empty");
    });
    expect(result.current.catalog.categories).toEqual(categories);
  });

  test("commits search only when submitted", async () => {
    const client = createCatalogClient({
      listResults: [
        catalogSuccess({ products: [tagliatelle] }),
        catalogSuccess({ products: [tagliatelle] })
      ]
    });

    const { result } = renderHook(() => useCatalogBrowser({ client }));
    await waitFor(() => {
      expect(result.current.catalog.status).toBe("success");
    });

    act(() => {
      result.current.updateDraftSearch(" fresh pasta ");
    });

    expect(client.getCatalog).toHaveBeenCalledTimes(1);

    act(() => {
      result.current.submitSearch();
    });

    await waitFor(() => {
      expect(client.getCatalog).toHaveBeenCalledTimes(2);
    });
    expect(client.getCatalog).toHaveBeenLastCalledWith({
      category_id: null,
      query: "fresh pasta"
    });
  });

  test("category changes refresh the list and close selected detail", async () => {
    const client = createCatalogClient({
      listResults: [
        catalogSuccess({ products: [tagliatelle] }),
        catalogSuccess({ products: [tagliatelle] })
      ],
      detailResults: [{ ok: true, data: tagliatelleDetail }]
    });

    const { result } = renderHook(() => useCatalogBrowser({ client }));
    await waitFor(() => {
      expect(result.current.catalog.status).toBe("success");
    });

    act(() => {
      result.current.openDetail("fresh-tagliatelle-250g");
    });
    await waitFor(() => {
      expect(result.current.detail.status).toBe("success");
    });

    act(() => {
      result.current.selectCategory("primi");
    });

    expect(result.current.detail.status).toBe("closed");
    await waitFor(() => {
      expect(client.getCatalog).toHaveBeenLastCalledWith({
        category_id: "primi",
        query: ""
      });
    });
  });

  test("reset clears filters, closes detail, and reloads the unfiltered catalog", async () => {
    const client = createCatalogClient({
      listResults: [
        catalogSuccess({ products: [tagliatelle] }),
        catalogSuccess({ products: [tagliatelle] }),
        catalogSuccess({ products: [tagliatelle] })
      ],
      detailResults: [{ ok: true, data: tagliatelleDetail }]
    });

    const { result } = renderHook(() => useCatalogBrowser({ client }));
    await waitFor(() => {
      expect(result.current.catalog.status).toBe("success");
    });

    act(() => {
      result.current.updateDraftSearch("pasta");
    });

    act(() => {
      result.current.submitSearch();
    });
    await waitFor(() => {
      expect(client.getCatalog).toHaveBeenCalledTimes(2);
    });

    act(() => {
      result.current.openDetail("fresh-tagliatelle-250g");
    });
    await waitFor(() => {
      expect(result.current.detail.status).toBe("success");
    });

    act(() => {
      result.current.resetFilters();
    });

    await waitFor(() => {
      expect(client.getCatalog).toHaveBeenCalledTimes(3);
    });
    expect(result.current.selectedCategoryId).toBeNull();
    expect(result.current.draftSearch).toBe("");
    expect(result.current.committedSearch).toBe("");
    expect(result.current.detail.status).toBe("closed");
    expect(client.getCatalog).toHaveBeenLastCalledWith({
      category_id: null,
      query: ""
    });
  });

  test("reload recovers from a failed list request", async () => {
    const client = createCatalogClient({
      listResults: [
        {
          ok: false,
          error: {
            kind: "network",
            message: "Could not reach the Tavola API."
          }
        },
        catalogSuccess({ products: [tagliatelle] })
      ]
    });

    const { result } = renderHook(() => useCatalogBrowser({ client }));

    await waitFor(() => {
      expect(result.current.catalog.status).toBe("error");
    });
    const failedCatalog = result.current.catalog;
    if (failedCatalog.status !== "error") {
      throw new Error(`Expected catalog error state, got ${failedCatalog.status}.`);
    }
    expect(failedCatalog.message).toBe("Could not reach the Tavola API.");

    act(() => {
      result.current.reloadCatalog();
    });

    await waitFor(() => {
      expect(result.current.catalog.status).toBe("success");
    });
  });

  test("detail failures stay scoped to the detail state and can be closed", async () => {
    const client = createCatalogClient({
      listResults: [catalogSuccess({ products: [tagliatelle] })],
      detailResults: [
        {
          ok: false,
          error: {
            kind: "http",
            message: "Request failed with status 404.",
            status: 404
          }
        }
      ]
    });

    const { result } = renderHook(() => useCatalogBrowser({ client }));
    await waitFor(() => {
      expect(result.current.catalog.status).toBe("success");
    });

    act(() => {
      result.current.openDetail("fresh-tagliatelle-250g");
    });

    await waitFor(() => {
      expect(result.current.detail.status).toBe("error");
    });
    expect(result.current.catalog.status).toBe("success");
    const failedDetail = result.current.detail;
    if (failedDetail.status !== "error") {
      throw new Error(`Expected detail error state, got ${failedDetail.status}.`);
    }
    expect(failedDetail.message).toBe("Request failed with status 404.");

    act(() => {
      result.current.closeDetail();
    });

    expect(result.current.detail.status).toBe("closed");
  });

  test("filter and detail changes do not mutate the browser URL", async () => {
    const client = createCatalogClient({
      listResults: [
        catalogSuccess({ products: [tagliatelle] }),
        catalogSuccess({ products: [tagliatelle] })
      ],
      detailResults: [{ ok: true, data: tagliatelleDetail }]
    });
    const startingUrl = window.location.href;

    const { result } = renderHook(() => useCatalogBrowser({ client }));
    await waitFor(() => {
      expect(result.current.catalog.status).toBe("success");
    });

    act(() => {
      result.current.selectCategory("primi");
      result.current.updateDraftSearch("pasta");
      result.current.submitSearch();
      result.current.openDetail("fresh-tagliatelle-250g");
    });

    expect(window.location.href).toBe(startingUrl);
  });
});

function createCatalogClient({
  listResults,
  detailResults = []
}: {
  listResults: ApiResult<CatalogListResponse>[];
  detailResults?: ApiResult<CatalogProductDetail>[];
}): CatalogClient {
  return {
    getCatalog: vi.fn(async () => {
      const result = listResults.shift();
      if (!result) {
        throw new Error("No catalog list result was queued.");
      }
      return result;
    }),
    getCatalogProduct: vi.fn(async () => {
      const result = detailResults.shift();
      if (!result) {
        throw new Error("No catalog detail result was queued.");
      }
      return result;
    })
  };
}

function catalogSuccess({
  products
}: {
  products: CatalogProductSummary[];
}): ApiResult<CatalogListResponse> {
  return {
    ok: true,
    data: {
      categories,
      products
    }
  };
}
