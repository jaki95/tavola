import { describe, expect, test } from "vitest";

import { catalogImageIds, getCatalogImageAsset } from "./catalogImages";

const seedCatalogImageIds = [
  "burrata-pugliese-125g",
  "marinated-nocellara-olives-250g",
  "caponata-siciliana-300g",
  "prosciutto-di-parma-100g",
  "grilled-artichokes-200g",
  "fresh-tagliatelle-250g",
  "ricotta-spinach-ravioli-300g",
  "beef-ragu-lasagne-serves-2",
  "parmigiana-melanzane-serves-2",
  "potato-gnocchi-500g",
  "pumpkin-sage-tortelloni-300g",
  "tiramisu-cup-single",
  "cannoli-siciliani-two-pack",
  "lemon-polenta-cake-slice",
  "san-pellegrino-aranciata-330ml",
  "limonata-sparkling-330ml",
  "chianti-classico-750ml",
  "sugo-pomodoro-500g",
  "pesto-genovese-180g",
  "extra-virgin-olive-oil-500ml"
];

describe("catalogImages", () => {
  test("maps every known seed catalog image ID to a static asset", () => {
    expect([...catalogImageIds]).toEqual(seedCatalogImageIds);

    for (const imageId of seedCatalogImageIds) {
      const asset = getCatalogImageAsset(imageId, "Tavola product");

      expect(asset.src).toMatch(/\S/);
      expect(asset.src).not.toContain("catalog-fallback");
      expect(asset.width).toBe(960);
      expect(asset.height).toBe(720);
      expect(asset.alt).toBe("Tavola product product image");
    }
  });

  test("returns the designed fallback asset for unknown image IDs", () => {
    const asset = getCatalogImageAsset("unknown-image-id", "Tavola product");

    expect(asset.src).toMatch(/\S/);
    expect(asset.src).not.toContain("unknown-image-id");
    expect(asset.width).toBe(960);
    expect(asset.height).toBe(720);
    expect(asset.alt).toBe("Tavola product product image");
  });
});
