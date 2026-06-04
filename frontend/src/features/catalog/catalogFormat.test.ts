import { describe, expect, test } from "vitest";

import {
  formatCatalogCategoryLabel,
  formatDietaryFacetBadges,
  formatMoney
} from "./catalogFormat";

describe("formatMoney", () => {
  test("formats backend GBP minor units for customer display", () => {
    expect(formatMoney({ amount_minor: 650, currency: "GBP" })).toBe("£6.50");
  });

  test("formats international currencies using their minor unit scale", () => {
    expect(formatMoney({ amount_minor: 1234, currency: "USD" }, "en-US")).toBe(
      "$12.34"
    );
    expect(formatMoney({ amount_minor: 1250, currency: "JPY" }, "ja-JP")).toBe(
      "￥1,250"
    );
  });
});

describe("formatCatalogCategoryLabel", () => {
  test("returns the canonical customer-facing labels for initial categories", () => {
    expect(formatCatalogCategoryLabel("antipasti")).toBe("Antipasti");
    expect(formatCatalogCategoryLabel("primi")).toBe("Primi");
    expect(formatCatalogCategoryLabel("desserts")).toBe("Desserts");
    expect(formatCatalogCategoryLabel("drinks")).toBe("Drinks");
    expect(formatCatalogCategoryLabel("pantry")).toBe("Pantry");
  });
});

describe("formatDietaryFacetBadges", () => {
  test("returns customer-facing labels for supported true dietary facets", () => {
    expect(
      formatDietaryFacetBadges({
        is_vegetarian: true,
        is_vegan: true,
        is_gluten_free: true,
        contains_alcohol: true
      })
    ).toEqual(["Vegetarian", "Vegan", "Gluten-free", "Contains alcohol"]);
  });

  test("omits false facets and avoids unsupported safety claims", () => {
    const labels = formatDietaryFacetBadges({
      is_vegetarian: false,
      is_vegan: false,
      is_gluten_free: true,
      contains_alcohol: false
    });

    expect(labels).toEqual(["Gluten-free"]);
    expect(labels).not.toContain("Coeliac-safe");
    expect(labels).not.toContain("Allergen-free");
  });
});
