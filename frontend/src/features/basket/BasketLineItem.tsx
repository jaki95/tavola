import { QuantityStepper } from "../../components/QuantityStepper";
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
  const unitPrice = formatBasketMoney({
    amount_minor: line.unit_price_minor,
    currency: line.currency
  });
  const lineTotal = formatBasketMoney({
    amount_minor: line.line_total_minor,
    currency: line.currency
  });
  const image = getCatalogImageAsset(line.image_id, line.name);

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
          <QuantityStepper
            className="basket-line__quantity"
            decreaseLabel={`Decrease ${line.name} quantity`}
            disabled={isPending}
            groupLabel={`${line.name} quantity`}
            increaseLabel={`Increase ${line.name} quantity`}
            inputLabel={`Quantity for ${line.name}`}
            quantity={line.quantity}
            onQuantityChange={(quantity) =>
              onSetLineQuantity(line.sku_id, quantity)
            }
          />
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
