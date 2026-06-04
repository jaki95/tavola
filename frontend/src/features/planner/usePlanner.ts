import { useCallback, useMemo, useState } from "react";

import {
  acceptProposal,
  answerFollowUp,
  createPlannerSession,
  fetchPlannerSession,
  validateProposal
} from "../../api/planner";
import type { ApiResult } from "../../api/client";
import type { Basket } from "../../types/basket";
import type {
  AcceptMenuProposalMode,
  AcceptMenuProposalRequest,
  AcceptMenuProposalResponse,
  CreatePlannerSessionRequest,
  MenuProposal,
  PlannerFollowUpRequest,
  PlannerSessionResponse,
  ValidateMenuProposalRequest
} from "../../types/planner";

export type PlannerClient = {
  createSession: (
    request: CreatePlannerSessionRequest
  ) => Promise<ApiResult<PlannerSessionResponse>>;
  answerFollowUp: (
    plannerSessionId: string,
    request: PlannerFollowUpRequest
  ) => Promise<ApiResult<PlannerSessionResponse>>;
  fetchSession: (plannerSessionId: string) => Promise<ApiResult<PlannerSessionResponse>>;
  validateProposal: (
    plannerSessionId: string,
    request: ValidateMenuProposalRequest
  ) => Promise<ApiResult<PlannerSessionResponse>>;
  acceptProposal: (
    plannerSessionId: string,
    request: AcceptMenuProposalRequest
  ) => Promise<ApiResult<AcceptMenuProposalResponse>>;
};

export type PlannerUiState =
  | {
      status: "empty";
      session: null;
      message: null;
    }
  | {
      status: "loading";
      session: PlannerSessionResponse | null;
      message: null;
    }
  | {
      status: "needs_input" | "proposal_ready";
      session: PlannerSessionResponse;
      message: null;
    }
  | {
      status: "validation_error" | "failed";
      session: PlannerSessionResponse | null;
      message: string;
    }
  | {
      status: "accept_pending";
      session: PlannerSessionResponse;
      message: null;
    }
  | {
      status: "accepted";
      session: PlannerSessionResponse;
      message: string;
      basket: Basket;
    };

type UsePlannerOptions = {
  client?: PlannerClient;
};

const defaultPlannerClient: PlannerClient = {
  createSession: createPlannerSession,
  answerFollowUp,
  fetchSession: fetchPlannerSession,
  validateProposal,
  acceptProposal
};

export function usePlanner({ client = defaultPlannerClient }: UsePlannerOptions = {}) {
  const [state, setState] = useState<PlannerUiState>({
    status: "empty",
    session: null,
    message: null
  });
  const [draftProposal, setDraftProposal] = useState<MenuProposal | null>(null);

  const currentSession = state.session;

  const applySession = useCallback((session: PlannerSessionResponse) => {
    setDraftProposal(session.menu_proposal);

    if (session.status === "needs_input") {
      setState({ status: "needs_input", session, message: null });
      return;
    }

    if (session.status === "proposal_ready") {
      setState({ status: "proposal_ready", session, message: null });
      return;
    }

    if (session.status === "failed") {
      setState({
        status: "failed",
        session,
        message: errorMessageFromSession(session)
      });
      return;
    }

    setState({ status: "proposal_ready", session, message: null });
  }, []);

  const submitPrompt = useCallback(
    async (message: string) => {
      const trimmedMessage = message.trim();
      if (!trimmedMessage) {
        setState({
          status: "failed",
          session: currentSession,
          message: "Tell Tavola what you would like to serve."
        });
        return;
      }

      setDraftProposal(null);
      setState({ status: "loading", session: null, message: null });
      const result = await client.createSession({ message: trimmedMessage });

      if (result.ok) {
        applySession(result.data);
        return;
      }

      setState({
        status: "failed",
        session: null,
        message: result.error.message
      });
    },
    [applySession, client, currentSession]
  );

  const submitFollowUp = useCallback(
    async (message: string) => {
      const trimmedMessage = message.trim();
      if (!currentSession || currentSession.status !== "needs_input") {
        setState({
          status: "failed",
          session: currentSession,
          message: "Start a planner request before answering a follow-up."
        });
        return;
      }
      if (!trimmedMessage) {
        setState({
          status: "validation_error",
          session: currentSession,
          message: "Answer the planner question before continuing."
        });
        return;
      }

      setState({ status: "loading", session: currentSession, message: null });
      const result = await client.answerFollowUp(currentSession.planner_session_id, {
        message: trimmedMessage
      });

      if (result.ok) {
        applySession(result.data);
        return;
      }

      setState({
        status: "failed",
        session: currentSession,
        message: result.error.message
      });
    },
    [applySession, client, currentSession]
  );

  const setLineQuantity = useCallback((skuId: string, quantity: number) => {
    if (!Number.isInteger(quantity) || quantity < 1) {
      return;
    }

    setDraftProposal((proposal) =>
      proposal ? recalculateProposal(updateProposalLineQuantity(proposal, skuId, quantity)) : proposal
    );
  }, []);

  const removeLine = useCallback((skuId: string) => {
    setDraftProposal((proposal) =>
      proposal ? recalculateProposal(removeProposalLineIfCourseRemains(proposal, skuId)) : proposal
    );
  }, []);

  const validateDraftProposal = useCallback(async () => {
    if (!currentSession || !draftProposal) {
      setState({
        status: "validation_error",
        session: currentSession,
        message: "Create a menu proposal before validating it."
      });
      return;
    }

    const result = await client.validateProposal(currentSession.planner_session_id, {
      menu_proposal: draftProposal
    });

    if (result.ok) {
      applySession(result.data);
      return;
    }

    setState({
      status: "validation_error",
      session: currentSession,
      message: result.error.message
    });
  }, [applySession, client, currentSession, draftProposal]);

  const acceptDraftProposal = useCallback(
    async (
      basketId: string,
      mode: AcceptMenuProposalMode
    ): Promise<Basket | null> => {
      if (state.status === "accepted" || state.status === "accept_pending") {
        return null;
      }

      if (!currentSession || !draftProposal) {
        setState({
          status: "validation_error",
          session: currentSession,
          message: "Create a menu proposal before adding it to the basket."
        });
        return null;
      }

      setState({ status: "accept_pending", session: currentSession, message: null });
      const result = await client.acceptProposal(currentSession.planner_session_id, {
        basket_id: basketId,
        mode,
        menu_proposal: draftProposal
      });

      if (!result.ok) {
        setState({
          status: "validation_error",
          session: currentSession,
          message: result.error.message
        });
        return null;
      }

      setState({
        status: "accepted",
        session: {
          ...currentSession,
          status: "accepted",
          menu_proposal: draftProposal,
          follow_up_question: null
        },
        message: "Menu proposal added to your basket.",
        basket: result.data.basket
      });
      return result.data.basket;
    },
    [client, currentSession, draftProposal, state.status]
  );

  const hasProposalLines = useMemo(
    () => Boolean(draftProposal && draftProposal.line_count > 0),
    [draftProposal]
  );

  return {
    state,
    draftProposal,
    hasProposalLines,
    submitPrompt,
    submitFollowUp,
    setLineQuantity,
    removeLine,
    validateProposal: validateDraftProposal,
    acceptProposal: acceptDraftProposal
  };
}

function updateProposalLineQuantity(
  proposal: MenuProposal,
  skuId: string,
  quantity: number
): MenuProposal {
  return {
    ...proposal,
    courses: proposal.courses.map((course) => ({
      ...course,
      lines: course.lines.map((line) =>
        line.sku_id === skuId
          ? {
              ...line,
              quantity,
              line_total_minor: line.unit_price_minor * quantity
            }
          : line
      )
    }))
  };
}

function removeProposalLineIfCourseRemains(
  proposal: MenuProposal,
  skuId: string
): MenuProposal {
  const targetCourse = proposal.courses.find((course) =>
    course.lines.some((line) => line.sku_id === skuId)
  );
  if (!targetCourse || targetCourse.lines.length <= 1) {
    return proposal;
  }

  return {
    ...proposal,
    courses: proposal.courses
      .map((course) => ({
        ...course,
        lines: course.lines.filter((line) => line.sku_id !== skuId)
      }))
      .filter((course) => course.lines.length > 0)
  };
}

function recalculateProposal(proposal: MenuProposal): MenuProposal {
  const lines = proposal.courses.flatMap((course) => course.lines);
  const totalMinor = lines.reduce((total, line) => total + line.line_total_minor, 0);
  const itemCount = lines.reduce((total, line) => total + line.quantity, 0);

  return {
    ...proposal,
    total_minor: totalMinor,
    item_count: itemCount,
    line_count: lines.length
  };
}

function errorMessageFromSession(session: PlannerSessionResponse): string {
  return (
    session.validation_errors.map((error) => error.message).find(Boolean) ??
    "Tavola could not build that menu from the current catalog."
  );
}
