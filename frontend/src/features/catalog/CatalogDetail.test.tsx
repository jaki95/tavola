import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { CatalogDetail } from "./CatalogDetail";
import type { CatalogProductDetail } from "../../types/catalog";

const tagliatelle: CatalogProductDetail = {
  sku_id: "fresh-tagliatelle-250g",
  name: "Fresh Tagliatelle",
  category_id: "primi",
  category_label: "Primi",
  unit_label: "250g",
  unit_price_minor: 425,
  currency: "GBP",
  short_description: "Fresh egg pasta cut into ribbons for a quick supper.",
  detail_description:
    "Silky tagliatelle made with durum wheat flour and free-range egg. Toss with sugo for a simple Tavola supper.",
  image_id: "fresh-tagliatelle-250g",
  is_vegetarian: true,
  is_vegan: false,
  is_gluten_free: false,
  contains_alcohol: false
};

describe("CatalogDetail", () => {
  test("does not render a detail side panel when closed", () => {
    render(<CatalogDetail detail={{ status: "closed" }} onClose={vi.fn()} />);

    expect(
      screen.queryByRole("complementary", { name: "Product detail" })
    ).not.toBeInTheDocument();
  });

  test("shows an explicit loading state scoped to the detail side panel", () => {
    render(
      <CatalogDetail
        detail={{ status: "loading", skuId: "fresh-tagliatelle-250g" }}
        onClose={vi.fn()}
      />
    );

    const panel = screen.getByRole("complementary", { name: "Product detail" });

    expect(within(panel).getByText("Loading product details")).toBeInTheDocument();
    expect(within(panel).getByRole("status")).toHaveTextContent(
      "Fetching detail for fresh-tagliatelle-250g."
    );
  });

  test("keeps detail errors inside the panel and lets customers close them", () => {
    const onClose = vi.fn();

    render(
      <CatalogDetail
        detail={{
          status: "error",
          skuId: "fresh-tagliatelle-250g",
          message: "Request failed with status 404."
        }}
        onClose={onClose}
      />
    );

    const panel = screen.getByRole("complementary", { name: "Product detail" });

    expect(
      within(panel).getByRole("heading", { level: 2, name: "Product detail" })
    ).toBeInTheDocument();
    expect(within(panel).getByRole("alert")).toHaveTextContent(
      "Request failed with status 404."
    );

    fireEvent.click(within(panel).getByRole("button", { name: "Close product detail" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test("closes from the close button with the keyboard", () => {
    const onClose = vi.fn();

    render(
      <CatalogDetail
        detail={{ status: "success", skuId: tagliatelle.sku_id, product: tagliatelle }}
        onClose={onClose}
      />
    );

    const closeButton = screen.getByRole("button", {
      name: "Close product detail"
    });

    closeButton.focus();
    fireEvent.keyDown(closeButton, { key: "Enter" });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test("renders populated product detail from backend fields without purchase placeholders", () => {
    render(
      <CatalogDetail
        detail={{ status: "success", skuId: tagliatelle.sku_id, product: tagliatelle }}
        onClose={vi.fn()}
      />
    );

    const panel = screen.getByRole("complementary", { name: "Product detail" });

    expect(
      within(panel).getByRole("heading", { level: 2, name: "Fresh Tagliatelle" })
    ).toBeInTheDocument();
    expect(within(panel).getByText("Primi")).toBeInTheDocument();
    expect(within(panel).getByText("250g")).toBeInTheDocument();
    expect(within(panel).getByText("£4.25")).toBeInTheDocument();
    expect(within(panel).getByText(tagliatelle.detail_description)).toBeInTheDocument();
    expect(within(panel).getByText("Vegetarian")).toBeInTheDocument();
    expect(
      within(panel).getByRole("img", { name: "Fresh Tagliatelle product image" })
    ).toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /add/i })).not.toBeInTheDocument();
    expect(within(panel).queryByText(/basket/i)).not.toBeInTheDocument();
    expect(within(panel).queryByText(/good for/i)).not.toBeInTheDocument();
    expect(within(panel).queryByText("primo")).not.toBeInTheDocument();
  });

  test("renders the detail product image as a static asset with stable desktop dimensions", () => {
    render(
      <CatalogDetail
        detail={{ status: "success", skuId: tagliatelle.sku_id, product: tagliatelle }}
        onClose={vi.fn()}
      />
    );

    const panel = screen.getByRole("complementary", { name: "Product detail" });
    const productImage = within(panel).getByRole("img", {
      name: "Fresh Tagliatelle product image"
    });

    expect(productImage).toBeInstanceOf(HTMLImageElement);
    expect(productImage).toHaveAttribute("src", expect.stringMatching(/\S/));
    expect(productImage).toHaveAttribute("width", expect.stringMatching(/^[1-9]\d*$/));
    expect(productImage).toHaveAttribute("height", expect.stringMatching(/^[1-9]\d*$/));
    expect(productImage).toBeEmptyDOMElement();
  });
});
