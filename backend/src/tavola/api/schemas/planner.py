from typing import Annotated, Literal

from pydantic import BaseModel, StrictInt, StringConstraints

from tavola.api.schemas.basket import BasketResponse
from tavola.application.planner import MealPlanGrouping
from tavola.config.settings import PlannerRuntimeStatus
from tavola.domain.planner import (
    Course,
    PlannerSession,
    PlannerValidationError,
    ValidatedMenuProposal,
    ValidatedProposalLine,
)

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class PlannerMessageRequest(BaseModel):
    message: NonBlankString


class PlannerRuntimeStatusResponse(BaseModel):
    enabled: bool
    mode: Literal["real_codex", "disabled"]
    message: str

    @classmethod
    def from_settings(
        cls, status: PlannerRuntimeStatus
    ) -> "PlannerRuntimeStatusResponse":
        return cls(
            enabled=status.enabled,
            mode=status.mode,
            message=status.message,
        )


class PlannerNoteRequest(BaseModel):
    note_type: NonBlankString = "evidence"
    source: NonBlankString = "tavola"
    message: NonBlankString


class PlannerProposalLineRequest(BaseModel):
    sku_id: NonBlankString
    quantity: StrictInt
    rationale: NonBlankString


class PlannerCourseRequest(BaseModel):
    course: Course
    lines: list[PlannerProposalLineRequest]


class PlannerMenuProposalRequest(BaseModel):
    title: NonBlankString
    explanation: NonBlankString
    planner_notes: list[PlannerNoteRequest]
    party_size: StrictInt | None = None
    package_template_id: NonBlankString
    courses: list[PlannerCourseRequest]
    warnings: list[NonBlankString] = []

    def to_raw_proposal(self) -> dict[str, object]:
        return {
            "title": self.title,
            "explanation": self.explanation,
            "planner_notes": tuple(note.message for note in self.planner_notes),
            "party_size": self.party_size,
            "package_template_id": self.package_template_id,
            "courses": tuple(
                {
                    "course": course.course.value,
                    "lines": tuple(
                        {
                            "sku_id": line.sku_id,
                            "quantity": line.quantity,
                            "rationale": line.rationale,
                        }
                        for line in course.lines
                    ),
                }
                for course in self.courses
            ),
            "warnings": tuple(self.warnings),
        }


class PlannerProposalValidationRequest(BaseModel):
    menu_proposal: PlannerMenuProposalRequest


class PlannerProposalAcceptanceRequest(BaseModel):
    basket_id: NonBlankString
    mode: Literal["append", "replace"]
    menu_proposal: PlannerMenuProposalRequest


class PlannerNoteResponse(BaseModel):
    note_type: str
    source: str
    message: str

    @classmethod
    def from_message(cls, message: str) -> "PlannerNoteResponse":
        return cls(note_type="evidence", source="tavola", message=message)


class PlannerProposalLineResponse(BaseModel):
    sku_id: str
    name: str
    category_id: str
    category_label: str
    unit_label: str
    quantity: int
    unit_price_minor: int
    line_total_minor: int
    currency: str
    image_id: str
    rationale: str

    @classmethod
    def from_domain(cls, line: ValidatedProposalLine) -> "PlannerProposalLineResponse":
        return cls(
            sku_id=line.sku.sku_id,
            name=line.sku.name,
            category_id=line.sku.category.category_id,
            category_label=line.sku.category.label,
            unit_label=line.sku.unit_label,
            quantity=line.quantity,
            unit_price_minor=line.sku.price.amount_minor,
            line_total_minor=line.line_total.amount_minor,
            currency=line.sku.price.currency,
            image_id=line.sku.image_id,
            rationale=line.rationale,
        )


class PlannerCourseResponse(BaseModel):
    course: str
    course_label: str
    lines: list[PlannerProposalLineResponse]


class PlannerMenuProposalResponse(BaseModel):
    title: str
    explanation: str
    planner_notes: list[PlannerNoteResponse]
    party_size: int | None
    package_template_id: str
    courses: list[PlannerCourseResponse]
    total_minor: int
    currency: str
    item_count: int
    line_count: int
    warnings: list[str]

    @classmethod
    def from_domain(
        cls, proposal: ValidatedMenuProposal
    ) -> "PlannerMenuProposalResponse":
        return cls(
            title=proposal.title,
            explanation=proposal.explanation,
            planner_notes=[
                PlannerNoteResponse.from_message(note)
                for note in proposal.planner_notes
            ],
            party_size=proposal.party_size,
            package_template_id=proposal.package_template_id,
            courses=[
                PlannerCourseResponse(
                    course=course.course.value,
                    course_label=course.course.label,
                    lines=[
                        PlannerProposalLineResponse.from_domain(line)
                        for line in course.lines
                    ],
                )
                for course in proposal.courses
            ],
            total_minor=proposal.total.amount_minor,
            currency=proposal.total.currency,
            item_count=proposal.item_count,
            line_count=proposal.line_count,
            warnings=list(proposal.warnings),
        )


class PlannerValidationErrorResponse(BaseModel):
    code: str
    message: str
    sku_id: str | None
    course: str | None

    @classmethod
    def from_domain(
        cls, error: PlannerValidationError
    ) -> "PlannerValidationErrorResponse":
        return cls(
            code=error.code.value,
            message=error.message,
            sku_id=error.sku_id,
            course=error.course.value if error.course is not None else None,
        )


class PlannerSessionResponse(BaseModel):
    planner_session_id: str
    status: str
    customer_request: str
    follow_up_answers: list[str]
    follow_up_question: str | None
    menu_proposal: PlannerMenuProposalResponse | None
    validation_errors: list[PlannerValidationErrorResponse]

    @classmethod
    def from_domain(cls, session: PlannerSession) -> "PlannerSessionResponse":
        return cls(
            planner_session_id=session.planner_session_id.value,
            status=session.status.value,
            customer_request=session.customer_request,
            follow_up_answers=list(session.follow_up_answers),
            follow_up_question=(
                session.follow_up_question.message
                if session.follow_up_question is not None
                else None
            ),
            menu_proposal=(
                PlannerMenuProposalResponse.from_domain(session.menu_proposal)
                if session.menu_proposal is not None
                else None
            ),
            validation_errors=[
                PlannerValidationErrorResponse.from_domain(error)
                for error in session.validation_errors
            ],
        )


class MealPlanCourseGroupingResponse(BaseModel):
    course: str
    course_label: str
    line_sku_ids: list[str]


class MealPlanGroupingResponse(BaseModel):
    title: str
    party_size: int | None
    package_template_id: str
    courses: list[MealPlanCourseGroupingResponse]

    @classmethod
    def from_domain(cls, grouping: MealPlanGrouping) -> "MealPlanGroupingResponse":
        return cls(
            title=grouping.title,
            party_size=grouping.party_size,
            package_template_id=grouping.package_template_id,
            courses=[
                MealPlanCourseGroupingResponse(
                    course=course.course.value,
                    course_label=course.course.label,
                    line_sku_ids=list(course.line_sku_ids),
                )
                for course in grouping.courses
            ],
        )


class PlannerAcceptanceResponse(BaseModel):
    basket: BasketResponse
    meal_plan_grouping: MealPlanGroupingResponse
