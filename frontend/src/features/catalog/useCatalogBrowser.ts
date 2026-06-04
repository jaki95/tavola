import { useCallback, useEffect, useRef, useState } from "react";

import { getCatalog, getCatalogProduct } from "../../api/catalog";
import type { ApiResult } from "../../api/client";
import type {
  CatalogCategory,
  CatalogCategoryId,
  CatalogListResponse,
  CatalogProductDetail,
  CatalogProductSummary
} from "../../types/catalog";

export type CatalogClient = {
  getCatalog: typeof getCatalog;
  getCatalogProduct: typeof getCatalogProduct;
};

export type CatalogListState =
  | {
      status: "loading";
      categories: CatalogCategory[];
      products: CatalogProductSummary[];
    }
  | {
      status: "success";
      categories: CatalogCategory[];
      products: CatalogProductSummary[];
    }
  | {
      status: "empty";
      categories: CatalogCategory[];
      products: CatalogProductSummary[];
    }
  | {
      status: "error";
      categories: CatalogCategory[];
      products: CatalogProductSummary[];
      message: string;
    };

export type CatalogDetailState =
  | {
      status: "closed";
    }
  | {
      status: "loading";
      skuId: string;
    }
  | {
      status: "success";
      skuId: string;
      product: CatalogProductDetail;
    }
  | {
      status: "error";
      skuId: string;
      message: string;
    };

type UseCatalogBrowserOptions = {
  client?: CatalogClient;
  isActive?: boolean;
};

const defaultCatalogClient: CatalogClient = {
  getCatalog,
  getCatalogProduct
};

const emptyCatalogState: CatalogListState = {
  status: "loading",
  categories: [],
  products: []
};

export function useCatalogBrowser({
  client = defaultCatalogClient,
  isActive = true
}: UseCatalogBrowserOptions = {}) {
  const [catalog, setCatalog] = useState<CatalogListState>(emptyCatalogState);
  const [detail, setDetail] = useState<CatalogDetailState>({ status: "closed" });
  const [selectedCategoryId, setSelectedCategoryId] =
    useState<CatalogCategoryId | null>(null);
  const [draftSearch, setDraftSearch] = useState("");
  const [committedSearch, setCommittedSearch] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const detailRequestId = useRef(0);
  const wasActive = useRef(isActive);

  useEffect(() => {
    let isCurrent = true;

    setCatalog((current) => ({
      status: "loading",
      categories: current.categories,
      products: current.products
    }));

    async function loadCatalog() {
      const result = await client.getCatalog({
        category_id: selectedCategoryId,
        query: committedSearch
      });

      if (!isCurrent) {
        return;
      }

      setCatalog(mapCatalogResult(result));
    }

    void loadCatalog();

    return () => {
      isCurrent = false;
    };
  }, [client, selectedCategoryId, committedSearch, reloadKey]);

  const closeDetail = useCallback(() => {
    detailRequestId.current += 1;
    setDetail({ status: "closed" });
  }, []);

  useEffect(() => {
    if (wasActive.current && !isActive) {
      closeDetail();
    }

    wasActive.current = isActive;
  }, [closeDetail, isActive]);

  const selectCategory = useCallback((categoryId: CatalogCategoryId | null) => {
    detailRequestId.current += 1;
    setSelectedCategoryId(categoryId);
    setDetail({ status: "closed" });
  }, []);

  const updateDraftSearch = useCallback((value: string) => {
    setDraftSearch(value);
  }, []);

  const submitSearch = useCallback(() => {
    detailRequestId.current += 1;
    setCommittedSearch(draftSearch.trim());
    setDetail({ status: "closed" });
  }, [draftSearch]);

  const resetFilters = useCallback(() => {
    detailRequestId.current += 1;
    setSelectedCategoryId(null);
    setDraftSearch("");
    setCommittedSearch("");
    setDetail({ status: "closed" });
    setReloadKey((current) => current + 1);
  }, []);

  const reloadCatalog = useCallback(() => {
    setReloadKey((current) => current + 1);
  }, []);

  const openDetail = useCallback(
    (skuId: string) => {
      const requestId = detailRequestId.current + 1;
      detailRequestId.current = requestId;

      setDetail({ status: "loading", skuId });

      async function loadDetail() {
        const result = await client.getCatalogProduct(skuId);

        if (detailRequestId.current !== requestId) {
          return;
        }

        setDetail(mapDetailResult(skuId, result));
      }

      void loadDetail();
    },
    [client]
  );

  return {
    catalog,
    detail,
    selectedCategoryId,
    draftSearch,
    committedSearch,
    selectCategory,
    updateDraftSearch,
    submitSearch,
    resetFilters,
    reloadCatalog,
    openDetail,
    closeDetail
  };
}

function mapCatalogResult(
  result: ApiResult<CatalogListResponse>
): CatalogListState {
  if (!result.ok) {
    return {
      status: "error",
      categories: [],
      products: [],
      message: result.error.message
    };
  }

  const { categories, products } = result.data;

  if (products.length === 0) {
    return {
      status: "empty",
      categories,
      products
    };
  }

  return {
    status: "success",
    categories,
    products
  };
}

function mapDetailResult(
  skuId: string,
  result: ApiResult<CatalogProductDetail>
): CatalogDetailState {
  if (!result.ok) {
    return {
      status: "error",
      skuId,
      message: result.error.message
    };
  }

  return {
    status: "success",
    skuId,
    product: result.data
  };
}
