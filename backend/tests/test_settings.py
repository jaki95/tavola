import pytest

from tavola.config.settings import MissingPlannerCodexCredentialsError, Settings


def test_settings_defaults_are_local_development_friendly() -> None:
    settings = Settings()

    assert settings.app_name == "Tavola API"
    assert settings.environment == "local"
    assert settings.api_prefix == "/api"
    assert settings.planner_codex_enabled is False
    assert settings.planner_codex_model == "gpt-5.2-codex"
    assert settings.planner_codex_sandbox_mode == "read-only"
    assert settings.planner_codex_timeout_seconds == 60
    assert settings.planner_codex_max_retries == 1
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
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_TIMEOUT_SECONDS", "120")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_MAX_RETRIES", "3")
    monkeypatch.setenv("TAVOLA_PLANNER_CODEX_MISSING_CREDENTIALS", "error")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    settings = Settings()

    assert settings.planner_codex_enabled is True
    assert settings.planner_codex_model == "gpt-test-codex"
    assert settings.planner_codex_sandbox_mode == "workspace-write"
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


def test_missing_codex_credentials_default_to_fake_planner(
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
