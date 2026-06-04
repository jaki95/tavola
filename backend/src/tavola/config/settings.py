import os
from dataclasses import dataclass, field
from typing import Literal

CodexSandboxMode = Literal["read-only", "workspace-write", "danger-full-access"]
MissingCredentialsBehavior = Literal["disable", "error"]
PlannerRuntimeMode = Literal["real_codex", "disabled"]


class MissingPlannerCodexCredentialsError(RuntimeError):
    """Raised when real Codex is required but no credential source is configured."""


@dataclass(frozen=True, slots=True)
class PlannerRuntimeStatus:
    enabled: bool
    mode: PlannerRuntimeMode
    message: str


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default

    normalized_value = raw_value.strip().lower()
    if normalized_value in {"1", "true", "yes", "on"}:
        return True
    if normalized_value in {"0", "false", "no", "off"}:
        return False

    msg = f"{name} must be a boolean value"
    raise ValueError(msg)


def _env_positive_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default

    value = int(raw_value)
    if value <= 0:
        msg = f"{name} must be greater than zero"
        raise ValueError(msg)
    return value


def _env_non_negative_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default

    value = int(raw_value)
    if value < 0:
        msg = f"{name} must be zero or greater"
        raise ValueError(msg)
    return value


def _env_codex_sandbox_mode() -> CodexSandboxMode:
    value = _env_str("TAVOLA_PLANNER_CODEX_SANDBOX_MODE", "read-only")
    allowed_values: tuple[CodexSandboxMode, ...] = (
        "read-only",
        "workspace-write",
        "danger-full-access",
    )
    if value not in allowed_values:
        msg = (
            "TAVOLA_PLANNER_CODEX_SANDBOX_MODE must be one of: read-only, "
            "workspace-write, danger-full-access"
        )
        raise ValueError(msg)
    return value


def _env_missing_credentials_behavior() -> MissingCredentialsBehavior:
    value = _env_str("TAVOLA_PLANNER_CODEX_MISSING_CREDENTIALS", "disable")
    allowed_values: tuple[MissingCredentialsBehavior, ...] = ("disable", "error")
    if value not in allowed_values:
        msg = "TAVOLA_PLANNER_CODEX_MISSING_CREDENTIALS must be one of: disable, error"
        raise ValueError(msg)
    return value


def _env_codex_credentials_configured() -> bool:
    if os.environ.get("OPENAI_API_KEY"):
        return True
    return _env_bool("TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED", False)


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = field(
        default_factory=lambda: _env_str("TAVOLA_APP_NAME", "Tavola API")
    )
    environment: str = field(
        default_factory=lambda: _env_str("TAVOLA_ENVIRONMENT", "local")
    )
    api_prefix: str = field(
        default_factory=lambda: _env_str("TAVOLA_API_PREFIX", "/api")
    )
    planner_codex_enabled: bool = field(
        default_factory=lambda: _env_bool("TAVOLA_PLANNER_CODEX_ENABLED", False)
    )
    planner_codex_model: str = field(
        default_factory=lambda: _env_str("TAVOLA_PLANNER_CODEX_MODEL", "gpt-5.5")
    )
    planner_codex_sandbox_mode: CodexSandboxMode = field(
        default_factory=_env_codex_sandbox_mode
    )
    planner_codex_timeout_seconds: int = field(
        default_factory=lambda: _env_positive_int(
            "TAVOLA_PLANNER_CODEX_TIMEOUT_SECONDS", 60
        )
    )
    planner_codex_max_retries: int = field(
        default_factory=lambda: _env_non_negative_int(
            "TAVOLA_PLANNER_CODEX_MAX_RETRIES", 1
        )
    )
    planner_codex_missing_credentials: MissingCredentialsBehavior = field(
        default_factory=_env_missing_credentials_behavior
    )
    planner_codex_credentials_configured: bool = field(
        default_factory=_env_codex_credentials_configured
    )

    def use_real_codex_planner(self) -> bool:
        if not self.planner_codex_enabled:
            return False
        if self.planner_codex_credentials_configured:
            return True
        if self.planner_codex_missing_credentials == "error":
            msg = (
                "Real Codex planner is enabled, but no Codex credential source "
                "is configured."
            )
            raise MissingPlannerCodexCredentialsError(msg)
        return False

    def planner_runtime_status(self) -> PlannerRuntimeStatus:
        if not self.planner_codex_enabled:
            return PlannerRuntimeStatus(
                enabled=False,
                mode="disabled",
                message="Planner is not enabled for this environment.",
            )
        if self.planner_codex_credentials_configured:
            return PlannerRuntimeStatus(
                enabled=True,
                mode="real_codex",
                message="Planner is running with live Codex assistance.",
            )
        return PlannerRuntimeStatus(
            enabled=False,
            mode="disabled",
            message="Planner needs local Codex access before live planning.",
        )
