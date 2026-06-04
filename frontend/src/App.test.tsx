import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { App } from "./App";
import { getCatalog, getCatalogProduct } from "./api/catalog";
import { getHealth } from "./api/health";
import type { CatalogListResponse, CatalogProductSummary } from "./types/catalog";

vi.mock("./api/health", () => ({
  getHealth: vi.fn()
}));

vi.mock("./api/catalog", () => ({
  getCatalog: vi.fn(),
  getCatalogProduct: vi.fn()
}));

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

describe("App", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  beforeEach(() => {
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
      screen.getByRole("heading", { level: 1, name: "Tavola" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Primary" })
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /catalog open/i })).toHaveAttribute(
      "href",
      "#catalog-title"
    );
    expect(
      screen.getByRole("button", { name: /basket planned/i })
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /checkout planned/i })
    ).toBeDisabled();
    expect(
      await screen.findByRole("heading", {
        level: 3,
        name: "Fresh Tagliatelle"
      })
    ).toBeInTheDocument();
  });

  test("shows the backend status loading state by default", () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    expect(screen.getByText("Checking backend")).toBeInTheDocument();
    expect(screen.getByText("Waiting for the health check.")).toBeInTheDocument();
  });

  test("shows the backend status success state from the health client", async () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    expect(await screen.findByText("Backend connected")).toBeInTheDocument();
    expect(screen.getByText("Tavola API is ready.")).toBeInTheDocument();
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

    expect(await screen.findByText("Backend unavailable")).toBeInTheDocument();
    expect(
      screen.getByText("Could not reach the Tavola API.")
    ).toBeInTheDocument();
  });
});
