import type { KeyboardEvent } from "react";

import type { CatalogCategory, CatalogCategoryId } from "../../types/catalog";

export type CatalogFiltersProps = {
  categories: CatalogCategory[];
  selectedCategoryId: CatalogCategoryId | null;
  searchText: string;
  onCategorySelect: (categoryId: CatalogCategoryId | null) => void;
  onSearchTextChange: (searchText: string) => void;
  onSearchSubmit: (searchText: string) => void;
  onReset: () => void;
  hasActiveFilters?: boolean;
  showResetAction?: boolean;
};

export function CatalogFilters({
  categories,
  selectedCategoryId,
  searchText,
  onCategorySelect,
  onSearchTextChange,
  onSearchSubmit,
  onReset,
  hasActiveFilters,
  showResetAction = true
}: CatalogFiltersProps) {
  const shouldShowReset =
    hasActiveFilters ?? (selectedCategoryId !== null || searchText.trim() !== "");

  function submitSearch() {
    onSearchSubmit(searchText);
  }

  function handleSearchKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      submitSearch();
    }
  }

  return (
    <section aria-label="Browse products" className="catalog-filters">
      <fieldset className="catalog-filters__categories">
        <legend id="catalog-category-filter">Category</legend>
        <div
          aria-labelledby="catalog-category-filter"
          className="catalog-filters__category-list"
          role="radiogroup"
        >
          <label className="catalog-filters__category-control">
            <input
              checked={selectedCategoryId === null}
              name="catalog-category"
              onChange={() => onCategorySelect(null)}
              type="radio"
              value="all"
            />
            All
          </label>
          {categories.map((category) => (
            <label
              className="catalog-filters__category-control"
              key={category.category_id}
            >
              <input
                checked={selectedCategoryId === category.category_id}
                name="catalog-category"
                onChange={() => onCategorySelect(category.category_id)}
                type="radio"
                value={category.category_id}
              />
              {category.label}
            </label>
          ))}
        </div>
      </fieldset>
      <form
        aria-label="Catalog search"
        className="catalog-filters__search"
        onSubmit={(event) => {
          event.preventDefault();
          submitSearch();
        }}
      >
        <label className="catalog-filters__search-field" htmlFor="catalog-search">
          <span>Search catalog</span>
          <input
            id="catalog-search"
            onChange={(event) => onSearchTextChange(event.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search products"
            type="search"
            value={searchText}
          />
        </label>
        <button className="catalog-filters__action" type="submit">
          Search
        </button>
        {shouldShowReset && showResetAction ? (
          <button
            aria-label="Reset filters"
            className="catalog-filters__action catalog-filters__action--secondary"
            onClick={onReset}
            type="button"
          >
            Reset
          </button>
        ) : null}
      </form>
    </section>
  );
}
