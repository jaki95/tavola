import { fireEvent, render, screen } from "@testing-library/react";
import { type ComponentProps, useState } from "react";
import { describe, expect, test, vi } from "vitest";

import { CatalogFilters } from "./CatalogFilters";
import type { CatalogCategory } from "../../types/catalog";

const categories: CatalogCategory[] = [
  { category_id: "primi", label: "Primi" },
  { category_id: "antipasti", label: "Antipasti" }
];

function renderCatalogFilters(
  overrides: Partial<ComponentProps<typeof CatalogFilters>> = {}
) {
  const props: ComponentProps<typeof CatalogFilters> = {
    categories,
    selectedCategoryId: null,
    searchText: "",
    onCategorySelect: vi.fn(),
    onSearchTextChange: vi.fn(),
    onSearchSubmit: vi.fn(),
    onReset: vi.fn(),
    ...overrides
  };

  render(<CatalogFilters {...props} />);

  return props;
}

describe("CatalogFilters", () => {
  test("renders All plus ordered API categories as accessible category controls", () => {
    renderCatalogFilters({ selectedCategoryId: "primi" });

    const categoryGroup = screen.getByRole("radiogroup", {
      name: "Category"
    });
    const categoryControls = screen.getAllByRole("radio");

    expect(categoryGroup).toBeInTheDocument();
    expect(categoryControls.map((control) => control.getAttribute("value"))).toEqual([
      "all",
      "primi",
      "antipasti"
    ]);
    expect(screen.getByRole("radio", { name: "Primi" })).toBeChecked();
    screen.getByRole("radio", { name: "All" }).focus();
    expect(screen.getByRole("radio", { name: "All" })).toHaveFocus();
    expect(screen.queryByRole("radio", { name: /vegetarian/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("radio", { name: /vegan/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("radio", { name: /gluten/i })).not.toBeInTheDocument();
  });

  test("selects categories through callback props without transport coupling", () => {
    const props = renderCatalogFilters({ selectedCategoryId: "primi" });

    fireEvent.click(screen.getByRole("radio", { name: "Antipasti" }));
    fireEvent.click(screen.getByRole("radio", { name: "All" }));

    expect(props.onCategorySelect).toHaveBeenNthCalledWith(1, "antipasti");
    expect(props.onCategorySelect).toHaveBeenNthCalledWith(2, null);
    expect(props.onSearchSubmit).not.toHaveBeenCalled();
    expect(props.onReset).not.toHaveBeenCalled();
  });

  test("shows a labelled search field and submits the draft search on Enter or button", () => {
    const onSearchTextChange = vi.fn();
    const onSearchSubmit = vi.fn();

    function ControlledCatalogFilters() {
      const [searchText, setSearchText] = useState("fresh pasta");

      return (
        <CatalogFilters
          categories={categories}
          onCategorySelect={vi.fn()}
          onReset={vi.fn()}
          onSearchSubmit={onSearchSubmit}
          onSearchTextChange={(nextSearchText) => {
            onSearchTextChange(nextSearchText);
            setSearchText(nextSearchText);
          }}
          searchText={searchText}
          selectedCategoryId={null}
        />
      );
    }

    render(<ControlledCatalogFilters />);

    const searchInput = screen.getByLabelText("Search catalog");

    expect(searchInput).toHaveValue("fresh pasta");

    fireEvent.change(searchInput, { target: { value: "vegan antipasti" } });
    expect(onSearchSubmit).not.toHaveBeenCalled();

    fireEvent.keyDown(searchInput, { key: "Enter" });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    expect(onSearchTextChange).toHaveBeenCalledWith("vegan antipasti");
    expect(onSearchSubmit).toHaveBeenNthCalledWith(1, "vegan antipasti");
    expect(onSearchSubmit).toHaveBeenNthCalledWith(2, "vegan antipasti");
  });

  test("delegates reset to the supplied reset callback", () => {
    const props = renderCatalogFilters({
      searchText: "pesto",
      selectedCategoryId: "pantry"
    });

    fireEvent.click(screen.getByRole("button", { name: "Reset filters" }));

    expect(props.onReset).toHaveBeenCalledOnce();
  });
});
