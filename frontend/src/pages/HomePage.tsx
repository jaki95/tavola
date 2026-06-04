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
      <header className="top-bar">
        <div className="top-bar__inner">
          <a className="brand-mark" href="#catalog-title">
            <span className="brand-mark__eyebrow">Independent Italian deli</span>
            <span className="brand-mark__name">Tavola</span>
          </a>
          <BackendStatusPanel status={backendStatus} />
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
