import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from tavola.application.catalog import BrowseCatalog, CatalogRepository
from tavola.application.planner import ValidateMenuProposal
from tavola.domain.catalog import CatalogSku
from tavola.domain.planner import (
    PackageTemplate,
    PlannerValidationError,
    ValidatedMenuProposal,
    ValidatedProposalLine,
)
from tavola.infrastructure.catalog_repository import StaticCatalogRepository

ToolPayload = dict[str, Any]
ToolHandler = Callable[[Mapping[str, Any]], ToolPayload]
JsonRpcMessage = Mapping[str, Any]

PLANNER_TOOL_INSTRUCTIONS = (
    "Use Tavola tools for SKU validity, availability, quantity, and totals. "
    "Do not invent SKUs or prices. Do not mutate baskets or checkout orders."
)
DEFAULT_SEARCH_LIMIT = 8
MAX_SEARCH_LIMIT = 12


@dataclass(frozen=True, slots=True)
class PlannerToolHandlers:
    _handlers: Mapping[str, ToolHandler]

    def available_tool_names(self) -> tuple[str, ...]:
        return tuple(self._handlers)

    def call(self, name: str, arguments: Mapping[str, Any]) -> ToolPayload:
        try:
            handler = self._handlers[name]
        except KeyError as error:
            raise ValueError(f"unknown planner tool: {name}") from error
        return handler(arguments)


def handle_mcp_message(
    message: JsonRpcMessage,
    tools: PlannerToolHandlers,
) -> ToolPayload | None:
    request_id = message.get("id")
    method = message.get("method")
    if request_id is None:
        return None
    if method == "initialize":
        return _json_rpc_result(
            request_id,
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "tavola-planner-tools", "version": "0.1.0"},
            },
        )
    if method == "tools/list":
        return _json_rpc_result(request_id, {"tools": _tool_descriptions()})
    if method == "tools/call":
        return _handle_tool_call(request_id, message, tools)
    return _json_rpc_error(request_id, -32601, f"unsupported method: {method}")


def run_stdio_server(
    tools: PlannerToolHandlers | None = None,
) -> None:
    active_tools = tools or create_planner_tool_handlers(
        StaticCatalogRepository.from_seed()
    )
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = handle_mcp_message(message, active_tools)
        except json.JSONDecodeError:
            response = _json_rpc_error(None, -32700, "invalid JSON-RPC message")
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


def create_planner_tool_handlers(
    catalog_repository: CatalogRepository,
) -> PlannerToolHandlers:
    return PlannerToolHandlers(
        {
            "list_package_templates": _list_package_templates,
            "search_catalog": _search_catalog_handler(catalog_repository),
            "get_sku_detail": _get_sku_detail_handler(catalog_repository),
            "validate_menu_proposal": _validate_proposal_handler(catalog_repository),
        }
    )


def _handle_tool_call(
    request_id: Any,
    message: JsonRpcMessage,
    tools: PlannerToolHandlers,
) -> ToolPayload:
    params = message.get("params")
    if not isinstance(params, Mapping):
        return _json_rpc_error(request_id, -32602, "tools/call params are required")
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if not isinstance(name, str) or not isinstance(arguments, Mapping):
        return _json_rpc_error(request_id, -32602, "invalid tool call")
    try:
        payload = tools.call(name, arguments)
    except ValueError as error:
        return _json_rpc_error(request_id, -32602, str(error))

    text = json.dumps(payload, separators=(",", ":"))
    return _json_rpc_result(
        request_id,
        {
            "content": [{"type": "text", "text": text}],
            "structuredContent": payload,
            "isError": False,
        },
    )


def _tool_descriptions() -> list[ToolPayload]:
    return [
        {
            "name": "list_package_templates",
            "description": (
                "List Tavola planner menu structures. Use this before choosing "
                "a proposal shape. Do not mention templates in customer-facing text."
            ),
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "search_catalog",
            "description": (
                "Search buyable Tavola products using customer request terms, "
                "tags, categories, and dietary facets. Returns compact summaries "
                "for proposal drafting."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "category_id": {"type": "string"},
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_SEARCH_LIMIT,
                    },
                },
            },
        },
        {
            "name": "get_sku_detail",
            "description": (
                "Get customer-safe detail for one Tavola product identity before "
                "adding it to a proposal."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {"sku_id": {"type": "string"}},
                "required": ["sku_id"],
            },
        },
        {
            "name": "validate_menu_proposal",
            "description": (
                "Validate SKU validity, availability, quantities, course "
                "structure, and server-calculated totals for a menu proposal."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {"proposal": {"type": "object"}},
                "required": ["proposal"],
            },
        },
    ]


def _json_rpc_result(request_id: Any, result: ToolPayload) -> ToolPayload:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _json_rpc_error(
    request_id: Any,
    code: int,
    message: str,
) -> ToolPayload:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _list_package_templates(arguments: Mapping[str, Any]) -> ToolPayload:
    del arguments
    return {
        "instructions": PLANNER_TOOL_INSTRUCTIONS,
        "recommended_next_action": (
            "Choose one menu structure, then call search_catalog for matching products."
        ),
        "templates": [
            {
                "template_id": template.template_id,
                "label": template.label,
                "courses": [
                    {"course": course.value, "label": course.label}
                    for course in template.courses
                ],
            }
            for template in (
                PackageTemplate.by_id(template_id)
                for template_id in PackageTemplate.supported_ids()
            )
        ],
    }


def _search_catalog_handler(catalog_repository: CatalogRepository) -> ToolHandler:
    def search_catalog(arguments: Mapping[str, Any]) -> ToolPayload:
        query = arguments.get("query")
        category_id = arguments.get("category_id")
        result = BrowseCatalog(catalog_repository)(
            query=query if isinstance(query, str) else None,
            category_id=category_id if isinstance(category_id, str) else None,
        )
        max_results = _search_limit(arguments.get("max_results"))
        products = result.products[:max_results]
        return {
            "result_count": len(result.products),
            "returned_count": len(products),
            "recommended_next_action": _search_recommended_next_action(products),
            "products": [_sku_summary_payload(sku) for sku in products],
        }

    return search_catalog


def _get_sku_detail_handler(catalog_repository: CatalogRepository) -> ToolHandler:
    def get_sku_detail(arguments: Mapping[str, Any]) -> ToolPayload:
        sku_id = arguments.get("sku_id")
        if not isinstance(sku_id, str):
            return {"product": None}

        sku = catalog_repository.get_sku(sku_id)
        if sku is None:
            return {"product": None}
        return {"product": _sku_detail_payload(sku)}

    return get_sku_detail


def _validate_proposal_handler(catalog_repository: CatalogRepository) -> ToolHandler:
    validator = ValidateMenuProposal(catalog_repository)

    def validate_proposal(arguments: Mapping[str, Any]) -> ToolPayload:
        raw_proposal = arguments.get("proposal")
        result = validator.validate_raw(raw_proposal)
        if result.menu_proposal is None:
            return {
                "is_valid": False,
                "menu_proposal": None,
                "recommended_next_action": (
                    "Revise the proposal using only valid catalog products and call "
                    "validate_menu_proposal again."
                ),
                "validation_errors": [
                    _validation_error_payload(error)
                    for error in result.validation_errors
                ],
            }
        return {
            "is_valid": True,
            "menu_proposal": _validated_menu_proposal_payload(result.menu_proposal),
            "recommended_next_action": (
                "Return the validated menu proposal as the final JSON object."
            ),
            "validation_errors": [],
        }

    return validate_proposal


def _search_limit(raw_limit: Any) -> int:
    if not isinstance(raw_limit, int):
        return DEFAULT_SEARCH_LIMIT
    return min(max(raw_limit, 1), MAX_SEARCH_LIMIT)


def _search_recommended_next_action(products: tuple[CatalogSku, ...]) -> str:
    if not products:
        return "Search again with broader request terms or a different category."
    return (
        "Build a draft menu proposal from these products, then call "
        "validate_menu_proposal."
    )


def _sku_summary_payload(sku: CatalogSku) -> ToolPayload:
    return {
        "sku_id": sku.sku_id,
        "name": sku.name,
        "category_id": sku.category.category_id,
        "category_label": sku.category.label,
        "unit_label": sku.unit_label,
        "unit_price_minor": sku.price.amount_minor,
        "currency": sku.price.currency,
        "short_description": sku.short_description,
        "tags": list(sku.tags),
        "dietary_facets": _dietary_facets_payload(sku),
        "is_available": sku.is_available,
        "image_id": sku.image_id,
    }


def _sku_detail_payload(sku: CatalogSku) -> ToolPayload:
    return {
        **_sku_summary_payload(sku),
        "detail_description": sku.detail_description,
    }


def _dietary_facets_payload(sku: CatalogSku) -> ToolPayload:
    return {
        "is_vegetarian": sku.facets.is_vegetarian,
        "is_vegan": sku.facets.is_vegan,
        "is_gluten_free": sku.facets.is_gluten_free,
        "contains_alcohol": sku.facets.contains_alcohol,
    }


def _validated_menu_proposal_payload(
    proposal: ValidatedMenuProposal,
) -> ToolPayload:
    return {
        "title": proposal.title,
        "explanation": proposal.explanation,
        "planner_notes": list(proposal.planner_notes),
        "party_size": proposal.party_size,
        "package_template_id": proposal.package_template_id,
        "courses": [
            {
                "course": course.course.value,
                "label": course.course.label,
                "lines": [_validated_line_payload(line) for line in course.lines],
            }
            for course in proposal.courses
        ],
        "total": {
            "amount_minor": proposal.total.amount_minor,
            "currency": proposal.total.currency,
        },
        "item_count": proposal.item_count,
        "line_count": proposal.line_count,
        "warnings": list(proposal.warnings),
    }


def _validated_line_payload(line: ValidatedProposalLine) -> ToolPayload:
    return {
        **_sku_summary_payload(line.sku),
        "quantity": line.quantity,
        "line_total_minor": line.line_total.amount_minor,
        "rationale": line.rationale,
    }


def _validation_error_payload(error: PlannerValidationError) -> ToolPayload:
    return {
        "code": error.code.value,
        "message": error.message,
        "sku_id": error.sku_id,
        "course": error.course.value if error.course is not None else None,
    }


def main() -> None:
    run_stdio_server()


if __name__ == "__main__":
    main()
