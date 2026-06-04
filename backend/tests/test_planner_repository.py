from tavola.domain.planner import (
    FollowUpQuestion,
    PlannerSession,
    PlannerSessionId,
    ProposalStatus,
)
from tavola.infrastructure.planner_repository import InMemoryPlannerSessionRepository


def make_session(session_id: str = "planner-1") -> PlannerSession:
    return PlannerSession(
        planner_session_id=PlannerSessionId(session_id),
        customer_request="Dinner for four",
        status=ProposalStatus.NEEDS_INPUT,
        follow_up_question=FollowUpQuestion(
            message="How many people should the menu serve?"
        ),
    )


def test_create_session_assigns_deterministic_id_and_persists() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")

    session = repository.create_session(
        customer_request="Dinner for friends",
        status=ProposalStatus.NEEDS_INPUT,
        follow_up_question=FollowUpQuestion(
            message="How many people should the menu serve?"
        ),
    )

    assert session.planner_session_id == PlannerSessionId("planner-1")
    assert repository.get_session(PlannerSessionId("planner-1")) == session


def test_create_session_can_persist_planning_state() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")

    session = repository.create_session(
        customer_request="Dinner for friends",
        status=ProposalStatus.PLANNING,
    )

    assert session.status == ProposalStatus.PLANNING
    assert session.follow_up_question is None
    assert session.menu_proposal is None
    assert repository.get_session(PlannerSessionId("planner-1")) == session


def test_save_session_updates_existing_session_state() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    repository.create_session(
        customer_request="Dinner for friends",
        status=ProposalStatus.NEEDS_INPUT,
        follow_up_question=FollowUpQuestion(
            message="How many people should the menu serve?"
        ),
    )
    updated = make_session("planner-1")

    repository.save_session(updated)

    assert repository.get_session(PlannerSessionId("planner-1")) == updated


def test_missing_session_lookup_returns_none() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")

    assert repository.get_session(PlannerSessionId("missing-session")) is None
