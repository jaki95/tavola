import { CatalogCard } from "./CatalogCard";
import type { CatalogProductSummary } from "../../types/catalog";

type CatalogGridProps = {
  products: CatalogProductSummary[];
  basketQuantities?: Record<string, number>;
  isAddPending?: boolean;
  onAddProduct?: (skuId: string, quantity: number) => void;
  onSelectProduct: (skuId: string) => void;
  onResetFilters: () => void;
};

export function CatalogGrid({
  products,
  basketQuantities = {},
  isAddPending = false,
  onAddProduct = () => {},
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
          <CatalogCard
            basketQuantity={basketQuantities[product.sku_id] ?? 0}
            isAddPending={isAddPending}
            onAddProduct={onAddProduct}
            onSelectProduct={onSelectProduct}
            product={product}
          />
        </li>
      ))}
    </ul>
  );
}

function isAvailableProduct(product: CatalogProductSummary): boolean {
  return !("is_available" in product) || product.is_available !== false;
}
