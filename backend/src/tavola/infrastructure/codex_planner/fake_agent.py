from dataclasses import dataclass
from typing import Any

from tavola.application.planner import (
    MenuPlannerAgentResponse,
    PlannerAgentError,
    PlannerAgentErrorCode,
)
from tavola.domain.planner import FollowUpQuestion


@dataclass(frozen=True, slots=True)
class FakeMenuPlannerAgent:
    response: MenuPlannerAgentResponse

    @classmethod
    def with_follow_up(cls, question: FollowUpQuestion) -> "FakeMenuPlannerAgent":
        return cls(MenuPlannerAgentResponse(follow_up_question=question))

    @classmethod
    def with_proposal(cls, raw_proposal: dict[str, Any]) -> "FakeMenuPlannerAgent":
        return cls(MenuPlannerAgentResponse(raw_proposal=raw_proposal))

    @classmethod
    def with_failure(
        cls, code: PlannerAgentErrorCode, message: str
    ) -> "FakeMenuPlannerAgent":
        return cls(
            MenuPlannerAgentResponse(
                failure=PlannerAgentError(code=code, message=message)
            )
        )

    def plan_menu(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
    ) -> MenuPlannerAgentResponse:
        return self.response
