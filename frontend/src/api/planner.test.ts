import { afterEach, describe, expect, test, vi } from "vitest";

import type { Basket } from "../types/basket";
import type { MenuProposal, PlannerSessionResponse } from "../types/planner";

const proposal: MenuProposal = {
  title: "Vegetarian dinner for four",
  explanation: "A simple Tavola supper with antipasto, pasta, and dessert.",
  planner_notes: [
    { note_type: "evidence", source: "tavola", message: "Party size set to 4." },
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
    }
  ],
  total_minor: 850,
  currency: "GBP",
  item_count: 2,
  line_count: 1,
  warnings: []
};

const plannerSession: PlannerSessionResponse = {
  planner_session_id: "planner-1",
  status: "proposal_ready",
  customer_request: "Dinner for 4",
  follow_up_answers: [],
  follow_up_question: null,
  menu_proposal: proposal,
  validation_errors: []
};

const plannerStatus = {
  enabled: true,
  mode: "real_codex" as const,
  message: "Planner is running with live Codex assistance."
};

const basket: Basket = {
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
      course: "primo" as const,
      course_label: "Primo",
      line_sku_ids: ["fresh-tagliatelle-250g"]
    }
  ]
};

describe("planner API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
    vi.unstubAllEnvs();
  });

  test("creates a planner session with the expected request", async () => {
    const { createPlannerSession } = await loadPlannerClient();
    const fetchMock = stubJsonResponse(plannerSession);

    const result = await createPlannerSession({ message: "Dinner for 4" });

    expect(result).toEqual({ ok: true, data: plannerSession });
    expect(fetchMock).toHaveBeenCalledWith("/api/planner/sessions", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message: "Dinner for 4" })
    });
  });

  test("fetches planner status for live mode visibility", async () => {
    const { getPlannerStatus } = await loadPlannerClient();
    const fetchMock = stubJsonResponse(plannerStatus);

    const result = await getPlannerStatus();

    expect(result).toEqual({ ok: true, data: plannerStatus });
    expect(fetchMock).toHaveBeenCalledWith("/api/planner/status", {
      headers: { Accept: "application/json" }
    });
  });

  test("answers a follow-up with an encoded planner session ID", async () => {
    const { answerFollowUp } = await loadPlannerClient();
    const fetchMock = stubJsonResponse(plannerSession);

    const result = await answerFollowUp("planner one/two", {
      message: "4 people"
    });

    expect(result).toEqual({ ok: true, data: plannerSession });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/planner/sessions/planner%20one%2Ftwo/follow-up-answer",
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: "4 people" })
      }
    );
  });

  test("fetches a planner session by encoded ID", async () => {
    const { fetchPlannerSession } = await loadPlannerClient();
    const fetchMock = stubJsonResponse(plannerSession);

    const result = await fetchPlannerSession("planner one/two");

    expect(result).toEqual({ ok: true, data: plannerSession });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/planner/sessions/planner%20one%2Ftwo",
      {
        headers: { Accept: "application/json" }
      }
    );
  });

  test("validates an edited proposal without accepting it", async () => {
    const { validateProposal } = await loadPlannerClient();
    const fetchMock = stubJsonResponse(plannerSession);

    const result = await validateProposal("planner-1", {
      menu_proposal: proposal
    });

    expect(result).toEqual({ ok: true, data: plannerSession });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/planner/sessions/planner-1/proposal/validate",
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ menu_proposal: proposal })
      }
    );
  });

  test("accepts a proposal and maps the returned basket", async () => {
    const { acceptProposal } = await loadPlannerClient();
    const fetchMock = stubJsonResponse({
      basket,
      meal_plan_grouping: mealPlanGrouping
    });

    const result = await acceptProposal("planner-1", {
      basket_id: "basket-1",
      mode: "append",
      menu_proposal: proposal
    });

    expect(result).toEqual({
      ok: true,
      data: { basket, meal_plan_grouping: mealPlanGrouping }
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/planner/sessions/planner-1/accept",
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          basket_id: "basket-1",
          mode: "append",
          menu_proposal: proposal
        })
      }
    );
  });

  test.each([
    ["missing session ID", { ...plannerSession, planner_session_id: undefined }],
    ["unknown status", { ...plannerSession, status: "waiting" }],
    ["malformed proposal", { ...plannerSession, menu_proposal: { title: "Menu" } }],
    [
      "malformed validation error",
      { ...plannerSession, validation_errors: [{ code: "bad" }] }
    ]
  ])("rejects a malformed planner session response: %s", async (
    _caseName,
    malformedResponse
  ) => {
    const { createPlannerSession } = await loadPlannerClient();
    stubJsonResponse(malformedResponse);

    const result = await createPlannerSession({ message: "Dinner for 4" });

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid planner response."
      }
    });
  });

  test.each([
    ["missing enabled", { mode: "real_codex", message: "Ready." }],
    ["unknown mode", { enabled: true, mode: "sdk", message: "Ready." }],
    ["missing message", { enabled: true, mode: "real_codex" }]
  ])("rejects a malformed planner status response: %s", async (
    _caseName,
    malformedResponse
  ) => {
    const { getPlannerStatus } = await loadPlannerClient();
    stubJsonResponse(malformedResponse);

    const result = await getPlannerStatus();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "invalid_response",
        message: "The Tavola API returned an invalid planner status response."
      }
    });
  });

  test.each([
    ["create planner session", createPlannerSession],
    ["answer follow-up", answerFollowUp],
    ["fetch planner session", fetchPlannerSession],
    ["validate proposal", validateProposal],
    ["accept proposal", acceptProposal]
  ])("passes through HTTP errors from %s", async (_caseName, act) => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Planner could not find items." }), {
          status: 422
        })
      )
    );

    const result = await act();

    expect(result).toEqual({
      ok: false,
      error: {
        kind: "http",
        message: "Planner could not find items.",
        status: 422
      }
    });
  });
});

async function loadPlannerClient() {
  return await import("./planner");
}

async function createPlannerSession() {
  const { createPlannerSession } = await loadPlannerClient();

  return await createPlannerSession({ message: "Dinner for 4" });
}

async function answerFollowUp() {
  const { answerFollowUp } = await loadPlannerClient();

  return await answerFollowUp("planner-1", { message: "4 people" });
}

async function fetchPlannerSession() {
  const { fetchPlannerSession } = await loadPlannerClient();

  return await fetchPlannerSession("planner-1");
}

async function validateProposal() {
  const { validateProposal } = await loadPlannerClient();

  return await validateProposal("planner-1", { menu_proposal: proposal });
}

async function acceptProposal() {
  const { acceptProposal } = await loadPlannerClient();

  return await acceptProposal("planner-1", {
    basket_id: "basket-1",
    mode: "append",
    menu_proposal: proposal
  });
}

function stubJsonResponse(body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  return fetchMock;
}
