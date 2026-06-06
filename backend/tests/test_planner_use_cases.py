import pytest

from tavola.application.planner import (
    AcceptanceMode,
    AcceptMenuProposal,
    AnswerPlannerFollowUp,
    CompletePlanningSession,
    CreatePlanningSession,
    MenuPlannerAgentResponse,
    PlanMenuFromRequest,
    PlannerInputInvalid,
    PlannerProposalInvalid,
    PlannerSessionNotFound,
    PlannerSessionStateInvalid,
    RevalidateMenuProposal,
    StartPlannerSession,
    SubmitPlannerFollowUp,
    ValidateMenuProposal,
)
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
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.codex_planner import FakeMenuPlannerAgent
from tavola.infrastructure.planner_repository import InMemoryPlannerSessionRepository


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


def make_drinks_sku(
    sku_id: str = "limonata-sparkling-330ml",
    *,
    amount_minor: int = 600,
) -> CatalogSku:
    return make_sku(
        sku_id,
        name="Homemade Limonata",
        category=CatalogCategory("drinks", "Drinks", 4),
        amount_minor=amount_minor,
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


def raw_proposal(
    *,
    sku_id: str = "fresh-tagliatelle-250g",
    quantity: int = 2,
    rationale: str = "A flexible pasta course.",
) -> dict[str, object]:
    return {
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
                        "sku_id": sku_id,
                        "quantity": quantity,
                        "rationale": rationale,
                    },
                ),
            },
        ),
    }


class RepairingPlannerAgent:
    def __init__(
        self,
        *,
        first: dict[str, object],
        repaired: dict[str, object],
    ) -> None:
        self._first = first
        self._repaired = repaired
        self.repair_requests: list[dict[str, object]] = []

    def plan_menu(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
    ) -> MenuPlannerAgentResponse:
        del customer_request, follow_up_answers
        return MenuPlannerAgentResponse(raw_proposal=self._first)

    def repair_menu(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
        raw_proposal: dict[str, object],
        validation_errors: tuple[object, ...],
    ) -> MenuPlannerAgentResponse:
        self.repair_requests.append(
            {
                "customer_request": customer_request,
                "follow_up_answers": follow_up_answers,
                "raw_proposal": raw_proposal,
                "validation_errors": validation_errors,
            }
        )
        return MenuPlannerAgentResponse(raw_proposal=self._repaired)


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


def test_validate_menu_proposal_prices_appended_drinks_course() -> None:
    pasta = make_sku(amount_minor=425)
    drinks = make_drinks_sku(amount_minor=600)
    proposal = MenuProposal(
        title="Pasta With Drinks",
        explanation="A compact pasta proposal with drinks.",
        planner_notes=("Catalog identities checked.",),
        party_size=2,
        package_template_id="primo-only",
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
                course=Course.DRINKS,
                lines=(
                    ProposalLine(
                        sku_id="limonata-sparkling-330ml",
                        quantity=1,
                        rationale="Bright drink pairing.",
                    ),
                ),
            ),
        ),
    )

    result = ValidateMenuProposal(StaticCatalogRepository([pasta, drinks]))(proposal)

    assert result.validation_errors == ()
    assert result.menu_proposal is not None
    assert [course.course for course in result.menu_proposal.courses] == [
        Course.PRIMO,
        Course.DRINKS,
    ]
    assert result.menu_proposal.total.amount_minor == 1450
    assert result.menu_proposal.item_count == 3
    assert result.menu_proposal.line_count == 2
    assert result.menu_proposal.courses[1].lines[0].line_total.amount_minor == 600


def test_validate_menu_proposal_rejects_drink_product_in_required_course() -> None:
    drinks = make_drinks_sku()
    proposal = MenuProposal(
        title="Aperitivo",
        explanation="A compact aperitivo proposal.",
        planner_notes=("Catalog identities checked.",),
        party_size=2,
        package_template_id="aperitivo",
        courses=(
            CourseProposal(
                course=Course.APERITIVO,
                lines=(
                    ProposalLine(
                        sku_id="limonata-sparkling-330ml",
                        quantity=1,
                        rationale="Drink should be separate from food.",
                    ),
                ),
            ),
        ),
    )

    result = ValidateMenuProposal(StaticCatalogRepository([drinks]))(proposal)

    assert result.menu_proposal is None
    assert (
        result.validation_errors[0].code == PlannerValidationErrorCode.INVALID_PROPOSAL
    )
    assert result.validation_errors[0].sku_id == "limonata-sparkling-330ml"
    assert result.validation_errors[0].course == Course.APERITIVO


def test_validate_menu_proposal_rejects_food_product_in_drinks_course() -> None:
    pasta = make_sku()
    gnocchi = make_sku("potato-gnocchi-500g", name="Potato Gnocchi")
    proposal = MenuProposal(
        title="Pasta With Drinks",
        explanation="A compact pasta proposal with drinks.",
        planner_notes=("Catalog identities checked.",),
        party_size=2,
        package_template_id="primo-only",
        courses=(
            CourseProposal(
                course=Course.PRIMO,
                lines=(
                    ProposalLine(
                        sku_id="potato-gnocchi-500g",
                        quantity=1,
                        rationale="Main pasta course.",
                    ),
                ),
            ),
            CourseProposal(
                course=Course.DRINKS,
                lines=(
                    ProposalLine(
                        sku_id="fresh-tagliatelle-250g",
                        quantity=1,
                        rationale="Food should not be a drinks line.",
                    ),
                ),
            ),
        ),
    )

    result = ValidateMenuProposal(StaticCatalogRepository([pasta, gnocchi]))(proposal)

    assert result.menu_proposal is None
    assert (
        result.validation_errors[0].code == PlannerValidationErrorCode.INVALID_PROPOSAL
    )
    assert result.validation_errors[0].sku_id == "fresh-tagliatelle-250g"
    assert result.validation_errors[0].course == Course.DRINKS


def test_validate_menu_proposal_reports_unsupported_raw_course_name() -> None:
    result = ValidateMenuProposal(StaticCatalogRepository([make_sku()])).validate_raw(
        {
            "title": "Weeknight Pasta",
            "explanation": "A compact pasta proposal.",
            "planner_notes": ("Catalog identities checked.",),
            "party_size": 2,
            "package_template_id": "primo-only",
            "courses": (
                {
                    "course": "cocktail",
                    "lines": (
                        {
                            "sku_id": "fresh-tagliatelle-250g",
                            "quantity": 1,
                            "rationale": "A flexible pasta course.",
                        },
                    ),
                },
            ),
        }
    )

    assert result.menu_proposal is None
    assert (
        result.validation_errors[0].code
        == PlannerValidationErrorCode.UNSUPPORTED_COURSE
    )


def test_validate_menu_proposal_reports_empty_raw_course() -> None:
    result = ValidateMenuProposal(StaticCatalogRepository([make_sku()])).validate_raw(
        {
            "title": "Weeknight Pasta",
            "explanation": "A compact pasta proposal.",
            "planner_notes": ("Catalog identities checked.",),
            "party_size": 2,
            "package_template_id": "primo-only",
            "courses": (
                {
                    "course": "drinks",
                    "lines": (),
                },
            ),
        }
    )

    assert result.menu_proposal is None
    assert (
        result.validation_errors[0].code == PlannerValidationErrorCode.INVALID_PROPOSAL
    )


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


def test_plan_menu_from_request_repairs_once_after_tavola_validation_failure() -> None:
    agent = RepairingPlannerAgent(
        first=raw_proposal(sku_id="missing-product", quantity=2),
        repaired=raw_proposal(quantity=2),
    )
    planner = PlanMenuFromRequest(
        agent=agent,
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    result = planner(customer_request="Dinner for two")

    assert result.status == ProposalStatus.PROPOSAL_READY
    assert result.menu_proposal is not None
    assert result.menu_proposal.total.amount_minor == 850
    assert len(agent.repair_requests) == 1
    repair_request = agent.repair_requests[0]
    assert repair_request["customer_request"] == "Dinner for two"
    assert repair_request["raw_proposal"]["courses"][0]["lines"][0]["sku_id"] == (
        "missing-product"
    )
    assert repair_request["validation_errors"][0].code == (
        PlannerValidationErrorCode.UNKNOWN_SKU
    )


def test_plan_menu_from_request_stops_after_one_invalid_tavola_repair() -> None:
    agent = RepairingPlannerAgent(
        first=raw_proposal(sku_id="missing-product", quantity=2),
        repaired=raw_proposal(sku_id="still-missing", quantity=2),
    )
    planner = PlanMenuFromRequest(
        agent=agent,
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    result = planner(customer_request="Dinner for two")

    assert result.status == ProposalStatus.FAILED
    assert result.menu_proposal is None
    assert len(agent.repair_requests) == 1
    assert result.validation_errors[0].code == PlannerValidationErrorCode.UNKNOWN_SKU
    assert result.validation_errors[0].sku_id == "still-missing"


def test_start_planner_session_saves_validated_proposal() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    use_case = StartPlannerSession(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal(quantity=2)),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    session = use_case(message="Dinner for two")

    assert session.planner_session_id.value == "planner-1"
    assert session.customer_request == "Dinner for two"
    assert session.status == ProposalStatus.PROPOSAL_READY
    assert session.menu_proposal is not None
    assert session.menu_proposal.total.amount_minor == 850
    assert repository.get_session(session.planner_session_id) == session


def test_start_planner_session_rejects_empty_prompt() -> None:
    use_case = StartPlannerSession(
        planner_repository=InMemoryPlannerSessionRepository(),
        agent=FakeMenuPlannerAgent.with_follow_up(
            FollowUpQuestion(message="How many people?")
        ),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )

    with pytest.raises(PlannerInputInvalid):
        use_case(message=" ")


def test_start_planner_session_saves_follow_up_state() -> None:
    question = FollowUpQuestion(message="How many people should this serve?")
    use_case = StartPlannerSession(
        planner_repository=InMemoryPlannerSessionRepository(
            id_generator=lambda: "planner-1"
        ),
        agent=FakeMenuPlannerAgent.with_follow_up(question),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )

    session = use_case(message="Help me plan Sunday lunch")

    assert session.status == ProposalStatus.NEEDS_INPUT
    assert session.follow_up_question == question
    assert session.follow_up_answers == ()


def test_create_planning_session_saves_in_progress_state() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")

    session = CreatePlanningSession(planner_repository=repository)(
        message="Dinner for two"
    )

    assert session.planner_session_id.value == "planner-1"
    assert session.status == ProposalStatus.PLANNING
    assert session.customer_request == "Dinner for two"
    assert session.menu_proposal is None
    assert repository.get_session(session.planner_session_id) == session


def test_complete_planning_session_updates_same_session_to_ready_proposal() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    session = CreatePlanningSession(planner_repository=repository)(
        message="Dinner for two"
    )

    updated = CompletePlanningSession(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal(quantity=2)),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )(planner_session_id=session.planner_session_id.value)

    assert updated.planner_session_id == session.planner_session_id
    assert updated.status == ProposalStatus.PROPOSAL_READY
    assert updated.menu_proposal is not None
    assert updated.menu_proposal.total.amount_minor == 850
    assert repository.get_session(session.planner_session_id) == updated


def test_complete_planning_session_maps_worker_exception_to_failed_session() -> None:
    class RaisingAgent:
        def plan_menu(
            self,
            *,
            customer_request: str,
            follow_up_answers: tuple[str, ...] = (),
        ):
            raise RuntimeError("raw worker detail")

    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    session = CreatePlanningSession(planner_repository=repository)(
        message="Dinner for two"
    )

    updated = CompletePlanningSession(
        planner_repository=repository,
        agent=RaisingAgent(),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )(planner_session_id=session.planner_session_id.value)

    assert updated.status == ProposalStatus.FAILED
    assert updated.validation_errors[0].code == (
        PlannerValidationErrorCode.INVALID_PROPOSAL
    )
    assert updated.validation_errors[0].message == (
        "Planner could not complete this request."
    )


def test_answer_follow_up_saves_answer_and_ready_proposal() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    start = StartPlannerSession(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_follow_up(
            FollowUpQuestion(message="How many people should this serve?")
        ),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )
    session = start(message="Help me plan Sunday lunch")
    answer = AnswerPlannerFollowUp(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal(quantity=4)),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )

    updated = answer(
        planner_session_id=session.planner_session_id.value,
        message="Four people",
    )

    assert updated.status == ProposalStatus.PROPOSAL_READY
    assert updated.customer_request == "Help me plan Sunday lunch"
    assert updated.follow_up_answers == ("Four people",)
    assert updated.menu_proposal is not None
    assert updated.menu_proposal.total.amount_minor == 1700


def test_submit_follow_up_saves_answer_and_returns_to_planning() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    session = StartPlannerSession(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_follow_up(
            FollowUpQuestion(message="How many people should this serve?")
        ),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )(message="Help me plan Sunday lunch")

    updated = SubmitPlannerFollowUp(planner_repository=repository)(
        planner_session_id=session.planner_session_id.value,
        message="Four people",
    )

    assert updated.status == ProposalStatus.PLANNING
    assert updated.customer_request == "Help me plan Sunday lunch"
    assert updated.follow_up_answers == ("Four people",)
    assert updated.follow_up_question is None
    assert updated.menu_proposal is None


def test_answer_follow_up_rejects_missing_or_ready_session() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    session = StartPlannerSession(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal()),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )(message="Dinner for two")
    use_case = AnswerPlannerFollowUp(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal()),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )

    with pytest.raises(PlannerSessionNotFound):
        use_case(planner_session_id="missing-session", message="Four")
    with pytest.raises(PlannerSessionStateInvalid):
        use_case(planner_session_id=session.planner_session_id.value, message="Four")


def test_revalidate_menu_proposal_recalculates_customer_edits() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    session = StartPlannerSession(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal(quantity=2)),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )(message="Dinner for two")
    use_case = RevalidateMenuProposal(
        planner_repository=repository,
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=500)]),
    )

    updated = use_case(
        planner_session_id=session.planner_session_id.value,
        raw_proposal=raw_proposal(quantity=3),
    )

    assert updated.status == ProposalStatus.PROPOSAL_READY
    assert updated.menu_proposal is not None
    assert updated.menu_proposal.total.amount_minor == 1500
    assert "Revalidated by Tavola." in updated.menu_proposal.planner_notes


def test_revalidate_menu_proposal_rejects_added_valid_products() -> None:
    pasta = make_sku(amount_minor=425)
    dessert = make_sku(
        "tiramisu-cup-single",
        name="Tiramisu Cup",
        category=CatalogCategory("desserts", "Desserts", 3),
        amount_minor=475,
    )
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    session = StartPlannerSession(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal(quantity=2)),
        catalog_repository=StaticCatalogRepository([pasta, dessert]),
    )(message="Dinner for two")
    use_case = RevalidateMenuProposal(
        planner_repository=repository,
        catalog_repository=StaticCatalogRepository([pasta, dessert]),
    )

    updated = use_case(
        planner_session_id=session.planner_session_id.value,
        raw_proposal=raw_proposal(sku_id="tiramisu-cup-single", quantity=1),
    )

    assert updated.status == ProposalStatus.FAILED
    assert (
        updated.validation_errors[0].code == PlannerValidationErrorCode.INVALID_PROPOSAL
    )
    assert "cannot add products" in updated.validation_errors[0].message


def test_revalidate_menu_proposal_rejects_empty_edited_proposal() -> None:
    repository = InMemoryPlannerSessionRepository(id_generator=lambda: "planner-1")
    session = StartPlannerSession(
        planner_repository=repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal()),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )(message="Dinner for two")
    use_case = RevalidateMenuProposal(
        planner_repository=repository,
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )

    updated = use_case(
        planner_session_id=session.planner_session_id.value,
        raw_proposal={
            "title": "Empty Dinner",
            "explanation": "No products remain.",
            "planner_notes": ("Catalog identities checked.",),
            "party_size": 2,
            "package_template_id": "primo-only",
            "courses": (),
        },
    )

    assert updated.status == ProposalStatus.FAILED
    assert updated.validation_errors[0].code == (
        PlannerValidationErrorCode.INVALID_PROPOSAL
    )


def test_accept_menu_proposal_appends_lines_to_basket_and_marks_session_accepted() -> (
    None
):
    planner_repository = InMemoryPlannerSessionRepository(id_generator=lambda: "p-1")
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()
    session = StartPlannerSession(
        planner_repository=planner_repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal(quantity=2)),
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )(message="Dinner for two")

    result = AcceptMenuProposal(
        planner_repository=planner_repository,
        basket_repository=basket_repository,
        catalog_repository=StaticCatalogRepository([make_sku(amount_minor=425)]),
    )(
        planner_session_id=session.planner_session_id.value,
        basket_id="basket-1",
        mode=AcceptanceMode.APPEND,
        raw_proposal=raw_proposal(quantity=2),
    )

    assert result.basket.item_count == 2
    assert result.basket.total.amount_minor == 850
    assert result.meal_plan_grouping.title == "Weeknight Pasta"
    assert result.meal_plan_grouping.courses[0].line_sku_ids == (
        "fresh-tagliatelle-250g",
    )
    accepted = planner_repository.get_session(session.planner_session_id)
    assert accepted is not None
    assert accepted.status == ProposalStatus.ACCEPTED


def test_accept_menu_proposal_replaces_existing_basket_lines() -> None:
    pasta = make_sku(amount_minor=425)
    dessert = make_sku(
        "tiramisu-cup-single",
        name="Tiramisu Cup",
        category=CatalogCategory("desserts", "Desserts", 3),
        amount_minor=475,
    )
    planner_repository = InMemoryPlannerSessionRepository(id_generator=lambda: "p-1")
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket = basket_repository.create_basket().add_line(pasta, quantity=2)
    basket_repository.save_basket(basket)
    session = StartPlannerSession(
        planner_repository=planner_repository,
        agent=FakeMenuPlannerAgent.with_proposal(
            raw_proposal(sku_id="tiramisu-cup-single", quantity=3)
        ),
        catalog_repository=StaticCatalogRepository([pasta, dessert]),
    )(message="Dessert for three")

    result = AcceptMenuProposal(
        planner_repository=planner_repository,
        basket_repository=basket_repository,
        catalog_repository=StaticCatalogRepository([pasta, dessert]),
    )(
        planner_session_id=session.planner_session_id.value,
        basket_id="basket-1",
        mode=AcceptanceMode.REPLACE,
        raw_proposal=raw_proposal(sku_id="tiramisu-cup-single", quantity=3),
    )

    assert [line.sku.sku_id for line in result.basket.lines] == ["tiramisu-cup-single"]
    assert result.basket.item_count == 3


def test_accept_menu_proposal_rejects_duplicate_acceptance() -> None:
    planner_repository = InMemoryPlannerSessionRepository(id_generator=lambda: "p-1")
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()
    session = StartPlannerSession(
        planner_repository=planner_repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal()),
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )(message="Dinner for two")
    accept = AcceptMenuProposal(
        planner_repository=planner_repository,
        basket_repository=basket_repository,
        catalog_repository=StaticCatalogRepository([make_sku()]),
    )
    accept(
        planner_session_id=session.planner_session_id.value,
        basket_id="basket-1",
        mode=AcceptanceMode.APPEND,
        raw_proposal=raw_proposal(),
    )

    with pytest.raises(PlannerSessionStateInvalid):
        accept(
            planner_session_id=session.planner_session_id.value,
            basket_id="basket-1",
            mode=AcceptanceMode.APPEND,
            raw_proposal=raw_proposal(),
        )


def test_accept_menu_proposal_rejects_added_valid_products() -> None:
    pasta = make_sku(amount_minor=425)
    dessert = make_sku(
        "tiramisu-cup-single",
        name="Tiramisu Cup",
        category=CatalogCategory("desserts", "Desserts", 3),
        amount_minor=475,
    )
    planner_repository = InMemoryPlannerSessionRepository(id_generator=lambda: "p-1")
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()
    session = StartPlannerSession(
        planner_repository=planner_repository,
        agent=FakeMenuPlannerAgent.with_proposal(raw_proposal()),
        catalog_repository=StaticCatalogRepository([pasta, dessert]),
    )(message="Dinner for two")
    accept = AcceptMenuProposal(
        planner_repository=planner_repository,
        basket_repository=basket_repository,
        catalog_repository=StaticCatalogRepository([pasta, dessert]),
    )

    with pytest.raises(PlannerProposalInvalid) as exc_info:
        accept(
            planner_session_id=session.planner_session_id.value,
            basket_id="basket-1",
            mode=AcceptanceMode.APPEND,
            raw_proposal=raw_proposal(sku_id="tiramisu-cup-single", quantity=1),
        )

    assert (
        exc_info.value.validation_errors[0].code
        == PlannerValidationErrorCode.INVALID_PROPOSAL
    )
    assert "cannot add products" in exc_info.value.validation_errors[0].message
