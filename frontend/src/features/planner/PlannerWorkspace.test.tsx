import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import type { ApiResult } from "../../api/client";
import type { Basket } from "../../types/basket";
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
              sku_id: "focaccia-genovese-slab",
              name: "Focaccia Genovese",
              category_id: "antipasti",
              category_label: "Antipasti",
              unit_label: "slab",
              quantity: 1,
              unit_price_minor: 650,
              line_total_minor: 650,
              currency: "GBP",
              image_id: "focaccia-genovese-slab",
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

const readySession: PlannerSessionResponse = {
  planner_session_id: "planner-1",
  status: "proposal_ready",
  customer_request: "Vegetarian dinner for 4 around £50",
  follow_up_answers: [],
  follow_up_question: null,
  menu_proposal: proposal,
  validation_errors: []
};

const planningSession: PlannerSessionResponse = {
  planner_session_id: "planner-1",
  status: "planning",
  customer_request: "Vegetarian dinner for 4 around £50",
  follow_up_answers: [],
  follow_up_question: null,
  menu_proposal: null,
  validation_errors: []
};

const pairedAntipastoSession: PlannerSessionResponse = {
  ...readySession,
  menu_proposal: pairedAntipastoProposal
};

const needsInputSession: PlannerSessionResponse = {
  planner_session_id: "planner-2",
  status: "needs_input",
  customer_request: "Plan a dinner",
  follow_up_answers: [],
  follow_up_question: "How many people are you serving?",
  menu_proposal: null,
  validation_errors: []
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

  test("renders the planner heading without the old decorative logo", () => {
    const client = createPlannerClient({});

    const { container } = renderPlannerWorkspace({ client });

    expect(
      screen.getByRole("heading", { level: 2, name: "Plan a menu" })
    ).toBeInTheDocument();
    expect(screen.getByText("powered by Codex")).toBeInTheDocument();
    expect(container.querySelector(".planner-workspace__icon")).toBeNull();
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
      "Tavola is planning your menu."
    );

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

  test("shows customer-safe progress copy while planning remains pending", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-04T12:00:00Z"));
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: Array.from({ length: 20 }, () => success(planningSession))
    });

    renderPlannerWorkspace({ client });
    submitReadyPrompt();

    expect(screen.getByRole("status")).toHaveTextContent(
      "Tavola is planning your menu."
    );

    act(() => {
      vi.advanceTimersByTime(5_000);
    });

    expect(screen.getByRole("status")).toHaveTextContent(
      "Checking the catalog and shaping a menu."
    );

    act(() => {
      vi.advanceTimersByTime(10_000);
    });

    expect(screen.getByRole("status")).toHaveTextContent(
      "Validating products and prices."
    );

    act(() => {
      vi.advanceTimersByTime(15_000);
    });

    const statusCopy = screen.getByRole("status").textContent ?? "";
    expect(statusCopy).toContain(
      "Still planning. Tavola is checking the proposal before review."
    );
    expect(statusCopy).not.toMatch(/\d+s elapsed/i);
    expect(screen.getByLabelText("Planning progress")).toHaveTextContent(
      "CatalogMenu shapePricesReview"
    );
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
    ).toHaveTextContent("Tavola validates before Basket changes.");
    expect(
      screen.getByText("Real Products from the catalog")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Prices come from Tavola's catalog")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Dietary requests checked against product labels")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Menu proposal shown for review")
    ).toBeInTheDocument();
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
      screen.getByRole("button", { name: "Classic Italian dinner for 2" })
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
      follow_up_answers: ["4 people"]
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
      "Tavola is planning your menu."
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
      "Tavola is planning your menu."
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
      "Tavola is planning your menu."
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
    expect(screen.getByText("£32.70")).toBeInTheDocument();
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
    expect(screen.getByText("£13.45")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
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
    expect(screen.getByRole("button", { name: "Add to basket" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Replace basket" })).toBeDisabled();
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
      screen.getByText("This will replace the current basket.")
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Confirm replace basket" }));

    await waitFor(() => {
      expect(client.acceptProposal).toHaveBeenCalledWith(
        "planner-1",
        expect.objectContaining({ mode: "replace" })
      );
    });
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
  client,
  onBasketAccepted = vi.fn()
}: {
  basket?: Basket | null;
  client: PlannerClient;
  onBasketAccepted?: (basket: Basket) => void;
}) {
  return render(
    <PlannerWorkspace
      basket={basket}
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
