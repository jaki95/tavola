from tavola.config.settings import Settings


def test_settings_defaults_are_local_development_friendly() -> None:
    settings = Settings()

    assert settings.app_name == "Tavola API"
    assert settings.environment == "local"
    assert settings.api_prefix == "/api"


def test_api_prefix_can_be_configured_at_construction() -> None:
    settings = Settings(api_prefix="/internal")

    assert settings.api_prefix == "/internal"
