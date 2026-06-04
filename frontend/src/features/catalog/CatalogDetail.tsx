import type { KeyboardEvent } from "react";

import { formatDietaryFacetBadges, formatMoney } from "./catalogFormat";
import { getCatalogImageAsset } from "./catalogImages";
import type { CatalogDetailState } from "./useCatalogBrowser";
import type { CatalogProductDetail } from "../../types/catalog";

type CatalogDetailProps = {
  detail: CatalogDetailState;
  onClose: () => void;
};

export function CatalogDetail({ detail, onClose }: CatalogDetailProps) {
  if (detail.status === "closed") {
    return null;
  }

  return (
    <aside
      aria-label="Product detail"
      className="catalog-detail"
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
      {detail.status === "success" ? <PopulatedDetail product={detail.product} /> : null}
    </aside>
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

function PopulatedDetail({ product }: { product: CatalogProductDetail }) {
  const facetLabels = formatDietaryFacetBadges(product);
  const price = formatMoney({
    amount_minor: product.unit_price_minor,
    currency: product.currency
  });

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
      </div>
    </article>
  );
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
