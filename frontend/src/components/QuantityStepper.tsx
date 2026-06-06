import { useEffect, useState } from "react";

type QuantityStepperProps = {
  className?: string;
  decreaseLabel: string;
  disabled: boolean;
  groupLabel: string;
  increaseLabel: string;
  inputLabel: string;
  min?: number;
  quantity: number;
  onQuantityChange: (quantity: number) => void;
};

export function QuantityStepper({
  className,
  decreaseLabel,
  disabled,
  groupLabel,
  increaseLabel,
  inputLabel,
  min = 1,
  quantity,
  onQuantityChange
}: QuantityStepperProps) {
  const [draftQuantity, setDraftQuantity] = useState(String(quantity));

  useEffect(() => {
    setDraftQuantity(String(quantity));
  }, [quantity]);

  function submitDraftQuantity() {
    if (disabled) {
      setDraftQuantity(String(quantity));
      return;
    }

    const nextQuantity = Number.parseInt(draftQuantity, 10);

    if (!Number.isInteger(nextQuantity) || nextQuantity < min) {
      setDraftQuantity(String(quantity));
      return;
    }

    if (nextQuantity !== quantity) {
      onQuantityChange(nextQuantity);
    }
  }

  return (
    <div
      className={["quantity-stepper", className].filter(Boolean).join(" ")}
      aria-label={groupLabel}
      role="group"
    >
      <button
        aria-label={decreaseLabel}
        disabled={disabled || quantity <= min}
        onClick={() => onQuantityChange(quantity - 1)}
        type="button"
      >
        -
      </button>
      <input
        aria-label={inputLabel}
        disabled={disabled}
        inputMode="numeric"
        min={min}
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
        aria-label={increaseLabel}
        disabled={disabled}
        onClick={() => onQuantityChange(quantity + 1)}
        type="button"
      >
        +
      </button>
    </div>
  );
}
