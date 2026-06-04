import { afterEach, describe, expect, test, vi } from "vitest";

import type {
  PickupWindow,
  CheckoutResponse,
  PickupWindowsResponse
} from "../types/checkout";

const todayAfternoonPickupWindow: PickupWindow = {
  pickup_window_id: "today-afternoon",
  label: "Today, 2pm to 5pm",
  display_order: 1
};

const pickupWindowsResponse: PickupWindowsResponse = {
  pickup_windows: [
    todayAfternoonPickupWindow,
    {
      pickup_window_id: "tomorrow-morning",
      label: "Tomorrow, 10am to 1pm",
      display_order: 2
    }
  ]
};

const checkoutResponse: CheckoutResponse = {
  order: {
    order_id: "order-123",
    basket_id: "basket-123",
    contact_name: "Giulia Rossi",
    contact_email: "giulia@example.com",
    pickup_window: todayAfternoonPickupWindow,
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
  },
  basket: {
    basket_id: "basket-123",
    lines: [],
    total_minor: 0,
    currency: "GBP",
    item_count: 0,
    line_count: 0
  }
};

describe("checkout API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
    vi.unstubAllEnvs();
  });

  test("fetches pickup windows with the expected GET request", async () => {
    const { listPickupWindows } = await loadCheckoutClient();
    const fetchMock = stubJsonResponse(pickupWindowsResponse);

    const result = await listPickupWindows();

    expect(result).toEqual({ ok: true, data: pickupWindowsResponse });
    expect(fetchMock).toHaveBeenCalledWith("/api/checkout/pickup-windows", {
      headers: { Accept: "application/json" }
    });
  });

  test("posts checkout requests with the expected JSON body", async () => {
    const { createCheckout } = await loadCheckoutClient();
    const fetchMock = stubJsonResponse(checkoutResponse);

    const result = await createCheckout({
      basket_id: "basket-123",
      contact_name: "Giulia Rossi",
      contact_email: "giulia@example.com",
      pickup_window_id: "today-afternoon"
    });

    expect(result).toEqual({ ok: true, data: checkoutResponse });
    expect(fetchMock).toHaveBeenCalledWith("/api/checkout", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        basket_id: "basket-123",
        contact_name: "Giulia Rossi",
        contact_email: "giulia@example.com",
        pickup_window_id: "today-afternoon"
      })
    });
  });

  test.each([
    ["missing pickup windows", {}],
    [
      "malformed pickup window",
      {
        pickup_windows: [
          {
            ...pickupWindowsResponse.pickup_windows[0],
            display_order: 0
          }
        ]
      }
    ]
  ])("rejects malformed pickup window responses: %s", async (
    _caseName,
    malformedResponse
  ) => {
    const { listPickupWindows } = await loadCheckoutClient();
    stubJsonResponse(malformedResponse);

    const result = await listPickupWindows();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid pickup windows response."
      }
    });
  });

  test.each([
    ["missing checkout order", { ...checkoutResponse, order: undefined }],
    [
      "malformed order",
      {
        ...checkoutResponse,
        order: { ...checkoutResponse.order, total_minor: -1 }
      }
    ],
    [
      "malformed order line",
      {
        ...checkoutResponse,
        order: {
          ...checkoutResponse.order,
          lines: [{ ...checkoutResponse.order.lines[0], quantity: 0 }]
        }
      }
    ],
    [
      "malformed returned basket",
      {
        ...checkoutResponse,
        basket: { ...checkoutResponse.basket, line_count: -1 }
      }
    ]
  ])("rejects malformed checkout responses: %s", async (
    _caseName,
    malformedResponse
  ) => {
    const { createCheckout } = await loadCheckoutClient();
    stubJsonResponse(malformedResponse);

    const result = await createCheckout({
      basket_id: "basket-123",
      contact_name: "Giulia Rossi",
      contact_email: "giulia@example.com",
      pickup_window_id: "today-afternoon"
    });

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid checkout response."
      }
    });
  });

  test("passes through HTTP errors from pickup window fetches", async () => {
    const { listPickupWindows } = await loadCheckoutClient();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Pickup windows unavailable." }), {
          status: 503
        })
      )
    );

    const result = await listPickupWindows();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Pickup windows unavailable.",
        status: 503
      }
    });
  });

  test("passes through HTTP errors from checkout submissions", async () => {
    const { createCheckout } = await loadCheckoutClient();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Basket is empty." }), {
          status: 422
        })
      )
    );

    const result = await createCheckout({
      basket_id: "basket-123",
      contact_name: "Giulia Rossi",
      contact_email: "giulia@example.com",
      pickup_window_id: "today-afternoon"
    });

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Basket is empty.",
        status: 422
      }
    });
  });
});

async function loadCheckoutClient() {
  return await import("./checkout");
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
