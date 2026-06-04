import { useCallback, useRef, useState } from "react";

import {
  StorefrontWorkflowTabs,
  type StorefrontWorkflow
} from "../components/StorefrontWorkflowTabs";
import {
  getWorkflowPanelId,
  getWorkflowTabId
} from "../components/storefrontWorkflowIds";
import { BasketPanel } from "../features/basket/BasketPanel";
import { useBasket } from "../features/basket/useBasket";
import { CheckoutPanel } from "../features/checkout/CheckoutPanel";
import { CatalogBrowser } from "../features/catalog/CatalogBrowser";
import { PlannerWorkspace } from "../features/planner/PlannerWorkspace";

export function HomePage() {
  const basket = useBasket();
  const [activeWorkflow, setActiveWorkflow] =
    useState<StorefrontWorkflow>("shop");
  const activeWorkflowRef = useRef(activeWorkflow);
  const [hasUnseenPlanProposal, setHasUnseenPlanProposal] = useState(false);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const isBasketMutationPending = basket.mutation.status === "pending";
  const isBasketUpdating =
    isBasketMutationPending || basket.basket.status === "loading";
  const basketQuantities = getBasketQuantities(basket.basket.basket);
  const selectWorkflow = useCallback((workflow: StorefrontWorkflow) => {
    activeWorkflowRef.current = workflow;
    setActiveWorkflow(workflow);

    if (workflow === "plan") {
      setHasUnseenPlanProposal(false);
    }
  }, []);
  const handleProposalReadyChange = useCallback((isProposalReady: boolean) => {
    if (!isProposalReady) {
      setHasUnseenPlanProposal(false);
      return;
    }

    if (activeWorkflowRef.current === "shop") {
      setHasUnseenPlanProposal(true);
    }
  }, []);

  return (
    <div className="site-shell">
      <header aria-label="Tavola storefront" className="top-bar">
        <div className="top-bar__inner">
          <div className="top-bar__brand-area">
            <button
              className="brand-mark brand-mark--compact"
              onClick={() => selectWorkflow("shop")}
              type="button"
            >
              <span className="brand-mark__name">Tavola</span>
              <span className="brand-mark__eyebrow">Italian deli</span>
            </button>
          </div>
          <StorefrontWorkflowTabs
            activeWorkflow={activeWorkflow}
            onWorkflowChange={selectWorkflow}
            planBadgeLabel={
              hasUnseenPlanProposal ? "Proposal ready" : undefined
            }
          />
        </div>
      </header>

      <main className="storefront-main">
        <div className="storefront-main__commerce">
          <div className="storefront-main__primary">
            <section
              aria-labelledby={getWorkflowTabId("shop")}
              className="storefront-workflow-panel"
              hidden={activeWorkflow !== "shop"}
              id={getWorkflowPanelId("shop")}
              role="tabpanel"
            >
              <CatalogBrowser
                basketQuantities={basketQuantities}
                isActive={activeWorkflow === "shop"}
                isAddPending={isBasketMutationPending}
                onAddProduct={basket.addLine}
              />
            </section>
            <section
              aria-labelledby={getWorkflowTabId("plan")}
              className="storefront-workflow-panel"
              hidden={activeWorkflow !== "plan"}
              id={getWorkflowPanelId("plan")}
              role="tabpanel"
            >
              <PlannerWorkspace
                basket={basket.basket.basket}
                onBasketAccepted={basket.applyBasket}
                onProposalReadyChange={handleProposalReadyChange}
              />
            </section>
          </div>
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
