from collections.abc import Callable
from threading import RLock
from uuid import uuid4

from tavola.domain.planner import (
    FollowUpQuestion,
    PlannerSession,
    PlannerSessionId,
    PlannerValidationError,
    ProposalStatus,
    ValidatedMenuProposal,
)


class InMemoryPlannerSessionRepository:
    def __init__(self, id_generator: Callable[[], str] | None = None) -> None:
        self._id_generator = id_generator or (lambda: uuid4().hex)
        self._sessions_by_id: dict[PlannerSessionId, PlannerSession] = {}
        self._lock = RLock()

    def create_session(
        self,
        *,
        customer_request: str,
        status: ProposalStatus,
        follow_up_answers: tuple[str, ...] = (),
        follow_up_question: FollowUpQuestion | None = None,
        menu_proposal: ValidatedMenuProposal | None = None,
        validation_errors: tuple[PlannerValidationError, ...] = (),
    ) -> PlannerSession:
        with self._lock:
            session = PlannerSession(
                planner_session_id=PlannerSessionId(self._id_generator()),
                customer_request=customer_request,
                follow_up_answers=follow_up_answers,
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
        with self._lock:
            return self._sessions_by_id.get(planner_session_id)

    def save_session(self, session: PlannerSession) -> None:
        with self._lock:
            self._sessions_by_id[session.planner_session_id] = session
