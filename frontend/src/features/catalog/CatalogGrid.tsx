import { CatalogCard } from "./CatalogCard";
import type { CatalogProductSummary } from "../../types/catalog";

type CatalogGridProps = {
  products: CatalogProductSummary[];
  onSelectProduct: (skuId: string) => void;
  onResetFilters: () => void;
};

export function CatalogGrid({
  products,
  onSelectProduct,
  onResetFilters
}: CatalogGridProps) {
  const availableProducts = products.filter(isAvailableProduct);

  if (availableProducts.length === 0) {
    return (
      <section className="catalog-empty" aria-labelledby="catalog-empty-heading">
        <h2 id="catalog-empty-heading">No matching products</h2>
        <p>No products match the current filters.</p>
        <button type="button" onClick={onResetFilters}>
          Reset filters
        </button>
      </section>
    );
  }

  return (
    <ul className="catalog-grid" aria-label="Catalog products">
      {availableProducts.map((product) => (
        <li key={product.sku_id}>
          <CatalogCard product={product} onSelectProduct={onSelectProduct} />
        </li>
      ))}
    </ul>
  );
}

function isAvailableProduct(product: CatalogProductSummary): boolean {
  return !("is_available" in product) || product.is_available !== false;
}
