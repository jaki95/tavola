from fastapi import FastAPI

from tavola.api.routers import basket, catalog, checkout, health
from tavola.config.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings()
    fastapi_app = FastAPI(title=app_settings.app_name)
    fastapi_app.include_router(health.router, prefix=app_settings.api_prefix)
    fastapi_app.include_router(catalog.router, prefix=app_settings.api_prefix)
    fastapi_app.include_router(basket.router, prefix=app_settings.api_prefix)
    fastapi_app.include_router(checkout.router, prefix=app_settings.api_prefix)
    return fastapi_app


app = create_app()
