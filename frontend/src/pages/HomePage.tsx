import {
  BackendStatusPanel,
  type BackendStatus
} from "../components/BackendStatusPanel";
import { BasketPanel } from "../features/basket/BasketPanel";
import { useBasket } from "../features/basket/useBasket";
import { CheckoutPanel } from "../features/checkout/CheckoutPanel";
import { CatalogBrowser } from "../features/catalog/CatalogBrowser";

const workflowItems = [
  {
    label: "Catalog",
    href: "#catalog-title",
    status: "Open"
  },
  {
    label: "Basket",
    href: "#basket-panel-title",
    status: "Active"
  },
  {
    label: "Checkout",
    href: "#checkout-panel-title",
    status: "Ready"
  }
] as const;

type HomePageProps = {
  backendStatus: BackendStatus;
};

export function HomePage({ backendStatus }: HomePageProps) {
  const basket = useBasket();
  const isBasketMutationPending = basket.mutation.status === "pending";
  const isBasketUpdating =
    isBasketMutationPending || basket.basket.status === "loading";
  const basketQuantities = getBasketQuantities(basket.basket.basket);

  return (
    <div className="site-shell">
      <header className="top-bar">
        <a className="brand-mark" href="#workspace">
          <span className="brand-mark__eyebrow">Independent Italian deli</span>
          <span className="brand-mark__name">Tavola</span>
        </a>
        <nav aria-label="Primary" className="primary-nav">
          <a className="nav-link nav-link--active" href={workflowItems[0].href}>
            <span>{workflowItems[0].label}</span>
            <span>{workflowItems[0].status}</span>
          </a>
          <a className="nav-link" href={workflowItems[1].href}>
            <span>{workflowItems[1].label}</span>
            <span>{workflowItems[1].status}</span>
          </a>
          <a className="nav-link" href={workflowItems[2].href}>
            <span>{workflowItems[2].label}</span>
            <span>{workflowItems[2].status}</span>
          </a>
        </nav>
      </header>

      <main className="storefront-workspace" id="workspace">
        <section className="workspace-intro" aria-labelledby="app-title">
          <div className="workspace-intro__copy">
            <p className="eyebrow">Storefront workspace</p>
            <h1 id="app-title">Tavola</h1>
            <p className="intro">
              A practical deli counter for browsing real products and building a
              backend-owned basket before mock pickup checkout.
            </p>
          </div>
          <BackendStatusPanel status={backendStatus} />
        </section>

        <div className="storefront-workspace__commerce">
          <CatalogBrowser
            basketQuantities={basketQuantities}
            isAddPending={isBasketMutationPending}
            onAddProduct={basket.addLine}
          />
          <div className="storefront-workspace__side-panel">
            <BasketPanel
              basket={basket.basket}
              mutation={basket.mutation}
              onReload={basket.reload}
              onRemoveLine={basket.removeLine}
              onSetLineQuantity={basket.setLineQuantity}
            />
            <CheckoutPanel
              basket={basket.basket}
              isBasketUpdating={isBasketUpdating}
              onCheckoutSuccess={basket.applyBasket}
            />
          </div>
        </div>
      </main>
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
