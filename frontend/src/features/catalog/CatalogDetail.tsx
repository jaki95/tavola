import type { KeyboardEvent } from "react";

import { formatDietaryFacetBadges, formatMoney } from "./catalogFormat";
import { getCatalogImageAsset } from "./catalogImages";
import type { CatalogDetailState } from "./useCatalogBrowser";
import type { CatalogProductDetail } from "../../types/catalog";

type CatalogDetailProps = {
  detail: CatalogDetailState;
  basketQuantity?: number;
  isAddPending?: boolean;
  onAddProduct?: (skuId: string, quantity: number) => void;
  onClose: () => void;
};

export function CatalogDetail({
  detail,
  basketQuantity = 0,
  isAddPending = false,
  onAddProduct = () => {},
  onClose
}: CatalogDetailProps) {
  if (detail.status === "closed") {
    return null;
  }

  return (
    <div
      className="catalog-detail-backdrop"
      data-testid="catalog-detail-backdrop"
      onClick={onClose}
    >
      <section
        aria-label="Product detail"
        aria-modal="true"
        className="catalog-detail"
        role="dialog"
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            onClose();
          }
        }}
      >
        <div className="catalog-detail__header">
          <button
            className="catalog-detail__close"
            onClick={onClose}
            onKeyDown={(event) => handleCloseButtonKeyDown(event, onClose)}
            type="button"
          >
            Close product detail
          </button>
        </div>

        {detail.status === "loading" ? <LoadingDetail skuId={detail.skuId} /> : null}
        {detail.status === "error" ? (
          <ErrorDetail message={detail.message} skuId={detail.skuId} />
        ) : null}
        {detail.status === "success" ? (
          <PopulatedDetail
            basketQuantity={basketQuantity}
            isAddPending={isAddPending}
            onAddProduct={onAddProduct}
            product={detail.product}
          />
        ) : null}
      </section>
    </div>
  );
}

function LoadingDetail({ skuId }: { skuId: string }) {
  return (
    <section className="catalog-detail__state" aria-labelledby="catalog-detail-loading">
      <h2 id="catalog-detail-loading">Loading product details</h2>
      <p role="status">Fetching detail for {skuId}.</p>
    </section>
  );
}

function ErrorDetail({ message, skuId }: { message: string; skuId: string }) {
  return (
    <section className="catalog-detail__state" aria-labelledby="catalog-detail-error">
      <p className="catalog-detail__category">{skuId}</p>
      <h2 id="catalog-detail-error">Product detail</h2>
      <p role="alert">{message}</p>
    </section>
  );
}

function PopulatedDetail({
  product,
  basketQuantity,
  isAddPending,
  onAddProduct
}: {
  product: CatalogProductDetail;
  basketQuantity: number;
  isAddPending: boolean;
  onAddProduct: (skuId: string, quantity: number) => void;
}) {
  const facetLabels = formatDietaryFacetBadges(product);
  const price = formatMoney({
    amount_minor: product.unit_price_minor,
    currency: product.currency
  });
  const isInBasket = basketQuantity > 0;
  const basketQuantityLabel = formatBasketQuantityLabel(basketQuantity);

  return (
    <article
      className={`catalog-detail__content catalog-detail__content--${product.category_id}`}
    >
      <CatalogProductImage product={product} />

      <div className="catalog-detail__body">
        <h2>{product.name}</h2>
        <p>{product.detail_description}</p>

        <dl className="catalog-detail__facts">
          <div>
            <dt>Category</dt>
            <dd>{product.category_label}</dd>
          </div>
          <div>
            <dt>Unit</dt>
            <dd>{product.unit_label}</dd>
          </div>
          <div>
            <dt>Price</dt>
            <dd>{price}</dd>
          </div>
        </dl>

        {facetLabels.length > 0 ? (
          <ul className="catalog-detail__facets" aria-label="Dietary facets">
            {facetLabels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        ) : null}
        <button
          aria-label={
            isAddPending
              ? `Adding ${product.name} to basket`
              : `${isInBasket ? "Add another" : "Add"} ${product.name} to basket${
                  isInBasket ? `, ${basketQuantityLabel}` : ""
                }`
          }
          className="catalog-detail__add catalog-add-button"
          disabled={isAddPending}
          onClick={() => onAddProduct(product.sku_id, 1)}
          type="button"
        >
          <span>
            {isAddPending ? "Adding" : isInBasket ? "Add another" : "Add to basket"}
          </span>
          {isInBasket && !isAddPending ? (
            <span className="catalog-add-button__state">{basketQuantityLabel}</span>
          ) : null}
        </button>
      </div>
    </article>
  );
}

function formatBasketQuantityLabel(quantity: number): string {
  return `${quantity} in basket`;
}

function CatalogProductImage({ product }: { product: CatalogProductDetail }) {
  const image = getCatalogImageAsset(product.image_id, product.name);

  return (
    <div className="catalog-detail__image-frame">
      <img
        alt={image.alt}
        className="catalog-detail__image"
        decoding="async"
        height={image.height}
        src={image.src}
        width={image.width}
      />
    </div>
  );
}

function handleCloseButtonKeyDown(
  event: KeyboardEvent<HTMLButtonElement>,
  onClose: () => void
) {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    onClose();
  }
}
