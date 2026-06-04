import { CatalogDetail } from "./CatalogDetail";
import { CatalogFilters } from "./CatalogFilters";
import { CatalogGrid } from "./CatalogGrid";
import { useCatalogBrowser } from "./useCatalogBrowser";

type CatalogBrowserProps = {
  isAddPending?: boolean;
  onAddProduct?: (skuId: string, quantity: number) => void;
};

export function CatalogBrowser({
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
  } = useCatalogBrowser();

  const productCount = catalog.products.length;

  return (
    <section className="catalog-browser" aria-labelledby="catalog-title">
      <div className="catalog-browser__header">
        <div>
          <p className="eyebrow">Fresh from the counter</p>
          <h2 id="catalog-title">Browse Tavola products</h2>
          <p>
            Explore real antipasti, primi, desserts, drinks, and pantry staples
            priced by the deli.
          </p>
        </div>
        <div className="catalog-browser__summary" aria-live="polite">
          <span>{catalog.status === "loading" ? "Loading" : productCount}</span>
          <span>{productCount === 1 ? "product" : "products"}</span>
        </div>
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
          <CatalogFilters
            categories={catalog.categories}
            onCategorySelect={selectCategory}
            onReset={resetFilters}
            onSearchSubmit={submitSearch}
            onSearchTextChange={updateDraftSearch}
            searchText={draftSearch}
            selectedCategoryId={selectedCategoryId}
          />

          {catalog.status === "loading" ? (
            <div className="catalog-state" role="status">
              Loading catalog products.
            </div>
          ) : null}

          {committedSearch ? (
            <p className="catalog-browser__active-query">
              Showing matches for <strong>{committedSearch}</strong>
            </p>
          ) : null}

          <div className="catalog-browser__workspace">
            <CatalogGrid
              isAddPending={isAddPending}
              onAddProduct={onAddProduct}
              onResetFilters={resetFilters}
              onSelectProduct={openDetail}
              products={catalog.products}
            />
            <CatalogDetail
              detail={detail}
              isAddPending={isAddPending}
              onAddProduct={onAddProduct}
              onClose={closeDetail}
            />
          </div>
        </>
      )}
    </section>
  );
}
