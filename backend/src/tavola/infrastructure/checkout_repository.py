import json
from collections.abc import Callable, Iterable
from importlib.resources import files
from typing import Any
from uuid import uuid4

from tavola.domain.basket import BasketId
from tavola.domain.checkout import (
    ContactDetails,
    Order,
    OrderId,
    OrderLine,
    PickupWindow,
)

_DATA_PACKAGE = "tavola.infrastructure.data"
_PICKUP_WINDOWS_RESOURCE = "pickup_windows.json"


def load_seed_pickup_windows() -> tuple[PickupWindow, ...]:
    raw = json.loads(
        files(_DATA_PACKAGE)
        .joinpath(_PICKUP_WINDOWS_RESOURCE)
        .read_text(encoding="utf-8")
    )
    if not isinstance(raw, list):
        raise ValueError("pickup window seed must be a list")

    return tuple(_pickup_window_from_row(row) for row in raw)


def _pickup_window_from_row(row: object) -> PickupWindow:
    if not isinstance(row, dict):
        raise ValueError("pickup window seed rows must be objects")

    return PickupWindow(
        pickup_window_id=_string_field(row, "pickup_window_id"),
        label=_string_field(row, "label"),
        display_order=_int_field(row, "display_order"),
    )


def _string_field(row: dict[str, Any], field_name: str) -> str:
    value = row.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"pickup window seed field {field_name} must be a string")
    return value


def _int_field(row: dict[str, Any], field_name: str) -> int:
    value = row.get(field_name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"pickup window seed field {field_name} must be an integer")
    return value


SEED_PICKUP_WINDOWS: tuple[PickupWindow, ...] = load_seed_pickup_windows()


class StaticPickupWindowRepository:
    def __init__(self, pickup_windows: Iterable[PickupWindow]) -> None:
        self._pickup_windows = tuple(
            sorted(pickup_windows, key=lambda window: window.display_order)
        )
        self._pickup_windows_by_id = {
            window.pickup_window_id: window for window in self._pickup_windows
        }

    @classmethod
    def from_seed(cls) -> "StaticPickupWindowRepository":
        return cls(SEED_PICKUP_WINDOWS)

    def list_pickup_windows(self) -> tuple[PickupWindow, ...]:
        return self._pickup_windows

    def get_pickup_window(self, pickup_window_id: str) -> PickupWindow | None:
        return self._pickup_windows_by_id.get(pickup_window_id)


class InMemoryOrderRepository:
    def __init__(self, id_generator: Callable[[], str] | None = None) -> None:
        self._id_generator = id_generator or (lambda: uuid4().hex)
        self._orders_by_id: dict[OrderId, Order] = {}

    def create_order(
        self,
        *,
        basket_id: BasketId,
        contact_details: ContactDetails,
        pickup_window: PickupWindow,
        lines: Iterable[OrderLine],
    ) -> Order:
        order = Order(
            order_id=OrderId(self._id_generator()),
            basket_id=basket_id,
            contact=contact_details,
            pickup_window=pickup_window,
            lines=tuple(lines),
        )
        self.save_order(order)
        return order

    def get_order(self, order_id: OrderId) -> Order | None:
        return self._orders_by_id.get(order_id)

    def save_order(self, order: Order) -> None:
        self._orders_by_id[order.order_id] = order
