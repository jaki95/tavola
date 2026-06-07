import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { App } from "./App";
import { addBasketLine, createBasket } from "./api/basket";
import { getCatalog, getCatalogProduct } from "./api/catalog";
import { createCheckout, listPickupWindows } from "./api/checkout";
import {
  acceptProposal,
  createPlannerSession,
  fetchPlannerSession,
  getPlannerStatus
} from "./api/planner";
import type { Basket } from "./types/basket";
import type { CatalogListResponse, CatalogProductSummary } from "./types/catalog";
import type { CheckoutResponse, PickupWindow } from "./types/checkout";
import type { MenuProposal, PlannerSessionResponse } from "./types/planner";

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
  getPlannerStatus: vi.fn(),
  createPlannerSession: vi.fn(),
  answerFollowUp: vi.fn(),
  fetchPlannerSession: vi.fn(),
  validateProposal: vi.fn(),
  acceptProposal: vi.fn()
}));

const createBasketMock = vi.mocked(createBasket);
const addBasketLineMock = vi.mocked(addBasketLine);
const getCatalogMock = vi.mocked(getCatalog);
const getCatalogProductMock = vi.mocked(getCatalogProduct);
const listPickupWindowsMock = vi.mocked(listPickupWindows);
const createCheckoutMock = vi.mocked(createCheckout);
const getPlannerStatusMock = vi.mocked(getPlannerStatus);
const createPlannerSessionMock = vi.mocked(createPlannerSession);
const fetchPlannerSessionMock = vi.mocked(fetchPlannerSession);
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

const tagliatelleBasketAfterCatalogAdd: Basket = {
  ...tagliatelleBasket,
  lines: [
    {
      ...tagliatelleBasket.lines[0],
      quantity: 3,
      line_total_minor: 1275
    }
  ],
  total_minor: 1275,
  item_count: 3
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
  validation_errors: [],
  planning_updates: [
    { stage: "queued", message: "Sending request" },
    { stage: "ready", message: "Your menu proposal is ready to review." }
  ]
};

const plannerPlanningSession: PlannerSessionResponse = {
  planner_session_id: "planner-1",
  status: "planning",
  customer_request: "Plan pasta for 2",
  follow_up_answers: [],
  follow_up_question: null,
  menu_proposal: null,
  validation_errors: [],
  planning_updates: [
    { stage: "queued", message: "Sending request" }
  ]
};

describe("App", () => {
  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  beforeEach(() => {
    installLocalStorage();
    window.localStorage.clear();
    createBasketMock.mockResolvedValue({
      ok: true,
      data: emptyBasket
    });
    addBasketLineMock.mockResolvedValue({
      ok: true,
      data: tagliatelleBasketAfterCatalogAdd
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
    getPlannerStatusMock.mockResolvedValue({
      ok: true,
      data: {
        enabled: true,
        mode: "real_codex",
        message: "Planner is running with live Codex assistance."
      }
    });
    createPlannerSessionMock.mockResolvedValue({
      ok: true,
      data: plannerReadySession
    });
    fetchPlannerSessionMock.mockResolvedValue({
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

  test("renders Shop as the default storefront workflow", async () => {
    render(<App />);

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });
    expect(
      within(storefrontHeader).getByRole("button", {
        name: "Tavola Italian deli"
      })
    ).toBeInTheDocument();
    const shopTab = within(storefrontHeader).getByRole("tab", { name: "Shop" });
    const planTab = within(storefrontHeader).getByRole("tab", { name: "Plan" });
    expect(shopTab).toHaveAttribute("aria-selected", "true");
    expect(planTab).toHaveAttribute("aria-selected", "false");
    expect(
      within(storefrontHeader).queryByText(/service/i)
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("navigation", { name: "Primary" })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /checkout planned/i })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Shop" })
    ).toBeInTheDocument();
    expect(screen.queryByText("Fresh from the counter")).not.toBeInTheDocument();
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
    const basketPanel = screen.getByRole("region", { name: "Current basket" });
    expect(basketPanel.closest(".storefront-main__side-panel")).not.toBeNull();
    expect(
      screen.queryByRole("heading", { level: 2, name: "Plan a menu" })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("dialog", { name: "Pickup checkout" })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Review and checkout" })
    ).toBeDisabled();
  });

  test("switches workflows while keeping the basket visible in the side panel", async () => {
    createBasketMock.mockResolvedValue({
      ok: true,
      data: tagliatelleBasket
    });

    render(<App />);

    await screen.findByRole("button", {
      name: "View details for Fresh Tagliatelle"
    });

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });
    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Plan" }));

    expect(
      within(storefrontHeader).getByRole("tab", { name: "Plan" })
    ).toHaveAttribute("aria-selected", "true");
    expect(
      screen.getByRole("heading", { level: 2, name: "Plan a menu" })
    ).toBeInTheDocument();

    const basketPanel = screen.getByRole("region", {
      name: "Current basket"
    });
    expect(basketPanel.closest(".storefront-main__side-panel")).not.toBeNull();
    expect(within(basketPanel).getByText("Fresh Tagliatelle")).toBeInTheDocument();

    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Shop" }));

    expect(
      screen.getByRole("heading", { level: 1, name: "Shop" })
    ).toBeInTheDocument();
    expect(within(basketPanel).getByText("Fresh Tagliatelle")).toBeInTheDocument();
  });

  test("selecting the Tavola brand returns to Shop without clearing planner state", async () => {
    createBasketMock.mockResolvedValue({
      ok: true,
      data: tagliatelleBasket
    });

    render(<App />);

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });
    const basketPanel = await screen.findByRole("region", {
      name: "Current basket"
    });
    expect(within(basketPanel).getByText("Fresh Tagliatelle")).toBeInTheDocument();

    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Plan" }));
    const planner = screen.getByRole("region", { name: "Plan a menu" });
    fireEvent.change(within(planner).getByLabelText("Meal request"), {
      target: { value: "Picnic lunch for 4" }
    });

    fireEvent.click(
      within(storefrontHeader).getByRole("button", {
        name: "Tavola Italian deli"
      })
    );

    expect(
      within(storefrontHeader).getByRole("tab", { name: "Shop" })
    ).toHaveAttribute("aria-selected", "true");
    expect(
      screen.getByRole("heading", { level: 1, name: "Shop" })
    ).toBeInTheDocument();
    expect(within(basketPanel).getByText("Fresh Tagliatelle")).toBeInTheDocument();

    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Plan" }));

    expect(within(planner).getByLabelText("Meal request")).toHaveValue(
      "Picnic lunch for 4"
    );
  });

  test("keeps a returned planner proposal after switching workflows", async () => {
    render(<App />);

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });
    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Plan" }));

    const planner = screen.getByRole("region", { name: "Plan a menu" });
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

    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Shop" }));
    expect(
      screen.queryByRole("heading", {
        level: 3,
        name: "Fresh pasta supper"
      })
    ).not.toBeInTheDocument();

    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Plan" }));
    expect(
      within(planner).getByRole("heading", {
        level: 3,
        name: "Fresh pasta supper"
      })
    ).toBeInTheDocument();
  });

  test("badges Plan when a proposal becomes ready while Shop is active", async () => {
    vi.useFakeTimers();
    createPlannerSessionMock.mockResolvedValueOnce({
      ok: true,
      data: plannerPlanningSession
    });
    fetchPlannerSessionMock.mockResolvedValueOnce({
      ok: true,
      data: plannerReadySession
    });
    render(<App />);

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });
    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Plan" }));

    const planner = screen.getByRole("region", { name: "Plan a menu" });
    fireEvent.change(within(planner).getByLabelText("Meal request"), {
      target: { value: "Plan pasta for 2" }
    });
    fireEvent.click(within(planner).getByRole("button", { name: "Plan menu" }));

    await act(async () => {
      await Promise.resolve();
    });
    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Shop" }));

    expect(
      within(storefrontHeader).getByRole("tab", { name: "Plan" })
    ).not.toHaveAccessibleDescription("Proposal ready");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
      await Promise.resolve();
    });
    const readyPlanTab = within(storefrontHeader).getByRole("tab", { name: "Plan" });
    expect(readyPlanTab).toHaveAccessibleDescription("Proposal ready");
    expect(within(readyPlanTab).getByText("Proposal ready")).toBeInTheDocument();
    expect(storefrontHeader).not.toHaveTextContent(
      "Sending request"
    );

    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Plan" }));

    expect(
      within(storefrontHeader).getByRole("tab", { name: "Plan" })
    ).not.toHaveAccessibleDescription("Proposal ready");
    expect(
      within(planner).getByRole("heading", {
        level: 3,
        name: "Fresh pasta supper"
      })
    ).toBeInTheDocument();
  });

  test("preserves catalog filters but closes detail after leaving Shop", async () => {
    render(<App />);

    await screen.findByRole("heading", {
      level: 3,
      name: "Fresh Tagliatelle"
    });
    fireEvent.click(screen.getByLabelText("Primi"));
    fireEvent.change(screen.getByLabelText("Search catalog"), {
      target: { value: "pasta" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    await waitFor(() => {
      expect(getCatalogMock).toHaveBeenLastCalledWith({
        category_id: "primi",
        query: "pasta"
      });
    });

    fireEvent.click(
      screen.getByRole("button", { name: "View details for Fresh Tagliatelle" })
    );
    expect(
      await screen.findByRole("dialog", { name: "Product detail" })
    ).toBeInTheDocument();

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });
    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Plan" }));
    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Shop" }));

    expect(screen.getByLabelText("Primi")).toBeChecked();
    expect(screen.getByLabelText("Search catalog")).toHaveValue("pasta");
    expect(
      screen.getByText("Matches for", { exact: false })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("dialog", { name: "Product detail" })
    ).not.toBeInTheDocument();
  });

  test("synchronizes the visible basket after checkout succeeds", async () => {
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
        name: "Your deli pickup is arranged."
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
    render(<App />);

    const storefrontHeader = screen.getByRole("banner", {
      name: "Tavola storefront"
    });
    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Plan" }));

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

    fireEvent.click(within(storefrontHeader).getByRole("tab", { name: "Shop" }));

    expect(
      screen.getByRole("heading", { level: 1, name: "Shop" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "View details for Fresh Tagliatelle" })
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Add another Fresh Tagliatelle to basket, 2 in basket"
      })
    );

    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: "Add another Fresh Tagliatelle to basket, 3 in basket"
        })
      ).toBeInTheDocument();
    });
    expect(addBasketLineMock).toHaveBeenCalledWith("basket-1", {
      sku_id: "fresh-tagliatelle-250g",
      quantity: 1
    });
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
