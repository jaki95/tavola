from fastapi.testclient import TestClient

from tavola.api.main import app, create_app
from tavola.config.settings import Settings


def test_app_entrypoint_is_importable() -> None:
    assert app.title == "Tavola API"


def test_health_route_returns_service_status() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"service": "Tavola API", "status": "ok"}


def test_app_uses_configured_api_prefix() -> None:
    configured_app = create_app(Settings(api_prefix="/internal"))
    client = TestClient(configured_app)

    response = client.get("/internal/health")

    assert response.status_code == 200
    assert response.json() == {"service": "Tavola API", "status": "ok"}


def test_health_route_reports_configured_service_name() -> None:
    configured_app = create_app(Settings(app_name="Tavola Demo API"))
    client = TestClient(configured_app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"service": "Tavola Demo API", "status": "ok"}
