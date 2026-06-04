import pytest

from tavola.application.planner import PlanMenuFromRequest, ValidateMenuProposal
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.domain.planner import (
    Course,
    CourseProposal,
    FollowUpQuestion,
    MenuProposal,
    PlannerValidationErrorCode,
    ProposalLine,
    ProposalStatus,
)
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.codex_planner import FakeMenuPlannerAgent


def make_sku(
    sku_id: str = "fresh-tagliatelle-250g",
    *,
    name: str = "Fresh Tagliatelle",
    category: CatalogCategory | None = None,
    amount_minor: int = 425,
    is_available: bool = True,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name=name,
        category=category or CatalogCategory("primi", "Primi", 2),
        unit_label="250g",
        price=Money(amount_minor=amount_minor, currency="GBP"),
        short_description="Egg pasta cut fresh each morning.",
        detail_description="Silky ribbons of egg pasta for a quick supper.",
        tags=("pasta", "fresh"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id=sku_id,
        display_order=1,
        is_available=is_available,
    )


def make_proposal(*lines: ProposalLine) -> MenuProposal:
    return MenuProposal(
        title="Weeknight Pasta",
        explanation="A compact pasta proposal.",
        planner_notes=("Catalog identities checked.",),
        party_size=2,
        package_template_id="primo-only",
        courses=(CourseProposal(course=Course.PRIMO, lines=lines),),
    )


def test_validate_menu_proposal_resolves_products_and_recalculates_totals() -> None:
    catalog_repository = StaticCatalogRepository([make_sku(amount_minor=425)])

    result = ValidateMenuProposal(catalog_repository)(
        make_proposal(
            ProposalLine(
                sku_id="fresh-tagliatelle-250g",
                quantity=2,
                rationale="A flexible pasta course.",
            )
        )
    )

    assert result.validation_errors == ()
    assert result.menu_proposal is not None
    assert result.menu_proposal.total.amount_minor == 850
    assert result.menu_proposal.total.currency == "GBP"
    assert result.menu_proposal.item_count == 2
    assert result.menu_proposal.line_count == 1
    assert result.menu_proposal.courses[0].lines[0].sku.name == "Fresh Tagliatelle"
    assert result.menu_proposal.courses[0].lines[0].line_total.amount_minor == 850


def test_validate_menu_proposal_rejects_unknown_sku_with_typed_error() -> None:
    result = ValidateMenuProposal(StaticCatalogRepository([]))(
        make_proposal(
            ProposalLine(
                sku_id="missing-product",
                quantity=1,
                rationale="Codex guessed this product.",
            )
        )
    )

    assert result.menu_proposal is None
    assert result.validation_errors[0].code == PlannerValidationErrorCode.UNKNOWN_SKU
    assert result.validation_errors[0].sku_id == "missing-product"


def test_validate_menu_proposal_enforces_defensive_availability_guard() -> None:
    catalog_repository = StaticCatalogRepository(
        [make_sku(is_available=False)],
    )

    result = ValidateMenuProposal(catalog_repository)(
        make_proposal(
            ProposalLine(
                sku_id="fresh-tagliatelle-250g",
                quantity=1,
                rationale="Unavailable fixture should be guarded.",
            )
        )
    )

    assert result.menu_proposal is None
    assert (
        result.validation_errors[0].code == PlannerValidationErrorCode.UNAVAILABLE_SKU
    )


def test_validate_menu_proposal_rejects_duplicate_sku_lines() -> None:
    result = ValidateMenuProposal(StaticCatalogRepository([make_sku()]))(
        make_proposal(
            ProposalLine(
                sku_id="fresh-tagliatelle-250g",
                quantity=1,
                rationale="First pasta line.",
            ),
            ProposalLine(
                sku_id="fresh-tagliatelle-250g",
                quantity=2,
                rationale="Duplicate pasta line.",
            ),
        )
    )

    assert result.menu_proposal is None
    assert result.validation_errors[0].code == PlannerValidationErrorCode.DUPLICATE_SKU
    assert result.validation_errors[0].sku_id == "fresh-tagliatelle-250g"


@pytest.mark.parametrize("quantity", [0, True])
def test_validate_menu_proposal_reports_invalid_raw_quantities(
    quantity: object,
) -> None:
    result = ValidateMenuProposal(StaticCatalogRepository([make_sku()])).validate_raw(
        {
            "title": "Weeknight Pasta",
            "explanation": "A compact pasta proposal.",
            "planner_notes": ("Catalog identities checked.",),
            "party_size": 2,
            "package_template_id": "primo-only",
            "courses": (
                {
                    "course": "primo",
                    "lines": (
                        {
                            "sku_id": "fresh-tagliatelle-250g",
                            "quantity": quantity,
                            "rationale": "A flexible pasta course.",
                        },
                    ),
                },
            ),
        }
    )

    assert result.menu_proposal is None
    assert (
        result.validation_errors[0].code == PlannerValidationErrorCode.INVALID_QUANTITY
    )


@pytest.mark.parametrize(
    "raw_proposal",
    [
        None,
        {"title": None, "explanation": "A compact pasta proposal."},
        {
            "title": "Weeknight Pasta",
            "explanation": "A compact pasta proposal.",
            "planner_notes": (None,),
        },
        {
            "title": "Weeknight Pasta",
            "explanation": "A compact pasta proposal.",
            "planner_notes": ("Catalog identities checked.",),
            "package_template_id": "primo-only",
            "courses": None,
        },
        {
            "title": "Weeknight Pasta",
            "explanation": "A compact pasta proposal.",
            "planner_notes": ("Catalog identities checked.",),
            "package_template_id": "primo-only",
            "courses": (None,),
        },
        {
            "title": "Weeknight Pasta",
            "explanation": "A compact pasta proposal.",
            "planner_notes": ("Catalog identities checked.",),
            "package_template_id": "primo-only",
            "courses": ({"course": "primo", "lines": (None,)},),
        },
    ],
)
def test_validate_menu_proposal_reports_malformed_raw_shape(
    raw_proposal: object,
) -> None:
    result = ValidateMenuProposal(StaticCatalogRepository([make_sku()])).validate_raw(
        raw_proposal  # type: ignore[arg-type]
    )

    assert result.menu_proposal is None
    assert (
        result.validation_errors[0].code == PlannerValidationErrorCode.INVALID_PROPOSAL
    )


def test_validate_menu_proposal_preserves_course_grouping() -> None:
    primi = make_sku()
    dessert = make_sku(
        "tiramisu-cup-single",
        name="Tiramisu Cup",
        category=CatalogCategory("desserts", "Desserts", 3),
        amount_minor=475,
    )
    proposal = MenuProposal(
        title="Pasta And Dessert",
        explanation="A simple two-course meal.",
        planner_notes=("Template checked.",),
        party_size=2,
        package_template_id="primo-dessert",
        courses=(
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
            CourseProposal(
                course=Course.DESSERT,
                lines=(
                    ProposalLine(
                        sku_id="tiramisu-cup-single",
                        quantity=2,
                        rationale="Individual dessert cups.",
                    ),
                ),
            ),
        ),
    )

    result = ValidateMenuProposal(StaticCatalogRepository([primi, dessert]))(proposal)

    assert result.menu_proposal is not None
    assert [course.course for course in result.menu_proposal.courses] == [
        Course.PRIMO,
        Course.DESSERT,
    ]
    assert result.menu_proposal.total.amount_minor == 1800


def test_plan_menu_from_request_returns_follow_up_from_fake_agent() -> None:
    follow_up = FollowUpQuestion(message="How many people should this serve?")
    planner = PlanMenuFromRequest(
        agent=FakeMenuPlannerAgent.with_follow_up(follow_up),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )

    result = planner(customer_request="Help me plan Sunday lunch")

    assert result.status == ProposalStatus.NEEDS_INPUT
    assert result.follow_up_question == follow_up
    assert result.menu_proposal is None
    assert result.validation_errors == ()


def test_plan_menu_from_request_validates_fake_agent_proposal() -> None:
    planner = PlanMenuFromRequest(
        agent=FakeMenuPlannerAgent.with_proposal(
            {
                "title": "Weeknight Pasta",
                "explanation": "A compact pasta proposal.",
                "planner_notes": ("Catalog identities checked.",),
                "party_size": 2,
                "package_template_id": "primo-only",
                "courses": (
                    {
                        "course": "primo",
                        "lines": (
                            {
                                "sku_id": "fresh-tagliatelle-250g",
                                "quantity": 2,
                                "rationale": "A flexible pasta course.",
                            },
                        ),
                    },
                ),
            }
        ),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    result = planner(customer_request="Dinner for two")

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert result.menu_proposal is not None
    assert result.menu_proposal.total.amount_minor == 850
    assert result.validation_errors == ()


def test_plan_menu_from_request_maps_malformed_fake_agent_output_to_failed_state() -> (
    None
):
    planner = PlanMenuFromRequest(
        agent=FakeMenuPlannerAgent.with_proposal({"title": "Missing details"}),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )

    result = planner(customer_request="Dinner for two")

    assert result.status == ProposalStatus.FAILED
    assert result.menu_proposal is None
    assert (
        result.validation_errors[0].code == PlannerValidationErrorCode.INVALID_PROPOSAL
    )
