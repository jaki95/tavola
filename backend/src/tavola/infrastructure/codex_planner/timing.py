import time
from dataclasses import dataclass
from typing import Protocol

from tavola.application.planner import MenuPlannerAgentResponse


@dataclass(frozen=True, slots=True)
class PlannerTimingEvent:
    name: str
    elapsed_ms: int
    attributes: dict[str, object]


class PlannerTimingSink(Protocol):
    def __call__(self, event: PlannerTimingEvent) -> None: ...


def emit_timing(
    timing_sink: PlannerTimingSink | None,
    name: str,
    *,
    started_at: float,
    attributes: dict[str, object],
) -> None:
    if timing_sink is None:
        return
    timing_sink(
        PlannerTimingEvent(
            name=name,
            elapsed_ms=max(0, round((time.perf_counter() - started_at) * 1000)),
            attributes=attributes,
        )
    )


def emit_parse_timing(
    timing_sink: PlannerTimingSink | None,
    *,
    started_at: float,
    result: str,
) -> None:
    emit_timing(
        timing_sink,
        "parse_result",
        started_at=started_at,
        attributes={"result": result},
    )


def emit_total_timing(
    timing_sink: PlannerTimingSink | None,
    *,
    started_at: float,
    response: MenuPlannerAgentResponse,
    repair_attempts: int,
) -> None:
    emit_timing(
        timing_sink,
        "total_elapsed",
        started_at=started_at,
        attributes={
            "status": response_status(response),
            "repair_attempts": repair_attempts,
        },
    )


def response_status(response: MenuPlannerAgentResponse) -> str:
    if response.raw_proposal is not None:
        return "proposal_ready"
    if response.follow_up_question is not None:
        return "needs_input"
    if response.failure is not None:
        return response.failure.code.value
    return "unknown"
