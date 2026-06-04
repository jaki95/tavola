from dataclasses import dataclass
from typing import Any, Protocol

from tavola.application.catalog import CatalogRepository
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
        follow_up_question: FollowUpQuestion | None = None,
        menu_proposal: MenuProposal | None = None,
        validation_errors: tuple[PlannerValidationError, ...] = (),
    ) -> PlannerSession:
        """Create and persist a planner session."""

    def get_session(
        self, planner_session_id: PlannerSessionId
    ) -> PlannerSession | None:
        """Return one planner session, or None when the session is unknown."""

    def save_session(self, session: PlannerSession) -> None:
        """Persist the latest planner session state."""


@dataclass(frozen=True, slots=True)
class MenuProposalValidationResult:
    menu_proposal: ValidatedMenuProposal | None
    validation_errors: tuple[PlannerValidationError, ...]


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
        except ValueError as error:
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


def _parse_raw_proposal(raw: dict[str, Any]) -> MenuProposal:
    return MenuProposal(
        title=str(raw.get("title", "")),
        explanation=str(raw.get("explanation", "")),
        planner_notes=tuple(raw.get("planner_notes", ())),
        party_size=raw.get("party_size"),
        package_template_id=str(raw.get("package_template_id", "")),
        courses=tuple(
            CourseProposal(
                course=Course(str(raw_course.get("course", ""))),
                lines=tuple(
                    ProposalLine(
                        sku_id=str(raw_line.get("sku_id", "")),
                        quantity=raw_line.get("quantity"),
                        rationale=str(raw_line.get("rationale", "")),
                    )
                    for raw_line in raw_course.get("lines", ())
                ),
            )
            for raw_course in raw.get("courses", ())
        ),
    )


def _validation_error_from_value_error(error: ValueError) -> PlannerValidationError:
    message = str(error)
    code = PlannerValidationErrorCode.INVALID_PROPOSAL
    if "quantity" in message:
        code = PlannerValidationErrorCode.INVALID_QUANTITY
    if "cannot exceed" in message:
        code = PlannerValidationErrorCode.QUANTITY_EXCEEDS_MAX
    if "course" in message or "not a valid" in message:
        code = PlannerValidationErrorCode.UNSUPPORTED_COURSE
    return PlannerValidationError(code=code, message=message)
