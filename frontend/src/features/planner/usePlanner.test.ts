import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import type { ApiResult } from "../../api/client";
import type { Basket } from "../../types/basket";
import type {
  AcceptMenuProposalResponse,
  MenuProposal,
  PlannerSessionResponse,
  PlannerStatusResponse
} from "../../types/planner";
import { usePlanner, type PlannerClient } from "./usePlanner";

const proposal: MenuProposal = {
  title: "Vegetarian dinner for four",
  explanation: "A simple Tavola supper with antipasto, pasta, and dessert.",
  planner_notes: [
    { note_type: "evidence", source: "tavola", message: "Party size set to 4." },
    {
      note_type: "evidence",
      source: "tavola",
      message: "All products were checked against Tavola's catalog."
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
  warnings: []
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

const updatedBasket: Basket = {
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

describe("usePlanner", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test("starts empty and loads a proposal from a prompt", async () => {
    vi.useFakeTimers();
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: [success(readySession)]
    });

    const { result } = renderHook(() => usePlanner({ client }));

    expect(result.current.state.status).toBe("empty");

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    expect(client.createSession).toHaveBeenCalledWith({
      message: "Vegetarian dinner for 4 around £50"
    });
    expect(result.current.state.status).toBe("planning");
    expect(result.current.state.session?.planner_session_id).toBe("planner-1");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(client.fetchSession).toHaveBeenCalledWith("planner-1");
    expect(result.current.state.status).toBe("proposal_ready");
    expect(result.current.state.session?.planner_session_id).toBe("planner-1");
    expect(result.current.draftProposal?.title).toBe("Vegetarian dinner for four");
  });

  test("exposes planning updates from the latest polled session", async () => {
    vi.useFakeTimers();
    const startedSession: PlannerSessionResponse = {
      ...planningSession,
      planning_updates: [
        ...planningSession.planning_updates,
        { stage: "started", message: "Sending request" }
      ]
    };
    const catalogSession: PlannerSessionResponse = {
      ...planningSession,
      planning_updates: [
        ...startedSession.planning_updates,
        { stage: "planning", message: "Checking Tavola's catalog" }
      ]
    };
    const client = createPlannerClient({
      createResults: [success(startedSession)],
      fetchResults: [success(catalogSession), success(readySession)]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4");
    });

    expect(result.current.state.status).toBe("planning");
    expect(result.current.state.session?.planning_updates.at(-1)?.message).toBe(
      "Sending request"
    );
    expect(result.current).not.toHaveProperty("planningElapsedMs");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(result.current.state.status).toBe("planning");
    expect(result.current.state.session?.planning_updates.at(-1)?.message).toBe(
      "Checking Tavola's catalog"
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(result.current.state.status).toBe("proposal_ready");
  });

  test("keeps the original request visible while answering a follow-up", async () => {
    vi.useFakeTimers();
    const planningAfterFollowUp: PlannerSessionResponse = {
      ...planningSession,
      planner_session_id: "planner-2",
      customer_request: "Plan a dinner",
      follow_up_answers: ["4 people"],
      planning_updates: [
        ...needsInputSession.planning_updates,
        { stage: "queued", message: "Tavola is getting your updated menu request ready." }
      ]
    };
    const client = createPlannerClient({
      createResults: [success(needsInputSession)],
      followUpResults: [success(planningAfterFollowUp)],
      fetchResults: [success(readySession)]
    });

    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Plan a dinner");
    });

    expect(result.current.state.status).toBe("needs_input");
    expect(result.current.state.session?.customer_request).toBe("Plan a dinner");
    expect(result.current.state.session?.follow_up_question).toBe(
      "How many people are you serving?"
    );

    await act(async () => {
      await result.current.submitFollowUp("4 people");
    });

    expect(client.answerFollowUp).toHaveBeenCalledWith("planner-2", {
      message: "4 people"
    });
    expect(result.current.state.status).toBe("planning");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(result.current.state.status).toBe("proposal_ready");
  });

  test("ignores polling results from an older prompt after a new prompt starts", async () => {
    vi.useFakeTimers();
    const secondPlanningSession: PlannerSessionResponse = {
      ...planningSession,
      planner_session_id: "planner-2",
      customer_request: "Birthday lunch for 8"
    };
    const secondReadySession: PlannerSessionResponse = {
      ...readySession,
      planner_session_id: "planner-2",
      customer_request: "Birthday lunch for 8"
    };
    const client = createPlannerClient({
      createResults: [success(planningSession), success(secondPlanningSession)],
      fetchResults: [success(secondReadySession)]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });
    await act(async () => {
      await result.current.submitPrompt("Birthday lunch for 8");
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(client.fetchSession).toHaveBeenCalledWith("planner-2");
    expect(client.fetchSession).not.toHaveBeenCalledWith("planner-1");
    expect(result.current.state.status).toBe("proposal_ready");
    expect(result.current.state.session?.planner_session_id).toBe("planner-2");
  });

  test("keeps polling the current planning session when a replacement prompt is busy", async () => {
    vi.useFakeTimers();
    const client = createPlannerClient({
      createResults: [
        success(planningSession),
        {
          ok: false,
          error: {
            kind: "http",
            status: 503,
            message: "Tavola is already planning a menu."
          }
        }
      ],
      fetchResults: [success(readySession)]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });
    await act(async () => {
      await result.current.submitPrompt("Birthday lunch for 8");
    });

    expect(result.current.state.status).toBe("planning");
    expect(result.current.state.session?.planner_session_id).toBe("planner-1");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(client.fetchSession).toHaveBeenCalledWith("planner-1");
    expect(result.current.state.status).toBe("proposal_ready");
    expect(result.current.state.session?.planner_session_id).toBe("planner-1");
  });

  test("does not reset an in-progress planner session", async () => {
    vi.useFakeTimers();
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: [success(readySession)]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.state.status).toBe("planning");
    expect(result.current.state.session?.planner_session_id).toBe("planner-1");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
    });

    expect(client.fetchSession).toHaveBeenCalledWith("planner-1");
    expect(result.current.state.status).toBe("proposal_ready");
  });

  test("keeps polling when a planning session fetch fails", async () => {
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
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });
    await act(async () => {
      await Promise.resolve();
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
      await Promise.resolve();
    });

    expect(result.current.state.status).toBe("planning");
    expect(result.current.state.session?.planner_session_id).toBe("planner-1");
    expect(result.current.reset()).toBe(false);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
      await Promise.resolve();
    });

    expect(client.fetchSession).toHaveBeenCalledTimes(2);
    expect(result.current.state.status).toBe("proposal_ready");
  });

  test("fails instead of spinning forever when a planning poll response is invalid", async () => {
    vi.useFakeTimers();
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: [
        {
          ok: false,
          error: {
            kind: "invalid_response",
            message: "The Tavola API returned an invalid planner response."
          }
        }
      ]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Dinner with drinks for 6");
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
      await Promise.resolve();
    });

    expect(result.current.state.status).toBe("failed");
    expect(result.current.state.message).toBe(
      "The Tavola API returned an invalid planner response."
    );
  });

  test("fails instead of spinning forever when the planning session disappears", async () => {
    vi.useFakeTimers();
    const client = createPlannerClient({
      createResults: [success(planningSession)],
      fetchResults: [
        {
          ok: false,
          error: {
            kind: "http",
            status: 404,
            message: "Planner session not found."
          }
        }
      ]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Dinner with drinks for 6");
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2_000);
      await Promise.resolve();
    });

    expect(result.current.state.status).toBe("failed");
    expect(result.current.state.message).toBe("Planner session not found.");
  });

  test("loads disabled planner status and blocks prompt submission", async () => {
    const client = createPlannerClient({
      statusResult: success({
        enabled: false,
        mode: "disabled",
        message: "Planner setup is incomplete."
      })
    });

    const { result } = renderHook(() => usePlanner({ client }));

    await waitFor(() => {
      expect(result.current.plannerStatus.status).toBe("disabled");
    });

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    expect(client.createSession).not.toHaveBeenCalled();
    expect(result.current.state.status).toBe("failed");
    expect(result.current.state.message).toBe("Planner setup is incomplete.");
  });

  test("keeps internal setup wording out of planner status copy", async () => {
    const client = createPlannerClient({
      statusResult: success({
        enabled: false,
        mode: "disabled",
        message: "Missing Codex SDK token in backend credentials."
      })
    });

    const { result } = renderHook(() => usePlanner({ client }));

    await waitFor(() => {
      expect(result.current.plannerStatus.status).toBe("disabled");
    });

    expect(result.current.plannerStatus.message).toBe(
      "Planner is unavailable right now. You can still browse products and build a basket."
    );
    expect(result.current.plannerStatus.message).not.toMatch(
      /sdk|token|credential|stack/i
    );
  });

  test("clears a stale proposal when a new planner request fails", async () => {
    const client = createPlannerClient({
      createResults: [
        success(readySession),
        {
          ok: false,
          error: {
            kind: "http",
            status: 503,
            message: "Planner is not configured for this environment."
          }
        }
      ]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    expect(result.current.draftProposal?.title).toBe("Vegetarian dinner for four");

    await act(async () => {
      await result.current.submitPrompt("A birthday lunch for 8");
    });

    expect(result.current.state.status).toBe("failed");
    expect(result.current.draftProposal).toBeNull();
  });

  test("keeps proposal edits local until validation", async () => {
    const normalizedProposal: MenuProposal = {
      ...proposal,
      courses: proposal.courses.map((course) =>
        course.course === "primo"
          ? {
              ...course,
              lines: course.lines.map((line) => ({
                ...line,
                quantity: 3,
                line_total_minor: 1275
              }))
            }
          : course
      ),
      total_minor: 3270,
      item_count: 8
    };
    const client = createPlannerClient({
      createResults: [success(readySession)],
      validateResults: [
        success({
          ...readySession,
          menu_proposal: normalizedProposal
        })
      ]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    act(() => {
      result.current.setLineQuantity("fresh-tagliatelle-250g", 3);
    });

    expect(client.validateProposal).not.toHaveBeenCalled();
    const editedLine = result.current.draftProposal?.courses
      .flatMap((course) => course.lines)
      .find((line) => line.sku_id === "fresh-tagliatelle-250g");
    expect(editedLine?.quantity).toBe(3);

    await act(async () => {
      await result.current.validateProposal();
    });

    expect(client.validateProposal).toHaveBeenCalledWith("planner-1", {
      menu_proposal: expect.objectContaining({ total_minor: 3270 })
    });
    expect(result.current.state.status).toBe("proposal_ready");
    expect(result.current.draftProposal?.total_minor).toBe(3270);
  });

  test("removes proposal lines locally and surfaces validation errors", async () => {
    const client = createPlannerClient({
      createResults: [success(pairedAntipastoSession)],
      validateResults: [
        {
          ok: false,
          error: {
            kind: "http",
            status: 422,
            message: "One item is no longer available."
          }
        }
      ]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    act(() => {
      result.current.removeLine("focaccia-genovese-piece");
    });

    expect(result.current.draftProposal?.line_count).toBe(3);
    expect(result.current.draftProposal?.item_count).toBe(7);

    await act(async () => {
      await result.current.validateProposal();
    });

    expect(result.current.state.status).toBe("validation_error");
    expect(result.current.state.message).toBe("One item is no longer available.");
  });

  test("removes the final line in a course", async () => {
    const client = createPlannerClient({
      createResults: [success(readySession)]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    act(() => {
      result.current.removeLine("tiramisu-cup-single");
    });

    expect(result.current.draftProposal?.line_count).toBe(2);
    expect(result.current.draftProposal?.item_count).toBe(3);
    expect(result.current.draftProposal?.total_minor).toBe(1345);
    expect(
      result.current.draftProposal?.courses.find((course) => course.course === "dessert")
        ?.lines
    ).toBeUndefined();
  });

  test("accepts a proposal into the selected basket mode", async () => {
    const client = createPlannerClient({
      createResults: [success(readySession)],
      acceptResults: [
        success({ basket: updatedBasket, meal_plan_grouping: mealPlanGrouping })
      ]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    let acceptedBasket: Basket | null = null;
    await act(async () => {
      acceptedBasket = await result.current.acceptProposal("basket-1", "replace");
    });

    expect(client.acceptProposal).toHaveBeenCalledWith("planner-1", {
      basket_id: "basket-1",
      mode: "replace",
      menu_proposal: proposal
    });
    expect(acceptedBasket).toEqual(updatedBasket);
    expect(result.current.state.status).toBe("accepted");
    expect(result.current.state.message).toBe("Menu proposal replaced your basket.");
  });

  test("does not accept the same proposal again after it is accepted", async () => {
    const client = createPlannerClient({
      createResults: [success(readySession)],
      acceptResults: [
        success({ basket: updatedBasket, meal_plan_grouping: mealPlanGrouping })
      ]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    await act(async () => {
      await result.current.acceptProposal("basket-1", "append");
    });
    await act(async () => {
      await result.current.acceptProposal("basket-1", "append");
    });

    expect(client.acceptProposal).toHaveBeenCalledTimes(1);
    expect(result.current.state.status).toBe("accepted");
  });

  test("exposes pending state while accepting a proposal", async () => {
    const deferredAccept = createDeferred<ApiResult<AcceptMenuProposalResponse>>();
    const client = createPlannerClient({
      createResults: [success(readySession)],
      acceptResults: [deferredAccept.promise]
    });
    const { result } = renderHook(() => usePlanner({ client }));

    await act(async () => {
      await result.current.submitPrompt("Vegetarian dinner for 4 around £50");
    });

    void act(() => {
      void result.current.acceptProposal("basket-1", "append");
    });

    await waitFor(() => {
      expect(result.current.state.status).toBe("accept_pending");
    });

    await act(async () => {
      deferredAccept.resolve(
        success({ basket: updatedBasket, meal_plan_grouping: mealPlanGrouping })
      );
    });

    await waitFor(() => {
      expect(result.current.state.status).toBe("accepted");
    });
  });
});

function createPlannerClient({
  statusResult = success({
    enabled: true,
    mode: "real_codex",
    message: "Planner is running with live Codex assistance."
  }),
  createResults = [],
  followUpResults = [],
  fetchResults = [],
  validateResults = [],
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
  validateResults?: Array<
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
    validateProposal: vi.fn(
      async () => await shiftResult(validateResults, "validate")
    ),
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

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((promiseResolve) => {
    resolve = promiseResolve;
  });

  return { promise, resolve };
}
