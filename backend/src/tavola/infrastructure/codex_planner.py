import json
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
        "get_sku_detail",
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


class CodexSdkClient(Protocol):
    def run(
        self,
        *,
        prompt: str,
        model: str,
        sandbox_mode: str,
        mcp_servers: tuple[CodexMcpServerConfig, ...],
        timeout_seconds: float,
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
        mcp_servers: tuple[CodexMcpServerConfig, ...],
        timeout_seconds: float,
    ) -> CodexSdkRunResult:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            self._run_without_timeout,
            prompt=prompt,
            model=model,
            sandbox_mode=sandbox_mode,
            mcp_servers=mcp_servers,
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
        mcp_servers: tuple[CodexMcpServerConfig, ...],
    ) -> CodexSdkRunResult:
        if self._codex_factory is None:
            from openai_codex import ApprovalMode, Codex, CodexConfig, Sandbox
        else:
            from openai_codex import ApprovalMode, CodexConfig, Sandbox

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
        try:
            sandbox = _sdk_sandbox(Sandbox, sandbox_mode)
            thread = codex.thread_start(
                approval_mode=ApprovalMode.deny_all,
                model=model,
                sandbox=sandbox,
                ephemeral=True,
            )
            turn_result = thread.run(
                prompt,
                approval_mode=ApprovalMode.deny_all,
                model=model,
                sandbox=sandbox,
            )
            tool_error = None
            if getattr(turn_result, "error", None) is not None:
                tool_error = str(turn_result.error)
            return CodexSdkRunResult(
                final_output=getattr(turn_result, "final_response", None) or "",
                tool_names=_extract_tool_names(getattr(turn_result, "items", ())),
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
        timeout_seconds: float = 60.0,
        max_retries: int = 1,
        mcp_server_command: tuple[str, ...] = (
            "python",
            "-m",
            "tavola.infrastructure.planner_mcp_server",
        ),
    ) -> None:
        self._client = client
        self._model = model
        self._sandbox_mode = sandbox_mode
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
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
        prompt = _build_planner_prompt(customer_request, follow_up_answers)
        malformed_failure = _failure(
            PlannerAgentErrorCode.MALFORMED_OUTPUT,
            "Planner returned malformed proposal JSON.",
        )
        for attempt in range(self._max_retries + 1):
            try:
                run_result = self._client.run(
                    prompt=prompt,
                    model=self._model,
                    sandbox_mode=self._sandbox_mode,
                    mcp_servers=self._mcp_servers,
                    timeout_seconds=self._timeout_seconds,
                )
            except TimeoutError:
                return _failure(
                    PlannerAgentErrorCode.TIMEOUT,
                    "Planner run timed out before Tavola could validate a proposal.",
                )
            except Exception:
                return _failure(
                    PlannerAgentErrorCode.TOOL_FAILURE,
                    "Planner run failed before Tavola could validate a proposal.",
                )

            if run_result.tool_error is not None:
                return _failure(
                    PlannerAgentErrorCode.TOOL_FAILURE,
                    "Planner tool execution failed before Tavola could validate "
                    "a proposal.",
                )
            if not _used_required_tools(run_result.tool_names):
                return _failure(
                    PlannerAgentErrorCode.MISSING_TOOL_USE,
                    "Planner did not verify catalog and pricing with Tavola tools.",
                )

            parsed_response, repair_reason = _parse_final_output(run_result)
            if parsed_response is not None:
                return parsed_response

            malformed_failure = _failure(
                PlannerAgentErrorCode.MALFORMED_OUTPUT,
                repair_reason,
            )
            if attempt >= self._max_retries:
                return malformed_failure
            prompt = _build_repair_prompt(
                customer_request=customer_request,
                follow_up_answers=follow_up_answers,
                repair_reason=repair_reason,
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
            "Use only Tavola MCP tools before proposing products.",
            "Call list_package_templates before choosing a package template.",
            "Call search_catalog and get_sku_detail before selecting products.",
            "Call validate_menu_proposal before returning final JSON.",
            "SKU validity, availability, quantities, and totals must come from "
            "Tavola tools.",
            "Final JSON contract:",
            '{ "title": string, "explanation": string, '
            '"planner_notes": string[], "party_size": number | null, '
            '"package_template_id": string, "courses": [ { "course": string, '
            '"lines": [ { "sku_id": string, "quantity": number, '
            '"rationale": string } ] } ], "warnings"?: string[] }',
            "Return JSON only, without Markdown or commentary.",
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
