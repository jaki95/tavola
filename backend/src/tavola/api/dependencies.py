from pathlib import Path

from tavola.application.basket import BasketRepository
from tavola.application.catalog import CatalogRepository
from tavola.application.checkout import OrderRepository, PickupWindowRepository
from tavola.application.planner import (
    MenuPlannerAgent,
    PlannerAgentErrorCode,
    PlannerSessionRepository,
)
from tavola.config.settings import Settings
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.checkout_repository import (
    InMemoryOrderRepository,
    StaticPickupWindowRepository,
)
from tavola.infrastructure.codex_planner import (
    CodexMenuPlannerAgent,
    FakeMenuPlannerAgent,
    PythonCodexSdkClient,
)
from tavola.infrastructure.planner_repository import InMemoryPlannerSessionRepository

_basket_repository = InMemoryBasketRepository()
_planner_session_repository = InMemoryPlannerSessionRepository()
_pickup_window_repository = StaticPickupWindowRepository.from_seed()
_order_repository = InMemoryOrderRepository()


def get_basket_repository() -> BasketRepository:
    return _basket_repository


def get_catalog_repository() -> CatalogRepository:
    return StaticCatalogRepository.from_seed()


def get_planner_session_repository() -> PlannerSessionRepository:
    return _planner_session_repository


def get_menu_planner_agent() -> MenuPlannerAgent:
    settings = Settings()
    if settings.use_real_codex_planner():
        return CodexMenuPlannerAgent(
            client=PythonCodexSdkClient(cwd=Path.cwd()),
            model=settings.planner_codex_model,
            sandbox_mode=settings.planner_codex_sandbox_mode,
            timeout_seconds=settings.planner_codex_timeout_seconds,
            max_retries=settings.planner_codex_max_retries,
        )
    return FakeMenuPlannerAgent.with_failure(
        PlannerAgentErrorCode.TOOL_FAILURE,
        "Planner is not configured for this environment.",
    )


def get_pickup_window_repository() -> PickupWindowRepository:
    return _pickup_window_repository


def get_order_repository() -> OrderRepository:
    return _order_repository
