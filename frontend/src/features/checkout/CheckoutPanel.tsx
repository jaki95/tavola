import { useEffect, useMemo, useState, type FormEvent } from "react";

import { formatBasketCount, formatBasketMoney } from "../basket/basketFormat";
import type { BasketLoadState } from "../basket/useBasket";
import type { Basket } from "../../types/basket";
import type { Order } from "../../types/checkout";
import {
  useCheckout,
  type CheckoutClient,
  type CheckoutFormValues
} from "./useCheckout";

type CheckoutPanelProps = {
  basket: BasketLoadState;
  client?: CheckoutClient;
  isBasketUpdating: boolean;
  onClose: () => void;
  onCheckoutSuccess: (basket: Basket) => void;
};

export function CheckoutPanel({
  basket,
  client,
  isBasketUpdating,
  onClose,
  onCheckoutSuccess
}: CheckoutPanelProps) {
  const {
    pickupWindows,
    submission,
    reloadPickupWindows,
    submitCheckout,
    resetCheckout
  } = useCheckout({ client });
  const [formValues, setFormValues] = useState<CheckoutFormValues>({
    contactName: "",
    contactEmail: "",
    pickupWindowId: ""
  });
  const visibleBasket = basket.basket;
  const isBasketEmpty = !visibleBasket || visibleBasket.lines.length === 0;
  const isPending = submission.status === "pending";
  const canSubmit =
    !isBasketEmpty &&
    !isBasketUpdating &&
    pickupWindows.status === "success" &&
    !isPending;

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  useEffect(() => {
    const firstPickupWindow = pickupWindows.pickupWindows[0];
    if (
      pickupWindows.status === "success" &&
      firstPickupWindow &&
      formValues.pickupWindowId === ""
    ) {
      setFormValues((current) => ({
        ...current,
        pickupWindowId: firstPickupWindow.pickup_window_id
      }));
    }
  }, [formValues.pickupWindowId, pickupWindows]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    const result = await submitCheckout(visibleBasket, formValues);
    if (result) {
      onCheckoutSuccess(result.basket);
    }
  }

  function updateFormValue(field: keyof CheckoutFormValues, value: string) {
    setFormValues((current) => ({
      ...current,
      [field]: value
    }));
  }

  return (
    <div
      aria-labelledby="checkout-panel-title"
      aria-modal="true"
      className="checkout-modal"
      role="dialog"
    >
      <section className="checkout-panel" id="checkout-panel">
        <div className="checkout-panel__header">
          <div>
            <p className="eyebrow">Checkout</p>
            <h2 id="checkout-panel-title">Pickup checkout</h2>
          </div>
          <CheckoutSummary basket={visibleBasket} />
        </div>

        <div className="checkout-panel__body">
          <CheckoutReview basket={visibleBasket} />

          {submission.status === "success" ? (
            <CheckoutConfirmation
              onReset={resetCheckout}
              order={submission.order}
            />
          ) : (
            <form className="checkout-form" onSubmit={handleSubmit}>
              {isBasketEmpty ? (
                <p className="checkout-panel__empty">
                  Add at least one deli item before checkout.
                </p>
              ) : null}

              {isBasketUpdating ? (
                <p className="checkout-panel__status" role="status">
                  Basket is updating.
                </p>
              ) : null}

              {pickupWindows.status === "loading" ? (
                <p className="checkout-panel__status" role="status">
                  Loading pickup windows.
                </p>
              ) : null}

              {pickupWindows.status === "error" ? (
                <div className="checkout-panel__alert" role="alert">
                  <p>{pickupWindows.message}</p>
                  <button type="button" onClick={reloadPickupWindows}>
                    Retry windows
                  </button>
                </div>
              ) : null}

              {pickupWindows.status === "empty" ? (
                <p className="checkout-panel__alert" role="alert">
                  {pickupWindows.message}
                </p>
              ) : null}

              <label className="checkout-form__field">
                <span>Contact name</span>
                <input
                  autoComplete="name"
                  disabled={!canSubmit}
                  onChange={(event) =>
                    updateFormValue("contactName", event.target.value)
                  }
                  required
                  type="text"
                  value={formValues.contactName}
                />
              </label>

              <label className="checkout-form__field">
                <span>Contact email</span>
                <input
                  autoComplete="email"
                  disabled={!canSubmit}
                  onChange={(event) =>
                    updateFormValue("contactEmail", event.target.value)
                  }
                  required
                  type="email"
                  value={formValues.contactEmail}
                />
              </label>

              <label className="checkout-form__field">
                <span>Pickup window</span>
                <select
                  disabled={!canSubmit}
                  onChange={(event) =>
                    updateFormValue("pickupWindowId", event.target.value)
                  }
                  required
                  value={formValues.pickupWindowId}
                >
                  {pickupWindows.pickupWindows.map((window) => (
                    <option
                      key={window.pickup_window_id}
                      value={window.pickup_window_id}
                    >
                      {window.label}
                    </option>
                  ))}
                </select>
              </label>

              {submission.status === "error" ? (
                <p className="checkout-panel__alert" role="alert">
                  {submission.message}
                </p>
              ) : null}

              <button disabled={!canSubmit} type="submit">
                {isPending ? "Creating order" : "Create pickup order"}
              </button>
            </form>
          )}
        </div>

        <div className="checkout-panel__footer">
          <button
            className="checkout-panel__back"
            onClick={onClose}
            type="button"
          >
            Back to basket
          </button>
        </div>
      </section>
    </div>
  );
}

function CheckoutSummary({ basket }: { basket: Basket | null }) {
  return (
    <div className="checkout-panel__summary" aria-live="polite">
      <span>
        {formatBasketMoney({
          amount_minor: basket?.total_minor ?? 0,
          currency: basket?.currency ?? "GBP"
        })}
      </span>
      <span>{formatBasketCount(basket?.item_count ?? 0)}</span>
    </div>
  );
}

function CheckoutReview({ basket }: { basket: Basket | null }) {
  if (!basket || basket.lines.length === 0) {
    return (
      <div className="checkout-review checkout-review--empty">
        <h3>Basket review</h3>
        <p>Your basket is ready for deli selections.</p>
      </div>
    );
  }

  return (
    <div className="checkout-review">
      <h3>Basket review</h3>
      <ul aria-label="Checkout basket lines">
        {basket.lines.map((line) => (
          <li key={line.sku_id}>
            <span>{line.name}</span>
            <span>
              {line.quantity} x {line.unit_label}
            </span>
            <span>
              {formatBasketMoney({
                amount_minor: line.line_total_minor,
                currency: line.currency
              })}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function CheckoutConfirmation({
  order,
  onReset
}: {
  order: Order;
  onReset: () => void;
}) {
  const lineSummaries = useMemo(
    () => order.lines.map((line) => `${line.name} x ${line.quantity}`),
    [order.lines]
  );

  return (
    <div className="checkout-confirmation" role="status">
      <h3>Order confirmed</h3>
      <dl>
        <div>
          <dt>Order</dt>
          <dd>{order.order_id}</dd>
        </div>
        <div>
          <dt>Pickup</dt>
          <dd>{order.pickup_window.label}</dd>
        </div>
        <div>
          <dt>Email</dt>
          <dd>{order.contact_email}</dd>
        </div>
        <div>
          <dt>Total</dt>
          <dd>
            {formatBasketMoney({
              amount_minor: order.total_minor,
              currency: order.currency
            })}
          </dd>
        </div>
        <div>
          <dt>Items</dt>
          <dd>{formatBasketCount(order.item_count)}</dd>
        </div>
      </dl>
      <ul aria-label="Confirmed order lines">
        {lineSummaries.map((summary) => (
          <li key={summary}>{summary}</li>
        ))}
      </ul>
      <button type="button" onClick={onReset}>
        Place another order
      </button>
    </div>
  );
}
