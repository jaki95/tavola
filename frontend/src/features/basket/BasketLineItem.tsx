import { useEffect, useState } from "react";

import { formatBasketMoney } from "./basketFormat";
import { getCatalogImageAsset } from "../catalog/catalogImages";
import type { BasketLine } from "../../types/basket";

type BasketLineItemProps = {
  line: BasketLine;
  isPending: boolean;
  onRemoveLine: (skuId: string) => void;
  onSetLineQuantity: (skuId: string, quantity: number) => void;
};

export function BasketLineItem({
  line,
  isPending,
  onRemoveLine,
  onSetLineQuantity
}: BasketLineItemProps) {
  const [draftQuantity, setDraftQuantity] = useState(String(line.quantity));

  useEffect(() => {
    setDraftQuantity(String(line.quantity));
  }, [line.quantity]);

  const unitPrice = formatBasketMoney({
    amount_minor: line.unit_price_minor,
    currency: line.currency
  });
  const lineTotal = formatBasketMoney({
    amount_minor: line.line_total_minor,
    currency: line.currency
  });
  const image = getCatalogImageAsset(line.image_id, line.name);

  function submitDraftQuantity() {
    if (isPending) {
      setDraftQuantity(String(line.quantity));
      return;
    }

    const nextQuantity = Number.parseInt(draftQuantity, 10);

    if (!Number.isInteger(nextQuantity) || nextQuantity < 1) {
      setDraftQuantity(String(line.quantity));
      return;
    }

    if (nextQuantity !== line.quantity) {
      onSetLineQuantity(line.sku_id, nextQuantity);
    }
  }

  return (
    <li className="basket-line" aria-label={line.name}>
      <img
        alt={image.alt}
        className="basket-line__image"
        height={image.height}
        src={image.src}
        width={image.width}
      />

      <div className="basket-line__content">
        <div className="basket-line__summary">
          <div>
            <h3>{line.name}</h3>
            <p>
              <span>{line.unit_label}</span>
              <span>{unitPrice} each</span>
            </p>
          </div>
          <strong>{lineTotal}</strong>
        </div>

        <div className="basket-line__controls">
          <div
            className="basket-line__quantity"
            aria-label={`${line.name} quantity`}
          >
            <button
              aria-label={`Decrease ${line.name} quantity`}
              disabled={isPending || line.quantity <= 1}
              onClick={() => onSetLineQuantity(line.sku_id, line.quantity - 1)}
              type="button"
            >
              -
            </button>
            <input
              aria-label={`Quantity for ${line.name}`}
              disabled={isPending}
              inputMode="numeric"
              min={1}
              onBlur={submitDraftQuantity}
              onChange={(event) => setDraftQuantity(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.currentTarget.blur();
                }
              }}
              type="number"
              value={draftQuantity}
            />
            <button
              aria-label={`Increase ${line.name} quantity`}
              disabled={isPending}
              onClick={() => onSetLineQuantity(line.sku_id, line.quantity + 1)}
              type="button"
            >
              +
            </button>
          </div>
          <button
            aria-label={`Remove ${line.name} from basket`}
            className="basket-line__remove"
            disabled={isPending}
            onClick={() => onRemoveLine(line.sku_id)}
            type="button"
          >
            Remove
          </button>
        </div>
      </div>
    </li>
  );
}
