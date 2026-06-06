import { CatalogDetail } from "./CatalogDetail";
import { CatalogFilters } from "./CatalogFilters";
import { CatalogGrid } from "./CatalogGrid";
import { useCatalogBrowser } from "./useCatalogBrowser";

type CatalogBrowserProps = {
  basketQuantities?: Record<string, number>;
  isActive?: boolean;
  isAddPending?: boolean;
  onAddProduct?: (skuId: string, quantity: number) => void;
};

export function CatalogBrowser({
  basketQuantities = {},
  isActive = true,
  isAddPending = false,
  onAddProduct = () => {}
}: CatalogBrowserProps) {
  const {
    catalog,
    detail,
    selectedCategoryId,
    draftSearch,
    committedSearch,
    selectCategory,
    updateDraftSearch,
    submitSearch,
    resetFilters,
    reloadCatalog,
    openDetail,
    closeDetail
  } = useCatalogBrowser({ isActive });

  const productCount = catalog.products.length;
  const productCountLabel =
    catalog.status === "loading"
      ? "Loading products"
      : `${productCount} ${productCount === 1 ? "product" : "products"}`;
  const isResetDisabled =
    selectedCategoryId === null && !draftSearch.trim() && !committedSearch;

  return (
    <section className="catalog-browser" aria-labelledby="catalog-title">
      <div className="catalog-browser__controls">
        <div className="catalog-browser__header">
          <div className="catalog-browser__header-copy">
            <h1 id="catalog-title">Shop</h1>
            <p className="catalog-browser__lede">
              Browse deli products and add your picks to the basket.
            </p>
          </div>
        </div>

        {catalog.status === "error" ? null : (
          <CatalogFilters
            categories={catalog.categories}
            isResetDisabled={isResetDisabled}
            onCategorySelect={selectCategory}
            onReset={resetFilters}
            onSearchSubmit={submitSearch}
            onSearchTextChange={updateDraftSearch}
            searchText={draftSearch}
            selectedCategoryId={selectedCategoryId}
          />
        )}
      </div>

      {catalog.status === "error" ? (
        <div className="catalog-state catalog-state--error" role="alert">
          <h3>Catalog unavailable</h3>
          <p>{catalog.message}</p>
          <button type="button" onClick={reloadCatalog}>
            Reload catalog
          </button>
        </div>
      ) : (
        <>
          {catalog.status === "loading" ? (
            <div className="catalog-state" role="status">
              Loading catalog products.
            </div>
          ) : null}

          <div className="catalog-browser__results-bar">
            <p className="catalog-browser__summary" aria-live="polite">
              {productCountLabel}
            </p>
            {committedSearch ? (
              <p className="catalog-browser__active-query">
                Showing matches for <strong>{committedSearch}</strong>
              </p>
            ) : null}
          </div>

          <div className="catalog-browser__workspace">
            <CatalogGrid
              basketQuantities={basketQuantities}
              isAddPending={isAddPending}
              onAddProduct={onAddProduct}
              onResetFilters={resetFilters}
              onSelectProduct={openDetail}
              products={catalog.products}
            />
          </div>

          <CatalogDetail
            basketQuantity={getDetailBasketQuantity(detail, basketQuantities)}
            detail={detail}
            isAddPending={isAddPending}
            onAddProduct={onAddProduct}
            onClose={closeDetail}
          />
        </>
      )}
    </section>
  );
}

function getDetailBasketQuantity(
  detail: ReturnType<typeof useCatalogBrowser>["detail"],
  basketQuantities: Record<string, number>
): number {
  if (detail.status === "closed") {
    return 0;
  }

  return basketQuantities[detail.skuId] ?? 0;
}
