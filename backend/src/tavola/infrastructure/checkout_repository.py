from collections.abc import Callable, Iterable
from uuid import uuid4

from tavola.domain.basket import BasketId
from tavola.domain.checkout import (
    ContactDetails,
    Order,
    OrderId,
    OrderLine,
    PickupWindow,
)

SEED_PICKUP_WINDOWS: tuple[PickupWindow, ...] = (
    PickupWindow(
        pickup_window_id="friday-afternoon",
        label="Friday afternoon collection",
        display_order=1,
    ),
    PickupWindow(
        pickup_window_id="saturday-midday",
        label="Saturday midday collection",
        display_order=2,
    ),
    PickupWindow(
        pickup_window_id="sunday-morning",
        label="Sunday morning collection",
        display_order=3,
    ),
)


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
