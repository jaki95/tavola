import pytest

from tavola.domain.planner import (
    Course,
    CourseProposal,
    FollowUpQuestion,
    MenuProposal,
    PackageTemplate,
    PlannerSession,
    PlannerSessionId,
    PlannerValidationError,
    PlannerValidationErrorCode,
    ProposalLine,
    ProposalStatus,
)


def test_supported_package_templates_are_fixed_menu_structures() -> None:
    assert PackageTemplate.supported_ids() == (
        "antipasto-primo-dessert",
        "antipasto-primo",
        "primo-dessert",
        "primo-only",
        "aperitivo",
    )
    assert PackageTemplate.by_id("antipasto-primo-dessert").courses == (
        Course.ANTIPASTO,
        Course.PRIMO,
        Course.DESSERT,
    )
    assert PackageTemplate.by_id("aperitivo").courses == (Course.APERITIVO,)


def test_unknown_package_template_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported package_template_id"):
        PackageTemplate.by_id("banquet")


def test_proposal_lines_require_stable_sku_quantity_and_rationale() -> None:
    line = ProposalLine(
        sku_id="fresh-tagliatelle-250g",
        quantity=2,
        rationale="A flexible primo for a small supper.",
    )

    assert line.sku_id == "fresh-tagliatelle-250g"
    assert line.quantity == 2


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("sku_id", "Fresh Tagliatelle", "sku_id must be a stable slug"),
        ("quantity", 0, "quantity must be positive"),
        ("quantity", True, "quantity must be an integer"),
        ("rationale", "", "rationale is required"),
    ],
)
def test_proposal_line_rejects_invalid_values(
    field: str,
    value: object,
    expected: str,
) -> None:
    values = {
        "sku_id": "fresh-tagliatelle-250g",
        "quantity": 1,
        "rationale": "A useful product for this course.",
    }
    values[field] = value

    with pytest.raises(ValueError, match=expected):
        ProposalLine(**values)  # type: ignore[arg-type]


def test_menu_proposal_preserves_course_grouping_for_supported_template() -> None:
    proposal = MenuProposal(
        title="Small Dinner",
        explanation="A simple antipasto and pasta supper.",
        planner_notes=("Party size: 2.", "Prices checked by Tavola."),
        party_size=2,
        package_template_id="antipasto-primo",
        courses=(
            CourseProposal(
                course=Course.ANTIPASTO,
                lines=(
                    ProposalLine(
                        sku_id="marinated-nocellara-olives-250g",
                        quantity=1,
                        rationale="Bright opening bite.",
                    ),
                ),
            ),
            CourseProposal(
                course=Course.PRIMO,
                lines=(
                    ProposalLine(
                        sku_id="fresh-tagliatelle-250g",
                        quantity=2,
                        rationale="Main pasta course.",
                    ),
                ),
            ),
        ),
    )

    assert proposal.template.courses == (Course.ANTIPASTO, Course.PRIMO)
    assert proposal.line_count == 2
    assert proposal.item_count == 3


def test_menu_proposal_party_size_is_not_capped_by_basket_line_quantity() -> None:
    proposal = MenuProposal(
        title="Office Lunch",
        explanation="A simple pasta lunch for a larger group.",
        planner_notes=("Party size: 12.",),
        party_size=12,
        package_template_id="primo-only",
        courses=(
            CourseProposal(
                course=Course.PRIMO,
                lines=(
                    ProposalLine(
                        sku_id="beef-ragu-lasagne-serves-2",
                        quantity=6,
                        rationale="Prepared trays work for a larger lunch.",
                    ),
                ),
            ),
        ),
    )

    assert proposal.party_size == 12


def test_menu_proposal_rejects_unsupported_course_for_template() -> None:
    with pytest.raises(ValueError, match="courses must match package template"):
        MenuProposal(
            title="Confused Dinner",
            explanation="Dessert does not belong in this template.",
            planner_notes=("Template checked.",),
            party_size=2,
            package_template_id="primo-only",
            courses=(
                CourseProposal(
                    course=Course.DESSERT,
                    lines=(
                        ProposalLine(
                            sku_id="tiramisu-cup-single",
                            quantity=2,
                            rationale="Dessert line.",
                        ),
                    ),
                ),
            ),
        )


def test_planner_session_can_represent_follow_up_without_product_lines() -> None:
    session = PlannerSession(
        planner_session_id=PlannerSessionId("planner-1"),
        customer_request="Dinner for friends",
        status=ProposalStatus.NEEDS_INPUT,
        follow_up_question=FollowUpQuestion(
            message="How many people should the menu serve?"
        ),
    )

    assert session.menu_proposal is None
    assert session.follow_up_question is not None


def test_planner_session_enforces_status_payload_shape() -> None:
    with pytest.raises(ValueError, match="follow_up_question is required"):
        PlannerSession(
            planner_session_id=PlannerSessionId("planner-1"),
            customer_request="Dinner",
            status=ProposalStatus.NEEDS_INPUT,
        )

    with pytest.raises(ValueError, match="menu_proposal is required"):
        PlannerSession(
            planner_session_id=PlannerSessionId("planner-1"),
            customer_request="Dinner",
            status=ProposalStatus.PROPOSAL_READY,
        )


def test_validation_error_is_typed_and_customer_readable() -> None:
    error = PlannerValidationError(
        code=PlannerValidationErrorCode.UNKNOWN_SKU,
        message="Product is not in the current catalog.",
        sku_id="missing-product",
    )

    assert error.code == PlannerValidationErrorCode.UNKNOWN_SKU
    assert error.sku_id == "missing-product"
