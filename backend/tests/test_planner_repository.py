from tavola.domain.planner import (
    FollowUpQuestion,
    PlannerSession,
    PlannerSessionId,
    PlanningUpdate,
    PlanningUpdateStage,
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


def test_append_planning_update_preserves_session_fields_and_order() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    session = repository.create_session(
        customer_request="Dinner for friends",
        status=ProposalStatus.NEEDS_INPUT,
        follow_up_answers=("Four people.",),
        follow_up_question=FollowUpQuestion(message="Any dietary preferences?"),
    )
    first = PlanningUpdate(
        stage=PlanningUpdateStage.QUEUED,
        message="We have added your request to the planning queue.",
    )
    second = PlanningUpdate(
        stage=PlanningUpdateStage.STARTED,
        message="We have started planning your menu.",
    )

    repository.append_planning_update(session.planner_session_id, first)
    updated = repository.append_planning_update(session.planner_session_id, second)

    assert updated == PlannerSession(
        planner_session_id=PlannerSessionId("planner-1"),
        customer_request="Dinner for friends",
        follow_up_answers=("Four people.",),
        status=ProposalStatus.NEEDS_INPUT,
        follow_up_question=FollowUpQuestion(message="Any dietary preferences?"),
        planning_updates=(first, second),
    )
    assert repository.get_session(session.planner_session_id) == updated


def test_append_planning_update_returns_none_for_missing_session() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    update = PlanningUpdate(
        stage=PlanningUpdateStage.QUEUED,
        message="We have added your request to the planning queue.",
    )

    result = repository.append_planning_update(
        PlannerSessionId("missing-session"),
        update,
    )

    assert result is None
