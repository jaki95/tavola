import json
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from tavola.application.planner import (
    MenuPlannerAgentResponse,
    PlannerAgentError,
    PlannerAgentErrorCode,
)
from tavola.domain.planner import FollowUpQuestion

_PLANNER_MCP_SERVER_NAME = "tavola-planner-tools"
_REQUIRED_TOOL_NAMES = frozenset(
    {
        "list_package_templates",
        "search_catalog",
        "validate_menu_proposal",
    }
)


@dataclass(frozen=True, slots=True)
class CodexMcpServerConfig:
    name: str
    command: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CodexSdkRunResult:
    final_output: str
    tool_names: tuple[str, ...]
    tool_error: str | None = None


@dataclass(frozen=True, slots=True)
class PlannerTimingEvent:
    name: str
    elapsed_ms: int
    attributes: dict[str, object]


class PlannerTimingSink(Protocol):
    def __call__(self, event: PlannerTimingEvent) -> None: ...


class CodexSdkClient(Protocol):
    def run(
        self,
        *,
        prompt: str,
        model: str,
        sandbox_mode: str,
        reasoning_effort: str | None,
        mcp_servers: tuple[CodexMcpServerConfig, ...],
        timeout_seconds: float,
        timing_sink: PlannerTimingSink | None = None,
    ) -> CodexSdkRunResult:
        """Run one Codex task and return its final customer-safe output."""


class PythonCodexSdkClient:
    """Thin wrapper around the Python Codex SDK for one planner turn."""

    def __init__(
        self,
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        codex_factory: Any | None = None,
    ) -> None:
        self._cwd = cwd
        self._env = env
        self._codex_factory = codex_factory

    def run(
        self,
        *,
        prompt: str,
        model: str,
        sandbox_mode: str,
        reasoning_effort: str | None,
        mcp_servers: tuple[CodexMcpServerConfig, ...],
        timeout_seconds: float,
        timing_sink: PlannerTimingSink | None = None,
    ) -> CodexSdkRunResult:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            self._run_without_timeout,
            prompt=prompt,
            model=model,
            sandbox_mode=sandbox_mode,
            reasoning_effort=reasoning_effort,
            mcp_servers=mcp_servers,
            timing_sink=timing_sink,
        )
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError as error:
            future.cancel()
            raise TimeoutError from error
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _run_without_timeout(
        self,
        *,
        prompt: str,
        model: str,
        sandbox_mode: str,
        reasoning_effort: str | None,
        mcp_servers: tuple[CodexMcpServerConfig, ...],
        timing_sink: PlannerTimingSink | None,
    ) -> CodexSdkRunResult:
        if self._codex_factory is None:
            from openai_codex import ApprovalMode, Codex, CodexConfig, Sandbox
            from openai_codex.generated.v2_all import ReasoningEffort
        else:
            from openai_codex import ApprovalMode, CodexConfig, Sandbox
            from openai_codex.generated.v2_all import ReasoningEffort

        run_started_at = time.perf_counter()
        client_started_at = time.perf_counter()
        codex_config = CodexConfig(
            cwd=str(self._cwd) if self._cwd is not None else None,
            env=self._env,
            config_overrides=_mcp_config_overrides(mcp_servers),
        )
        codex = (
            self._codex_factory(codex_config)
            if self._codex_factory is not None
            else Codex(codex_config)
        )
        _emit_timing(
            timing_sink,
            "sdk_client_create",
            started_at=client_started_at,
            attributes={"mcp_server_count": len(mcp_servers)},
        )
        try:
            sandbox = _sdk_sandbox(Sandbox, sandbox_mode)
            thread_started_at = time.perf_counter()
            thread = codex.thread_start(
                approval_mode=ApprovalMode.auto_review,
                model=model,
                sandbox=sandbox,
                ephemeral=True,
            )
            _emit_timing(
                timing_sink,
                "sdk_thread_start",
                started_at=thread_started_at,
                attributes={},
            )
            turn_started_at = time.perf_counter()
            turn_result = thread.run(
                prompt,
                approval_mode=ApprovalMode.auto_review,
                effort=ReasoningEffort(reasoning_effort)
                if reasoning_effort is not None
                else None,
                model=model,
                sandbox=sandbox,
            )
            _emit_timing(
                timing_sink,
                "sdk_turn_run",
                started_at=turn_started_at,
                attributes={},
            )
            tool_error = None
            if getattr(turn_result, "error", None) is not None:
                tool_error = str(turn_result.error)
            tool_names = _extract_tool_names(getattr(turn_result, "items", ()))
            _emit_timing(
                timing_sink,
                "tool_names_detected",
                started_at=run_started_at,
                attributes={"tool_names": tool_names},
            )
            return CodexSdkRunResult(
                final_output=getattr(turn_result, "final_response", None) or "",
                tool_names=tool_names,
                tool_error=tool_error,
            )
        finally:
            close = getattr(codex, "close", None)
            if callable(close):
                close()


@dataclass(frozen=True, slots=True)
class FakeMenuPlannerAgent:
    response: MenuPlannerAgentResponse

    @classmethod
    def with_follow_up(cls, question: FollowUpQuestion) -> "FakeMenuPlannerAgent":
        return cls(MenuPlannerAgentResponse(follow_up_question=question))

    @classmethod
    def with_proposal(cls, raw_proposal: dict[str, Any]) -> "FakeMenuPlannerAgent":
        return cls(MenuPlannerAgentResponse(raw_proposal=raw_proposal))

    @classmethod
    def with_failure(
        cls, code: PlannerAgentErrorCode, message: str
    ) -> "FakeMenuPlannerAgent":
        return cls(
            MenuPlannerAgentResponse(
                failure=PlannerAgentError(code=code, message=message)
            )
        )

    def plan_menu(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
    ) -> MenuPlannerAgentResponse:
        return self.response


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
        timeout_seconds: float = 60.0,
        max_retries: int = 0,
        timing_sink: PlannerTimingSink | None = None,
        mcp_server_command: tuple[str, ...] = (
            "python",
            "-m",
            "tavola.infrastructure.planner_mcp_server",
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

    def plan_menu(
        self,
        *,
        customer_request: str,
        follow_up_answers: tuple[str, ...] = (),
    ) -> MenuPlannerAgentResponse:
        run_started_at = time.perf_counter()
        prompt = _build_planner_prompt(customer_request, follow_up_answers)
        malformed_failure = _failure(
            PlannerAgentErrorCode.MALFORMED_OUTPUT,
            "Planner returned malformed proposal JSON.",
        )
        repair_attempts = 0
        for attempt in range(self._max_retries + 1):
            try:
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
                _emit_timing(
                    self._timing_sink,
                    "timeout",
                    started_at=run_started_at,
                    attributes={"timeout_seconds": self._timeout_seconds},
                )
                _emit_total_timing(
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
                _emit_total_timing(
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
                _emit_total_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    response=response,
                    repair_attempts=repair_attempts,
                )
                return response
            if not _used_required_tools(run_result.tool_names):
                response = _failure(
                    PlannerAgentErrorCode.MISSING_TOOL_USE,
                    "Planner did not verify catalog and pricing with Tavola checks.",
                )
                _emit_parse_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    result="missing_tool_use",
                )
                _emit_total_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    response=response,
                    repair_attempts=repair_attempts,
                )
                return response

            parsed_response, repair_reason = _parse_final_output(run_result)
            if parsed_response is not None:
                _emit_parse_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    result=_response_status(parsed_response),
                )
                _emit_total_timing(
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
            _emit_parse_timing(
                self._timing_sink,
                started_at=run_started_at,
                result="malformed_output",
            )
            if attempt >= self._max_retries:
                _emit_total_timing(
                    self._timing_sink,
                    started_at=run_started_at,
                    response=malformed_failure,
                    repair_attempts=repair_attempts,
                )
                return malformed_failure
            repair_attempts += 1
            _emit_timing(
                self._timing_sink,
                "repair_attempt",
                started_at=run_started_at,
                attributes={"repair_attempts": repair_attempts},
            )
            prompt = _build_repair_prompt(
                customer_request=customer_request,
                follow_up_answers=follow_up_answers,
                repair_reason=repair_reason,
            )

        _emit_total_timing(
            self._timing_sink,
            started_at=run_started_at,
            response=malformed_failure,
            repair_attempts=repair_attempts,
        )
        return malformed_failure


def _build_planner_prompt(
    customer_request: str,
    follow_up_answers: tuple[str, ...] = (),
) -> str:
    follow_up_text = (
        "\n".join(f"- {answer}" for answer in follow_up_answers)
        or "No follow-up answers yet."
    )
    return "\n".join(
        (
            "You are Tavola's Planner for a small Italian deli.",
            "Minimum contract: choose a menu structure with list_package_templates; "
            "call search_catalog and validate_menu_proposal before any menu proposal.",
            "If party size is missing, ask one follow-up question instead of "
            "guessing quantities.",
            "Use search_catalog summaries for product names, units, prices, "
            "availability, dietary facets, and short descriptions.",
            "Call get_sku_detail only when a chosen product needs extra detail.",
            "Do not invent products or prices; Tavola validation owns SKU "
            "validity, availability, quantities, and totals.",
            "In customer-facing text, say menu structure or course structure; "
            "do not mention templates.",
            "Apply supported vegetarian, vegan, gluten-free, no-alcohol, and "
            "budget constraints honestly. Explain unsupported constraints.",
            "Final JSON contract:",
            '{ "follow_up_question": string } OR',
            '{ "title": string, "explanation": string, '
            '"planner_notes": string[], "party_size": number | null, '
            '"package_template_id": string, "courses": [ { "course": string, '
            '"lines": [ { "sku_id": string, "quantity": number, '
            '"rationale": string } ] } ], "warnings"?: string[] }',
            "Return one JSON object only, without Markdown or commentary.",
            "Customer request:",
            customer_request,
            "Follow-up answers:",
            follow_up_text,
        )
    )


def _build_repair_prompt(
    *,
    customer_request: str,
    follow_up_answers: tuple[str, ...],
    repair_reason: str,
) -> str:
    return "\n".join(
        (
            _build_planner_prompt(customer_request, follow_up_answers),
            "Repair your previous planner output.",
            repair_reason,
            "Do not repeat invalid JSON, Markdown, stack traces, credentials, "
            "or tool transcripts.",
            "Return one corrected JSON object that matches the Final JSON contract.",
        )
    )


def _parse_final_output(
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


def _used_required_tools(tool_names: tuple[str, ...]) -> bool:
    return _REQUIRED_TOOL_NAMES.issubset(frozenset(tool_names))


def _mcp_config_overrides(
    mcp_servers: tuple[CodexMcpServerConfig, ...],
) -> tuple[str, ...]:
    overrides: list[str] = []
    for server in mcp_servers:
        command, *args = server.command
        key = f"mcp_servers.{server.name}"
        overrides.append(f"{key}.command={json.dumps(command)}")
        overrides.append(f"{key}.args={json.dumps(args)}")
    return tuple(overrides)


def _sdk_sandbox(sandbox_type: Any, sandbox_mode: str) -> Any:
    if sandbox_mode == "read-only":
        return sandbox_type.read_only
    if sandbox_mode == "workspace-write":
        return sandbox_type.workspace_write
    if sandbox_mode == "danger-full-access":
        return sandbox_type.full_access
    raise ValueError(f"unsupported Codex sandbox mode: {sandbox_mode}")


def _extract_tool_names(items: Any) -> tuple[str, ...]:
    tool_names: list[str] = []
    for item in items or ():
        name = _tool_name_for_item(item)
        if isinstance(name, str) and name not in tool_names:
            tool_names.append(name)
    return tuple(tool_names)


def _tool_name_for_item(item: Any) -> str | None:
    candidates = (item, _item_value(item, "root"))
    for candidate in candidates:
        if candidate is None:
            continue
        for key in ("tool_name", "name", "tool"):
            value = _item_value(candidate, key)
            if isinstance(value, str):
                return value
    return None


def _item_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _emit_timing(
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


def _emit_parse_timing(
    timing_sink: PlannerTimingSink | None,
    *,
    started_at: float,
    result: str,
) -> None:
    _emit_timing(
        timing_sink,
        "parse_result",
        started_at=started_at,
        attributes={"result": result},
    )


def _emit_total_timing(
    timing_sink: PlannerTimingSink | None,
    *,
    started_at: float,
    response: MenuPlannerAgentResponse,
    repair_attempts: int,
) -> None:
    _emit_timing(
        timing_sink,
        "total_elapsed",
        started_at=started_at,
        attributes={
            "status": _response_status(response),
            "repair_attempts": repair_attempts,
        },
    )


def _response_status(response: MenuPlannerAgentResponse) -> str:
    if response.raw_proposal is not None:
        return "proposal_ready"
    if response.follow_up_question is not None:
        return "needs_input"
    if response.failure is not None:
        return response.failure.code.value
    return "unknown"


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
