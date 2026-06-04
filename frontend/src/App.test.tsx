import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { App } from "./App";
import { createBasket } from "./api/basket";
import { getCatalog, getCatalogProduct } from "./api/catalog";
import { getHealth } from "./api/health";
import type { Basket } from "./types/basket";
import type { CatalogListResponse, CatalogProductSummary } from "./types/catalog";

vi.mock("./api/health", () => ({
  getHealth: vi.fn()
}));

vi.mock("./api/catalog", () => ({
  getCatalog: vi.fn(),
  getCatalogProduct: vi.fn()
}));

vi.mock("./api/basket", () => ({
  createBasket: vi.fn(),
  getBasket: vi.fn(),
  addBasketLine: vi.fn(),
  setBasketLineQuantity: vi.fn(),
  removeBasketLine: vi.fn()
}));

const createBasketMock = vi.mocked(createBasket);
const getHealthMock = vi.mocked(getHealth);
const getCatalogMock = vi.mocked(getCatalog);
const getCatalogProductMock = vi.mocked(getCatalogProduct);

const tagliatelle: CatalogProductSummary = {
  sku_id: "fresh-tagliatelle-250g",
  name: "Fresh Tagliatelle",
  category_id: "primi",
  category_label: "Primi",
  unit_label: "250g",
  unit_price_minor: 425,
  currency: "GBP",
  short_description: "Silky fresh pasta nests for a quick supper.",
  is_vegetarian: true,
  is_vegan: false,
  is_gluten_free: false,
  contains_alcohol: false,
  image_id: "fresh-tagliatelle-250g"
};

const catalogResponse: CatalogListResponse = {
  categories: [
    { category_id: "antipasti", label: "Antipasti" },
    { category_id: "primi", label: "Primi" }
  ],
  products: [tagliatelle]
};

const emptyBasket: Basket = {
  basket_id: "basket-1",
  lines: [],
  total_minor: 0,
  currency: "GBP",
  item_count: 0,
  line_count: 0
};

describe("App", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  beforeEach(() => {
    installLocalStorage();
    window.localStorage.clear();
    createBasketMock.mockResolvedValue({
      ok: true,
      data: emptyBasket
    });
    getCatalogMock.mockResolvedValue({
      ok: true,
      data: catalogResponse
    });
    getCatalogProductMock.mockResolvedValue({
      ok: true,
      data: {
        ...tagliatelle,
        detail_description: "Silky tagliatelle made for a simple Tavola supper."
      }
    });
  });

  test("renders the Tavola catalog as the first storefront screen", async () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    expect(
      screen.getByRole("link", { name: /independent italian deli tavola/i })
    ).toHaveAttribute("href", "#catalog-title");
    expect(
      screen.queryByRole("navigation", { name: "Primary" })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /checkout planned/i })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Catalog" })
    ).toBeInTheDocument();
    expect(
      screen.getByText("Browse real deli products, then add your picks to the basket.")
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", {
        level: 3,
        name: "Fresh Tagliatelle"
      })
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("region", { name: "Current basket" })
    ).toBeInTheDocument();
  });

  test("shows the backend status loading state by default", () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    expect(screen.getByLabelText("Service status")).toHaveAttribute(
      "role",
      "status"
    );
    expect(screen.getByText("Checking service")).toBeInTheDocument();
    expect(screen.getByText("Waiting for the health check.")).toBeInTheDocument();
  });

  test("shows the backend status success state from the health client", async () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    expect(await screen.findByText("Service ready")).toBeInTheDocument();
    expect(screen.getByText("Tavola API ready.")).toBeInTheDocument();
  });

  test("shows the backend status error state from the health client", async () => {
    getHealthMock.mockResolvedValue({
      ok: false,
      error: {
        kind: "network",
        message: "Could not reach the Tavola API."
      }
    });

    render(<App />);

    const alert = await screen.findByLabelText("Service status");

    expect(alert).toHaveAttribute("role", "alert");
    expect(screen.getByText("Service unavailable")).toBeInTheDocument();
    expect(screen.getByText("Could not reach the Tavola API.")).toBeInTheDocument();
  });
});

function installLocalStorage() {
  if (window.localStorage) {
    return;
  }

  const values = new Map<string, string>();

  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      get length() {
        return values.size;
      },
      clear() {
        values.clear();
      },
      getItem(key: string) {
        return values.get(key) ?? null;
      },
      key(index: number) {
        return Array.from(values.keys())[index] ?? null;
      },
      removeItem(key: string) {
        values.delete(key);
      },
      setItem(key: string, value: string) {
        values.set(key, value);
      }
    }
  });
}
