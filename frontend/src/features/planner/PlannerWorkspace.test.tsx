import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import type { ApiResult } from "../../api/client";
import type { Basket } from "../../types/basket";
import type {
  AcceptMenuProposalResponse,
  MenuProposal,
  PlannerSessionResponse
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

  test("submits a meal prompt and renders a reviewable proposal", async () => {
    const client = createPlannerClient({
      createResults: [success(readySession)]
    });

    renderPlannerWorkspace({ client });

    fireEvent.change(screen.getByLabelText("Meal request"), {
      target: { value: "Vegetarian dinner for 4 around £50" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Plan menu" }));

    expect(client.createSession).toHaveBeenCalledWith({
      message: "Vegetarian dinner for 4 around £50"
    });
    expect(
      await screen.findByRole("heading", {
        level: 3,
        name: "Vegetarian dinner for four"
      })
    ).toBeInTheDocument();
    expect(screen.getByText("powered by Codex")).toBeInTheDocument();
    expect(screen.getByText("Fresh Tagliatelle")).toBeInTheDocument();
    expect(screen.getByText("Prices were calculated by Tavola.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add to basket" })).toBeEnabled();
  });

  test("answers a required follow-up while preserving the original request", async () => {
    const client = createPlannerClient({
      createResults: [success(needsInputSession)],
      followUpResults: [success(readySession)]
    });

    renderPlannerWorkspace({ client });

    fireEvent.change(screen.getByLabelText("Meal request"), {
      target: { value: "Plan a dinner" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Plan menu" }));

    expect(await screen.findByText("Plan a dinner")).toBeInTheDocument();
    expect(
      screen.getByText("How many people are you serving?")
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Follow-up answer"), {
      target: { value: "4 people" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Continue planning" }));

    await waitFor(() => {
      expect(client.answerFollowUp).toHaveBeenCalledWith("planner-2", {
        message: "4 people"
      });
    });
    expect(await screen.findByText("Vegetarian dinner for four")).toBeInTheDocument();
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

  test("does not allow removing the final item from a package course", async () => {
    const client = createPlannerClient({
      createResults: [success(readySession)]
    });

    renderPlannerWorkspace({ client });
    submitReadyPrompt();

    expect(
      await screen.findByRole("button", {
        name: "Remove Tiramisu Cup from proposal"
      })
    ).toBeDisabled();
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
  render(
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
  createResults = [],
  followUpResults = [],
  acceptResults = []
}: {
  createResults?: Array<
    ApiResult<PlannerSessionResponse> | Promise<ApiResult<PlannerSessionResponse>>
  >;
  followUpResults?: Array<
    ApiResult<PlannerSessionResponse> | Promise<ApiResult<PlannerSessionResponse>>
  >;
  acceptResults?: Array<
    ApiResult<AcceptMenuProposalResponse> | Promise<ApiResult<AcceptMenuProposalResponse>>
  >;
}): PlannerClient {
  return {
    createSession: vi.fn(async () => await shiftResult(createResults, "create")),
    answerFollowUp: vi.fn(
      async () => await shiftResult(followUpResults, "follow-up")
    ),
    fetchSession: vi.fn(),
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
