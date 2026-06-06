import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from tavola.domain.planner import PlannerValidationError

_PLANNER_PROMPT_FILE = "codex_planner_prompt.md"


def build_planner_prompt(
    customer_request: str,
    follow_up_answers: tuple[str, ...] = (),
) -> str:
    follow_up_text = (
        "\n".join(f"- {answer}" for answer in follow_up_answers)
        or "No follow-up answers yet."
    )
    return "\n".join(
        (
            _planner_prompt_template(),
            "Customer request:",
            customer_request,
            "Follow-up answers:",
            follow_up_text,
        )
    )


@lru_cache(maxsize=1)
def _planner_prompt_template() -> str:
    return (
        Path(__file__)
        .with_name(_PLANNER_PROMPT_FILE)
        .read_text(encoding="utf-8")
        .strip()
    )


def build_repair_prompt(
    *,
    customer_request: str,
    follow_up_answers: tuple[str, ...],
    repair_reason: str,
) -> str:
    return "\n".join(
        (
            build_planner_prompt(customer_request, follow_up_answers),
            "Repair your previous planner output.",
            repair_reason,
            "Do not repeat invalid JSON, Markdown, stack traces, credentials, "
            "or tool transcripts.",
            "Return one corrected JSON object that matches the Final JSON contract.",
        )
    )


def build_validation_repair_prompt(
    *,
    customer_request: str,
    follow_up_answers: tuple[str, ...],
    raw_proposal: dict[str, Any],
    validation_errors: tuple[PlannerValidationError, ...],
) -> str:
    return "\n".join(
        (
            build_planner_prompt(customer_request, follow_up_answers),
            "Repair your previous menu proposal.",
            "Tavola validation errors:",
            json.dumps(
                [_validation_error_payload(error) for error in validation_errors],
                separators=(",", ":"),
            ),
            "Previous proposal JSON:",
            json.dumps(raw_proposal, separators=(",", ":")),
            "Use Tavola catalog candidates to replace invalid products, quantities, "
            "or courses. Do not invent products, prices, SKUs, or templates.",
            "Do not repeat stack traces, credentials, tool transcripts, or raw "
            "runtime details.",
            "Return one corrected JSON object that matches the Final JSON contract.",
        )
    )


def _validation_error_payload(error: PlannerValidationError) -> dict[str, object]:
    return {
        "code": error.code.value,
        "message": error.message,
        "sku_id": error.sku_id,
        "course": error.course.value if error.course is not None else None,
    }
