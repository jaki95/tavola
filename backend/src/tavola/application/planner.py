from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from tavola.application.basket import (
    BasketNotFound,
    BasketRepository,
)
from tavola.application.catalog import CatalogRepository
from tavola.domain.basket import Basket, BasketId
from tavola.domain.catalog import Money
from tavola.domain.planner import (
    Course,
    CourseProposal,
    FollowUpQuestion,
    MenuProposal,
    PlannerSession,
    PlannerSessionId,
    PlannerValidationError,
    PlannerValidationErrorCode,
    ProposalLine,
    ProposalStatus,
    ValidatedCourseProposal,
    ValidatedMenuProposal,
    ValidatedProposalLine,
    zero_money,
)


class PlannerSessionRepository(Protocol):
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
        """Create and persist a planner session."""

    def get_session(
        self, planner_session_id: PlannerSessionId
    ) -> PlannerSession | None:
        """Return one planner session, or None when the session is unknown."""

    def save_session(self, session: PlannerSession) -> None:
        """Persist the latest planner session state."""


class PlannerBackgroundRunner(Protocol):
    def try_acquire(self) -> bool:
        """Reserve the one process-local planning slot if it is free."""

    def submit(self, task: Callable[[], None]) -> None:
        """Run a reserved planning task in the background."""

    def release(self) -> None:
        """Release a reserved planning slot when dispatch cannot continue."""


class PlannerAgentErrorCode(StrEnum):
    MALFORMED_OUTPUT = "malformed_output"
    MISSING_TOOL_USE = "missing_tool_use"
    TOOL_FAILURE = "tool_failure"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class PlannerAgentError:
    code: PlannerAgentErrorCode
    message: str

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("message is required")


@dataclass(frozen=True, slots=True)
class MenuPlannerAgentResponse:
    follow_up_question: FollowUpQuestion | None = None
    raw_proposal: dict[str, Any] | None = None
    failure: PlannerAgentError | None = None

    def __post_init__(self) -> None:
        states = (
            self.follow_up_question is not None,
            self.raw_proposal is not None,
            self.failure is not None,
        )
        if sum(states) > 1:
            raise ValueError("planner response cannot include multiple states")


class MenuPlannerAgent(Protocol):
    def plan_menu(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
    ) -> MenuPlannerAgentResponse:
        """Return a follow-up question or raw menu proposal from the planner."""


class AcceptanceMode(StrEnum):
    APPEND = "append"
    REPLACE = "replace"


class PlannerApplicationError(Exception):
    code = "planner_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class PlannerInputInvalid(PlannerApplicationError):
    code = "invalid_input"

    def __init__(self, message: str = "message is required") -> None:
        super().__init__(message)


class PlannerSessionNotFound(PlannerApplicationError):
    code = "planner_session_not_found"

    def __init__(self, planner_session_id: str) -> None:
        self.planner_session_id = planner_session_id
        super().__init__("planner session not found")


class PlannerSessionStateInvalid(PlannerApplicationError):
    code = "planner_session_state_invalid"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PlannerUnavailable(PlannerApplicationError):
    code = "planner_unavailable"


class PlannerBusy(PlannerApplicationError):
    code = "planner_busy"

    def __init__(self) -> None:
        super().__init__(
            "Tavola is already planning a menu. Please wait for it to finish."
        )


class PlannerProposalInvalid(PlannerApplicationError):
    code = "planner_proposal_invalid"

    def __init__(
        self,
        validation_errors: tuple[PlannerValidationError, ...],
    ) -> None:
        self.validation_errors = validation_errors
        super().__init__("menu proposal is not valid")


_REVALIDATED_NOTE = "Revalidated by Tavola."


@dataclass(frozen=True, slots=True)
class MenuProposalValidationResult:
    menu_proposal: ValidatedMenuProposal | None
    validation_errors: tuple[PlannerValidationError, ...]


@dataclass(frozen=True, slots=True)
class MenuProposalEditResult:
    menu_proposal: MenuProposal | None
    validation_errors: tuple[PlannerValidationError, ...]


@dataclass(frozen=True, slots=True)
class MenuPlannerRunResult:
    status: ProposalStatus
    follow_up_question: FollowUpQuestion | None = None
    menu_proposal: ValidatedMenuProposal | None = None
    validation_errors: tuple[PlannerValidationError, ...] = ()
    agent_error: PlannerAgentError | None = None


@dataclass(frozen=True, slots=True)
class MealPlanCourseGrouping:
    course: Course
    line_sku_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MealPlanGrouping:
    title: str
    party_size: int | None
    package_template_id: str
    courses: tuple[MealPlanCourseGrouping, ...]


@dataclass(frozen=True, slots=True)
class AcceptedMenuProposal:
    basket: Basket
    meal_plan_grouping: MealPlanGrouping


class PlanMenuFromRequest:
    """Ask a planner agent for a proposal and validate it through Tavola."""

    def __init__(
        self,
        *,
        agent: MenuPlannerAgent,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._agent = agent
        self._validate_menu_proposal = ValidateMenuProposal(catalog_repository)

    def __call__(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
    ) -> MenuPlannerRunResult:
        if not customer_request.strip():
            return MenuPlannerRunResult(
                status=ProposalStatus.FAILED,
                validation_errors=(
                    PlannerValidationError(
                        code=PlannerValidationErrorCode.INVALID_PROPOSAL,
                        message="customer_request is required",
                    ),
                ),
            )

        response = self._agent.plan_menu(
            customer_request=customer_request,
            follow_up_answers=follow_up_answers,
        )
        if response.failure is not None:
            return MenuPlannerRunResult(
                status=ProposalStatus.FAILED,
                validation_errors=(
                    PlannerValidationError(
                        code=PlannerValidationErrorCode.INVALID_PROPOSAL,
                        message=response.failure.message,
                    ),
                ),
                agent_error=response.failure,
            )
        if response.follow_up_question is not None:
            return MenuPlannerRunResult(
                status=ProposalStatus.NEEDS_INPUT,
                follow_up_question=response.follow_up_question,
            )
        if response.raw_proposal is None:
            return MenuPlannerRunResult(
                status=ProposalStatus.FAILED,
                validation_errors=(
                    PlannerValidationError(
                        code=PlannerValidationErrorCode.INVALID_PROPOSAL,
                        message="planner did not return a menu proposal",
                    ),
                ),
            )

        validation_result = self._validate_menu_proposal.validate_raw(
            response.raw_proposal
        )
        if validation_result.menu_proposal is None:
            return MenuPlannerRunResult(
                status=ProposalStatus.FAILED,
                validation_errors=validation_result.validation_errors,
            )
        return MenuPlannerRunResult(
            status=ProposalStatus.PROPOSAL_READY,
            menu_proposal=validation_result.menu_proposal,
        )


class StartPlannerSession:
    def __init__(
        self,
        *,
        planner_repository: PlannerSessionRepository,
        agent: MenuPlannerAgent,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._planner_repository = planner_repository
        self._plan_menu = PlanMenuFromRequest(
            agent=agent,
            catalog_repository=catalog_repository,
        )

    def __call__(self, *, message: str) -> PlannerSession:
        customer_request = _require_message(message)
        result = self._plan_menu(customer_request=customer_request)
        return self._create_session_from_run(
            customer_request=customer_request,
            follow_up_answers=(),
            result=result,
        )

    def _create_session_from_run(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...],
        result: MenuPlannerRunResult,
    ) -> PlannerSession:
        return self._planner_repository.create_session(
            customer_request=customer_request,
            follow_up_answers=follow_up_answers,
            status=result.status,
            follow_up_question=result.follow_up_question,
            menu_proposal=result.menu_proposal,
            validation_errors=result.validation_errors,
        )


class CreatePlanningSession:
    def __init__(self, *, planner_repository: PlannerSessionRepository) -> None:
        self._planner_repository = planner_repository

    def __call__(self, *, message: str) -> PlannerSession:
        customer_request = _require_message(message)
        return self._planner_repository.create_session(
            customer_request=customer_request,
            status=ProposalStatus.PLANNING,
        )


class SubmitPlannerFollowUp:
    def __init__(self, *, planner_repository: PlannerSessionRepository) -> None:
        self._planner_repository = planner_repository

    def __call__(self, *, planner_session_id: str, message: str) -> PlannerSession:
        answer = _require_message(message)
        session = _get_session_or_raise(
            self._planner_repository,
            planner_session_id,
        )
        if session.status != ProposalStatus.NEEDS_INPUT:
            raise PlannerSessionStateInvalid(
                "follow-up answers are accepted only while input is needed"
            )

        updated = PlannerSession(
            planner_session_id=session.planner_session_id,
            customer_request=session.customer_request,
            follow_up_answers=(*session.follow_up_answers, answer),
            status=ProposalStatus.PLANNING,
        )
        self._planner_repository.save_session(updated)
        return updated


class CompletePlanningSession:
    def __init__(
        self,
        *,
        planner_repository: PlannerSessionRepository,
        agent: MenuPlannerAgent,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._planner_repository = planner_repository
        self._plan_menu = PlanMenuFromRequest(
            agent=agent,
            catalog_repository=catalog_repository,
        )

    def __call__(self, *, planner_session_id: str) -> PlannerSession:
        session = _get_session_or_raise(
            self._planner_repository,
            planner_session_id,
        )
        if session.status != ProposalStatus.PLANNING:
            raise PlannerSessionStateInvalid(
                "planner completion is accepted only while planning"
            )

        try:
            result = self._plan_menu(
                customer_request=session.customer_request,
                follow_up_answers=session.follow_up_answers,
            )
        except Exception:
            result = MenuPlannerRunResult(
                status=ProposalStatus.FAILED,
                validation_errors=(
                    PlannerValidationError(
                        code=PlannerValidationErrorCode.INVALID_PROPOSAL,
                        message="Planner could not complete this request.",
                    ),
                ),
            )

        updated = PlannerSession(
            planner_session_id=session.planner_session_id,
            customer_request=session.customer_request,
            follow_up_answers=session.follow_up_answers,
            status=result.status,
            follow_up_question=result.follow_up_question,
            menu_proposal=result.menu_proposal,
            validation_errors=result.validation_errors,
        )
        self._planner_repository.save_session(updated)
        return updated


class AnswerPlannerFollowUp:
    def __init__(
        self,
        *,
        planner_repository: PlannerSessionRepository,
        agent: MenuPlannerAgent,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._planner_repository = planner_repository
        self._plan_menu = PlanMenuFromRequest(
            agent=agent,
            catalog_repository=catalog_repository,
        )

    def __call__(self, *, planner_session_id: str, message: str) -> PlannerSession:
        answer = _require_message(message)
        session = _get_session_or_raise(
            self._planner_repository,
            planner_session_id,
        )
        if session.status != ProposalStatus.NEEDS_INPUT:
            raise PlannerSessionStateInvalid(
                "follow-up answers are accepted only while input is needed"
            )

        follow_up_answers = (*session.follow_up_answers, answer)
        result = self._plan_menu(
            customer_request=session.customer_request,
            follow_up_answers=follow_up_answers,
        )
        updated = PlannerSession(
            planner_session_id=session.planner_session_id,
            customer_request=session.customer_request,
            follow_up_answers=follow_up_answers,
            status=result.status,
            follow_up_question=result.follow_up_question,
            menu_proposal=result.menu_proposal,
            validation_errors=result.validation_errors,
        )
        self._planner_repository.save_session(updated)
        return updated


class RevalidateMenuProposal:
    def __init__(
        self,
        *,
        planner_repository: PlannerSessionRepository,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._planner_repository = planner_repository
        self._validate_menu_proposal = ValidateMenuProposal(catalog_repository)

    def __call__(
        self,
        *,
        planner_session_id: str,
        raw_proposal: dict[str, Any],
    ) -> PlannerSession:
        session = _get_session_or_raise(
            self._planner_repository,
            planner_session_id,
        )
        if session.status not in (
            ProposalStatus.PROPOSAL_READY,
            ProposalStatus.FAILED,
        ):
            raise PlannerSessionStateInvalid(
                "menu proposal can be revalidated only after a proposal is ready"
            )

        edit_result = _editable_proposal_for_session(
            session,
            raw_proposal,
            append_revalidation_note=True,
        )
        if edit_result.menu_proposal is None:
            validation_result = MenuProposalValidationResult(
                menu_proposal=None,
                validation_errors=edit_result.validation_errors,
            )
        else:
            validation_result = self._validate_menu_proposal(edit_result.menu_proposal)
        if validation_result.menu_proposal is None:
            updated = PlannerSession(
                planner_session_id=session.planner_session_id,
                customer_request=session.customer_request,
                follow_up_answers=session.follow_up_answers,
                status=ProposalStatus.FAILED,
                validation_errors=validation_result.validation_errors,
            )
        else:
            updated = PlannerSession(
                planner_session_id=session.planner_session_id,
                customer_request=session.customer_request,
                follow_up_answers=session.follow_up_answers,
                status=ProposalStatus.PROPOSAL_READY,
                menu_proposal=validation_result.menu_proposal,
            )
        self._planner_repository.save_session(updated)
        return updated


class AcceptMenuProposal:
    def __init__(
        self,
        *,
        planner_repository: PlannerSessionRepository,
        basket_repository: BasketRepository,
        catalog_repository: CatalogRepository,
    ) -> None:
        self._planner_repository = planner_repository
        self._basket_repository = basket_repository
        self._validate_menu_proposal = ValidateMenuProposal(catalog_repository)

    def __call__(
        self,
        *,
        planner_session_id: str,
        basket_id: str,
        mode: AcceptanceMode,
        raw_proposal: dict[str, Any],
    ) -> AcceptedMenuProposal:
        session = _get_session_or_raise(
            self._planner_repository,
            planner_session_id,
        )
        if session.status == ProposalStatus.ACCEPTED:
            raise PlannerSessionStateInvalid("menu proposal has already been accepted")
        if session.status != ProposalStatus.PROPOSAL_READY:
            raise PlannerSessionStateInvalid(
                "menu proposal can be accepted only after it is ready"
            )

        edit_result = _editable_proposal_for_session(
            session,
            raw_proposal,
            append_revalidation_note=False,
        )
        if edit_result.menu_proposal is None:
            validation_result = MenuProposalValidationResult(
                menu_proposal=None,
                validation_errors=edit_result.validation_errors,
            )
        else:
            validation_result = self._validate_menu_proposal(edit_result.menu_proposal)
        if validation_result.menu_proposal is None:
            raise PlannerProposalInvalid(validation_result.validation_errors)
        menu_proposal = validation_result.menu_proposal

        basket = _get_basket_or_raise(self._basket_repository, basket_id)
        line_specs = tuple(
            (line.sku, line.quantity)
            for course in menu_proposal.courses
            for line in course.lines
        )
        try:
            if mode == AcceptanceMode.REPLACE:
                updated_basket = basket.replace_lines(line_specs)
            else:
                updated_basket = basket
                for sku, quantity in line_specs:
                    updated_basket = updated_basket.add_line(sku, quantity=quantity)
        except ValueError as error:
            raise PlannerProposalInvalid(
                (
                    PlannerValidationError(
                        code=PlannerValidationErrorCode.QUANTITY_EXCEEDS_MAX,
                        message=str(error),
                    ),
                )
            ) from error

        self._basket_repository.save_basket(updated_basket)
        accepted = PlannerSession(
            planner_session_id=session.planner_session_id,
            customer_request=session.customer_request,
            follow_up_answers=session.follow_up_answers,
            status=ProposalStatus.ACCEPTED,
            menu_proposal=menu_proposal,
        )
        self._planner_repository.save_session(accepted)
        return AcceptedMenuProposal(
            basket=updated_basket,
            meal_plan_grouping=_meal_plan_grouping(menu_proposal, updated_basket),
        )


class ValidateMenuProposal:
    """Validate proposed products without mutating a basket.

    Duplicate product identities are rejected rather than merged so customer-facing
    course grouping remains unambiguous in the review surface.
    """

    def __init__(self, catalog_repository: CatalogRepository) -> None:
        self._catalog_repository = catalog_repository

    def __call__(self, proposal: MenuProposal) -> MenuProposalValidationResult:
        errors = _duplicate_errors(proposal)
        if errors:
            return MenuProposalValidationResult(
                menu_proposal=None,
                validation_errors=errors,
            )

        validated_courses: list[ValidatedCourseProposal] = []
        total_amount_minor = 0
        item_count = 0
        line_count = 0
        for course in proposal.courses:
            validated_lines: list[ValidatedProposalLine] = []
            for line in course.lines:
                sku = self._catalog_repository.get_sku(line.sku_id)
                if sku is None:
                    errors.append(
                        PlannerValidationError(
                            code=PlannerValidationErrorCode.UNKNOWN_SKU,
                            message="Product is not in the current catalog.",
                            sku_id=line.sku_id,
                            course=course.course,
                        )
                    )
                    continue
                if not sku.is_available:
                    errors.append(
                        PlannerValidationError(
                            code=PlannerValidationErrorCode.UNAVAILABLE_SKU,
                            message="Product is not currently available.",
                            sku_id=line.sku_id,
                            course=course.course,
                        )
                    )
                    continue

                line_total = Money(
                    amount_minor=sku.price.amount_minor * line.quantity,
                    currency=sku.price.currency,
                )
                total_amount_minor += line_total.amount_minor
                item_count += line.quantity
                line_count += 1
                validated_lines.append(
                    ValidatedProposalLine(
                        sku=sku,
                        quantity=line.quantity,
                        rationale=line.rationale,
                        line_total=line_total,
                    )
                )
            validated_courses.append(
                ValidatedCourseProposal(
                    course=course.course,
                    lines=tuple(validated_lines),
                )
            )

        if errors:
            return MenuProposalValidationResult(
                menu_proposal=None,
                validation_errors=tuple(errors),
            )

        total = zero_money()
        if line_count:
            total = Money(amount_minor=total_amount_minor, currency="GBP")
        return MenuProposalValidationResult(
            menu_proposal=ValidatedMenuProposal(
                title=proposal.title,
                explanation=proposal.explanation,
                planner_notes=proposal.planner_notes,
                party_size=proposal.party_size,
                package_template_id=proposal.package_template_id,
                courses=tuple(validated_courses),
                total=total,
                item_count=item_count,
                line_count=line_count,
                warnings=proposal.warnings,
            ),
            validation_errors=(),
        )

    def validate_raw(
        self, raw_proposal: dict[str, Any]
    ) -> MenuProposalValidationResult:
        try:
            proposal = _parse_raw_proposal(raw_proposal)
        except (TypeError, ValueError) as error:
            return MenuProposalValidationResult(
                menu_proposal=None,
                validation_errors=(_validation_error_from_value_error(error),),
            )
        return self(proposal)


def _duplicate_errors(proposal: MenuProposal) -> list[PlannerValidationError]:
    errors: list[PlannerValidationError] = []
    seen_sku_ids: set[str] = set()
    for course in proposal.courses:
        for line in course.lines:
            if line.sku_id in seen_sku_ids:
                errors.append(
                    PlannerValidationError(
                        code=PlannerValidationErrorCode.DUPLICATE_SKU,
                        message="Product appears more than once in the proposal.",
                        sku_id=line.sku_id,
                        course=course.course,
                    )
                )
            seen_sku_ids.add(line.sku_id)
    return errors


def _editable_proposal_for_session(
    session: PlannerSession,
    raw_proposal: dict[str, Any],
    *,
    append_revalidation_note: bool,
) -> MenuProposalEditResult:
    if session.menu_proposal is None:
        return MenuProposalEditResult(
            menu_proposal=None,
            validation_errors=(
                _invalid_proposal_error("current menu proposal is required"),
            ),
        )

    try:
        proposal = _parse_raw_proposal(raw_proposal)
    except (TypeError, ValueError) as error:
        return MenuProposalEditResult(
            menu_proposal=None,
            validation_errors=(_validation_error_from_value_error(error),),
        )

    errors = _edit_errors(session.menu_proposal, proposal)
    if errors:
        return MenuProposalEditResult(menu_proposal=None, validation_errors=errors)
    if append_revalidation_note:
        proposal = _with_revalidation_note(proposal)
    return MenuProposalEditResult(menu_proposal=proposal, validation_errors=())


def _edit_errors(
    current: ValidatedMenuProposal,
    candidate: MenuProposal,
) -> tuple[PlannerValidationError, ...]:
    if candidate.title != current.title:
        return (_invalid_proposal_error("menu proposal title cannot be edited"),)
    if candidate.explanation != current.explanation:
        return (_invalid_proposal_error("menu proposal explanation cannot be edited"),)
    if candidate.party_size != current.party_size:
        return (_invalid_proposal_error("party size cannot be edited"),)
    if candidate.package_template_id != current.package_template_id:
        return (_invalid_proposal_error("package template cannot be edited"),)
    if candidate.warnings != current.warnings:
        return (_invalid_proposal_error("menu proposal warnings cannot be edited"),)
    if _normalized_notes(candidate.planner_notes) != _normalized_notes(
        current.planner_notes
    ):
        return (_invalid_proposal_error("planner notes cannot be edited"),)

    current_line_courses = {
        line.sku.sku_id: course.course
        for course in current.courses
        for line in course.lines
    }
    for course in candidate.courses:
        for line in course.lines:
            current_course = current_line_courses.get(line.sku_id)
            if current_course is None:
                return (
                    _invalid_proposal_error(
                        "customer edits cannot add products to a menu proposal"
                    ),
                )
            if course.course != current_course:
                return (
                    _invalid_proposal_error(
                        "customer edits cannot move products between courses"
                    ),
                )
    return ()


def _normalized_notes(notes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(note for note in notes if note != _REVALIDATED_NOTE)


def _invalid_proposal_error(message: str) -> PlannerValidationError:
    return PlannerValidationError(
        code=PlannerValidationErrorCode.INVALID_PROPOSAL,
        message=message,
    )


def _require_message(message: str) -> str:
    stripped = message.strip()
    if not stripped:
        raise PlannerInputInvalid()
    return stripped


def _get_session_or_raise(
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


def _get_basket_or_raise(
    repository: BasketRepository,
    basket_id: str,
) -> Basket:
    try:
        parsed_basket_id = BasketId(basket_id)
    except ValueError as error:
        raise BasketNotFound(basket_id) from error

    basket = repository.get_basket(parsed_basket_id)
    if basket is None:
        raise BasketNotFound(basket_id)
    return basket


def _with_revalidation_note(proposal: MenuProposal) -> MenuProposal:
    if _REVALIDATED_NOTE in proposal.planner_notes:
        return proposal
    return MenuProposal(
        title=proposal.title,
        explanation=proposal.explanation,
        planner_notes=(*proposal.planner_notes, _REVALIDATED_NOTE),
        party_size=proposal.party_size,
        package_template_id=proposal.package_template_id,
        courses=proposal.courses,
        warnings=proposal.warnings,
    )


def _meal_plan_grouping(
    menu_proposal: ValidatedMenuProposal,
    basket: Basket,
) -> MealPlanGrouping:
    basket_sku_ids = {line.sku.sku_id for line in basket.lines}
    courses = tuple(
        MealPlanCourseGrouping(
            course=course.course,
            line_sku_ids=tuple(
                line.sku.sku_id
                for line in course.lines
                if line.sku.sku_id in basket_sku_ids
            ),
        )
        for course in menu_proposal.courses
    )
    non_empty_courses = tuple(course for course in courses if course.line_sku_ids)
    return MealPlanGrouping(
        title=menu_proposal.title,
        party_size=menu_proposal.party_size,
        package_template_id=menu_proposal.package_template_id,
        courses=non_empty_courses,
    )


def _parse_raw_proposal(raw: dict[str, Any]) -> MenuProposal:
    if not isinstance(raw, Mapping):
        raise ValueError("proposal must be an object")

    return MenuProposal(
        title=_required_text(raw, "title"),
        explanation=_required_text(raw, "explanation"),
        planner_notes=tuple(_text_sequence(raw.get("planner_notes"), "planner_notes")),
        party_size=raw.get("party_size"),
        package_template_id=_required_text(raw, "package_template_id"),
        courses=tuple(
            _parse_raw_course(raw_course) for raw_course in _items(raw, "courses")
        ),
        warnings=tuple(_text_sequence(raw.get("warnings", ()), "warnings")),
    )


def _parse_raw_course(raw_course: Any) -> CourseProposal:
    if not isinstance(raw_course, Mapping):
        raise ValueError("course must be an object")
    return CourseProposal(
        course=Course(_required_text(raw_course, "course")),
        lines=tuple(
            _parse_raw_line(raw_line) for raw_line in _items(raw_course, "lines")
        ),
    )


def _parse_raw_line(raw_line: Any) -> ProposalLine:
    if not isinstance(raw_line, Mapping):
        raise ValueError("line must be an object")
    return ProposalLine(
        sku_id=_required_text(raw_line, "sku_id"),
        quantity=raw_line.get("quantity"),
        rationale=_required_text(raw_line, "rationale"),
    )


def _required_text(raw: Mapping[str, Any], field_name: str) -> str:
    value = raw.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be text")
    return value


def _text_sequence(value: Any, field_name: str) -> tuple[str, ...]:
    if not _is_sequence(value):
        raise ValueError(f"{field_name} must be a sequence")
    notes = tuple(value)
    if any(type(note) is not str for note in notes):
        raise ValueError(f"{field_name} must contain text")
    return notes


def _items(raw: Mapping[str, Any], field_name: str) -> tuple[Any, ...]:
    value = raw.get(field_name)
    if not _is_sequence(value):
        raise ValueError(f"{field_name} must be a sequence")
    return tuple(value)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Iterable) and not isinstance(value, str | bytes)


def _validation_error_from_value_error(error: Exception) -> PlannerValidationError:
    message = str(error)
    code = PlannerValidationErrorCode.INVALID_PROPOSAL
    if "quantity" in message:
        code = PlannerValidationErrorCode.INVALID_QUANTITY
    if "cannot exceed" in message:
        code = PlannerValidationErrorCode.QUANTITY_EXCEEDS_MAX
    if message == "courses must match package template" or "not a valid" in message:
        code = PlannerValidationErrorCode.UNSUPPORTED_COURSE
    return PlannerValidationError(code=code, message=message)
