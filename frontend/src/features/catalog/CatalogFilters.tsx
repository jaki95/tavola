import type { KeyboardEvent } from "react";

import type { CatalogCategory, CatalogCategoryId } from "../../types/catalog";

export type CatalogFiltersProps = {
  categories: CatalogCategory[];
  isResetDisabled?: boolean;
  selectedCategoryId: CatalogCategoryId | null;
  searchText: string;
  onCategorySelect: (categoryId: CatalogCategoryId | null) => void;
  onSearchTextChange: (searchText: string) => void;
  onSearchSubmit: (searchText: string) => void;
  onReset: () => void;
};

export function CatalogFilters({
  categories,
  isResetDisabled = false,
  selectedCategoryId,
  searchText,
  onCategorySelect,
  onSearchTextChange,
  onSearchSubmit,
  onReset
}: CatalogFiltersProps) {
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
    <section aria-label="Catalog filters" className="catalog-filters">
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
          Search catalog
          <input
            id="catalog-search"
            onChange={(event) => onSearchTextChange(event.target.value)}
            onKeyDown={handleSearchKeyDown}
            type="search"
            value={searchText}
          />
        </label>
        <button className="catalog-filters__action" type="submit">
          Search
        </button>
        <button
          className="catalog-filters__action catalog-filters__action--secondary"
          disabled={isResetDisabled}
          onClick={onReset}
          type="button"
        >
          Reset filters
        </button>
      </form>
    </section>
  );
}
