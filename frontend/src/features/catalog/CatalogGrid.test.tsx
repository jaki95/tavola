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
    expect(within(item).getByText("Vegetarian")).toBeInTheDocument();
    expect(
      within(item).getByRole("img", { name: "Fresh Tagliatelle product image" })
    ).toBeInTheDocument();
    expect(
      within(item).getByRole("button", { name: "View details for Fresh Tagliatelle" })
    ).toBeInTheDocument();
    expect(
      within(item).queryByRole("button", { name: /add/i })
    ).not.toBeInTheDocument();
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

    fireEvent.click(
      screen.getByRole("button", { name: "View details for Fresh Tagliatelle" })
    );

    expect(onSelectProduct).toHaveBeenCalledTimes(1);
    expect(onSelectProduct).toHaveBeenCalledWith("fresh-tagliatelle-250g");
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
