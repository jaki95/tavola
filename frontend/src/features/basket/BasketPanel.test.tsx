import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { BasketPanel } from "./BasketPanel";
import type { BasketLoadState, BasketMutationState } from "./useBasket";
import type { Basket } from "../../types/basket";

const emptyBasket: Basket = {
  basket_id: "basket-1",
  lines: [],
  total_minor: 0,
  currency: "GBP",
  item_count: 0,
  line_count: 0
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

const idleMutation: BasketMutationState = {
  status: "idle",
  message: null
};

describe("BasketPanel", () => {
  test("keeps an empty basket visible and ready for catalog additions", () => {
    renderBasketPanel({
      basket: {
        status: "success",
        basket: emptyBasket
      }
    });

    const panel = screen.getByRole("region", { name: "Current basket" });

    expect(
      within(panel).getByRole("heading", { level: 2, name: "Basket" })
    ).toBeInTheDocument();
    expect(within(panel).getByText("Your basket is empty.")).toBeInTheDocument();
    expect(
      within(panel).getByText("Add products from the catalog to start your basket.")
    ).toBeInTheDocument();
    expect(within(panel).getByText("£0.00")).toBeInTheDocument();
    expect(within(panel).getByText("0 items")).toBeInTheDocument();
    expect(
      within(panel).getByRole("button", { name: "Review and checkout" })
    ).toBeDisabled();
  });

  test("renders the loading state without hiding the previous basket", () => {
    renderBasketPanel({
      basket: {
        status: "loading",
        basket: tagliatelleBasket
      }
    });

    const panel = screen.getByRole("region", { name: "Current basket" });

    expect(within(panel).getByRole("status")).toHaveTextContent(
      "Refreshing basket."
    );
    expect(within(panel).getByText("Fresh Tagliatelle")).toBeInTheDocument();
  });

  test("renders load errors and keeps reload available", () => {
    const onReload = vi.fn();

    renderBasketPanel({
      basket: {
        status: "error",
        basket: null,
        message: "Could not load basket."
      },
      onReload
    });

    const panel = screen.getByRole("region", { name: "Current basket" });

    expect(within(panel).getByRole("alert")).toHaveTextContent(
      "Could not load basket."
    );

    fireEvent.click(within(panel).getByRole("button", { name: "Reload basket" }));

    expect(onReload).toHaveBeenCalledTimes(1);
  });

  test("renders populated basket lines and server-provided totals", () => {
    renderBasketPanel({
      basket: {
        status: "success",
        basket: tagliatelleBasket
      }
    });

    const panel = screen.getByRole("region", { name: "Current basket" });
    const line = within(panel).getByRole("listitem", { name: /fresh tagliatelle/i });

    expect(within(line).getByText("250g")).toBeInTheDocument();
    expect(
      within(line).getByRole("img", {
        name: "Fresh Tagliatelle product image"
      })
    ).toBeInTheDocument();
    expect(within(line).getByText("£4.25 each")).toBeInTheDocument();
    expect(within(line).getByText("£8.50")).toBeInTheDocument();
    expect(within(panel).getAllByText("£8.50")).toHaveLength(2);
    expect(within(panel).getByText("2 items")).toBeInTheDocument();
    expect(
      within(panel).getByRole("button", { name: "Review and checkout" })
    ).toBeEnabled();
  });

  test("opens checkout from a populated basket", () => {
    const onCheckout = vi.fn();

    renderBasketPanel({
      basket: {
        status: "success",
        basket: tagliatelleBasket
      },
      onCheckout
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Review and checkout" })
    );

    expect(onCheckout).toHaveBeenCalledTimes(1);
  });

  test("changes quantity with buttons and a numeric input", () => {
    const onSetLineQuantity = vi.fn();

    renderBasketPanel({
      basket: {
        status: "success",
        basket: tagliatelleBasket
      },
      onSetLineQuantity
    });

    const panel = screen.getByRole("region", { name: "Current basket" });
    const line = within(panel).getByRole("listitem", { name: /fresh tagliatelle/i });
    const quantityInput = within(line).getByLabelText(
      "Quantity for Fresh Tagliatelle"
    );

    fireEvent.click(
      within(line).getByRole("button", { name: "Decrease Fresh Tagliatelle quantity" })
    );
    fireEvent.click(
      within(line).getByRole("button", { name: "Increase Fresh Tagliatelle quantity" })
    );
    fireEvent.change(quantityInput, { target: { value: "11" } });
    fireEvent.blur(quantityInput);

    expect(onSetLineQuantity).toHaveBeenNthCalledWith(
      1,
      "fresh-tagliatelle-250g",
      1
    );
    expect(onSetLineQuantity).toHaveBeenNthCalledWith(
      2,
      "fresh-tagliatelle-250g",
      3
    );
    expect(onSetLineQuantity).toHaveBeenNthCalledWith(
      3,
      "fresh-tagliatelle-250g",
      11
    );
  });

  test("removes a basket line", () => {
    const onRemoveLine = vi.fn();

    renderBasketPanel({
      basket: {
        status: "success",
        basket: tagliatelleBasket
      },
      onRemoveLine
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Remove Fresh Tagliatelle from basket" })
    );

    expect(onRemoveLine).toHaveBeenCalledWith("fresh-tagliatelle-250g");
  });

  test("renders backend validation errors near basket controls", () => {
    renderBasketPanel({
      basket: {
        status: "success",
        basket: tagliatelleBasket
      },
      mutation: {
        status: "error",
        message: "Quantity must be no more than 10."
      }
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Quantity must be no more than 10."
    );
  });

  test("disables mutation controls while a basket mutation is pending", () => {
    const onSetLineQuantity = vi.fn();

    renderBasketPanel({
      basket: {
        status: "success",
        basket: tagliatelleBasket
      },
      mutation: {
        status: "pending",
        message: null
      },
      onSetLineQuantity
    });

    const quantityInput = screen.getByLabelText("Quantity for Fresh Tagliatelle");

    expect(quantityInput).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Increase Fresh Tagliatelle quantity" })
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Remove Fresh Tagliatelle from basket" })
    ).toBeDisabled();

    fireEvent.change(quantityInput, { target: { value: "4" } });
    fireEvent.blur(quantityInput);

    expect(onSetLineQuantity).not.toHaveBeenCalled();
  });
});

function renderBasketPanel({
  basket,
  mutation = idleMutation,
  onReload = vi.fn(),
  onCheckout = vi.fn(),
  onRemoveLine = vi.fn(),
  onSetLineQuantity = vi.fn()
}: {
  basket: BasketLoadState;
  mutation?: BasketMutationState;
  onCheckout?: () => void;
  onReload?: () => void;
  onRemoveLine?: (skuId: string) => void;
  onSetLineQuantity?: (skuId: string, quantity: number) => void;
}) {
  render(
    <BasketPanel
      basket={basket}
      mutation={mutation}
      onCheckout={onCheckout}
      onReload={onReload}
      onRemoveLine={onRemoveLine}
      onSetLineQuantity={onSetLineQuantity}
    />
  );
}
