import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import type { ApiResult } from "../../api/client";
import type {
  CheckoutResponse,
  Order,
  PickupWindow
} from "../../types/checkout";
import type { Basket } from "../../types/basket";
import { useCheckout, type CheckoutClient } from "./useCheckout";

const todayAfternoonPickupWindow: PickupWindow = {
  pickup_window_id: "today-afternoon",
  label: "Today afternoon pickup",
  display_order: 1
};

const pickupWindows: PickupWindow[] = [
  todayAfternoonPickupWindow,
  {
    pickup_window_id: "tomorrow-morning",
    label: "Tomorrow morning pickup",
    display_order: 2
  }
];

const tagliatelleBasket: Basket = {
  basket_id: "basket-1",
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

const emptyBasket: Basket = {
  basket_id: "basket-1",
  lines: [],
  total_minor: 0,
  currency: "GBP",
  item_count: 0,
  line_count: 0
};

const order: Order = {
  order_id: "order-1",
  basket_id: "basket-1",
  contact_name: "Ada Lovelace",
  contact_email: "ada@example.com",
  pickup_window: todayAfternoonPickupWindow,
  lines: tagliatelleBasket.lines,
  total_minor: 850,
  currency: "GBP",
  item_count: 2,
  line_count: 1
};

const checkoutResponse: CheckoutResponse = {
  order,
  basket: emptyBasket
};

describe("useCheckout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("loads pickup windows when mounted", async () => {
    const client = createCheckoutClient({
      pickupWindowResults: [success({ pickup_windows: pickupWindows })]
    });

    const { result } = renderHook(() => useCheckout({ client }));

    expect(result.current.pickupWindows.status).toBe("loading");

    await waitFor(() => {
      expect(result.current.pickupWindows.status).toBe("success");
    });
    expect(result.current.pickupWindows.pickupWindows).toEqual(pickupWindows);
    expect(client.getPickupWindows).toHaveBeenCalledTimes(1);
  });

  test("exposes pickup window load errors and retries", async () => {
    const client = createCheckoutClient({
      pickupWindowResults: [
        httpError(500, "Could not load pickup windows."),
        success({ pickup_windows: pickupWindows })
      ]
    });

    const { result } = renderHook(() => useCheckout({ client }));

    await waitFor(() => {
      expect(result.current.pickupWindows.status).toBe("error");
    });
    expect(result.current.pickupWindows.message).toBe(
      "Could not load pickup windows."
    );

    await act(async () => {
      await result.current.reloadPickupWindows();
    });

    expect(result.current.pickupWindows.status).toBe("success");
    expect(result.current.pickupWindows.pickupWindows).toEqual(pickupWindows);
  });

  test("blocks submission when the basket is empty", async () => {
    const client = createCheckoutClient({
      pickupWindowResults: [success({ pickup_windows: pickupWindows })]
    });
    const { result } = renderHook(() => useCheckout({ client }));

    await waitFor(() => {
      expect(result.current.pickupWindows.status).toBe("success");
    });

    let submitResult: CheckoutResponse | null = null;
    await act(async () => {
      submitResult = await result.current.submitCheckout(emptyBasket, {
        contactName: "Ada Lovelace",
        contactEmail: "ada@example.com",
        pickupWindowId: "today-afternoon"
      });
    });

    expect(submitResult).toBeNull();
    expect(result.current.submission.status).toBe("error");
    expect(result.current.submission.message).toBe(
      "Add at least one deli item before checkout."
    );
    expect(client.createCheckout).not.toHaveBeenCalled();
  });

  test("submits contact details and returns the created order with the emptied basket", async () => {
    const client = createCheckoutClient({
      pickupWindowResults: [success({ pickup_windows: pickupWindows })],
      checkoutResults: [success(checkoutResponse)]
    });
    const { result } = renderHook(() => useCheckout({ client }));

    await waitFor(() => {
      expect(result.current.pickupWindows.status).toBe("success");
    });

    let submitResult: CheckoutResponse | null = null;
    await act(async () => {
      submitResult = await result.current.submitCheckout(tagliatelleBasket, {
        contactName: "Ada Lovelace",
        contactEmail: "ada@example.com",
        pickupWindowId: "today-afternoon"
      });
    });

    expect(client.createCheckout).toHaveBeenCalledWith({
      basket_id: "basket-1",
      contact_name: "Ada Lovelace",
      contact_email: "ada@example.com",
      pickup_window_id: "today-afternoon"
    });
    expect(submitResult).toEqual(checkoutResponse);
    expect(result.current.submission.status).toBe("success");
    expect(result.current.submission.order).toEqual(order);
  });

  test("surfaces backend checkout validation errors", async () => {
    const client = createCheckoutClient({
      pickupWindowResults: [success({ pickup_windows: pickupWindows })],
      checkoutResults: [httpError(422, "Contact email must include @.")]
    });
    const { result } = renderHook(() => useCheckout({ client }));

    await waitFor(() => {
      expect(result.current.pickupWindows.status).toBe("success");
    });

    await act(async () => {
      await result.current.submitCheckout(tagliatelleBasket, {
        contactName: "Ada Lovelace",
        contactEmail: "not-an-email",
        pickupWindowId: "today-afternoon"
      });
    });

    expect(result.current.submission.status).toBe("error");
    expect(result.current.submission.message).toBe(
      "Contact email must include @."
    );
  });

  test("resets a completed order so another checkout can be started", async () => {
    const client = createCheckoutClient({
      pickupWindowResults: [success({ pickup_windows: pickupWindows })],
      checkoutResults: [success(checkoutResponse)]
    });
    const { result } = renderHook(() => useCheckout({ client }));

    await waitFor(() => {
      expect(result.current.pickupWindows.status).toBe("success");
    });

    await act(async () => {
      await result.current.submitCheckout(tagliatelleBasket, {
        contactName: "Ada Lovelace",
        contactEmail: "ada@example.com",
        pickupWindowId: "today-afternoon"
      });
    });
    expect(result.current.submission.status).toBe("success");

    act(() => {
      result.current.resetCheckout();
    });

    expect(result.current.submission).toEqual({
      status: "idle",
      message: null,
      order: null
    });
  });
});

function createCheckoutClient({
  pickupWindowResults = [],
  checkoutResults = []
}: {
  pickupWindowResults?: Array<
    ApiResult<{ pickup_windows: PickupWindow[] }> | Promise<ApiResult<{ pickup_windows: PickupWindow[] }>>
  >;
  checkoutResults?: Array<
    ApiResult<CheckoutResponse> | Promise<ApiResult<CheckoutResponse>>
  >;
}): CheckoutClient {
  return {
    getPickupWindows: vi.fn(
      async () => await shiftResult(pickupWindowResults, "pickup windows")
    ),
    createCheckout: vi.fn(
      async () => await shiftResult(checkoutResults, "checkout")
    )
  };
}

async function shiftResult<T>(
  results: Array<ApiResult<T> | Promise<ApiResult<T>>>,
  action: string
): Promise<ApiResult<T>> {
  const result = results.shift();
  if (!result) {
    throw new Error(`No ${action} result was queued.`);
  }

  return await result;
}

function success<T>(data: T): ApiResult<T> {
  return { ok: true, data };
}

function httpError<T>(status: number, message: string): ApiResult<T> {
  return {
    ok: false,
    error: {
      kind: "http",
      status,
      message
    }
  };
}
