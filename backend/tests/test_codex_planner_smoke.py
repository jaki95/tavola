import pytest

from tavola.config.settings import Settings
from tavola.infrastructure.codex_planner import PlannerTimingEvent
from tavola.infrastructure.codex_planner_smoke import (
    BenchmarkRun,
    _benchmark_classification,
    _benchmark_payload,
    _benchmark_summary,
    main,
)


def test_benchmark_classifies_ideal_acceptable_and_slow_runs() -> None:
    assert _benchmark_classification(9_999) == "ideal"
    assert _benchmark_classification(10_000) == "acceptable"
    assert _benchmark_classification(29_999) == "acceptable"
    assert _benchmark_classification(30_000) == "slow"


def test_benchmark_summary_reports_min_median_max_totals() -> None:
    runs = [
        _benchmark_run(iteration=1, total_elapsed_ms=32_000),
        _benchmark_run(iteration=2, total_elapsed_ms=8_000),
        _benchmark_run(iteration=3, total_elapsed_ms=18_000),
    ]

    summary = _benchmark_summary(runs)

    assert summary == {
        "successful_runs": 3,
        "failed_runs": 0,
        "ideal_runs": 1,
        "acceptable_runs": 1,
        "slow_runs": 1,
        "min_total_elapsed_ms": 8_000,
        "median_total_elapsed_ms": 18_000,
        "max_total_elapsed_ms": 32_000,
    }


def test_benchmark_payload_omits_proposals_by_default() -> None:
    payload = _benchmark_payload(
        [_benchmark_run(iteration=1, total_elapsed_ms=11_000)],
        settings=Settings(),
        include_proposal=False,
    )

    assert payload["mode"] == "benchmark"
    assert payload["reasoning_effort"] == "low"
    assert payload["thresholds"] == {"ideal_ms": 10_000, "acceptable_ms": 30_000}
    runs = payload["runs"]
    assert isinstance(runs, list)
    assert "proposal" not in runs[0]


def test_repeat_must_be_positive() -> None:
    with pytest.raises(SystemExit) as error:
        main(["--benchmark", "--repeat", "0", "Dinner for two"])

    assert error.value.code == 2


def test_repeat_greater_than_one_requires_benchmark_mode() -> None:
    with pytest.raises(SystemExit) as error:
        main(["--repeat", "2", "Dinner for two"])

    assert error.value.code == 2


def _benchmark_run(*, iteration: int, total_elapsed_ms: int) -> BenchmarkRun:
    benchmark = _benchmark_classification(total_elapsed_ms)
    return BenchmarkRun(
        iteration=iteration,
        status="proposal_ready",
        total_elapsed_ms=total_elapsed_ms,
        benchmark=benchmark,
        hit_ideal=total_elapsed_ms < 10_000,
        hit_acceptable=total_elapsed_ms < 30_000,
        timing_events=[
            PlannerTimingEvent(
                name="total_elapsed",
                elapsed_ms=total_elapsed_ms,
                attributes={"status": "proposal_ready", "repair_attempts": 0},
            )
        ],
        proposal=None,
        agent_error=None,
        validation_errors=[],
    )
