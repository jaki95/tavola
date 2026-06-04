from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from tavola.api.dependencies import (
    get_basket_repository,
    get_catalog_repository,
    get_menu_planner_agent,
    get_planner_session_repository,
)
from tavola.api.schemas.basket import BasketResponse
from tavola.api.schemas.planner import (
    MealPlanGroupingResponse,
    PlannerAcceptanceResponse,
    PlannerMessageRequest,
    PlannerProposalAcceptanceRequest,
    PlannerProposalValidationRequest,
    PlannerSessionResponse,
)
from tavola.application.basket import (
    BasketApplicationError,
    BasketNotFound,
    BasketRepository,
)
from tavola.application.catalog import CatalogRepository
from tavola.application.planner import (
    AcceptanceMode,
    AcceptMenuProposal,
    AnswerPlannerFollowUp,
    MenuPlannerAgent,
    PlannerApplicationError,
    PlannerInputInvalid,
    PlannerProposalInvalid,
    PlannerSessionNotFound,
    PlannerSessionRepository,
    PlannerSessionStateInvalid,
    RevalidateMenuProposal,
    StartPlannerSession,
)
from tavola.domain.planner import (
    PlannerSession,
    PlannerSessionId,
    PlannerValidationError,
)

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post(
    "/sessions",
    response_model=PlannerSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_planner_session(
    request: PlannerMessageRequest,
    planner_repository: Annotated[
        PlannerSessionRepository, Depends(get_planner_session_repository)
    ],
    agent: Annotated[MenuPlannerAgent, Depends(get_menu_planner_agent)],
    catalog_repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
) -> PlannerSessionResponse:
    try:
        session = StartPlannerSession(
            planner_repository=planner_repository,
            agent=agent,
            catalog_repository=catalog_repository,
        )(message=request.message)
    except PlannerApplicationError as error:
        raise _planner_http_exception(error) from error

    return PlannerSessionResponse.from_domain(session)


@router.get("/sessions/{planner_session_id}", response_model=PlannerSessionResponse)
def get_planner_session(
    planner_session_id: str,
    planner_repository: Annotated[
        PlannerSessionRepository, Depends(get_planner_session_repository)
    ],
) -> PlannerSessionResponse:
    try:
        session = _get_session_or_404(planner_repository, planner_session_id)
    except PlannerApplicationError as error:
        raise _planner_http_exception(error) from error
    return PlannerSessionResponse.from_domain(session)


@router.post(
    "/sessions/{planner_session_id}/follow-up-answer",
    response_model=PlannerSessionResponse,
)
def answer_follow_up(
    planner_session_id: str,
    request: PlannerMessageRequest,
    planner_repository: Annotated[
        PlannerSessionRepository, Depends(get_planner_session_repository)
    ],
    agent: Annotated[MenuPlannerAgent, Depends(get_menu_planner_agent)],
    catalog_repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
) -> PlannerSessionResponse:
    try:
        session = AnswerPlannerFollowUp(
            planner_repository=planner_repository,
            agent=agent,
            catalog_repository=catalog_repository,
        )(planner_session_id=planner_session_id, message=request.message)
    except PlannerApplicationError as error:
        raise _planner_http_exception(error) from error

    return PlannerSessionResponse.from_domain(session)


@router.post(
    "/sessions/{planner_session_id}/proposal/validate",
    response_model=PlannerSessionResponse,
)
def validate_proposal(
    planner_session_id: str,
    request: PlannerProposalValidationRequest,
    planner_repository: Annotated[
        PlannerSessionRepository, Depends(get_planner_session_repository)
    ],
    catalog_repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
) -> PlannerSessionResponse:
    try:
        session = RevalidateMenuProposal(
            planner_repository=planner_repository,
            catalog_repository=catalog_repository,
        )(
            planner_session_id=planner_session_id,
            raw_proposal=request.menu_proposal.to_raw_proposal(),
        )
    except PlannerApplicationError as error:
        raise _planner_http_exception(error) from error
    if session.validation_errors:
        raise _validation_errors_exception(session.validation_errors)

    return PlannerSessionResponse.from_domain(session)


@router.post(
    "/sessions/{planner_session_id}/accept",
    response_model=PlannerAcceptanceResponse,
)
def accept_proposal(
    planner_session_id: str,
    request: PlannerProposalAcceptanceRequest,
    planner_repository: Annotated[
        PlannerSessionRepository, Depends(get_planner_session_repository)
    ],
    basket_repository: Annotated[BasketRepository, Depends(get_basket_repository)],
    catalog_repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
) -> PlannerAcceptanceResponse:
    try:
        result = AcceptMenuProposal(
            planner_repository=planner_repository,
            basket_repository=basket_repository,
            catalog_repository=catalog_repository,
        )(
            planner_session_id=planner_session_id,
            basket_id=request.basket_id,
            mode=AcceptanceMode(request.mode),
            raw_proposal=request.menu_proposal.to_raw_proposal(),
        )
    except (PlannerApplicationError, BasketApplicationError) as error:
        raise _planner_http_exception(error) from error

    return PlannerAcceptanceResponse(
        basket=BasketResponse.from_domain(result.basket),
        meal_plan_grouping=MealPlanGroupingResponse.from_domain(
            result.meal_plan_grouping
        ),
    )


def _get_session_or_404(
    repository: PlannerSessionRepository,
    planner_session_id: str,
) -> PlannerSession:
    try:
        parsed_session_id = PlannerSessionId(planner_session_id)
    except ValueError as error:
        raise PlannerSessionNotFound(planner_session_id) from error
    session = repository.get_session(parsed_session_id)
    if session is None:
        raise PlannerSessionNotFound(planner_session_id)
    return session


def _planner_http_exception(
    error: PlannerApplicationError | BasketApplicationError,
) -> HTTPException:
    if isinstance(error, (PlannerSessionNotFound, BasketNotFound)):
        return HTTPException(status_code=404, detail=error.message)
    if isinstance(error, PlannerProposalInvalid):
        return _validation_errors_exception(error.validation_errors)
    if isinstance(error, PlannerInputInvalid):
        return _validation_exception("message", error.message, error.code)
    if isinstance(error, PlannerSessionStateInvalid):
        return HTTPException(status_code=422, detail=error.message)
    return HTTPException(status_code=422, detail=error.message)


def _validation_errors_exception(
    validation_errors: tuple[PlannerValidationError, ...],
) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail=[
            {
                "loc": ["body", "menu_proposal"],
                "msg": error.message,
                "type": error.code.value,
                "ctx": {
                    "sku_id": error.sku_id,
                    "course": error.course.value if error.course is not None else None,
                },
            }
            for error in validation_errors
        ],
    )


def _validation_exception(
    field: str,
    message: str,
    error_type: str,
) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail=[{"loc": ["body", field], "msg": message, "type": error_type}],
    )
