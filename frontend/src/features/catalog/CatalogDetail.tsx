import { useEffect, useRef, type KeyboardEvent } from "react";

import { formatDietaryFacetBadges, formatMoney } from "./catalogFormat";
import { getCatalogImageAsset } from "./catalogImages";
import type { CatalogDetailState } from "./useCatalogBrowser";
import type { CatalogProductDetail } from "../../types/catalog";

type CatalogDetailProps = {
  detail: CatalogDetailState;
  basketQuantity?: number;
  isAddPending?: boolean;
  showAddAction?: boolean;
  onAddProduct?: (skuId: string, quantity: number) => void;
  onClose: () => void;
};

export function CatalogDetail({
  detail,
  basketQuantity = 0,
  isAddPending = false,
  showAddAction = true,
  onAddProduct = () => {},
  onClose
}: CatalogDetailProps) {
  const isOpen = detail.status !== "closed";
  const dialogRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const previouslyFocusedElement =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;
    const focusTarget = dialog ? getFocusableElements(dialog)[0] ?? dialog : null;

    focusTarget?.focus();

    return () => {
      if (previouslyFocusedElement?.isConnected) {
        previouslyFocusedElement.focus();
      }
    };
  }, [isOpen]);

  if (!isOpen) {
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
        ref={dialogRef}
        role="dialog"
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => handleDialogKeyDown(event, onClose)}
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

        {detail.status === "loading" ? <LoadingDetail /> : null}
        {detail.status === "error" ? (
          <ErrorDetail message={detail.message} />
        ) : null}
        {detail.status === "success" ? (
          <PopulatedDetail
            basketQuantity={basketQuantity}
            isAddPending={isAddPending}
            onAddProduct={onAddProduct}
            product={detail.product}
            showAddAction={showAddAction}
          />
        ) : null}
      </section>
    </div>
  );
}

function handleDialogKeyDown(
  event: KeyboardEvent<HTMLElement>,
  onClose: () => void
) {
  if (event.key === "Escape") {
    event.preventDefault();
    onClose();
    return;
  }

  if (event.key === "Tab") {
    trapDialogFocus(event);
  }
}

function trapDialogFocus(event: KeyboardEvent<HTMLElement>) {
  const dialog = event.currentTarget;
  const focusableElements = getFocusableElements(dialog);

  if (focusableElements.length === 0) {
    event.preventDefault();
    dialog.focus();
    return;
  }

  const firstElement = focusableElements[0]!;
  const lastElement = focusableElements[focusableElements.length - 1]!;
  const activeElement = document.activeElement;

  if (event.shiftKey) {
    if (activeElement === firstElement || !dialog.contains(activeElement)) {
      event.preventDefault();
      lastElement.focus();
    }
    return;
  }

  if (activeElement === lastElement || !dialog.contains(activeElement)) {
    event.preventDefault();
    firstElement.focus();
  }
}

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  return Array.from(
    container.querySelectorAll<HTMLElement>(
      [
        "a[href]",
        "button:not([disabled])",
        "input:not([disabled])",
        "select:not([disabled])",
        "textarea:not([disabled])",
        '[tabindex]:not([tabindex="-1"])'
      ].join(",")
    )
  ).filter((element) => element.tabIndex >= 0);
}

function LoadingDetail() {
  return (
    <section className="catalog-detail__state" aria-labelledby="catalog-detail-loading">
      <h2 id="catalog-detail-loading">Loading product details</h2>
      <p role="status">Fetching product details.</p>
    </section>
  );
}

function ErrorDetail({ message }: { message: string }) {
  return (
    <section className="catalog-detail__state" aria-labelledby="catalog-detail-error">
      <h2 id="catalog-detail-error">Product detail</h2>
      <p role="alert">{message}</p>
    </section>
  );
}

function PopulatedDetail({
  product,
  basketQuantity,
  isAddPending,
  showAddAction,
  onAddProduct
}: {
  product: CatalogProductDetail;
  basketQuantity: number;
  isAddPending: boolean;
  showAddAction: boolean;
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
        <p className="catalog-detail__category">{product.category_label}</p>
        <h2>{product.name}</h2>
        <div className="catalog-detail__purchase">
          <p className="catalog-detail__price">{price}</p>
          <p className="catalog-detail__unit">{product.unit_label}</p>
        </div>
        <p className="catalog-detail__description">{product.detail_description}</p>

        {facetLabels.length > 0 ? (
          <ul className="catalog-detail__facets" aria-label="Dietary facets">
            {facetLabels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        ) : null}
        {showAddAction ? (
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
        ) : null}
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
