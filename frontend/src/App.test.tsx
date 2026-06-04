import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { App } from "./App";
import { createBasket } from "./api/basket";
import { getCatalog, getCatalogProduct } from "./api/catalog";
import { createCheckout, listPickupWindows } from "./api/checkout";
import { getHealth } from "./api/health";
import { acceptProposal, createPlannerSession } from "./api/planner";
import type { Basket } from "./types/basket";
import type { CatalogListResponse, CatalogProductSummary } from "./types/catalog";
import type { CheckoutResponse, PickupWindow } from "./types/checkout";
import type { MenuProposal, PlannerSessionResponse } from "./types/planner";

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

vi.mock("./api/checkout", () => ({
  listPickupWindows: vi.fn(),
  createCheckout: vi.fn()
}));

vi.mock("./api/planner", () => ({
  createPlannerSession: vi.fn(),
  answerFollowUp: vi.fn(),
  fetchPlannerSession: vi.fn(),
  validateProposal: vi.fn(),
  acceptProposal: vi.fn()
}));

const createBasketMock = vi.mocked(createBasket);
const getHealthMock = vi.mocked(getHealth);
const getCatalogMock = vi.mocked(getCatalog);
const getCatalogProductMock = vi.mocked(getCatalogProduct);
const listPickupWindowsMock = vi.mocked(listPickupWindows);
const createCheckoutMock = vi.mocked(createCheckout);
const createPlannerSessionMock = vi.mocked(createPlannerSession);
const acceptProposalMock = vi.mocked(acceptProposal);

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

const tagliatelleBasket: Basket = {
  basket_id: "basket-1",
  lines: [
    {
      sku_id: "fresh-tagliatelle-250g",
      name: "Fresh Tagliatelle",
      category_id: "primi",
      category_label: "Primi",
      unit_label: "250g",
      quantity: 2,
      unit_price_minor: 425,
      line_total_minor: 850,
      currency: "GBP",
      image_id: "fresh-tagliatelle-250g"
    }
  ],
  total_minor: 850,
  currency: "GBP",
  item_count: 2,
  line_count: 1
};

const pickupWindow: PickupWindow = {
  pickup_window_id: "today-afternoon",
  label: "Today afternoon pickup",
  display_order: 1
};

const checkoutResponse: CheckoutResponse = {
  order: {
    order_id: "order-1",
    basket_id: "basket-1",
    contact_name: "Ada Lovelace",
    contact_email: "ada@example.com",
    pickup_window: pickupWindow,
    lines: tagliatelleBasket.lines,
    total_minor: 850,
    currency: "GBP",
    item_count: 2,
    line_count: 1
  },
  basket: emptyBasket
};

const plannerProposal: MenuProposal = {
  title: "Fresh pasta supper",
  explanation: "A simple Tavola pasta plan for a relaxed dinner.",
  planner_notes: [
    { note_type: "evidence", source: "tavola", message: "Party size set to 2." },
    {
      note_type: "evidence",
      source: "tavola",
      message: "Products were checked against Tavola's catalog."
    },
    {
      note_type: "evidence",
      source: "tavola",
      message: "Prices were calculated by Tavola."
    }
  ],
  party_size: 2,
  package_template_id: "primo-only",
  courses: [
    {
      course: "primo",
      course_label: "Primo",
      lines: [
        {
          ...tagliatelleBasket.lines[0],
          rationale: "Fresh pasta keeps the meal simple and generous."
        }
      ]
    }
  ],
  total_minor: 850,
  currency: "GBP",
  item_count: 2,
  line_count: 1,
  warnings: []
};

const plannerReadySession: PlannerSessionResponse = {
  planner_session_id: "planner-1",
  status: "proposal_ready",
  customer_request: "Plan pasta for 2",
  follow_up_answers: [],
  follow_up_question: null,
  menu_proposal: plannerProposal,
  validation_errors: []
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
    listPickupWindowsMock.mockResolvedValue({
      ok: true,
      data: { pickup_windows: [pickupWindow] }
    });
    createCheckoutMock.mockResolvedValue({
      ok: true,
      data: checkoutResponse
    });
    createPlannerSessionMock.mockResolvedValue({
      ok: true,
      data: plannerReadySession
    });
    acceptProposalMock.mockResolvedValue({
      ok: true,
      data: {
        basket: tagliatelleBasket,
        meal_plan_grouping: {
          title: "Fresh pasta supper",
          party_size: 2,
          package_template_id: "primo-only",
          courses: [
            {
              course: "primo",
              course_label: "Primo",
              line_sku_ids: ["fresh-tagliatelle-250g"]
            }
          ]
        }
      }
    });
  });

  test("renders the Tavola catalog as the first storefront screen", async () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });
    expect(
      within(storefrontHeader).getByRole("link", { name: "Tavola Italian deli" })
    ).toHaveAttribute("href", "#catalog-title");
    expect(
      within(storefrontHeader).getByLabelText("Service status")
    ).toBeInTheDocument();
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
      screen.getByText("Browse deli products and add your picks to the basket.")
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
    const planner = screen.getByRole("region", { name: "Plan a menu" });
    const basketPanel = screen.getByRole("region", { name: "Current basket" });
    expect(planner.closest(".storefront-main__primary")).not.toBeNull();
    expect(basketPanel.closest(".storefront-main__side-panel")).not.toBeNull();
    expect(
      screen.queryByRole("dialog", { name: "Pickup checkout" })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Review and checkout" })
    ).toBeDisabled();
  });

  test("synchronizes the visible basket after checkout succeeds", async () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });
    createBasketMock.mockResolvedValue({
      ok: true,
      data: tagliatelleBasket
    });

    render(<App />);

    const basketPanel = await screen.findByRole("region", {
      name: "Current basket"
    });
    expect(within(basketPanel).getByText("Fresh Tagliatelle")).toBeInTheDocument();

    fireEvent.click(
      within(basketPanel).getByRole("button", { name: "Review and checkout" })
    );

    const checkoutPanel = await screen.findByRole("dialog", {
      name: "Pickup checkout"
    });
    fireEvent.change(await within(checkoutPanel).findByLabelText("Contact name"), {
      target: { value: "Ada Lovelace" }
    });
    fireEvent.change(within(checkoutPanel).getByLabelText("Contact email"), {
      target: { value: "ada@example.com" }
    });
    fireEvent.click(
      within(checkoutPanel).getByRole("button", { name: "Create pickup order" })
    );

    expect(
      await within(checkoutPanel).findByRole("heading", {
        level: 3,
        name: "Order confirmed. Thank you for shopping with us."
      })
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(within(basketPanel).getByText("Your basket is empty.")).toBeInTheDocument();
    });
    expect(createCheckoutMock).toHaveBeenCalledWith({
      basket_id: "basket-1",
      contact_name: "Ada Lovelace",
      contact_email: "ada@example.com",
      pickup_window_id: "today-afternoon"
    });
  });

  test("adds an accepted planner proposal to the visible basket", async () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    const planner = await screen.findByRole("region", { name: "Plan a menu" });
    fireEvent.change(within(planner).getByLabelText("Meal request"), {
      target: { value: "Plan pasta for 2" }
    });
    fireEvent.click(within(planner).getByRole("button", { name: "Plan menu" }));

    expect(
      await within(planner).findByRole("heading", {
        level: 3,
        name: "Fresh pasta supper"
      })
    ).toBeInTheDocument();

    fireEvent.click(within(planner).getByRole("button", { name: "Add to basket" }));

    const basketPanel = await screen.findByRole("region", {
      name: "Current basket"
    });
    await waitFor(() => {
      expect(within(basketPanel).getByText("Fresh Tagliatelle")).toBeInTheDocument();
    });
    expect(acceptProposalMock).toHaveBeenCalledWith("planner-1", {
      basket_id: "basket-1",
      mode: "append",
      menu_proposal: plannerProposal
    });
  });

  test("shows the backend status loading state by default", () => {
    getHealthMock.mockResolvedValue({
      ok: true,
      data: { service: "Tavola API", status: "ok" }
    });

    render(<App />);

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });

    expect(within(storefrontHeader).getByLabelText("Service status")).toHaveAttribute(
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

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });

    expect(
      within(storefrontHeader).getByLabelText("Service status")
    ).toBeInTheDocument();
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

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });
    const alert = await within(storefrontHeader).findByRole("alert", {
      name: "Service status"
    });

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
