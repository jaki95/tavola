import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from tavola.application.catalog import (
    DEFAULT_CATALOG_CANDIDATE_LIMIT,
    MAX_CATALOG_CANDIDATE_LIMIT,
    CatalogRepository,
    FindCatalogCandidates,
    FindCatalogCandidatesInput,
    ListAvailableCatalogTags,
)
from tavola.application.planner import ValidateMenuProposal
from tavola.domain.catalog import (
    CatalogSku,
    catalog_category_ids,
    catalog_dietary_facet_ids,
)
from tavola.domain.planner import (
    PlannerValidationError,
    ValidatedMenuProposal,
    ValidatedProposalLine,
)
from tavola.infrastructure.catalog_repository import StaticCatalogRepository

ToolPayload = dict[str, Any]
ToolHandler = Callable[[Mapping[str, Any]], ToolPayload]
JsonRpcMessage = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class PlannerToolHandlers:
    _handlers: Mapping[str, ToolHandler]
    _tool_descriptions: tuple[ToolPayload, ...]

    def available_tool_names(self) -> tuple[str, ...]:
        return tuple(self._handlers)

    def tool_descriptions(self) -> tuple[ToolPayload, ...]:
        return self._tool_descriptions

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
        return _json_rpc_result(request_id, {"tools": list(tools.tool_descriptions())})
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
    tag_vocabulary = ListAvailableCatalogTags(catalog_repository)().tags
    return PlannerToolHandlers(
        {
            "find_catalog_candidates": _find_catalog_candidates_handler(
                catalog_repository,
                tag_vocabulary,
            ),
            "validate_menu_proposal": _validate_proposal_handler(catalog_repository),
        },
        _tool_descriptions(tag_vocabulary),
    )


def create_catalog_candidate_tool_handlers(
    catalog_repository: CatalogRepository,
) -> PlannerToolHandlers:
    tag_vocabulary = ListAvailableCatalogTags(catalog_repository)().tags
    return PlannerToolHandlers(
        {
            "find_catalog_candidates": _find_catalog_candidates_handler(
                catalog_repository,
                tag_vocabulary,
                include_validation_next_action=False,
            ),
        },
        (_tool_descriptions(tag_vocabulary)[0],),
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


def _tool_descriptions(tag_vocabulary: tuple[str, ...]) -> tuple[ToolPayload, ...]:
    tag_items: ToolPayload = {"type": "string"}
    if tag_vocabulary:
        tag_items["enum"] = list(tag_vocabulary)
    return (
        {
            "name": "find_catalog_candidates",
            "description": (
                "Find buyable Tavola products with catalog-native filters. Use "
                "category ids, dietary facets, tags, alcohol mode, and a bounded "
                "result limit; do not pass party size, budget, occasion, or menu "
                "structure as search text."
            ),
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "category_ids": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(catalog_category_ids()),
                        },
                    },
                    "dietary_facets": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": list(catalog_dietary_facet_ids()),
                        },
                    },
                    "tags": {
                        "type": "array",
                        "items": tag_items,
                    },
                    "tag_match": {
                        "type": "string",
                        "enum": ["any", "all"],
                        "default": "any",
                    },
                    "alcohol": {
                        "type": "string",
                        "enum": ["include", "exclude", "only"],
                        "default": "include",
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_CATALOG_CANDIDATE_LIMIT,
                        "default": DEFAULT_CATALOG_CANDIDATE_LIMIT,
                    },
                },
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
    )


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


def _find_catalog_candidates_handler(
    catalog_repository: CatalogRepository,
    tag_vocabulary: tuple[str, ...],
    *,
    include_validation_next_action: bool = True,
) -> ToolHandler:
    candidate_finder = FindCatalogCandidates(catalog_repository)

    def find_catalog_candidates(arguments: Mapping[str, Any]) -> ToolPayload:
        result = candidate_finder(_parse_candidate_filters(arguments, tag_vocabulary))
        products = result.products
        return {
            "result_count": result.result_count,
            "returned_count": len(products),
            "recommended_next_action": _candidate_recommended_next_action(
                products,
                include_validation_next_action=include_validation_next_action,
            ),
            "products": [_sku_summary_payload(sku) for sku in products],
        }

    return find_catalog_candidates


def _parse_candidate_filters(
    arguments: Mapping[str, Any],
    tag_vocabulary: tuple[str, ...],
) -> FindCatalogCandidatesInput:
    _reject_unsupported_candidate_fields(arguments)
    category_ids = _optional_string_array(
        arguments,
        "category_ids",
        allowed_values=catalog_category_ids(),
    )
    dietary_facets = _optional_string_array(
        arguments,
        "dietary_facets",
        allowed_values=catalog_dietary_facet_ids(),
    )
    tags = _optional_string_array(
        arguments,
        "tags",
        allowed_values=tag_vocabulary,
    )
    tag_match = _optional_enum(arguments, "tag_match", ("any", "all"), default="any")
    alcohol = _optional_enum(
        arguments,
        "alcohol",
        ("include", "exclude", "only"),
        default="include",
    )
    max_results = _optional_integer(
        arguments,
        "max_results",
        default=DEFAULT_CATALOG_CANDIDATE_LIMIT,
    )
    return FindCatalogCandidatesInput(
        category_ids=category_ids,
        dietary_facets=dietary_facets,
        tags=tags,
        tag_match=tag_match,  # type: ignore[arg-type]
        alcohol=alcohol,  # type: ignore[arg-type]
        max_results=max_results,
    )


def _reject_unsupported_candidate_fields(arguments: Mapping[str, Any]) -> None:
    supported_fields = {
        "category_ids",
        "dietary_facets",
        "tags",
        "tag_match",
        "alcohol",
        "max_results",
    }
    unsupported_fields = sorted(set(arguments) - supported_fields)
    if unsupported_fields:
        raise ValueError(
            f"unsupported find_catalog_candidates fields: {unsupported_fields}"
        )


def _optional_string_array(
    arguments: Mapping[str, Any],
    field_name: str,
    *,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if field_name not in arguments:
        return ()
    raw_value = arguments[field_name]
    if not isinstance(raw_value, list | tuple):
        raise ValueError(f"{field_name} must be an array")
    if not all(isinstance(value, str) for value in raw_value):
        raise ValueError(f"{field_name} must contain only strings")

    values = tuple(raw_value)
    unknown_values = sorted(set(values) - set(allowed_values))
    if unknown_values:
        raise ValueError(f"unsupported {field_name}: {unknown_values}")
    return values


def _optional_enum(
    arguments: Mapping[str, Any],
    field_name: str,
    allowed_values: tuple[str, ...],
    *,
    default: str,
) -> str:
    if field_name not in arguments:
        return default
    raw_value = arguments[field_name]
    if not isinstance(raw_value, str):
        raise ValueError(f"{field_name} must be a string")
    if raw_value not in allowed_values:
        raise ValueError(f"unsupported {field_name}: {raw_value}")
    return raw_value


def _optional_integer(
    arguments: Mapping[str, Any],
    field_name: str,
    *,
    default: int,
) -> int:
    if field_name not in arguments:
        return default
    raw_value = arguments[field_name]
    if not isinstance(raw_value, int) or isinstance(raw_value, bool):
        raise ValueError(f"{field_name} must be an integer")
    return raw_value


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


def _candidate_recommended_next_action(
    products: tuple[CatalogSku, ...],
    *,
    include_validation_next_action: bool = True,
) -> str:
    if not products:
        return (
            "Broaden the catalog-native filters, then call "
            "find_catalog_candidates again."
        )
    if not include_validation_next_action:
        return (
            "Build a draft menu proposal from these products; Tavola will validate "
            "the returned proposal after the planner responds."
        )
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
