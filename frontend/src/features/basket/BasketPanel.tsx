import { BasketLineItem } from "./BasketLineItem";
import { formatBasketCount, formatBasketMoney } from "./basketFormat";
import type { BasketLoadState, BasketMutationState } from "./useBasket";
import type { Basket } from "../../types/basket";

type BasketPanelProps = {
  basket: BasketLoadState;
  mutation: BasketMutationState;
  onCheckout: () => void;
  onReload: () => void;
  onRemoveLine: (skuId: string) => void;
  onSetLineQuantity: (skuId: string, quantity: number) => void;
};

export function BasketPanel({
  basket,
  mutation,
  onCheckout,
  onReload,
  onRemoveLine,
  onSetLineQuantity
}: BasketPanelProps) {
  const visibleBasket = basket.basket;
  const isPending = mutation.status === "pending";
  const pendingSkuId = isPending ? mutation.skuId : null;
  const canCheckout =
    basket.status === "success" &&
    Boolean(visibleBasket && visibleBasket.lines.length > 0) &&
    !isPending;

  return (
    <section
      aria-label="Current basket"
      className="basket-panel"
      id="basket-panel"
    >
      <div className="basket-panel__header">
        <div>
          <h2 id="basket-panel-title">Basket</h2>
        </div>
        <BasketSummary basket={visibleBasket} />
      </div>

      {basket.status === "loading" ? (
        <p className="basket-panel__status" role="status">
          Refreshing basket.
        </p>
      ) : null}

      {basket.status === "error" ? (
        <div className="basket-panel__alert" role="alert">
          <p>{basket.message}</p>
          <button type="button" onClick={onReload}>
            Reload basket
          </button>
        </div>
      ) : null}

      {mutation.status === "error" ? (
        <p className="basket-panel__alert" role="alert">
          {mutation.message}
        </p>
      ) : null}

      <BasketContents
        basket={visibleBasket}
        onRemoveLine={onRemoveLine}
        onSetLineQuantity={onSetLineQuantity}
        pendingSkuId={pendingSkuId}
      />

      <div className="basket-panel__checkout">
        <button disabled={!canCheckout} onClick={onCheckout} type="button">
          Review and checkout
        </button>
      </div>
    </section>
  );
}

function BasketSummary({ basket }: { basket: Basket | null }) {
  const total = basket
    ? formatBasketMoney({
        amount_minor: basket.total_minor,
        currency: basket.currency
      })
    : "£0.00";
  const itemCount = basket ? formatBasketCount(basket.item_count) : "0 items";

  return (
    <div className="basket-panel__summary" aria-live="polite">
      <span>{total}</span>
      <span>{itemCount}</span>
    </div>
  );
}

function BasketContents({
  basket,
  onRemoveLine,
  onSetLineQuantity,
  pendingSkuId
}: {
  basket: Basket | null;
  onRemoveLine: (skuId: string) => void;
  onSetLineQuantity: (skuId: string, quantity: number) => void;
  pendingSkuId: string | null;
}) {
  if (!basket || basket.lines.length === 0) {
    return (
      <div className="basket-panel__empty">
        <h3>Your basket is empty.</h3>
        <p>Add products from the catalog to start your basket.</p>
      </div>
    );
  }

  return (
    <ul className="basket-panel__lines" aria-label="Basket lines">
      {basket.lines.map((line) => (
        <BasketLineItem
          isPending={pendingSkuId === line.sku_id}
          key={line.sku_id}
          line={line}
          onRemoveLine={onRemoveLine}
          onSetLineQuantity={onSetLineQuantity}
        />
      ))}
    </ul>
  );
}
