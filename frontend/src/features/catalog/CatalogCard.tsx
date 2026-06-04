import {
  formatDietaryFacetBadges,
  formatMoney
} from "./catalogFormat";
import type { CatalogProductSummary } from "../../types/catalog";

type CatalogCardProps = {
  product: CatalogProductSummary;
  onSelectProduct: (skuId: string) => void;
};

export function CatalogCard({ product, onSelectProduct }: CatalogCardProps) {
  const dietaryBadges = formatDietaryFacetBadges(product);

  return (
    <article
      className={`catalog-card catalog-card--${product.category_id}`}
      aria-labelledby={`${product.sku_id}-name`}
    >
      <div
        className="catalog-card__image"
        role="img"
        aria-label={`${product.name} product image`}
      >
        <span aria-hidden="true">{formatImageId(product.image_id)}</span>
      </div>
      <div className="catalog-card__body">
        <p className="catalog-card__category">{product.category_label}</p>
        <h3 id={`${product.sku_id}-name`}>{product.name}</h3>
        <p className="catalog-card__description">{product.short_description}</p>
        <dl className="catalog-card__facts">
          <div>
            <dt>Unit</dt>
            <dd>{product.unit_label}</dd>
          </div>
          <div>
            <dt>Price</dt>
            <dd>
              {formatMoney({
                amount_minor: product.unit_price_minor,
                currency: product.currency
              })}
            </dd>
          </div>
        </dl>
        {dietaryBadges.length > 0 ? (
          <ul className="catalog-card__badges" aria-label="Dietary badges">
            {dietaryBadges.map((badge) => (
              <li key={badge}>{badge}</li>
            ))}
          </ul>
        ) : null}
        <button
          aria-label={`View details for ${product.name}`}
          type="button"
          onClick={() => onSelectProduct(product.sku_id)}
        >
          View details
        </button>
      </div>
    </article>
  );
}

function formatImageId(imageId: string): string {
  return imageId.trim().replace(/[-_]+/g, " ");
}
