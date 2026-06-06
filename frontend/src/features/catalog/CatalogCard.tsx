import { formatMoney } from "./catalogFormat";
import { getCatalogImageAsset } from "./catalogImages";
import type { CatalogProductSummary } from "../../types/catalog";

type CatalogCardProps = {
  product: CatalogProductSummary;
  basketQuantity?: number;
  isAddPending?: boolean;
  onAddProduct?: (skuId: string, quantity: number) => void;
  onSelectProduct: (skuId: string) => void;
};

export function CatalogCard({
  product,
  basketQuantity = 0,
  isAddPending = false,
  onAddProduct = () => {},
  onSelectProduct
}: CatalogCardProps) {
  const image = getCatalogImageAsset(product.image_id, product.name);
  const isInBasket = basketQuantity > 0;
  const basketQuantityLabel = formatBasketQuantityLabel(basketQuantity);
  const price = formatMoney({
    amount_minor: product.unit_price_minor,
    currency: product.currency
  });

  return (
    <article
      className={`catalog-card catalog-card--${product.category_id}`}
      aria-labelledby={`${product.sku_id}-name`}
    >
      <div className="catalog-card__image-frame">
        <img
          alt={image.alt}
          className="catalog-card__image"
          decoding="async"
          height={image.height}
          loading="lazy"
          src={image.src}
          width={image.width}
        />
      </div>
      <div className="catalog-card__body">
        <p className="catalog-card__category">{product.category_label}</p>
        <h3 id={`${product.sku_id}-name`}>{product.name}</h3>
        <div className="catalog-card__purchase">
          <p className="catalog-card__price">{price}</p>
          <p className="catalog-card__unit">{product.unit_label}</p>
        </div>
        <p className="catalog-card__description">{product.short_description}</p>
        <div className="catalog-card__actions">
          <button
            aria-label={`View details for ${product.name}`}
            className="catalog-card__detail-action"
            title={`View details for ${product.name}`}
            type="button"
            onClick={() => onSelectProduct(product.sku_id)}
          >
            <span aria-hidden="true">i</span>
          </button>
          <div className="catalog-card__basket-action">
            {isInBasket && !isAddPending ? (
              <span
                aria-live="polite"
                className="catalog-card__basket-quantity"
                title={basketQuantityLabel}
              >
                {basketQuantity}
              </span>
            ) : null}
            <button
              aria-label={
                isAddPending
                  ? `Adding ${product.name} to basket`
                  : `${isInBasket ? "Add another" : "Add"} ${product.name} to basket${
                      isInBasket ? `, ${basketQuantityLabel}` : ""
                    }`
              }
              className="catalog-card__add catalog-add-button"
              disabled={isAddPending}
              type="button"
              onClick={() => onAddProduct(product.sku_id, 1)}
            >
              <span>{isAddPending ? "Adding" : "Add"}</span>
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

function formatBasketQuantityLabel(quantity: number): string {
  return `${quantity} in basket`;
}
