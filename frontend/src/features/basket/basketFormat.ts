type BasketMoney = {
  amount_minor: number;
  currency: string;
};

export function formatBasketMoney(
  money: BasketMoney,
  locale: Intl.LocalesArgument = "en-GB"
): string {
  const formatter = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: money.currency
  });
  const fractionDigits = formatter.resolvedOptions().maximumFractionDigits ?? 2;
  const majorUnits = money.amount_minor / 10 ** fractionDigits;

  return formatter.format(majorUnits);
}

export function formatBasketCount(itemCount: number): string {
  return `${itemCount} ${itemCount === 1 ? "item" : "items"}`;
}
