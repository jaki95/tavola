import { describe, expect, test } from "vitest";

import { formatBasketCount, formatBasketMoney } from "./basketFormat";

describe("basketFormat", () => {
  test("formats server-provided basket money in pounds sterling", () => {
    expect(formatBasketMoney({ amount_minor: 1275, currency: "GBP" })).toBe(
      "£12.75"
    );
  });

  test("formats item counts from backend totals", () => {
    expect(formatBasketCount(1)).toBe("1 item");
    expect(formatBasketCount(4)).toBe("4 items");
  });
});
