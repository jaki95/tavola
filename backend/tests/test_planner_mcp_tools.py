from tavola.domain.catalog import CatalogCategory, CatalogSku, DietaryFacets, Money
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.planner_mcp_server import (
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


def test_list_package_templates_exposes_courses_and_instructions() -> None:
    tools = create_planner_tool_handlers(StaticCatalogRepository([]))

    result = tools.call("list_package_templates", {})

    assert {
        "template_id": "antipasto-primo-dessert",
        "label": "Antipasto + Primo + Dessert",
        "courses": [
            {"course": "antipasto", "label": "Antipasto"},
            {"course": "primo", "label": "Primo"},
            {"course": "dessert", "label": "Dessert"},
        ],
    } in result["templates"]
    assert (
        "Use Tavola tools for SKU validity, availability, quantity, and totals."
        in result["instructions"]
    )
    assert "Do not mutate baskets or checkout orders." in result["instructions"]
    assert set(tools.available_tool_names()) == {
        "list_package_templates",
        "search_catalog",
        "get_sku_detail",
        "validate_menu_proposal",
    }


def test_search_catalog_returns_customer_safe_sku_summaries() -> None:
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

    result = tools.call("search_catalog", {"query": "vegetarian pasta"})

    assert result == {
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


def test_get_sku_detail_returns_customer_safe_detail_for_catalog_identity() -> None:
    tools = create_planner_tool_handlers(
        StaticCatalogRepository(
            [
                make_sku(
                    facets=DietaryFacets(is_vegetarian=True, is_gluten_free=True),
                )
            ]
        )
    )

    result = tools.call("get_sku_detail", {"sku_id": "fresh-tagliatelle-250g"})

    assert result["product"]["sku_id"] == "fresh-tagliatelle-250g"
    assert result["product"]["detail_description"] == (
        "Silky ribbons of egg pasta for a quick supper."
    )
    assert result["product"]["dietary_facets"]["is_gluten_free"] is True
    assert "display_order" not in result["product"]
    assert "basket" not in result


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
                "name": "search_catalog",
                "arguments": {"query": "pasta"},
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
        "list_package_templates",
        "search_catalog",
        "get_sku_detail",
        "validate_menu_proposal",
    }
    assert call_response is not None
    assert call_response["result"]["isError"] is False
    assert call_response["result"]["structuredContent"]["products"][0]["sku_id"] == (
        "fresh-tagliatelle-250g"
    )
    assert call_response["result"]["content"][0]["type"] == "text"
