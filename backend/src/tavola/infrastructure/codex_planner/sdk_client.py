import json
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from tavola.infrastructure.codex_planner.timing import (
    PlannerTimingSink,
    emit_lifecycle_timing,
    emit_timing,
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
        emit_timing(
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
            emit_timing(
                timing_sink,
                "sdk_thread_start",
                started_at=thread_started_at,
                attributes={},
            )
            turn_started_at = time.perf_counter()
            emit_lifecycle_timing(
                timing_sink,
                "planning",
                started_at=turn_started_at,
            )
            turn_result = thread.run(
                prompt,
                approval_mode=ApprovalMode.auto_review,
                effort=ReasoningEffort(reasoning_effort)
                if reasoning_effort is not None
                else None,
                model=model,
                sandbox=sandbox,
            )
            emit_timing(
                timing_sink,
                "sdk_turn_run",
                started_at=turn_started_at,
                attributes={},
            )
            tool_error = None
            if getattr(turn_result, "error", None) is not None:
                tool_error = str(turn_result.error)
            tool_names = _extract_tool_names(getattr(turn_result, "items", ()))
            emit_timing(
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
