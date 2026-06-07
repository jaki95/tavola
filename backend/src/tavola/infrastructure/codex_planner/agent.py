import time

from tavola.application.planner import (
    MenuPlannerAgentResponse,
    PlannerAgentError,
    PlannerAgentErrorCode,
)
from tavola.domain.planner import PlannerValidationError
from tavola.infrastructure.codex_planner.output import parse_final_output
from tavola.infrastructure.codex_planner.prompt import (
    build_planner_prompt,
    build_repair_prompt,
    build_validation_repair_prompt,
)
from tavola.infrastructure.codex_planner.sdk_client import (
    CodexMcpServerConfig,
    CodexSdkClient,
)
from tavola.infrastructure.codex_planner.timing import (
    PlannerTimingSink,
    emit_lifecycle_timing,
    emit_parse_timing,
    emit_timing,
    emit_total_timing,
    response_status,
)

_PLANNER_MCP_SERVER_NAME = "tavola-planner-tools"


class CodexMenuPlannerAgent:
    """Codex-backed planner adapter shell.

    The real SDK client is injected so application tests can prove the Tavola
    contract without local credentials. Codex imports stay in infrastructure.
    """

    def __init__(
        self,
        *,
        client: CodexSdkClient,
        model: str,
        sandbox_mode: str = "read-only",
        reasoning_effort: str | None = None,
        timeout_seconds: float = 120.0,
        max_retries: int = 0,
        timing_sink: PlannerTimingSink | None = None,
        mcp_server_command: tuple[str, ...] = (
            "python",
            "-m",
            "tavola.infrastructure.planner_catalog_mcp_server",
        ),
    ) -> None:
        self._client = client
        self._model = model
        self._sandbox_mode = sandbox_mode
        self._reasoning_effort = reasoning_effort
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._timing_sink = timing_sink
        self._mcp_servers = (
            CodexMcpServerConfig(
                name=_PLANNER_MCP_SERVER_NAME,
                command=mcp_server_command,
            ),
        )
        self._mcp_server_command = mcp_server_command

    def with_timing_sink(
        self,
        timing_sink: PlannerTimingSink | None,
    ) -> "CodexMenuPlannerAgent":
        return CodexMenuPlannerAgent(
            client=self._client,
            model=self._model,
            sandbox_mode=self._sandbox_mode,
            reasoning_effort=self._reasoning_effort,
            timeout_seconds=self._timeout_seconds,
            max_retries=self._max_retries,
            timing_sink=timing_sink,
            mcp_server_command=self._mcp_server_command,
        )

    def plan_menu(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
    ) -> MenuPlannerAgentResponse:
        run_started_at = time.perf_counter()
        prompt = build_planner_prompt(customer_request, follow_up_answers)
        malformed_failure = _failure(
            PlannerAgentErrorCode.MALFORMED_OUTPUT,
            "Planner returned malformed proposal JSON.",
        )
        repair_attempts = 0
        for attempt in range(self._max_retries + 1):
            try:
                emit_lifecycle_timing(
                    self._timing_sink,
                    "connecting",
                    started_at=run_started_at,
                )
                run_result = self._client.run(
                    prompt=prompt,
                    model=self._model,
                    sandbox_mode=self._sandbox_mode,
                    reasoning_effort=self._reasoning_effort,
                    mcp_servers=self._mcp_servers,
                    timeout_seconds=self._timeout_seconds,
                    timing_sink=self._timing_sink,
                )
            except TimeoutError:
                response = _failure(
                    PlannerAgentErrorCode.TIMEOUT,
                    "Planner run timed out before Tavola could validate a proposal.",
                )
                emit_timing(
                    self._timing_sink,
                    "timeout",
                    started_at=run_started_at,
                    attributes={"timeout_seconds": self._timeout_seconds},
                )
                emit_total_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    response=response,
                    repair_attempts=repair_attempts,
                )
                return response
            except Exception:
                response = _failure(
                    PlannerAgentErrorCode.TOOL_FAILURE,
                    "Planner run failed before Tavola could validate a proposal.",
                )
                emit_total_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    response=response,
                    repair_attempts=repair_attempts,
                )
                return response

            if run_result.tool_error is not None:
                response = _failure(
                    PlannerAgentErrorCode.TOOL_FAILURE,
                    "Planner checks failed before Tavola could validate a proposal.",
                )
                emit_total_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    response=response,
                    repair_attempts=repair_attempts,
                )
                return response

            parsed_response, repair_reason = parse_final_output(run_result)

            if parsed_response is not None:
                emit_parse_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    result=response_status(parsed_response),
                )
                emit_total_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    response=parsed_response,
                    repair_attempts=repair_attempts,
                )
                return parsed_response

            malformed_failure = _failure(
                PlannerAgentErrorCode.MALFORMED_OUTPUT,
                repair_reason,
            )
            emit_parse_timing(
                self._timing_sink,
                started_at=run_started_at,
                result="malformed_output",
            )
            if attempt >= self._max_retries:
                emit_total_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    response=malformed_failure,
                    repair_attempts=repair_attempts,
                )
                return malformed_failure
            repair_attempts += 1
            emit_timing(
                self._timing_sink,
                "repair_attempt",
                started_at=run_started_at,
                attributes={"repair_attempts": repair_attempts},
            )
            prompt = build_repair_prompt(
                customer_request=customer_request,
                follow_up_answers=follow_up_answers,
                repair_reason=repair_reason,
            )

        emit_total_timing(
            self._timing_sink,
            started_at=run_started_at,
            response=malformed_failure,
            repair_attempts=repair_attempts,
        )
        return malformed_failure

    def repair_menu(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
        raw_proposal: dict[str, object],
        validation_errors: tuple[PlannerValidationError, ...],
    ) -> MenuPlannerAgentResponse:
        run_started_at = time.perf_counter()
        prompt = build_validation_repair_prompt(
            customer_request=customer_request,
            follow_up_answers=follow_up_answers,
            raw_proposal=raw_proposal,
            validation_errors=validation_errors,
        )
        try:
            emit_lifecycle_timing(
                self._timing_sink,
                "connecting",
                started_at=run_started_at,
            )
            run_result = self._client.run(
                prompt=prompt,
                model=self._model,
                sandbox_mode=self._sandbox_mode,
                reasoning_effort=self._reasoning_effort,
                mcp_servers=self._mcp_servers,
                timeout_seconds=self._timeout_seconds,
                timing_sink=self._timing_sink,
            )
        except TimeoutError:
            response = _failure(
                PlannerAgentErrorCode.TIMEOUT,
                "Planner repair timed out before Tavola could validate a proposal.",
            )
            emit_timing(
                self._timing_sink,
                "timeout",
                started_at=run_started_at,
                attributes={"timeout_seconds": self._timeout_seconds},
            )
            emit_total_timing(
                self._timing_sink,
                started_at=run_started_at,
                response=response,
                repair_attempts=0,
            )
            return response
        except Exception:
            response = _failure(
                PlannerAgentErrorCode.TOOL_FAILURE,
                "Planner repair failed before Tavola could validate a proposal.",
            )
            emit_total_timing(
                self._timing_sink,
                started_at=run_started_at,
                response=response,
                repair_attempts=0,
            )
            return response

        if run_result.tool_error is not None:
            response = _failure(
                PlannerAgentErrorCode.TOOL_FAILURE,
                "Planner repair checks failed before Tavola could validate a proposal.",
            )
            emit_total_timing(
                self._timing_sink,
                started_at=run_started_at,
                response=response,
                repair_attempts=0,
            )
            return response

        parsed_response, repair_reason = parse_final_output(run_result)

        if parsed_response is not None:
            emit_parse_timing(
                self._timing_sink,
                started_at=run_started_at,
                result=response_status(parsed_response),
            )
            emit_total_timing(
                self._timing_sink,
                started_at=run_started_at,
                response=parsed_response,
                repair_attempts=0,
            )
            return parsed_response

        response = _failure(PlannerAgentErrorCode.MALFORMED_OUTPUT, repair_reason)
        emit_parse_timing(
            self._timing_sink,
            started_at=run_started_at,
            result="malformed_output",
        )
        emit_total_timing(
            self._timing_sink,
            started_at=run_started_at,
            response=response,
            repair_attempts=0,
        )
        return response


def _failure(
    code: PlannerAgentErrorCode,
    message: str,
) -> MenuPlannerAgentResponse:
    return MenuPlannerAgentResponse(
        failure=PlannerAgentError(
            code=code,
            message=message,
        )
    )
