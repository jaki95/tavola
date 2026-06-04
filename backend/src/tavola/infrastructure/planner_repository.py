from collections.abc import Callable
from uuid import uuid4

from tavola.domain.planner import (
    FollowUpQuestion,
    MenuProposal,
    PlannerSession,
    PlannerSessionId,
    PlannerValidationError,
    ProposalStatus,
)


class InMemoryPlannerSessionRepository:
    def __init__(self, id_generator: Callable[[], str] | None = None) -> None:
        self._id_generator = id_generator or (lambda: uuid4().hex)
        self._sessions_by_id: dict[PlannerSessionId, PlannerSession] = {}

    def create_session(
        self,
        *,
        customer_request: str,
        status: ProposalStatus,
        follow_up_question: FollowUpQuestion | None = None,
        menu_proposal: MenuProposal | None = None,
        validation_errors: tuple[PlannerValidationError, ...] = (),
    ) -> PlannerSession:
        session = PlannerSession(
            planner_session_id=PlannerSessionId(self._id_generator()),
            customer_request=customer_request,
            status=status,
            follow_up_question=follow_up_question,
            menu_proposal=menu_proposal,
            validation_errors=validation_errors,
        )
        self.save_session(session)
        return session

    def get_session(
        self, planner_session_id: PlannerSessionId
    ) -> PlannerSession | None:
        return self._sessions_by_id.get(planner_session_id)

    def save_session(self, session: PlannerSession) -> None:
        self._sessions_by_id[session.planner_session_id] = session
