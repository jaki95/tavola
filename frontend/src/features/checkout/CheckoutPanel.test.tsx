import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import type { ApiResult } from "../../api/client";
import type { BasketLoadState } from "../basket/useBasket";
import type { Basket } from "../../types/basket";
import type {
  CheckoutResponse,
  PickupWindow,
  PickupWindowsResponse
} from "../../types/checkout";
import { CheckoutPanel } from "./CheckoutPanel";
import type { CheckoutClient } from "./useCheckout";

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

const checkoutResponse: CheckoutResponse = {
  order: {
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
  },
  basket: emptyBasket
};

describe("CheckoutPanel", () => {
  test("opens as a checkout dialog with a route back to basket editing", async () => {
    const onClose = vi.fn();

    renderCheckoutPanel({ onClose });

    const dialog = screen.getByRole("dialog", { name: "Pickup checkout" });

    expect(dialog).toHaveAttribute("aria-modal", "true");
    fireEvent.click(
      await within(dialog).findByRole("button", { name: "Back to basket" })
    );

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test("blocks checkout while keeping the empty basket state visible", async () => {
    renderCheckoutPanel({
      basket: { status: "success", basket: emptyBasket }
    });

    const panel = screen.getByRole("dialog", { name: "Pickup checkout" });

    expect(
      within(panel).getByText("Add at least one deli item before checkout.")
    ).toBeInTheDocument();
    expect(
      within(panel).getByRole("button", { name: "Create pickup order" })
    ).toBeDisabled();
  });

  test("renders pickup window loading without hiding the basket review", () => {
    const deferred = createDeferred<ApiResult<PickupWindowsResponse>>();

    renderCheckoutPanel({
      client: createCheckoutClient({
        pickupWindowResults: [deferred.promise]
      })
    });

    const panel = screen.getByRole("dialog", { name: "Pickup checkout" });

    expect(within(panel).getByRole("status")).toHaveTextContent(
      "Loading pickup windows."
    );
    expect(within(panel).getByText("Fresh Tagliatelle")).toBeInTheDocument();
  });

  test("renders pickup window load errors with a retry control", async () => {
    const client = createCheckoutClient({
      pickupWindowResults: [
        httpError(500, "Could not load pickup windows."),
        success({ pickup_windows: pickupWindows })
      ]
    });

    renderCheckoutPanel({ client });

    const panel = screen.getByRole("dialog", { name: "Pickup checkout" });
    expect(await within(panel).findByRole("alert")).toHaveTextContent(
      "Could not load pickup windows."
    );

    fireEvent.click(within(panel).getByRole("button", { name: "Retry windows" }));

    expect(await within(panel).findByLabelText("Pickup window")).toHaveValue(
      "today-afternoon"
    );
  });

  test("renders the ready checkout form with accessible fields", async () => {
    renderCheckoutPanel();

    const panel = screen.getByRole("dialog", { name: "Pickup checkout" });

    expect(await within(panel).findByLabelText("Contact name")).toBeEnabled();
    expect(within(panel).getByLabelText("Contact email")).toBeEnabled();
    expect(within(panel).getByLabelText("Pickup window")).toHaveDisplayValue(
      "Today afternoon pickup"
    );
    expect(within(panel).getAllByText("£8.50").length).toBeGreaterThan(0);
  });

  test("blocks checkout while the basket is updating", async () => {
    const client = createCheckoutClient({
      pickupWindowResults: [success({ pickup_windows: pickupWindows })],
      checkoutResults: [success(checkoutResponse)]
    });

    renderCheckoutPanel({ client, isBasketUpdating: true });

    const panel = screen.getByRole("dialog", { name: "Pickup checkout" });

    expect(await within(panel).findByText("Basket is updating.")).toBeInTheDocument();
    expect(
      within(panel).getByRole("button", { name: "Create pickup order" })
    ).toBeDisabled();

    fireEvent.submit(within(panel).getByRole("button", { name: "Create pickup order" }));

    expect(client.createCheckout).not.toHaveBeenCalled();
  });

  test("disables submission while checkout is pending", async () => {
    const deferredCheckout = createDeferred<ApiResult<CheckoutResponse>>();
    const client = createCheckoutClient({
      pickupWindowResults: [success({ pickup_windows: pickupWindows })],
      checkoutResults: [deferredCheckout.promise]
    });

    renderCheckoutPanel({ client });
    const panel = screen.getByRole("dialog", { name: "Pickup checkout" });

    await fillReadyForm(panel);
    fireEvent.click(
      within(panel).getByRole("button", { name: "Create pickup order" })
    );

    await waitFor(() => {
      expect(
        within(panel).getByRole("button", { name: "Creating order" })
      ).toBeDisabled();
    });
  });

  test("renders backend validation errors near the form", async () => {
    const client = createCheckoutClient({
      pickupWindowResults: [success({ pickup_windows: pickupWindows })],
      checkoutResults: [httpError(422, "Contact email must include @.")]
    });

    renderCheckoutPanel({ client });
    const panel = screen.getByRole("dialog", { name: "Pickup checkout" });

    await fillReadyForm(panel, { contactEmail: "ada@example.com" });
    fireEvent.click(
      within(panel).getByRole("button", { name: "Create pickup order" })
    );

    expect(await within(panel).findByRole("alert")).toHaveTextContent(
      "Contact email must include @."
    );
  });

  test("shows order confirmation and returns the emptied basket", async () => {
    const onCheckoutSuccess = vi.fn();
    const client = createCheckoutClient({
      pickupWindowResults: [success({ pickup_windows: pickupWindows })],
      checkoutResults: [success(checkoutResponse)]
    });

    renderCheckoutPanel({ client, onCheckoutSuccess });
    const panel = screen.getByRole("dialog", { name: "Pickup checkout" });

    await fillReadyForm(panel);
    fireEvent.click(
      within(panel).getByRole("button", { name: "Create pickup order" })
    );

    expect(
      await within(panel).findByRole("heading", {
        level: 3,
        name: "Order confirmed"
      })
    ).toBeInTheDocument();
    expect(within(panel).getByText("order-1")).toBeInTheDocument();
    expect(within(panel).getByText("ada@example.com")).toBeInTheDocument();
    expect(within(panel).getByText("Today afternoon pickup")).toBeInTheDocument();
    expect(within(panel).getByText("Fresh Tagliatelle x 2")).toBeInTheDocument();
    expect(
      within(panel).getByText("Thank you for shopping with us.")
    ).toBeInTheDocument();
    const confirmation = within(panel).getByRole("status");
    expect(within(confirmation).getByText("2 items")).toBeInTheDocument();
    expect(onCheckoutSuccess).toHaveBeenCalledWith(emptyBasket);
  });
});

async function fillReadyForm(
  panel: HTMLElement,
  values: {
    contactName?: string;
    contactEmail?: string;
    pickupWindowId?: string;
  } = {}
) {
  fireEvent.change(await within(panel).findByLabelText("Contact name"), {
    target: { value: values.contactName ?? "Ada Lovelace" }
  });
  fireEvent.change(within(panel).getByLabelText("Contact email"), {
    target: { value: values.contactEmail ?? "ada@example.com" }
  });
  fireEvent.change(within(panel).getByLabelText("Pickup window"), {
    target: { value: values.pickupWindowId ?? "today-afternoon" }
  });
}

function renderCheckoutPanel({
  basket = { status: "success", basket: tagliatelleBasket },
  client = createCheckoutClient({
    pickupWindowResults: [success({ pickup_windows: pickupWindows })],
    checkoutResults: [success(checkoutResponse)]
  }),
  isBasketUpdating = false,
  onClose = vi.fn(),
  onCheckoutSuccess = vi.fn()
}: {
  basket?: BasketLoadState;
  client?: CheckoutClient;
  isBasketUpdating?: boolean;
  onClose?: () => void;
  onCheckoutSuccess?: (basket: Basket) => void;
} = {}) {
  render(
    <CheckoutPanel
      basket={basket}
      client={client}
      isBasketUpdating={isBasketUpdating}
      onClose={onClose}
      onCheckoutSuccess={onCheckoutSuccess}
    />
  );
}

function createCheckoutClient({
  pickupWindowResults = [],
  checkoutResults = []
}: {
  pickupWindowResults?: Array<
    ApiResult<PickupWindowsResponse> | Promise<ApiResult<PickupWindowsResponse>>
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

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((innerResolve) => {
    resolve = innerResolve;
  });

  return { promise, resolve };
}
