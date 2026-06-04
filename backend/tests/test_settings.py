import pytest

from tavola.api.dependencies import get_menu_planner_agent
from tavola.config.settings import MissingPlannerCodexCredentialsError, Settings
from tavola.infrastructure.codex_planner import (
    CodexMenuPlannerAgent,
    FakeMenuPlannerAgent,
)


def test_settings_defaults_are_local_development_friendly() -> None:
    settings = Settings()

    assert settings.app_name == "Tavola API"
    assert settings.environment == "local"
    assert settings.api_prefix == "/api"
    assert settings.planner_codex_enabled is False
    assert settings.planner_codex_model == "gpt-5.5"
    assert settings.planner_codex_sandbox_mode == "read-only"
    assert settings.planner_codex_reasoning_effort == "low"
    assert settings.codex_sdk_reasoning_effort() == "low"
    assert settings.planner_codex_timeout_seconds == 60
    assert settings.planner_codex_max_retries == 0
    assert settings.planner_codex_missing_credentials == "disable"
    assert settings.planner_codex_credentials_configured is False
    assert settings.use_real_codex_planner() is False


def test_api_prefix_can_be_configured_at_construction() -> None:
    settings = Settings(api_prefix="/internal")

    assert settings.api_prefix == "/internal"


def test_planner_codex_settings_can_be_configured_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_ENABLED", "true")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_MODEL", "gpt-test-codex")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_SANDBOX_MODE", "workspace-write")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_REASONING_EFFORT", "minimal")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_TIMEOUT_SECONDS", "120")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_MAX_RETRIES", "3")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_MISSING_CREDENTIALS", "error")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    settings = Settings()

    assert settings.planner_codex_enabled is True
    assert settings.planner_codex_model == "gpt-test-codex"
    assert settings.planner_codex_sandbox_mode == "workspace-write"
    assert settings.planner_codex_reasoning_effort == "minimal"
    assert settings.codex_sdk_reasoning_effort() == "minimal"
    assert settings.planner_codex_timeout_seconds == 120
    assert settings.planner_codex_max_retries == 3
    assert settings.planner_codex_missing_credentials == "error"
    assert settings.planner_codex_credentials_configured is True
    assert settings.use_real_codex_planner() is True


def test_existing_codex_login_can_be_declared_without_committing_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_ENABLED", "true")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED", "true")

    settings = Settings()

    assert settings.planner_codex_credentials_configured is True
    assert settings.use_real_codex_planner() is True


def test_missing_codex_credentials_default_to_disabled_planner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_ENABLED", "true")

    settings = Settings()

    assert settings.use_real_codex_planner() is False


def test_missing_codex_credentials_can_raise_for_demo_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_ENABLED", "true")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_MISSING_CREDENTIALS", "error")

    settings = Settings()

    with pytest.raises(MissingPlannerCodexCredentialsError):
        settings.use_real_codex_planner()


def test_codex_reasoning_effort_can_use_sdk_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_REASONING_EFFORT", "sdk-default")

    settings = Settings()

    assert settings.planner_codex_reasoning_effort == "sdk-default"
    assert settings.codex_sdk_reasoning_effort() is None


def test_invalid_codex_reasoning_effort_fails_settings_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_REASONING_EFFORT", "faster-please")

    with pytest.raises(ValueError, match="TAVOLA_PLANNER_CODEX_REASONING_EFFORT"):
        Settings()


def test_planner_runtime_status_reports_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVOLA_PLANNER_CODEX_ENABLED", raising=False)
    monkeypatch.delenv("TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED", raising=False)

    status = Settings().planner_runtime_status()

    assert status.enabled is False
    assert status.mode == "disabled"
    assert status.message == "Planner is not enabled for this environment."


def test_planner_runtime_status_reports_disabled_when_real_mode_lacks_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_ENABLED", "true")

    status = Settings().planner_runtime_status()

    assert status.enabled is False
    assert status.mode == "disabled"
    assert status.message == "Planner needs local Codex access before live planning."


def test_planner_runtime_status_reports_real_codex_mode_when_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_ENABLED", "true")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED", "true")

    status = Settings().planner_runtime_status()

    assert status.enabled is True
    assert status.mode == "real_codex"
    assert status.message == "Planner is running with live Codex assistance."


def test_menu_planner_agent_dependency_uses_settings_for_real_codex(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_ENABLED", "true")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED", "true")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_MODEL", "codex-test-model")

    assert isinstance(get_menu_planner_agent(), CodexMenuPlannerAgent)


def test_menu_planner_agent_dependency_returns_disabled_agent_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TAVOLA_PLANNER_CODEX_ENABLED", raising=False)
    monkeypatch.delenv("TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED", raising=False)

    assert isinstance(get_menu_planner_agent(), FakeMenuPlannerAgent)


def test_menu_planner_agent_dependency_returns_disabled_agent_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_ENABLED", "true")
    monkeypatch.delenv("TAVOLA_PLANNER_CODEX_CREDENTIALS_CONFIGURED", raising=False)

    assert isinstance(get_menu_planner_agent(), FakeMenuPlannerAgent)
