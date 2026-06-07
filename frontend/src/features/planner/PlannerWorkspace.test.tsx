import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import type { ApiResult } from "../../api/client";
import type { Basket } from "../../types/basket";
import type { CatalogProductDetail } from "../../types/catalog";
import type {
  AcceptMenuProposalResponse,
  MenuProposal,
  PlannerSessionResponse,
  PlannerStatusResponse
} from "../../types/planner";
import { PlannerWorkspace } from "./PlannerWorkspace";
import type { PlannerClient } from "./usePlanner";

const proposal: MenuProposal = {
  title: "Vegetarian dinner for four",
  explanation: "A simple Tavola supper with antipasto, pasta, and dessert.",
  planner_notes: [
    { note_type: "evidence", source: "tavola", message: "Party size set to 4." },
    {
      note_type: "evidence",
      source: "tavola",
      message: "Vegetarian products were checked against Tavola's catalog."
    },
    {
      note_type: "evidence",
      source: "tavola",
      message: "Prices were calculated by Tavola."
    }
  ],
  party_size: 4,
  package_template_id: "antipasto-primo-dessert",
  courses: [
    {
      course: "antipasto",
      course_label: "Antipasto",
      lines: [
        {
          sku_id: "marinated-nocellara-olives-250g",
          name: "Marinated Nocellara Olives",
          category_id: "antipasti",
          category_label: "Antipasti",
          unit_label: "250g",
          quantity: 1,
          unit_price_minor: 495,
          line_total_minor: 495,
          currency: "GBP",
          image_id: "marinated-nocellara-olives-250g",
          rationale: "Bright, salty opener for the table."
        }
      ]
    },
    {
      course: "primo",
      course_label: "Primo",
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
          image_id: "fresh-tagliatelle-250g",
          rationale: "Fresh pasta anchors the main course."
        }
      ]
    },
    {
      course: "dessert",
      course_label: "Dessert",
      lines: [
        {
          sku_id: "tiramisu-cup-single",
          name: "Tiramisu Cup",
          category_id: "desserts",
          category_label: "Desserts",
          unit_label: "single",
          quantity: 4,
          unit_price_minor: 375,
          line_total_minor: 1500,
          currency: "GBP",
          image_id: "tiramisu-cup-single",
          rationale: "Individual desserts keep serving easy."
        }
      ]
    }
  ],
  total_minor: 2845,
  currency: "GBP",
  item_count: 7,
  line_count: 3,
  warnings: ["Budget is approximate; Tavola priced the final items."]
};

const pairedAntipastoProposal: MenuProposal = {
  ...proposal,
  courses: proposal.courses.map((course) =>
    course.course === "antipasto"
      ? {
          ...course,
          lines: [
            ...course.lines,
            {
              sku_id: "focaccia-genovese-piece",
              name: "Focaccia Genovese",
              category_id: "antipasti",
              category_label: "Antipasti",
              unit_label: "piece",
              quantity: 1,
              unit_price_minor: 650,
              line_total_minor: 650,
              currency: "GBP",
              image_id: "focaccia-genovese-piece",
              rationale: "Soft bread rounds out the antipasto plate."
            }
          ]
        }
      : course
  ),
  total_minor: 3495,
  item_count: 8,
  line_count: 4
};

const pairedInternalCopyProposal: MenuProposal = {
  ...pairedAntipastoProposal,
  title: "SKU-backed dinner",
  explanation: "A validated SKU proposal using a package template.",
  planner_notes: [
    {
      note_type: "evidence",
      source: "tavola",
      message: "Validated by Tavola for SKU validity."
    }
  ],
  courses: pairedAntipastoProposal.courses.map((course) => ({
    ...course,
    lines: course.lines.map((line) => ({
      ...line,
      rationale:
        line.sku_id === "focaccia-genovese-piece"
          ? "This SKU rounds out the antipasto plate."
          : line.rationale
    }))
  })),
  warnings: ["One SKU was adjusted."]
};

const readySession: PlannerSessionResponse = {
  planner_session_id: "planner-1",
  status: "proposal_ready",
  customer_request: "Vegetarian dinner for 4 around £50",
  follow_up_answers: [],
  follow_up_question: null,
  menu_proposal: proposal,
  validation_errors: [],
  planning_updates: [
    { stage: "queued", message: "Sending request" },
    { stage: "ready", message: "Your menu proposal is ready to review." }
  ]
};

const planningSession: PlannerSessionResponse = {
  planner_session_id: "planner-1",
  status: "planning",
  customer_request: "Vegetarian dinner for 4 around £50",
  follow_up_answers: [],
  follow_up_question: null,
  menu_proposal: null,
  validation_errors: [],
  planning_updates: [
    { stage: "queued", message: "Sending request" }
  ]
};

const pairedAntipastoSession: PlannerSessionResponse = {
  ...readySession,
  menu_proposal: pairedAntipastoProposal
};

const pairedInternalCopySession: PlannerSessionResponse = {
  ...readySession,
  menu_proposal: pairedInternalCopyProposal
};

const needsInputSession: PlannerSessionResponse = {
  planner_session_id: "planner-2",
  status: "needs_input",
  customer_request: "Plan a dinner",
  follow_up_answers: [],
  follow_up_question: "How many people are you serving?",
  menu_proposal: null,
  validation_errors: [],
  planning_updates: [
    { stage: "queued", message: "Sending request" },
    { stage: "needs_input", message: "Tavola needs one more detail." }
  ]
};

const emptyBasket: Basket = {
  basket_id: "basket-1",
  lines: [],
  total_minor: 0,
  currency: "GBP",
  item_count: 0,
  line_count: 0
};

const populatedBasket: Basket = {
  ...emptyBasket,
  lines: [
    {
      sku_id: "fresh-tagliatelle-250g",
      name: "Fresh Tagliatelle",
      category_id: "primi",
      category_label: "Primi",
      unit_label: "250g",
      quantity: 1,
      unit_price_minor: 425,
      line_total_minor: 425,
      currency: "GBP",
      image_id: "fresh-tagliatelle-250g"
    }
  ],
  total_minor: 425,
  item_count: 1,
  line_count: 1
};

const tagliatelleDetail: CatalogProductDetail = {
  sku_id: "fresh-tagliatelle-250g",
  name: "Fresh Tagliatelle",
  category_id: "primi",
  category_label: "Primi",
  unit_label: "250g",
  unit_price_minor: 425,
  currency: "GBP",
  short_description: "Egg pasta ribbons cut fresh for quick suppers.",
  detail_description:
    "Fresh egg tagliatelle cut into ribbons for ragu, mushrooms, or butter.",
  image_id: "fresh-tagliatelle-250g",
  is_vegetarian: true,
  is_vegan: false,
  is_gluten_free: false,
  contains_alcohol: false
};

const mealPlanGrouping = {
  title: "Vegetarian dinner for four",
  party_size: 4,
  package_template_id: "antipasto-primo-dessert" as const,
  courses: [
    {
      course: "antipasto" as const,
      course_label: "Antipasto",
      line_sku_ids: ["marinated-nocellara-olives-250g"]
    },
    {
      course: "primo" as const,
      course_label: "Primo",
      line_sku_ids: ["fresh-tagliatelle-250g"]
    },
    {
      course: "dessert" as const,
      course_label: "Dessert",
      line_sku_ids: ["tiramisu-cup-single"]
    }
  ]
};

describe("PlannerWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test("renders the planner heading with Codex branding and without the old decorative logo", () => {
    const client = createPlannerClient({});

    const { container } = renderPlannerWorkspace({ client });

    expect(
      screen.getByRole("heading", { level: 2, name: "Plan a menu" })
    ).toBeInTheDocument();
    expect(screen.getByText("powered by Codex")).toBeInTheDocument();
    expect(container.querySelector(".planner-workspace__icon")).toBeNull();
  });

  test("shows persona examples and a neutral request prompt", () => {
    const client = createPlannerClient({});

    const { container } = renderPlannerWorkspace({ client });

    expect(screen.getByPlaceholderText("What are you planning?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Plan menu" })).toBeDisabled();
    expect(container.querySelector(".planner-composer__spark")).toHaveAttribute(
      "aria-hidden",
      "true"
    );
    expect(
      screen.queryByPlaceholderText("Vegetarian dinner for 4 around £50")
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Dinner for 10 with one vegetarian guest"
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Antipasti and pasta for 4 around £50"
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Aperitivo for 6 with drinks" })
    ).toBeInTheDocument();
  });

  test("submits a meal prompt and renders a reviewable proposal", async () => {
    vi.useFakeTimers();
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: [success(readySession)]
    });

    renderPlannerWorkspace({ client });

    fireEvent.change(screen.getByLabelText("Meal request"), {
      target: { value: "Vegetarian dinner for 4 around £50" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Plan menu" }));

    expect(client.createSession).toHaveBeenCalledWith({
      message: "Vegetarian dinner for 4 around £50"
    });
    await act(async () => {
      await Promise.resolve();
    });
    expect(screen.getByRole("status")).toHaveTextContent(
      "Reading your request"
    );
    expect(screen.getByLabelText("Menu planning")).toHaveTextContent(
      "Tavola checks products, prices, and labels before review."
    );
    expect(screen.queryByLabelText("Planning update history")).not.toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(
      screen.getByRole("heading", {
        level: 3,
        name: "Vegetarian dinner for four"
      })
    ).toBeInTheDocument();
    expect(screen.getByText("powered by Codex")).toBeInTheDocument();
    expect(screen.getByText("Fresh Tagliatelle")).toBeInTheDocument();
    expect(screen.getByText("Prices were calculated by Tavola.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add to basket" })).toBeEnabled();
  });

  test("renders proposal copy without internal SKU language", async () => {
    vi.useFakeTimers();
    const firstCourse = proposal.courses[0]!;
    const firstLine = firstCourse.lines[0]!;
    const proposalWithInternalCopy: MenuProposal = {
      ...proposal,
      title: "SKU-backed dinner",
      explanation: "A validated SKU proposal using a package template.",
      planner_notes: [
        {
          note_type: "evidence",
          source: "tavola",
          message: "Validated by Tavola for SKU validity."
        }
      ],
      courses: [
        {
          ...firstCourse,
          lines: [
            {
              ...firstLine,
              rationale: "This SKU works well for the course."
            }
          ]
        }
      ],
      warnings: ["One SKU was adjusted."]
    };
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: [
        success({
          ...readySession,
          menu_proposal: proposalWithInternalCopy
        })
      ]
    });

    renderPlannerWorkspace({ client });
    submitReadyPrompt();

    await act(async () => {
      await Promise.resolve();
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(screen.getByRole("heading", { name: "product-backed dinner" })).toBeInTheDocument();
    expect(
      screen.getByText("A validated product proposal using a menu plan.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Validated by Tavola for product validity.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("This product works well for the course.")
    ).toBeInTheDocument();
    expect(screen.getByText("One product was adjusted.")).toBeInTheDocument();
    expect(screen.getByLabelText("Menu proposal")).not.toHaveTextContent(/sku/i);
    expect(screen.getByLabelText("Menu proposal")).not.toHaveTextContent(
      /template/i
    );
  });

  test("shows backend planning updates while planning remains pending", async () => {
    vi.useFakeTimers();
    const planningWithCatalogUpdate: PlannerSessionResponse = {
      ...planningSession,
      planning_updates: [
        ...planningSession.planning_updates,
        { stage: "planning", message: "Checking Tavola's catalog" }
      ]
    };
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: Array.from({ length: 20 }, () =>
        success(planningWithCatalogUpdate)
      )
    });

    renderPlannerWorkspace({ client });
    submitReadyPrompt();
    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByRole("status")).toHaveTextContent(
      "Reading your request"
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(screen.getByRole("status")).toHaveTextContent(
      "Matching catalog products"
    );
    expect(screen.getByLabelText("Menu planning")).toHaveTextContent(
      "Tavola checks products, prices, and labels before review."
    );
    expect(screen.queryByLabelText("Planning update history")).not.toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });

    const statusCopy = screen.getByRole("status").textContent ?? "";
    expect(statusCopy).toContain("Matching catalog products");
    expect(statusCopy).not.toContain("Still planning.");
    expect(statusCopy).not.toMatch(/\d+s elapsed/i);
    expect(screen.queryByLabelText("Planning progress")).not.toBeInTheDocument();
    expect(statusCopy).not.toMatch(
      /codex|sdk|tool|thread|model|retry|token|credential/i
    );
    expect(screen.queryByLabelText("Meal request")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Plan menu" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Current planner request")).toHaveTextContent(
      "Vegetarian dinner for 4 around £50"
    );
    expect(screen.getByRole("button", { name: "New request" })).toBeDisabled();
  });

  test("keeps planner availability out of the primary composer when available", async () => {
    const client = createPlannerClient({
      statusResult: success({
        enabled: true,
        mode: "real_codex",
        message: "Live planner is ready."
      }),
      createResults: [success(readySession)]
    });

    renderPlannerWorkspace({ client });

    expect(await screen.findByLabelText("Meal request")).toBeEnabled();
    expect(screen.queryByText("Live planner mode")).not.toBeInTheDocument();
    expect(screen.queryByText("Live planner is ready.")).not.toBeInTheDocument();
    expect(
      screen.getByLabelText("Planner validation promise")
    ).toHaveTextContent("Tavola checks every proposal before Basket changes.");
    expect(screen.getByText("Real catalog products only")).toBeInTheDocument();
    expect(screen.getByText("Prices and totals checked")).toBeInTheDocument();
    expect(screen.getByText("Product labels checked")).toBeInTheDocument();
    expect(screen.getByText("You review before adding")).toBeInTheDocument();
  });

  test("disables prompt submission when the planner is unavailable", async () => {
    const client = createPlannerClient({
      statusResult: success({
        enabled: false,
        mode: "disabled",
        message: "Planner setup is incomplete."
      })
    });

    renderPlannerWorkspace({ client });

    expect(
      await screen.findByText("Planner setup is incomplete.")
    ).toBeInTheDocument();
    expect(screen.queryByText("Planner unavailable")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Meal request")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Plan menu" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Aperitivo for 6 with drinks" })
    ).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Meal request"), {
      target: { value: "Vegetarian dinner for 4 around £50" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Plan menu" }));

    expect(client.createSession).not.toHaveBeenCalled();
  });

  test("answers a required follow-up after locking the submitted request", async () => {
    vi.useFakeTimers();
    const planningAfterFollowUp: PlannerSessionResponse = {
      ...planningSession,
      planner_session_id: "planner-2",
      customer_request: "Plan a dinner",
      follow_up_answers: ["4 people"],
      planning_updates: [
        ...needsInputSession.planning_updates,
        { stage: "planning", message: "Checking Tavola's catalog" }
      ]
    };
    const client = createPlannerClient({
      createResults: [success(needsInputSession)],
      followUpResults: [success(planningAfterFollowUp)],
      fetchResults: [success(readySession)]
    });

    renderPlannerWorkspace({ client });

    fireEvent.change(screen.getByLabelText("Meal request"), {
      target: { value: "Plan a dinner" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Plan menu" }));
    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getAllByText("Plan a dinner")).toHaveLength(1);
    expect(
      screen.getByText("Planner needs one choice before review.")
    ).toBeInTheDocument();
    expect(screen.getByText("How many people are you serving?")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Follow-up answer"), {
      target: { value: "4 people" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Continue planning" }));
    await act(async () => {
      await Promise.resolve();
    });

    expect(client.answerFollowUp).toHaveBeenCalledWith("planner-2", {
      message: "4 people"
    });
    expect(screen.getByRole("status")).toHaveTextContent(
      "Matching catalog products"
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(screen.getByText("Vegetarian dinner for four")).toBeInTheDocument();
  });

  test("keeps new request blocked while planning remains in progress", async () => {
    vi.useFakeTimers();
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: [success(readySession)]
    });

    renderPlannerWorkspace({ client });
    submitReadyPrompt();
    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.queryByLabelText("Meal request")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Current planner request")).toHaveTextContent(
      "Vegetarian dinner for 4 around £50"
    );

    const newRequestButton = screen.getByRole("button", { name: "New request" });
    expect(newRequestButton).toBeDisabled();
    fireEvent.click(newRequestButton);

    expect(screen.queryByLabelText("Meal request")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Current planner request")).toHaveTextContent(
      "Vegetarian dinner for 4 around £50"
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "Reading your request"
    );
    expect(client.createSession).toHaveBeenCalledTimes(1);

    await act(async () => {
      await Promise.resolve();
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
      await Promise.resolve();
    });

    expect(screen.getByText("Vegetarian dinner for four")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New request" })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "New request" }));

    expect(screen.getByLabelText("Meal request")).toBeEnabled();
    expect(screen.getByLabelText("Meal request")).toHaveValue("");
  });

  test("keeps new request blocked when planning status temporarily fails", async () => {
    vi.useFakeTimers();
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: [
        {
          ok: false,
          error: {
            kind: "http",
            status: 502,
            message: "Planner status is temporarily unavailable."
          }
        },
        success(readySession)
      ]
    });

    renderPlannerWorkspace({ client });
    submitReadyPrompt();
    await act(async () => {
      await Promise.resolve();
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
      await Promise.resolve();
    });

    const newRequestButton = screen.getByRole("button", { name: "New request" });
    expect(newRequestButton).toBeDisabled();
    fireEvent.click(newRequestButton);

    expect(screen.queryByLabelText("Meal request")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Reading your request"
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
      await Promise.resolve();
    });

    expect(screen.getByText("Vegetarian dinner for four")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New request" })).toBeEnabled();
  });

  test("edits quantities and removes proposal lines before acceptance", async () => {
    const client = createPlannerClient({
      createResults: [success(pairedAntipastoSession)]
    });

    renderPlannerWorkspace({ client });
    submitReadyPrompt();

    const tagliatelleLine = await screen.findByRole("listitem", {
      name: /fresh tagliatelle/i
    });
    fireEvent.change(within(tagliatelleLine).getByLabelText(
      "Quantity for Fresh Tagliatelle"
    ), {
      target: { value: "3" }
    });
    fireEvent.blur(within(tagliatelleLine).getByLabelText(
      "Quantity for Fresh Tagliatelle"
    ));

    expect(within(tagliatelleLine).getByText("£12.75")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Remove Focaccia Genovese from proposal" })
    );

    expect(screen.queryByText("Focaccia Genovese")).not.toBeInTheDocument();
    expect(screen.getAllByText("£32.70")).toHaveLength(2);
  });

  test("preserves backend planner notes when accepting after removing a line", async () => {
    const onBasketAccepted = vi.fn();
    const client = createPlannerClient({
      createResults: [success(pairedInternalCopySession)],
      acceptResults: [
        success({ basket: populatedBasket, meal_plan_grouping: mealPlanGrouping })
      ]
    });

    renderPlannerWorkspace({ client, onBasketAccepted });
    submitReadyPrompt();

    expect(
      await screen.findByRole("heading", { name: "product-backed dinner" })
    ).toBeInTheDocument();
    expect(
      screen.getByText("A validated product proposal using a menu plan.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Validated by Tavola for product validity.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("This product rounds out the antipasto plate.")
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Remove Focaccia Genovese from proposal" })
    );
    fireEvent.click(screen.getByRole("button", { name: "Add to basket" }));

    await waitFor(() => {
      expect(client.acceptProposal).toHaveBeenCalledWith("planner-1", {
        basket_id: "basket-1",
        mode: "append",
        menu_proposal: expect.objectContaining({
          title: "SKU-backed dinner",
          explanation: "A validated SKU proposal using a package template.",
          planner_notes: [
            {
              note_type: "evidence",
              source: "tavola",
              message: "Validated by Tavola for SKU validity."
            }
          ],
          warnings: ["One SKU was adjusted."]
        })
      });
    });
    const acceptedProposal =
      vi.mocked(client.acceptProposal).mock.calls[0]![1].menu_proposal;
    expect(
      acceptedProposal.courses.flatMap((course) =>
        course.lines.map((line) => line.sku_id)
      )
    ).not.toContain("focaccia-genovese-piece");
    expect(onBasketAccepted).toHaveBeenCalledWith(populatedBasket);
  });

  test("opens catalog product details from a planned menu line", async () => {
    const client = createPlannerClient({
      createResults: [success(readySession)]
    });
    const catalogClient = createCatalogClient({
      detailResults: [success(tagliatelleDetail)]
    });

    renderPlannerWorkspace({ catalogClient, client });
    submitReadyPrompt();

    const tagliatelleLine = await screen.findByRole("listitem", {
      name: /fresh tagliatelle/i
    });
    fireEvent.click(
      within(tagliatelleLine).getByRole("button", {
        name: "View details for Fresh Tagliatelle"
      })
    );

    await waitFor(() => {
      expect(catalogClient.getCatalogProduct).toHaveBeenCalledWith(
        "fresh-tagliatelle-250g"
      );
    });

    const dialog = await screen.findByRole("dialog", { name: "Product detail" });

    expect(
      within(dialog).getByRole("heading", { level: 2, name: "Fresh Tagliatelle" })
    ).toBeInTheDocument();
    expect(
      within(dialog).getByText(
        "Fresh egg tagliatelle cut into ribbons for ragu, mushrooms, or butter."
      )
    ).toBeInTheDocument();
    expect(
      within(dialog).queryByRole("button", {
        name: "Add Fresh Tagliatelle to basket"
      })
    ).not.toBeInTheDocument();
  });

  test("removes the final item from a package course", async () => {
    const client = createPlannerClient({
      createResults: [success(readySession)]
    });

    renderPlannerWorkspace({ client });
    submitReadyPrompt();

    const removeDessert = await screen.findByRole("button", {
      name: "Remove Tiramisu Cup from proposal"
    });

    expect(removeDessert).toBeEnabled();
    fireEvent.click(removeDessert);

    expect(screen.queryByText("Tiramisu Cup")).not.toBeInTheDocument();
    expect(screen.queryByText("Dessert")).not.toBeInTheDocument();
    expect(screen.getAllByText("£13.45")).toHaveLength(2);
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByLabelText("Proposal basket actions")).toHaveTextContent(
      "3 items"
    );
  });

  test("keeps proposal basket actions visible near the top of review", async () => {
    const client = createPlannerClient({
      createResults: [success(readySession)]
    });

    renderPlannerWorkspace({ basket: populatedBasket, client });
    submitReadyPrompt();

    const actionStrip = await screen.findByLabelText("Proposal basket actions");

    expect(actionStrip).toHaveTextContent("£28.45");
    expect(actionStrip).toHaveTextContent("7 items");
    expect(actionStrip).toHaveTextContent(
      "1 Product already in Basket. Add increases quantities; Replace swaps Basket."
    );
    expect(
      within(actionStrip).getByRole("button", { name: "Add proposal to basket" })
    ).toHaveTextContent("Add to basket");
    expect(
      within(actionStrip).getByRole("button", {
        name: "Replace basket with proposal"
      })
    ).toHaveTextContent("Replace basket");

    fireEvent.click(
      within(actionStrip).getByRole("button", {
        name: "Replace basket with proposal"
      })
    );

    expect(actionStrip).toHaveTextContent("This will replace the current Basket.");
    expect(
      within(actionStrip).getByRole("button", { name: "Confirm replace basket" })
    ).toBeInTheDocument();
    expect(
      within(actionStrip).getByRole("button", { name: "Keep current basket" })
    ).toBeInTheDocument();

    fireEvent.click(
      within(actionStrip).getByRole("button", { name: "Keep current basket" })
    );

    expect(
      within(actionStrip).getByRole("button", {
        name: "Replace basket with proposal"
      })
    ).toHaveTextContent("Replace basket");
  });

  test("accepts a proposal by appending it to the basket", async () => {
    const onBasketAccepted = vi.fn();
    const client = createPlannerClient({
      createResults: [success(readySession)],
      acceptResults: [
        success({ basket: populatedBasket, meal_plan_grouping: mealPlanGrouping })
      ]
    });

    renderPlannerWorkspace({ client, onBasketAccepted });
    submitReadyPrompt();

    fireEvent.click(await screen.findByRole("button", { name: "Add to basket" }));

    await waitFor(() => {
      expect(client.acceptProposal).toHaveBeenCalledWith("planner-1", {
        basket_id: "basket-1",
        mode: "append",
        menu_proposal: proposal
      });
    });
    expect(onBasketAccepted).toHaveBeenCalledWith(populatedBasket);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Menu proposal added to your basket."
    );
    expect(screen.getByLabelText("Menu proposal receipt")).toHaveTextContent(
      "Basket updated"
    );
    expect(screen.getByLabelText("Menu proposal receipt")).toHaveTextContent(
      "£28.45 · 7 items moved to Basket. Continue from Basket when ready."
    );
    expect(screen.queryByLabelText("Proposal basket actions")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add to basket" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Replace basket" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Proposal courses")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "View proposal" }));

    expect(screen.getByLabelText("Proposal courses")).toHaveTextContent(
      "Fresh Tagliatelle"
    );
    expect(screen.queryByRole("button", {
      name: "Remove Fresh Tagliatelle from proposal"
    })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Quantity for Fresh Tagliatelle")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hide proposal" })).toBeInTheDocument();
  });

  test("requires confirmation before replacing a non-empty basket", async () => {
    const client = createPlannerClient({
      createResults: [success(readySession)],
      acceptResults: [
        success({ basket: populatedBasket, meal_plan_grouping: mealPlanGrouping })
      ]
    });

    renderPlannerWorkspace({ basket: populatedBasket, client });
    submitReadyPrompt();

    fireEvent.click(
      await screen.findByRole("button", { name: "Replace basket" })
    );

    expect(client.acceptProposal).not.toHaveBeenCalled();
    expect(
      screen.getByText("This will replace the current Basket.")
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Confirm replace basket" }));

    await waitFor(() => {
      expect(client.acceptProposal).toHaveBeenCalledWith(
        "planner-1",
        expect.objectContaining({ mode: "replace" })
      );
    });
    expect(screen.getByRole("status")).toHaveTextContent(
      "Menu proposal replaced your basket."
    );
  });

  test("renders planner errors with product language", async () => {
    const client = createPlannerClient({
      createResults: [
        {
          ok: false,
          error: {
            kind: "http",
            status: 422,
            message: "Tavola could not find matching products."
          }
        }
      ]
    });

    renderPlannerWorkspace({ client });

    fireEvent.change(screen.getByLabelText("Meal request"), {
      target: { value: "Dairy-free feast for 10" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Plan menu" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Tavola could not find matching products."
    );
    expect(screen.getByRole("alert")).not.toHaveTextContent(/sku/i);
  });
});

function renderPlannerWorkspace({
  basket = emptyBasket,
  catalogClient,
  client,
  onBasketAccepted = vi.fn()
}: {
  basket?: Basket | null;
  catalogClient?: { getCatalogProduct: (skuId: string) => Promise<ApiResult<CatalogProductDetail>> };
  client: PlannerClient;
  onBasketAccepted?: (basket: Basket) => void;
}) {
  return render(
    <PlannerWorkspace
      basket={basket}
      catalogClient={catalogClient}
      client={client}
      onBasketAccepted={onBasketAccepted}
    />
  );
}

function submitReadyPrompt() {
  fireEvent.change(screen.getByLabelText("Meal request"), {
    target: { value: "Vegetarian dinner for 4 around £50" }
  });
  fireEvent.click(screen.getByRole("button", { name: "Plan menu" }));
}

function createPlannerClient({
  statusResult = success({
    enabled: true,
    mode: "real_codex",
    message: "Planner is running with live Codex assistance."
  }),
  createResults = [],
  followUpResults = [],
  fetchResults = [],
  acceptResults = []
}: {
  statusResult?: ApiResult<PlannerStatusResponse>;
  createResults?: Array<
    ApiResult<PlannerSessionResponse> | Promise<ApiResult<PlannerSessionResponse>>
  >;
  followUpResults?: Array<
    ApiResult<PlannerSessionResponse> | Promise<ApiResult<PlannerSessionResponse>>
  >;
  fetchResults?: Array<
    ApiResult<PlannerSessionResponse> | Promise<ApiResult<PlannerSessionResponse>>
  >;
  acceptResults?: Array<
    ApiResult<AcceptMenuProposalResponse> | Promise<ApiResult<AcceptMenuProposalResponse>>
  >;
}): PlannerClient {
  return {
    getStatus: vi.fn(async () => await statusResult),
    createSession: vi.fn(async () => await shiftResult(createResults, "create")),
    answerFollowUp: vi.fn(
      async () => await shiftResult(followUpResults, "follow-up")
    ),
    fetchSession: vi.fn(async () => await shiftResult(fetchResults, "fetch")),
    validateProposal: vi.fn(),
    acceptProposal: vi.fn(async () => await shiftResult(acceptResults, "accept"))
  };
}

function createCatalogClient({
  detailResults = []
}: {
  detailResults?: Array<
    ApiResult<CatalogProductDetail> | Promise<ApiResult<CatalogProductDetail>>
  >;
}) {
  return {
    getCatalogProduct: vi.fn(
      async () => await shiftResult(detailResults, "catalog detail")
    )
  };
}

async function shiftResult<T>(
  results: Array<ApiResult<T> | Promise<ApiResult<T>>>,
  action: string
): Promise<ApiResult<T>> {
  const result = results.shift();
  if (!result) {
    throw new Error(`No planner ${action} result was queued.`);
  }

  return await result;
}

function success<T>(data: T): ApiResult<T> {
  return { ok: true, data };
}
