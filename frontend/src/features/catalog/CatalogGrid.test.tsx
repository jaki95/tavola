import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { CatalogGrid } from "./CatalogGrid";
import type { CatalogProductSummary } from "../../types/catalog";

const tagliatelle: CatalogProductSummary = {
  sku_id: "fresh-tagliatelle-250g",
  name: "Fresh Tagliatelle",
  category_id: "primi",
  category_label: "Primi",
  unit_label: "250g",
  unit_price_minor: 425,
  currency: "GBP",
  short_description: "Fresh egg pasta cut into ribbons for a quick supper.",
  image_id: "fresh-tagliatelle-250g",
  is_vegetarian: true,
  is_vegan: false,
  is_gluten_free: false,
  contains_alcohol: false
};

const ravioli: CatalogProductSummary = {
  ...tagliatelle,
  sku_id: "ricotta-spinach-ravioli-300g",
  name: "Ricotta Spinach Ravioli",
  unit_label: "300g",
  unit_price_minor: 575,
  short_description: "Fresh ravioli filled with ricotta and spinach.",
  image_id: "ricotta-spinach-ravioli-300g"
};

describe("CatalogGrid", () => {
  test("renders backend catalog products as semantic product cards", () => {
    render(
      <CatalogGrid
        products={[tagliatelle]}
        onSelectProduct={vi.fn()}
        onResetFilters={vi.fn()}
      />
    );

    const list = screen.getByRole("list", { name: "Catalog products" });
    const item = within(list).getAllByRole("listitem")[0];
    if (!item) {
      throw new Error("Expected at least one catalog product card.");
    }

    expect(
      within(item).getByRole("heading", { level: 3, name: "Fresh Tagliatelle" })
    ).toBeInTheDocument();
    expect(within(item).getByText("Primi")).toBeInTheDocument();
    expect(within(item).getByText("250g")).toBeInTheDocument();
    expect(within(item).getByText("£4.25")).toBeInTheDocument();
    expect(
      within(item).getByText("Fresh egg pasta cut into ribbons for a quick supper.")
    ).toBeInTheDocument();
    expect(within(item).queryByText("Vegetarian")).not.toBeInTheDocument();
    expect(
      within(item).getByRole("img", { name: "Fresh Tagliatelle product image" })
    ).toBeInTheDocument();
    expect(
      within(item).getByRole("button", { name: "View details for Fresh Tagliatelle" })
    ).toBeInTheDocument();
    expect(
      within(item).getByRole("button", { name: "Add Fresh Tagliatelle to basket" })
    ).toBeInTheDocument();
  });

  test("renders known catalog image IDs as static image assets with stable dimensions", () => {
    render(
      <CatalogGrid
        products={[tagliatelle]}
        onSelectProduct={vi.fn()}
        onResetFilters={vi.fn()}
      />
    );

    const productImage = screen.getByRole("img", {
      name: "Fresh Tagliatelle product image"
    });

    expect(productImage).toBeInstanceOf(HTMLImageElement);
    expect(productImage).toHaveAttribute("src", expect.stringMatching(/\S/));
    expect(productImage).toHaveAttribute("width", expect.stringMatching(/^[1-9]\d*$/));
    expect(productImage).toHaveAttribute("height", expect.stringMatching(/^[1-9]\d*$/));
    expect(productImage).toBeEmptyDOMElement();
  });

  test("renders a designed fallback image for unknown image IDs without leaking backend identifiers", () => {
    const productWithUnknownImage = {
      ...tagliatelle,
      image_id: "missing-demo-image-id"
    };

    render(
      <CatalogGrid
        products={[productWithUnknownImage]}
        onSelectProduct={vi.fn()}
        onResetFilters={vi.fn()}
      />
    );

    const productImage = screen.getByRole("img", {
      name: "Fresh Tagliatelle product image"
    });

    expect(productImage).toBeInstanceOf(HTMLImageElement);
    expect(productImage).toHaveAttribute("src", expect.stringMatching(/\S/));
    expect(productImage).not.toHaveTextContent("missing demo image id");
  });

  test("renders only available products from browse results", () => {
    const unavailableLasagne = {
      ...tagliatelle,
      sku_id: "lasagne-al-forno",
      name: "Lasagne al Forno",
      is_available: false
    } satisfies CatalogProductSummary & { is_available: false };

    render(
      <CatalogGrid
        products={[tagliatelle, unavailableLasagne]}
        onSelectProduct={vi.fn()}
        onResetFilters={vi.fn()}
      />
    );

    expect(
      screen.getByRole("heading", { level: 3, name: "Fresh Tagliatelle" })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { level: 3, name: "Lasagne al Forno" })
    ).not.toBeInTheDocument();
  });

  test("calls the detail action callback with the selected SKU", () => {
    const onSelectProduct = vi.fn();

    render(
      <CatalogGrid
        products={[tagliatelle]}
        onSelectProduct={onSelectProduct}
        onResetFilters={vi.fn()}
      />
    );

    const productCard = screen
      .getByRole("heading", { level: 3, name: "Fresh Tagliatelle" })
      .closest("article");
    if (!productCard) {
      throw new Error("Expected Fresh Tagliatelle to render inside a product card.");
    }

    fireEvent.click(
      within(productCard).getByRole("button", {
        name: "View details for Fresh Tagliatelle"
      })
    );

    expect(onSelectProduct).toHaveBeenCalledTimes(1);
    expect(onSelectProduct).toHaveBeenCalledWith("fresh-tagliatelle-250g");
  });

  test("calls the add action callback with one unit of the selected SKU", () => {
    const onAddProduct = vi.fn();

    render(
      <CatalogGrid
        products={[tagliatelle]}
        onAddProduct={onAddProduct}
        onSelectProduct={vi.fn()}
        onResetFilters={vi.fn()}
      />
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Add Fresh Tagliatelle to basket" })
    );

    expect(onAddProduct).toHaveBeenCalledTimes(1);
    expect(onAddProduct).toHaveBeenCalledWith("fresh-tagliatelle-250g", 1);
  });

  test("shows when a catalog product is already in the basket", () => {
    render(
      <CatalogGrid
        basketQuantities={{ "fresh-tagliatelle-250g": 2 }}
        products={[tagliatelle]}
        onAddProduct={vi.fn()}
        onSelectProduct={vi.fn()}
        onResetFilters={vi.fn()}
      />
    );

    const productCard = screen
      .getByRole("heading", { level: 3, name: "Fresh Tagliatelle" })
      .closest("article");
    if (!productCard) {
      throw new Error("Expected Fresh Tagliatelle to render inside a product card.");
    }

    const addButton = within(productCard).getByRole("button", {
      name: "Add another Fresh Tagliatelle to basket, 2 in basket"
    });

    expect(within(addButton).getByText("Add")).toBeInTheDocument();
    expect(within(productCard).getByTitle("2 in basket")).toHaveTextContent("2");
  });

  test("keeps catalog add controls visually stable while a product is being added", () => {
    render(
      <CatalogGrid
        basketQuantities={{
          "fresh-tagliatelle-250g": 2,
          "ricotta-spinach-ravioli-300g": 1
        }}
        pendingAddSkuId="fresh-tagliatelle-250g"
        products={[tagliatelle, ravioli]}
        onAddProduct={vi.fn()}
        onSelectProduct={vi.fn()}
        onResetFilters={vi.fn()}
      />
    );

    const pendingAddButton = screen.getByRole("button", {
      name: "Add another Fresh Tagliatelle to basket, 2 in basket"
    });
    expect(pendingAddButton).toBeEnabled();
    expect(pendingAddButton).toHaveAttribute("aria-disabled", "true");
    expect(within(pendingAddButton).getByText("Add")).toBeInTheDocument();
    expect(screen.getByTitle("2 in basket")).toHaveTextContent("2");
    expect(
      screen.getByRole("button", {
        name: "Add another Ricotta Spinach Ravioli to basket, 1 in basket"
      })
    ).toBeEnabled();
    expect(screen.getByTitle("1 in basket")).toHaveTextContent("1");
  });

  test("shows an empty matching-products state with reset action", () => {
    const onResetFilters = vi.fn();

    render(
      <CatalogGrid
        products={[]}
        onSelectProduct={vi.fn()}
        onResetFilters={onResetFilters}
      />
    );

    expect(
      screen.getByRole("heading", { level: 2, name: "No matching products" })
    ).toBeInTheDocument();
    expect(
      screen.getByText("No products match the current filters.")
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reset filters" }));

    expect(onResetFilters).toHaveBeenCalledTimes(1);
  });
});
