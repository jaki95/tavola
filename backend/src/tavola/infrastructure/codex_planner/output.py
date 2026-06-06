import json
from typing import Any

from tavola.application.planner import MenuPlannerAgentResponse
from tavola.domain.planner import FollowUpQuestion
from tavola.infrastructure.codex_planner.sdk_client import CodexSdkRunResult


def parse_final_output(
    run_result: CodexSdkRunResult,
) -> tuple[MenuPlannerAgentResponse | None, str]:
    try:
        raw_output = json.loads(run_result.final_output)
    except json.JSONDecodeError:
        return None, "Planner returned malformed proposal JSON."
    if not isinstance(raw_output, dict):
        return None, "Planner proposal JSON must be an object."

    follow_up_question = raw_output.get("follow_up_question")
    if isinstance(follow_up_question, str) and follow_up_question.strip():
        return (
            MenuPlannerAgentResponse(
                follow_up_question=FollowUpQuestion(message=follow_up_question)
            ),
            "",
        )

    contract_error = _proposal_contract_error(raw_output)
    if contract_error is not None:
        return None, contract_error
    return MenuPlannerAgentResponse(raw_proposal=raw_output), ""


def _proposal_contract_error(raw_output: dict[str, Any]) -> str | None:
    required_fields = (
        "title",
        "explanation",
        "planner_notes",
        "party_size",
        "package_template_id",
        "courses",
    )
    if any(field not in raw_output for field in required_fields):
        return "Final output did not match Tavola's JSON contract."
    if not all(
        isinstance(raw_output[field], str)
        for field in ("title", "explanation", "package_template_id")
    ):
        return "Final output did not match Tavola's JSON contract."
    if not isinstance(raw_output["planner_notes"], list) or not all(
        isinstance(note, str) for note in raw_output["planner_notes"]
    ):
        return "Final output did not match Tavola's JSON contract."
    party_size = raw_output["party_size"]
    if party_size is not None and not isinstance(party_size, int):
        return "Final output did not match Tavola's JSON contract."
    courses = raw_output["courses"]
    if not isinstance(courses, list) or not courses:
        return "Final output did not match Tavola's JSON contract."
    for course in courses:
        if not _course_matches_contract(course):
            return "Final output did not match Tavola's JSON contract."
    warnings = raw_output.get("warnings", [])
    if not isinstance(warnings, list) or not all(
        isinstance(warning, str) for warning in warnings
    ):
        return "Final output did not match Tavola's JSON contract."
    return None


def _course_matches_contract(course: Any) -> bool:
    if not isinstance(course, dict):
        return False
    if not isinstance(course.get("course"), str):
        return False
    lines = course.get("lines")
    if not isinstance(lines, list) or not lines:
        return False
    return all(_line_matches_contract(line) for line in lines)


def _line_matches_contract(line: Any) -> bool:
    return (
        isinstance(line, dict)
        and isinstance(line.get("sku_id"), str)
        and isinstance(line.get("quantity"), int)
        and isinstance(line.get("rationale"), str)
    )
