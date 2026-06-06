from tavola.domain.catalog import CatalogCategory, CatalogSku, DietaryFacets, Money
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.planner_mcp_server import (
    create_catalog_candidate_tool_handlers,
    create_planner_tool_handlers,
    handle_mcp_message,
)


def make_sku(
    sku_id: str = "fresh-tagliatelle-250g",
    *,
    name: str = "Fresh Tagliatelle",
    category: CatalogCategory | None = None,
    amount_minor: int = 425,
    unit_label: str = "250g",
    tags: tuple[str, ...] = ("pasta", "fresh"),
    facets: DietaryFacets | None = None,
    is_available: bool = True,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name=name,
        category=category or CatalogCategory("primi", "Primi", 2),
        unit_label=unit_label,
        price=Money(amount_minor=amount_minor, currency="GBP"),
        short_description="Egg pasta cut fresh each morning.",
        detail_description="Silky ribbons of egg pasta for a quick supper.",
        tags=tags,
        facets=facets or DietaryFacets(is_vegetarian=True),
        image_id=sku_id,
        display_order=1,
        is_available=is_available,
    )


def test_find_catalog_candidates_returns_candidate_summaries() -> None:
    tools = create_planner_tool_handlers(
        StaticCatalogRepository(
            [
                make_sku(),
                make_sku(
                    "chianti-classico-750ml",
                    name="Chianti Classico",
                    category=CatalogCategory("drinks", "Drinks", 4),
                    amount_minor=1850,
                    unit_label="750ml",
                    tags=("wine", "red"),
                    facets=DietaryFacets(contains_alcohol=True),
                ),
            ]
        )
    )

    result = tools.call(
        "find_catalog_candidates",
        {
            "category_ids": ["primi"],
            "dietary_facets": ["vegetarian"],
            "tags": ["pasta"],
            "alcohol": "exclude",
        },
    )

    assert result == {
        "result_count": 1,
        "returned_count": 1,
        "recommended_next_action": (
            "Build a draft menu proposal from these products, then call "
            "validate_menu_proposal."
        ),
        "products": [
            {
                "sku_id": "fresh-tagliatelle-250g",
                "name": "Fresh Tagliatelle",
                "category_id": "primi",
                "category_label": "Primi",
                "unit_label": "250g",
                "unit_price_minor": 425,
                "currency": "GBP",
                "short_description": "Egg pasta cut fresh each morning.",
                "tags": ["pasta", "fresh"],
                "dietary_facets": {
                    "is_vegetarian": True,
                    "is_vegan": False,
                    "is_gluten_free": False,
                    "contains_alcohol": False,
                },
                "is_available": True,
                "image_id": "fresh-tagliatelle-250g",
            }
        ],
    }
    assert "detail_description" not in result["products"][0]


def test_catalog_candidate_handlers_expose_only_catalog_lookup() -> None:
    tools = create_catalog_candidate_tool_handlers(
        StaticCatalogRepository([make_sku()])
    )

    result = tools.call("find_catalog_candidates", {"category_ids": ["primi"]})

    assert tools.available_tool_names() == ("find_catalog_candidates",)
    assert [tool["name"] for tool in tools.tool_descriptions()] == [
        "find_catalog_candidates"
    ]
    assert result["recommended_next_action"] == (
        "Build a draft menu proposal from these products; Tavola will validate "
        "the returned proposal after the planner responds."
    )


def test_find_catalog_candidates_seed_finds_pantry_pesto_by_tag() -> None:
    tools = create_planner_tool_handlers(StaticCatalogRepository.from_seed())

    result = tools.call("find_catalog_candidates", {"tags": ["pasta"]})

    assert "pesto-genovese-180g" in {
        product["sku_id"] for product in result["products"]
    }


def test_find_catalog_candidates_limits_results_and_reports_available_count() -> None:
    tools = create_planner_tool_handlers(
        StaticCatalogRepository(
            [
                make_sku(
                    f"pasta-{index}",
                    name=f"Pasta {index}",
                    tags=("pasta", "fresh"),
                )
                for index in range(10)
            ]
        )
    )

    result = tools.call(
        "find_catalog_candidates",
        {"tags": ["pasta"], "max_results": 3},
    )

    assert result["result_count"] == 10
    assert result["returned_count"] == 3
    assert [product["sku_id"] for product in result["products"]] == [
        "pasta-0",
        "pasta-1",
        "pasta-2",
    ]
    assert result["recommended_next_action"] == (
        "Build a draft menu proposal from these products, then call "
        "validate_menu_proposal."
    )


def test_find_catalog_candidates_empty_results_recommends_broadening_filters() -> None:
    tools = create_planner_tool_handlers(
        StaticCatalogRepository([make_sku(facets=DietaryFacets(is_vegetarian=True))])
    )

    result = tools.call(
        "find_catalog_candidates",
        {"dietary_facets": ["vegan"]},
    )

    assert result["products"] == []
    assert result["result_count"] == 0
    assert result["returned_count"] == 0
    assert result["recommended_next_action"] == (
        "Broaden the catalog-native filters, then call find_catalog_candidates again."
    )


def test_validate_proposal_returns_normalized_totals_from_tavola_validation() -> None:
    tools = create_planner_tool_handlers(
        StaticCatalogRepository([make_sku(amount_minor=500)])
    )

    result = tools.call(
        "validate_menu_proposal",
        {
            "proposal": {
                "title": "Weeknight Pasta",
                "explanation": "A compact pasta proposal.",
                "planner_notes": ["Catalog identities checked."],
                "party_size": 2,
                "package_template_id": "primo-only",
                "courses": [
                    {
                        "course": "primo",
                        "lines": [
                            {
                                "sku_id": "fresh-tagliatelle-250g",
                                "quantity": 3,
                                "rationale": "A flexible pasta course.",
                            },
                        ],
                    },
                ],
            }
        },
    )

    assert result["is_valid"] is True
    assert result["recommended_next_action"] == (
        "Return the validated menu proposal as the final JSON object."
    )
    assert result["validation_errors"] == []
    assert result["menu_proposal"]["total"] == {
        "amount_minor": 1500,
        "currency": "GBP",
    }
    assert result["menu_proposal"]["item_count"] == 3
    assert result["menu_proposal"]["line_count"] == 1
    line = result["menu_proposal"]["courses"][0]["lines"][0]
    assert line["sku_id"] == "fresh-tagliatelle-250g"
    assert line["name"] == "Fresh Tagliatelle"
    assert line["category_id"] == "primi"
    assert line["unit_label"] == "250g"
    assert line["quantity"] == 3
    assert line["unit_price_minor"] == 500
    assert line["line_total_minor"] == 1500
    assert line["rationale"] == "A flexible pasta course."
    assert line["tags"] == ["pasta", "fresh"]
    assert line["dietary_facets"]["is_vegetarian"] is True
    assert line["is_available"] is True


def test_validate_proposal_returns_structured_validation_errors() -> None:
    tools = create_planner_tool_handlers(StaticCatalogRepository([make_sku()]))

    result = tools.call(
        "validate_menu_proposal",
        {
            "proposal": {
                "title": "Weeknight Pasta",
                "explanation": "A compact pasta proposal.",
                "planner_notes": ["Catalog identities checked."],
                "party_size": 2,
                "package_template_id": "primo-only",
                "courses": [
                    {
                        "course": "primo",
                        "lines": [
                            {
                                "sku_id": "missing-product",
                                "quantity": 1,
                                "rationale": "Codex guessed this product.",
                            },
                        ],
                    },
                ],
            }
        },
    )

    assert result == {
        "is_valid": False,
        "menu_proposal": None,
        "recommended_next_action": (
            "Revise the proposal using only valid catalog products and call "
            "validate_menu_proposal again."
        ),
        "validation_errors": [
            {
                "code": "unknown_sku",
                "message": "Product is not in the current catalog.",
                "sku_id": "missing-product",
                "course": "primo",
            }
        ],
    }


def test_mcp_protocol_lists_and_calls_planner_tools() -> None:
    tools = create_planner_tool_handlers(
        StaticCatalogRepository([make_sku(amount_minor=500)])
    )

    initialize_response = handle_mcp_message(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
        tools,
    )
    list_response = handle_mcp_message(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        tools,
    )
    call_response = handle_mcp_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "find_catalog_candidates",
                "arguments": {"tags": ["pasta"]},
            },
        },
        tools,
    )

    assert initialize_response is not None
    assert initialize_response["result"]["capabilities"] == {
        "tools": {"listChanged": False}
    }
    assert list_response is not None
    tool_names = {tool["name"] for tool in list_response["result"]["tools"]}
    assert tool_names == {
        "find_catalog_candidates",
        "validate_menu_proposal",
    }
    assert call_response is not None
    assert call_response["result"]["isError"] is False
    assert call_response["result"]["structuredContent"]["products"][0]["sku_id"] == (
        "fresh-tagliatelle-250g"
    )
    assert call_response["result"]["content"][0]["type"] == "text"


def test_mcp_protocol_lists_candidate_schema_with_repository_tag_enums() -> None:
    tools = create_planner_tool_handlers(
        StaticCatalogRepository([make_sku(tags=("pasta", "fresh"))])
    )

    list_response = handle_mcp_message(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        tools,
    )

    assert list_response is not None
    candidate_tool = next(
        tool
        for tool in list_response["result"]["tools"]
        if tool["name"] == "find_catalog_candidates"
    )
    properties = candidate_tool["inputSchema"]["properties"]
    assert candidate_tool["inputSchema"]["additionalProperties"] is False
    assert properties["category_ids"]["items"]["enum"] == [
        "antipasti",
        "primi",
        "desserts",
        "drinks",
        "pantry",
    ]
    assert properties["dietary_facets"]["items"]["enum"] == [
        "vegetarian",
        "vegan",
        "gluten_free",
    ]
    assert properties["tags"]["items"]["enum"] == ["fresh", "pasta"]
    assert properties["tag_match"]["enum"] == ["any", "all"]
    assert properties["alcohol"]["enum"] == ["include", "exclude", "only"]
    assert properties["max_results"]["minimum"] == 1
    assert properties["max_results"]["maximum"] == 20


def test_mcp_protocol_omits_tag_enum_for_empty_catalog() -> None:
    tools = create_planner_tool_handlers(StaticCatalogRepository([]))

    list_response = handle_mcp_message(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        tools,
    )

    assert list_response is not None
    candidate_tool = next(
        tool
        for tool in list_response["result"]["tools"]
        if tool["name"] == "find_catalog_candidates"
    )
    tag_items = candidate_tool["inputSchema"]["properties"]["tags"]["items"]
    assert tag_items == {"type": "string"}


def test_mcp_protocol_rejects_invalid_candidate_enum() -> None:
    tools = create_planner_tool_handlers(StaticCatalogRepository([make_sku()]))

    response = handle_mcp_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "find_catalog_candidates",
                "arguments": {"category_ids": ["meat-counter"]},
            },
        },
        tools,
    )

    assert response is not None
    assert response["error"]["code"] == -32602
    assert "unsupported category_ids" in response["error"]["message"]


def test_mcp_protocol_rejects_non_array_candidate_filters() -> None:
    tools = create_planner_tool_handlers(StaticCatalogRepository([make_sku()]))

    response = handle_mcp_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "find_catalog_candidates",
                "arguments": {"tags": "pasta"},
            },
        },
        tools,
    )

    assert response is not None
    assert response["error"]["code"] == -32602
    assert "tags must be an array" in response["error"]["message"]


def test_mcp_protocol_rejects_unsupported_candidate_fields() -> None:
    tools = create_planner_tool_handlers(StaticCatalogRepository([make_sku()]))

    response = handle_mcp_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "find_catalog_candidates",
                "arguments": {"query": "pasta"},
            },
        },
        tools,
    )

    assert response is not None
    assert response["error"]["code"] == -32602
    assert "unsupported find_catalog_candidates fields" in response["error"]["message"]
