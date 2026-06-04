import re
from dataclasses import dataclass
from enum import StrEnum

from tavola.domain.basket import MAX_BASKET_LINE_QUANTITY
from tavola.domain.catalog import SUPPORTED_CURRENCY, CatalogSku, Money

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_MAX_RATIONALE_WORDS = 30


class Course(StrEnum):
    ANTIPASTO = "antipasto"
    PRIMO = "primo"
    DESSERT = "dessert"
    APERITIVO = "aperitivo"

    @property
    def label(self) -> str:
        return {
            Course.ANTIPASTO: "Antipasto",
            Course.PRIMO: "Primo",
            Course.DESSERT: "Dessert",
            Course.APERITIVO: "Aperitivo",
        }[self]


class ProposalStatus(StrEnum):
    NEEDS_INPUT = "needs_input"
    PROPOSAL_READY = "proposal_ready"
    ACCEPTED = "accepted"
    FAILED = "failed"


class PlannerValidationErrorCode(StrEnum):
    UNKNOWN_SKU = "unknown_sku"
    UNAVAILABLE_SKU = "unavailable_sku"
    INVALID_QUANTITY = "invalid_quantity"
    QUANTITY_EXCEEDS_MAX = "quantity_exceeds_max"
    DUPLICATE_SKU = "duplicate_sku"
    UNSUPPORTED_COURSE = "unsupported_course"
    INVALID_PROPOSAL = "invalid_proposal"


@dataclass(frozen=True, slots=True)
class PackageTemplate:
    template_id: str
    label: str
    courses: tuple[Course, ...]

    @classmethod
    def by_id(cls, template_id: str) -> "PackageTemplate":
        try:
            return _PACKAGE_TEMPLATES[template_id]
        except KeyError as error:
            raise ValueError(
                f"unsupported package_template_id: {template_id}"
            ) from error

    @classmethod
    def supported_ids(cls) -> tuple[str, ...]:
        return tuple(_PACKAGE_TEMPLATES)


_PACKAGE_TEMPLATES = {
    "antipasto-primo-dessert": PackageTemplate(
        template_id="antipasto-primo-dessert",
        label="Antipasto + Primo + Dessert",
        courses=(Course.ANTIPASTO, Course.PRIMO, Course.DESSERT),
    ),
    "antipasto-primo": PackageTemplate(
        template_id="antipasto-primo",
        label="Antipasto + Primo",
        courses=(Course.ANTIPASTO, Course.PRIMO),
    ),
    "primo-dessert": PackageTemplate(
        template_id="primo-dessert",
        label="Primo + Dessert",
        courses=(Course.PRIMO, Course.DESSERT),
    ),
    "primo-only": PackageTemplate(
        template_id="primo-only",
        label="Primo only",
        courses=(Course.PRIMO,),
    ),
    "aperitivo": PackageTemplate(
        template_id="aperitivo",
        label="Aperitivo",
        courses=(Course.APERITIVO,),
    ),
}


@dataclass(frozen=True, slots=True)
class PlannerSessionId:
    value: str

    def __post_init__(self) -> None:
        _require_text(self.value, "planner_session_id")


@dataclass(frozen=True, slots=True)
class ProposalLine:
    sku_id: str
    quantity: int
    rationale: str

    def __post_init__(self) -> None:
        _require_slug(self.sku_id, "sku_id")
        _validate_quantity(self.quantity)
        _require_text(self.rationale, "rationale")
        if len(self.rationale.split()) > _MAX_RATIONALE_WORDS:
            raise ValueError("rationale must be concise")


@dataclass(frozen=True, slots=True)
class CourseProposal:
    course: Course
    lines: tuple[ProposalLine, ...]

    def __post_init__(self) -> None:
        if not self.lines:
            raise ValueError("course proposal requires at least one line")


@dataclass(frozen=True, slots=True)
class MenuProposal:
    title: str
    explanation: str
    planner_notes: tuple[str, ...]
    party_size: int | None
    package_template_id: str
    courses: tuple[CourseProposal, ...]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.title, "title")
        _require_text(self.explanation, "explanation")
        if not self.planner_notes:
            raise ValueError("planner_notes are required")
        for note in self.planner_notes:
            _require_text(note, "planner_note")
        if self.party_size is not None:
            _validate_positive_integer(self.party_size, field_name="party_size")
        if not self.courses:
            raise ValueError("menu proposal requires at least one course")

        template = PackageTemplate.by_id(self.package_template_id)
        if tuple(course.course for course in self.courses) != template.courses:
            raise ValueError("courses must match package template")

    @property
    def template(self) -> PackageTemplate:
        return PackageTemplate.by_id(self.package_template_id)

    @property
    def line_count(self) -> int:
        return sum(len(course.lines) for course in self.courses)

    @property
    def item_count(self) -> int:
        return sum(line.quantity for course in self.courses for line in course.lines)


@dataclass(frozen=True, slots=True)
class FollowUpQuestion:
    message: str

    def __post_init__(self) -> None:
        _require_text(self.message, "message")


@dataclass(frozen=True, slots=True)
class PlannerValidationError:
    code: PlannerValidationErrorCode
    message: str
    sku_id: str | None = None
    course: Course | None = None

    def __post_init__(self) -> None:
        _require_text(self.message, "message")


@dataclass(frozen=True, slots=True)
class PlannerSession:
    planner_session_id: PlannerSessionId
    customer_request: str
    status: ProposalStatus
    follow_up_question: FollowUpQuestion | None = None
    menu_proposal: MenuProposal | None = None
    validation_errors: tuple[PlannerValidationError, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.customer_request, "customer_request")
        if self.status == ProposalStatus.NEEDS_INPUT:
            if self.follow_up_question is None:
                raise ValueError("follow_up_question is required")
            if self.menu_proposal is not None:
                raise ValueError("needs_input sessions cannot include a menu proposal")
        if self.status in (ProposalStatus.PROPOSAL_READY, ProposalStatus.ACCEPTED):
            if self.menu_proposal is None:
                raise ValueError("menu_proposal is required")
            if self.follow_up_question is not None:
                raise ValueError(
                    "proposal sessions cannot include a follow-up question"
                )
        if self.status == ProposalStatus.FAILED and not self.validation_errors:
            raise ValueError("failed sessions require validation_errors")


@dataclass(frozen=True, slots=True)
class ValidatedProposalLine:
    sku: CatalogSku
    quantity: int
    rationale: str
    line_total: Money


@dataclass(frozen=True, slots=True)
class ValidatedCourseProposal:
    course: Course
    lines: tuple[ValidatedProposalLine, ...]


@dataclass(frozen=True, slots=True)
class ValidatedMenuProposal:
    title: str
    explanation: str
    planner_notes: tuple[str, ...]
    party_size: int | None
    package_template_id: str
    courses: tuple[ValidatedCourseProposal, ...]
    total: Money
    item_count: int
    line_count: int
    warnings: tuple[str, ...] = ()


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _require_slug(value: str, field_name: str) -> None:
    _require_text(value, field_name)
    if not _SLUG_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable slug")


def _validate_quantity(quantity: int, *, field_name: str = "quantity") -> None:
    _validate_positive_integer(quantity, field_name=field_name)
    if quantity > MAX_BASKET_LINE_QUANTITY:
        raise ValueError(f"{field_name} cannot exceed {MAX_BASKET_LINE_QUANTITY}")


def _validate_positive_integer(quantity: int, *, field_name: str) -> None:
    if type(quantity) is not int:
        raise ValueError(f"{field_name} must be an integer")
    if quantity <= 0:
        raise ValueError(f"{field_name} must be positive")


def zero_money() -> Money:
    return Money(amount_minor=0, currency=SUPPORTED_CURRENCY)
