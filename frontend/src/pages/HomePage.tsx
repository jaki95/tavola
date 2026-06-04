import { useState } from "react";

import {
  BackendStatusPanel,
  type BackendStatus
} from "../components/BackendStatusPanel";
import { BasketPanel } from "../features/basket/BasketPanel";
import { useBasket } from "../features/basket/useBasket";
import { CheckoutPanel } from "../features/checkout/CheckoutPanel";
import { CatalogBrowser } from "../features/catalog/CatalogBrowser";

type HomePageProps = {
  backendStatus: BackendStatus;
};

export function HomePage({ backendStatus }: HomePageProps) {
  const basket = useBasket();
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const isBasketMutationPending = basket.mutation.status === "pending";
  const isBasketUpdating =
    isBasketMutationPending || basket.basket.status === "loading";
  const basketQuantities = getBasketQuantities(basket.basket.basket);

  return (
    <div className="site-shell">
      <header aria-label="Tavola storefront" className="top-bar">
        <div className="top-bar__inner">
          <div className="top-bar__brand-area">
            <a className="brand-mark brand-mark--compact" href="#catalog-title">
              <span className="brand-mark__name">Tavola</span>
              <span className="brand-mark__eyebrow">Italian deli</span>
            </a>
          </div>
          <div className="top-bar__service-status">
            <BackendStatusPanel status={backendStatus} />
          </div>
        </div>
      </header>

      <main className="storefront-main">
        <div className="storefront-main__commerce">
          <CatalogBrowser
            basketQuantities={basketQuantities}
            isAddPending={isBasketMutationPending}
            onAddProduct={basket.addLine}
          />
          <div className="storefront-main__side-panel">
            <BasketPanel
              basket={basket.basket}
              mutation={basket.mutation}
              onCheckout={() => setIsCheckoutOpen(true)}
              onReload={basket.reload}
              onRemoveLine={basket.removeLine}
              onSetLineQuantity={basket.setLineQuantity}
            />
          </div>
        </div>
      </main>

      {isCheckoutOpen ? (
        <CheckoutPanel
          basket={basket.basket}
          isBasketUpdating={isBasketUpdating}
          onCheckoutSuccess={basket.applyBasket}
          onClose={() => setIsCheckoutOpen(false)}
        />
      ) : null}
    </div>
  );
}

function getBasketQuantities(
  basket: ReturnType<typeof useBasket>["basket"]["basket"]
): Record<string, number> {
  if (!basket) {
    return {};
  }

  return Object.fromEntries(
    basket.lines.map((line) => [line.sku_id, line.quantity])
  );
}
