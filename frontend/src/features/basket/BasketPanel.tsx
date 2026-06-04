import { BasketLineItem } from "./BasketLineItem";
import { formatBasketCount, formatBasketMoney } from "./basketFormat";
import type { BasketLoadState, BasketMutationState } from "./useBasket";
import type { Basket } from "../../types/basket";

type BasketPanelProps = {
  basket: BasketLoadState;
  mutation: BasketMutationState;
  onReload: () => void;
  onRemoveLine: (skuId: string) => void;
  onSetLineQuantity: (skuId: string, quantity: number) => void;
};

export function BasketPanel({
  basket,
  mutation,
  onReload,
  onRemoveLine,
  onSetLineQuantity
}: BasketPanelProps) {
  const visibleBasket = basket.basket;
  const isPending = mutation.status === "pending";

  return (
    <section
      aria-labelledby="basket-panel-title"
      className="basket-panel"
      id="basket-panel"
    >
      <div className="basket-panel__header">
        <div>
          <p className="eyebrow">Basket</p>
          <h2 id="basket-panel-title">Current basket</h2>
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
        isPending={isPending}
        onRemoveLine={onRemoveLine}
        onSetLineQuantity={onSetLineQuantity}
      />
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
  isPending,
  onRemoveLine,
  onSetLineQuantity
}: {
  basket: Basket | null;
  isPending: boolean;
  onRemoveLine: (skuId: string) => void;
  onSetLineQuantity: (skuId: string, quantity: number) => void;
}) {
  if (!basket || basket.lines.length === 0) {
    return (
      <div className="basket-panel__empty">
        <h3>Your basket is empty.</h3>
        <p>Add deli products from the catalog to start a backend-owned basket.</p>
      </div>
    );
  }

  return (
    <ul className="basket-panel__lines" aria-label="Basket lines">
      {basket.lines.map((line) => (
        <BasketLineItem
          isPending={isPending}
          key={line.sku_id}
          line={line}
          onRemoveLine={onRemoveLine}
          onSetLineQuantity={onSetLineQuantity}
        />
      ))}
    </ul>
  );
}
