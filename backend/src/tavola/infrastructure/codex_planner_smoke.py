import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from tavola.application.planner import PlanMenuFromRequest
from tavola.config.settings import (
    MissingPlannerCodexCredentialsError,
    Settings,
)
from tavola.domain.planner import ProposalStatus, ValidatedMenuProposal
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.codex_planner import (
    CodexMenuPlannerAgent,
    PlannerTimingEvent,
    PythonCodexSdkClient,
)


@dataclass(frozen=True, slots=True)
class BenchmarkRun:
    iteration: int
    status: str
    total_elapsed_ms: int
    benchmark: str
    hit_ideal: bool
    hit_acceptable: bool
    timing_events: list[PlannerTimingEvent]
    proposal: ValidatedMenuProposal | None
    agent_error: str | None
    validation_errors: list[dict[str, str]]

    @property
    def succeeded(self) -> bool:
        return self.status == ProposalStatus.PROPOSAL_READY.value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one opt-in real Codex planner smoke against seed catalog."
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Print safe timing summaries instead of proposal JSON.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of benchmark runs to execute. Requires --benchmark for repeats.",
    )
    parser.add_argument(
        "--show-proposal",
        action="store_true",
        help="Include validated proposal output. Off by default in benchmark mode.",
    )
    parser.add_argument("message", help="Customer meal request for Tavola Planner.")
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat must be greater than zero")
    if args.repeat > 1 and not args.benchmark:
        parser.error("--repeat greater than 1 requires --benchmark")

    settings = Settings()
    try:
        if not settings.use_real_codex_planner():
            print(
                "Real Codex planner is disabled or credentials are missing.",
                file=sys.stderr,
            )
            return 2
    except MissingPlannerCodexCredentialsError as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.benchmark:
        runs = [
            _run_benchmark_iteration(args.message, settings, iteration)
            for iteration in range(1, args.repeat + 1)
        ]
        print(
            json.dumps(
                _benchmark_payload(
                    runs,
                    settings=settings,
                    include_proposal=args.show_proposal,
                ),
                indent=2,
            )
        )
        return 0 if all(run.succeeded for run in runs) else 1

    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=PythonCodexSdkClient(cwd=Path.cwd()),
            model=settings.planner_codex_model,
            sandbox_mode=settings.planner_codex_sandbox_mode,
            timeout_seconds=settings.planner_codex_timeout_seconds,
            max_retries=settings.planner_codex_max_retries,
        ),
        catalog_repository=StaticCatalogRepository.from_seed(),
    )
    result = planner(customer_request=args.message)
    if result.status != ProposalStatus.PROPOSAL_READY or result.menu_proposal is None:
        payload = {
            "status": result.status.value,
            "validation_errors": [
                {"code": error.code.value, "message": error.message}
                for error in result.validation_errors
            ],
            "agent_error": result.agent_error.code.value
            if result.agent_error is not None
            else None,
        }
        print(json.dumps(payload, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(_proposal_payload(result.menu_proposal), indent=2))
    return 0


def _run_benchmark_iteration(
    message: str,
    settings: Settings,
    iteration: int,
) -> BenchmarkRun:
    events: list[PlannerTimingEvent] = []
    planner = PlanMenuFromRequest(
        agent=CodexMenuPlannerAgent(
            client=PythonCodexSdkClient(cwd=Path.cwd()),
            model=settings.planner_codex_model,
            sandbox_mode=settings.planner_codex_sandbox_mode,
            timeout_seconds=settings.planner_codex_timeout_seconds,
            max_retries=settings.planner_codex_max_retries,
            timing_sink=events.append,
        ),
        catalog_repository=StaticCatalogRepository.from_seed(),
    )
    started_at = time.perf_counter()
    result = planner(customer_request=message)
    fallback_elapsed_ms = round((time.perf_counter() - started_at) * 1000)
    total_elapsed_ms = _total_elapsed_ms(events) or fallback_elapsed_ms
    proposal = (
        result.menu_proposal if result.status == ProposalStatus.PROPOSAL_READY else None
    )
    return BenchmarkRun(
        iteration=iteration,
        status=result.status.value,
        total_elapsed_ms=total_elapsed_ms,
        benchmark=_benchmark_classification(total_elapsed_ms),
        hit_ideal=total_elapsed_ms < 10_000,
        hit_acceptable=total_elapsed_ms < 30_000,
        timing_events=events,
        proposal=proposal,
        agent_error=result.agent_error.code.value
        if result.agent_error is not None
        else None,
        validation_errors=[
            {"code": error.code.value, "message": error.message}
            for error in result.validation_errors
        ],
    )


def _benchmark_payload(
    runs: list[BenchmarkRun],
    *,
    settings: Settings,
    include_proposal: bool,
) -> dict[str, object]:
    return {
        "mode": "benchmark",
        "model": settings.planner_codex_model,
        "timeout_seconds": settings.planner_codex_timeout_seconds,
        "max_retries": settings.planner_codex_max_retries,
        "repeat": len(runs),
        "thresholds": {
            "ideal_ms": 10_000,
            "acceptable_ms": 30_000,
        },
        "runs": [
            _benchmark_run_payload(run, include_proposal=include_proposal)
            for run in runs
        ],
        "summary": _benchmark_summary(runs),
    }


def _benchmark_run_payload(
    run: BenchmarkRun,
    *,
    include_proposal: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "iteration": run.iteration,
        "status": run.status,
        "total_elapsed_ms": run.total_elapsed_ms,
        "benchmark": run.benchmark,
        "hit_ideal": run.hit_ideal,
        "hit_acceptable": run.hit_acceptable,
        "timing_events": [_timing_event_payload(event) for event in run.timing_events],
        "agent_error": run.agent_error,
        "validation_errors": run.validation_errors,
    }
    if include_proposal and run.proposal is not None:
        payload["proposal"] = _proposal_payload(run.proposal)
    return payload


def _benchmark_summary(runs: list[BenchmarkRun]) -> dict[str, object]:
    totals = [run.total_elapsed_ms for run in runs]
    return {
        "successful_runs": sum(run.succeeded for run in runs),
        "failed_runs": sum(not run.succeeded for run in runs),
        "ideal_runs": sum(run.benchmark == "ideal" for run in runs),
        "acceptable_runs": sum(run.benchmark == "acceptable" for run in runs),
        "slow_runs": sum(run.benchmark == "slow" for run in runs),
        "min_total_elapsed_ms": min(totals),
        "median_total_elapsed_ms": round(statistics.median(totals)),
        "max_total_elapsed_ms": max(totals),
    }


def _timing_event_payload(event: PlannerTimingEvent) -> dict[str, object]:
    return {
        "name": event.name,
        "elapsed_ms": event.elapsed_ms,
        "attributes": event.attributes,
    }


def _total_elapsed_ms(events: list[PlannerTimingEvent]) -> int | None:
    for event in reversed(events):
        if event.name == "total_elapsed":
            return event.elapsed_ms
    return None


def _benchmark_classification(total_elapsed_ms: int) -> str:
    if total_elapsed_ms < 10_000:
        return "ideal"
    if total_elapsed_ms < 30_000:
        return "acceptable"
    return "slow"


def _proposal_payload(proposal: ValidatedMenuProposal) -> dict[str, object]:
    return {
        "title": proposal.title,
        "explanation": proposal.explanation,
        "planner_notes": list(proposal.planner_notes),
        "party_size": proposal.party_size,
        "package_template_id": proposal.package_template_id,
        "courses": [
            {
                "course": course.course.value,
                "lines": [
                    {
                        "sku_id": line.sku.sku_id,
                        "name": line.sku.name,
                        "quantity": line.quantity,
                        "unit_label": line.sku.unit_label,
                        "unit_price_minor": line.sku.price.amount_minor,
                        "line_total_minor": line.line_total.amount_minor,
                        "rationale": line.rationale,
                    }
                    for line in course.lines
                ],
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


if __name__ == "__main__":
    raise SystemExit(main())
