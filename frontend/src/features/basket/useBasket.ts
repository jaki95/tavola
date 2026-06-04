import { useCallback, useEffect, useRef, useState } from "react";

import {
  addBasketLine,
  createBasket,
  getBasket,
  removeBasketLine,
  setBasketLineQuantity
} from "../../api/basket";
import type { ApiResult } from "../../api/client";
import type { Basket } from "../../types/basket";

const BASKET_ID_STORAGE_KEY = "tavola:basket_id";

export type BasketClient = {
  createBasket: typeof createBasket;
  getBasket: typeof getBasket;
  addBasketLine: typeof addBasketLine;
  setBasketLineQuantity: typeof setBasketLineQuantity;
  removeBasketLine: typeof removeBasketLine;
};

export type BasketLoadState =
  | {
      status: "loading";
      basket: Basket | null;
    }
  | {
      status: "success";
      basket: Basket;
    }
  | {
      status: "error";
      basket: Basket | null;
      message: string;
    };

export type BasketMutationState =
  | {
      status: "idle";
      message: null;
    }
  | {
      status: "pending";
      message: null;
    }
  | {
      status: "error";
      message: string;
    };

type UseBasketOptions = {
  client?: BasketClient;
  storage?: Storage;
};

const defaultBasketClient: BasketClient = {
  createBasket,
  getBasket,
  addBasketLine,
  setBasketLineQuantity,
  removeBasketLine
};

export function useBasket({
  client = defaultBasketClient,
  storage = getBasketStorage()
}: UseBasketOptions = {}) {
  const [basket, setBasket] = useState<BasketLoadState>({
    status: "loading",
    basket: null
  });
  const [mutation, setMutation] = useState<BasketMutationState>({
    status: "idle",
    message: null
  });
  const loadRequestId = useRef(0);
  const basketRef = useRef<Basket | null>(null);

  const applyBasket = useCallback(
    (nextBasket: Basket) => {
      basketRef.current = nextBasket;
      storage.setItem(BASKET_ID_STORAGE_KEY, nextBasket.basket_id);
      setBasket({
        status: "success",
        basket: nextBasket
      });
    },
    [storage]
  );

  const createFreshBasket = useCallback(async (): Promise<ApiResult<Basket>> => {
    return await client.createBasket();
  }, [client]);

  const loadCurrentBasket = useCallback(async () => {
    const requestId = loadRequestId.current + 1;
    loadRequestId.current = requestId;

    setBasket({
      status: "loading",
      basket: basketRef.current
    });
    setMutation({ status: "idle", message: null });

    const storedBasketId = storage.getItem(BASKET_ID_STORAGE_KEY);
    const result = storedBasketId
      ? await client.getBasket(storedBasketId)
      : await createFreshBasket();

    if (loadRequestId.current !== requestId) {
      return;
    }

    if (result.ok) {
      applyBasket(result.data);
      return;
    }

    if (storedBasketId && result.error.kind === "http" && result.error.status === 404) {
      const freshResult = await createFreshBasket();
      if (loadRequestId.current !== requestId) {
        return;
      }

      if (!freshResult.ok) {
        setBasket({
          status: "error",
          basket: basketRef.current,
          message: freshResult.error.message
        });
        return;
      }

      applyBasket(freshResult.data);
      return;
    }

    setBasket({
      status: "error",
      basket: basketRef.current,
      message: result.error.message
    });
  }, [applyBasket, client, createFreshBasket, storage]);

  useEffect(() => {
    void loadCurrentBasket();
  }, [loadCurrentBasket]);

  const mutateBasket = useCallback(
    async (mutationCall: (currentBasket: Basket) => Promise<ApiResult<Basket>>) => {
      const currentBasket = basketRef.current;
      if (!currentBasket) {
        setMutation({
          status: "error",
          message: "Basket is not ready yet."
        });
        return;
      }

      setMutation({ status: "pending", message: null });
      const result = await mutationCall(currentBasket);

      if (result.ok) {
        applyBasket(result.data);
        setMutation({ status: "idle", message: null });
        return;
      }

      setMutation({
        status: "error",
        message: result.error.message
      });
    },
    [applyBasket]
  );

  const addLine = useCallback(
    async (skuId: string, quantity: number) => {
      await mutateBasket(async (currentBasket) =>
        await client.addBasketLine(currentBasket.basket_id, {
          sku_id: skuId,
          quantity
        })
      );
    },
    [client, mutateBasket]
  );

  const setLineQuantity = useCallback(
    async (skuId: string, quantity: number) => {
      await mutateBasket(async (currentBasket) =>
        await client.setBasketLineQuantity(currentBasket.basket_id, skuId, {
          quantity
        })
      );
    },
    [client, mutateBasket]
  );

  const removeLine = useCallback(
    async (skuId: string) => {
      await mutateBasket(async (currentBasket) =>
        await client.removeBasketLine(currentBasket.basket_id, skuId)
      );
    },
    [client, mutateBasket]
  );

  return {
    basket,
    mutation,
    reload: loadCurrentBasket,
    applyBasket,
    addLine,
    setLineQuantity,
    removeLine
  };
}

function getBasketStorage(): Storage {
  if (typeof window !== "undefined" && window.localStorage) {
    return window.localStorage;
  }

  return createMemoryStorage();
}

function createMemoryStorage(): Storage {
  const values = new Map<string, string>();

  return {
    get length() {
      return values.size;
    },
    clear() {
      values.clear();
    },
    getItem(key: string) {
      return values.get(key) ?? null;
    },
    key(index: number) {
      return Array.from(values.keys())[index] ?? null;
    },
    removeItem(key: string) {
      values.delete(key);
    },
    setItem(key: string, value: string) {
      values.set(key, value);
    }
  };
}
