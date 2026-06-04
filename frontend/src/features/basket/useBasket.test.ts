import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import type { ApiResult } from "../../api/client";
import type { Basket } from "../../types/basket";
import { useBasket, type BasketClient } from "./useBasket";

const emptyBasket: Basket = {
  basket_id: "basket-1",
  lines: [],
  total_minor: 0,
  currency: "GBP",
  item_count: 0,
  line_count: 0
};

const replacementEmptyBasket: Basket = {
  ...emptyBasket,
  basket_id: "basket-2"
};

const tagliatelleBasket: Basket = {
  basket_id: "basket-1",
  lines: [
    {
      sku_id: "fresh-tagliatelle-250g",
      name: "Fresh Tagliatelle",
      category_id: "primi",
      category_label: "Primi",
      unit_label: "250g",
      quantity: 1,
      unit_price_minor: 425,
      line_total_minor: 425,
      currency: "GBP",
      image_id: "fresh-tagliatelle-250g"
    }
  ],
  total_minor: 425,
  currency: "GBP",
  item_count: 1,
  line_count: 1
};

const mergedTagliatelleBasket: Basket = {
  ...tagliatelleBasket,
  lines: [{ ...tagliatelleBasket.lines[0], quantity: 2, line_total_minor: 850 }],
  total_minor: 850,
  item_count: 2
};

describe("useBasket", () => {
  let storage: Storage;

  beforeEach(() => {
    storage = createMemoryStorage();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test("creates and stores a basket when no stored basket ID exists", async () => {
    const client = createBasketClient({
      createResults: [success(emptyBasket)]
    });

    const { result } = renderHook(() => useBasket({ client, storage }));

    expect(result.current.basket.status).toBe("loading");

    await waitFor(() => {
      expect(result.current.basket.status).toBe("success");
    });
    expect(result.current.basket.basket).toEqual(emptyBasket);
    expect(storage.getItem("tavola:basket_id")).toBe("basket-1");
    expect(client.createBasket).toHaveBeenCalledTimes(1);
    expect(client.getBasket).not.toHaveBeenCalled();
  });

  test("loads an existing basket when a basket ID is stored", async () => {
    storage.setItem("tavola:basket_id", "basket-1");
    const client = createBasketClient({
      getResults: [success(tagliatelleBasket)]
    });

    const { result } = renderHook(() => useBasket({ client, storage }));

    await waitFor(() => {
      expect(result.current.basket.status).toBe("success");
    });
    expect(result.current.basket.basket).toEqual(tagliatelleBasket);
    expect(client.getBasket).toHaveBeenCalledWith("basket-1");
    expect(client.createBasket).not.toHaveBeenCalled();
  });

  test("creates a fresh basket when the stored basket disappeared on the backend", async () => {
    storage.setItem("tavola:basket_id", "stale-basket");
    const client = createBasketClient({
      getResults: [httpError(404)],
      createResults: [success(emptyBasket)]
    });

    const { result } = renderHook(() => useBasket({ client, storage }));

    await waitFor(() => {
      expect(result.current.basket.status).toBe("success");
    });
    expect(result.current.basket.basket).toEqual(emptyBasket);
    expect(storage.getItem("tavola:basket_id")).toBe("basket-1");
    expect(client.getBasket).toHaveBeenCalledWith("stale-basket");
    expect(client.createBasket).toHaveBeenCalledTimes(1);
  });

  test("updates basket state from add, edit, and remove responses", async () => {
    const client = createBasketClient({
      createResults: [success(emptyBasket)],
      addResults: [success(tagliatelleBasket), success(mergedTagliatelleBasket)],
      setResults: [success(mergedTagliatelleBasket)],
      removeResults: [success(emptyBasket)]
    });

    const { result } = renderHook(() => useBasket({ client, storage }));
    await waitFor(() => {
      expect(result.current.basket.status).toBe("success");
    });

    await act(async () => {
      await result.current.addLine("fresh-tagliatelle-250g", 1);
    });

    expect(result.current.basket.basket).toEqual(tagliatelleBasket);
    expect(client.addBasketLine).toHaveBeenCalledWith("basket-1", {
      sku_id: "fresh-tagliatelle-250g",
      quantity: 1
    });

    await act(async () => {
      await result.current.addLine("fresh-tagliatelle-250g", 1);
    });

    expect(result.current.basket.basket).toEqual(mergedTagliatelleBasket);

    await act(async () => {
      await result.current.setLineQuantity("fresh-tagliatelle-250g", 2);
    });

    expect(client.setBasketLineQuantity).toHaveBeenCalledWith(
      "basket-1",
      "fresh-tagliatelle-250g",
      { quantity: 2 }
    );
    expect(result.current.basket.basket).toEqual(mergedTagliatelleBasket);

    await act(async () => {
      await result.current.removeLine("fresh-tagliatelle-250g");
    });

    expect(client.removeBasketLine).toHaveBeenCalledWith(
      "basket-1",
      "fresh-tagliatelle-250g"
    );
    expect(result.current.basket.basket).toEqual(emptyBasket);
  });

  test("preserves backend validation errors for user-visible display", async () => {
    const client = createBasketClient({
      createResults: [success(tagliatelleBasket)],
      setResults: [
        {
          ok: false,
          error: {
            kind: "http",
            status: 422,
            message: "Quantity must be no more than 10."
          }
        }
      ]
    });

    const { result } = renderHook(() => useBasket({ client, storage }));
    await waitFor(() => {
      expect(result.current.basket.status).toBe("success");
    });

    await act(async () => {
      await result.current.setLineQuantity("fresh-tagliatelle-250g", 11);
    });

    expect(result.current.basket.basket).toEqual(tagliatelleBasket);
    expect(result.current.mutation.status).toBe("error");
    expect(result.current.mutation.message).toBe(
      "Quantity must be no more than 10."
    );
  });

  test("exposes pending mutation state while a basket mutation is in flight", async () => {
    const deferredAdd = createDeferred<ApiResult<Basket>>();
    const client = createBasketClient({
      createResults: [success(emptyBasket)],
      addResults: [deferredAdd.promise]
    });

    const { result } = renderHook(() => useBasket({ client, storage }));
    await waitFor(() => {
      expect(result.current.basket.status).toBe("success");
    });

    void act(() => {
      void result.current.addLine("fresh-tagliatelle-250g", 1);
    });

    await waitFor(() => {
      expect(result.current.mutation.status).toBe("pending");
    });

    await act(async () => {
      deferredAdd.resolve(success(tagliatelleBasket));
    });

    await waitFor(() => {
      expect(result.current.mutation.status).toBe("idle");
    });
  });

  test("reload fetches the current backend-owned basket contents", async () => {
    storage.setItem("tavola:basket_id", "basket-1");
    const client = createBasketClient({
      getResults: [success(emptyBasket), success(tagliatelleBasket)]
    });

    const { result } = renderHook(() => useBasket({ client, storage }));
    await waitFor(() => {
      expect(result.current.basket.status).toBe("success");
    });

    await act(async () => {
      await result.current.reload();
    });

    expect(client.getBasket).toHaveBeenCalledTimes(2);
    expect(result.current.basket.basket).toEqual(tagliatelleBasket);
  });

  test("applies a backend-returned basket after a cross-workflow update", async () => {
    const client = createBasketClient({
      createResults: [success(tagliatelleBasket)]
    });

    const { result } = renderHook(() => useBasket({ client, storage }));
    await waitFor(() => {
      expect(result.current.basket.status).toBe("success");
    });

    act(() => {
      result.current.applyBasket(emptyBasket);
    });

    expect(result.current.basket.basket).toEqual(emptyBasket);
    expect(storage.getItem("tavola:basket_id")).toBe("basket-1");
  });

  test("ignores stale create responses when a newer basket load wins", async () => {
    const staleCreate = createDeferred<ApiResult<Basket>>();
    const currentCreate = createDeferred<ApiResult<Basket>>();
    const client = createBasketClient({
      createResults: [staleCreate.promise, currentCreate.promise]
    });

    const { result } = renderHook(() => useBasket({ client, storage }));

    await waitFor(() => {
      expect(client.createBasket).toHaveBeenCalledTimes(1);
    });

    void act(() => {
      void result.current.reload();
    });

    await waitFor(() => {
      expect(client.createBasket).toHaveBeenCalledTimes(2);
    });

    await act(async () => {
      currentCreate.resolve(success(replacementEmptyBasket));
    });

    await waitFor(() => {
      expect(result.current.basket.status).toBe("success");
    });
    expect(result.current.basket.basket).toEqual(replacementEmptyBasket);
    expect(storage.getItem("tavola:basket_id")).toBe("basket-2");

    await act(async () => {
      staleCreate.resolve(success(emptyBasket));
    });

    expect(result.current.basket.basket).toEqual(replacementEmptyBasket);
    expect(storage.getItem("tavola:basket_id")).toBe("basket-2");
  });
});

function createBasketClient({
  createResults = [],
  getResults = [],
  addResults = [],
  setResults = [],
  removeResults = []
}: {
  createResults?: Array<ApiResult<Basket> | Promise<ApiResult<Basket>>>;
  getResults?: Array<ApiResult<Basket> | Promise<ApiResult<Basket>>>;
  addResults?: Array<ApiResult<Basket> | Promise<ApiResult<Basket>>>;
  setResults?: Array<ApiResult<Basket> | Promise<ApiResult<Basket>>>;
  removeResults?: Array<ApiResult<Basket> | Promise<ApiResult<Basket>>>;
}): BasketClient {
  return {
    createBasket: vi.fn(async () => await shiftResult(createResults, "create")),
    getBasket: vi.fn(async () => await shiftResult(getResults, "get")),
    addBasketLine: vi.fn(async () => await shiftResult(addResults, "add")),
    setBasketLineQuantity: vi.fn(
      async () => await shiftResult(setResults, "set")
    ),
    removeBasketLine: vi.fn(
      async () => await shiftResult(removeResults, "remove")
    )
  };
}

async function shiftResult(
  results: Array<ApiResult<Basket> | Promise<ApiResult<Basket>>>,
  action: string
): Promise<ApiResult<Basket>> {
  const result = results.shift();
  if (!result) {
    throw new Error(`No basket ${action} result was queued.`);
  }

  return await result;
}

function success(basket: Basket): ApiResult<Basket> {
  return { ok: true, data: basket };
}

function httpError(status: number): ApiResult<Basket> {
  return {
    ok: false,
    error: {
      kind: "http",
      message: `Request failed with status ${status}.`,
      status
    }
  };
}

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((innerResolve) => {
    resolve = innerResolve;
  });

  return { promise, resolve };
}

function createMemoryStorage(): Storage {
  const store = new Map<string, string>();

  return {
    get length() {
      return store.size;
    },
    clear: vi.fn(() => {
      store.clear();
    }),
    getItem: vi.fn((key: string) => store.get(key) ?? null),
    key: vi.fn((index: number) => Array.from(store.keys())[index] ?? null),
    removeItem: vi.fn((key: string) => {
      store.delete(key);
    }),
    setItem: vi.fn((key: string, value: string) => {
      store.set(key, value);
    })
  };
}
