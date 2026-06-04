import type { CSSProperties, KeyboardEvent } from "react";

import type { CatalogCategory, CatalogCategoryId } from "../../types/catalog";

export type CatalogFiltersProps = {
  categories: CatalogCategory[];
  selectedCategoryId: CatalogCategoryId | null;
  searchText: string;
  onCategorySelect: (categoryId: CatalogCategoryId | null) => void;
  onSearchTextChange: (searchText: string) => void;
  onSearchSubmit: (searchText: string) => void;
  onReset: () => void;
};

const categoryControlStyle = {
  alignItems: "center",
  border: "1px solid #c8c0b2",
  borderRadius: "6px",
  display: "inline-flex",
  gap: "0.35rem",
  justifyContent: "center",
  minHeight: "2.5rem",
  minWidth: "7rem",
  padding: "0 0.75rem"
} satisfies CSSProperties;

const filterSectionStyle = {
  display: "grid",
  gap: "1rem"
} satisfies CSSProperties;

const categoryGroupStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "0.5rem"
} satisfies CSSProperties;

const searchFormStyle = {
  alignItems: "end",
  display: "grid",
  gap: "0.75rem",
  gridTemplateColumns: "minmax(18rem, 26rem) 7rem 8rem"
} satisfies CSSProperties;

const searchFieldStyle = {
  display: "grid",
  gap: "0.35rem"
} satisfies CSSProperties;

const searchInputStyle = {
  border: "1px solid #c8c0b2",
  borderRadius: "6px",
  boxSizing: "border-box",
  minHeight: "2.5rem",
  minWidth: 0,
  padding: "0 0.75rem",
  width: "100%"
} satisfies CSSProperties;

const actionButtonStyle = {
  border: "1px solid #8d2f23",
  borderRadius: "6px",
  minHeight: "2.5rem",
  minWidth: "7rem",
  padding: "0 0.75rem"
} satisfies CSSProperties;

export function CatalogFilters({
  categories,
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
    <section aria-label="Catalog filters" style={filterSectionStyle}>
      <fieldset>
        <legend id="catalog-category-filter">Category</legend>
        <div
          aria-labelledby="catalog-category-filter"
          role="radiogroup"
          style={categoryGroupStyle}
        >
          <label style={categoryControlStyle}>
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
            <label key={category.category_id} style={categoryControlStyle}>
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
        onSubmit={(event) => {
          event.preventDefault();
          submitSearch();
        }}
        style={searchFormStyle}
      >
        <label htmlFor="catalog-search" style={searchFieldStyle}>
          Search catalog
          <input
            id="catalog-search"
            onChange={(event) => onSearchTextChange(event.target.value)}
            onKeyDown={handleSearchKeyDown}
            style={searchInputStyle}
            type="search"
            value={searchText}
          />
        </label>
        <button style={actionButtonStyle} type="submit">
          Search
        </button>
        <button onClick={onReset} style={actionButtonStyle} type="button">
          Reset filters
        </button>
      </form>
    </section>
  );
}
