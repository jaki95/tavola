from tavola.application.checkout import OrderRepository, PickupWindowRepository
from tavola.domain.basket import BasketId
from tavola.domain.catalog import Money
from tavola.domain.checkout import (
    ContactDetails,
    Order,
    OrderId,
    OrderLine,
    PickupWindow,
)
from tavola.infrastructure.checkout_repository import (
    InMemoryOrderRepository,
    StaticPickupWindowRepository,
)


def make_order(order_id: str = "order-1") -> Order:
    pickup_window = PickupWindow(
        pickup_window_id="friday-afternoon",
        label="Friday afternoon collection",
        display_order=1,
    )
    return Order(
        order_id=OrderId(order_id),
        basket_id=BasketId("basket-1"),
        contact=ContactDetails(
            name="Giulia Rossi",
            email="giulia@example.com",
        ),
        pickup_window=pickup_window,
        lines=(
            OrderLine(
                sku_id="fresh-tagliatelle-250g",
                name="Fresh Tagliatelle",
                category_id="primi",
                category_label="Primi",
                unit_label="250g",
                quantity=2,
                unit_price=Money(amount_minor=425, currency="GBP"),
                line_total=Money(amount_minor=850, currency="GBP"),
                image_id="fresh-tagliatelle-250g",
            ),
        ),
    )


def test_static_pickup_window_repository_lists_windows_in_display_order() -> None:
    repository = StaticPickupWindowRepository(
        [
            PickupWindow("saturday-midday", "Saturday midday collection", 2),
            PickupWindow("friday-afternoon", "Friday afternoon collection", 1),
            PickupWindow("sunday-morning", "Sunday morning collection", 3),
        ]
    )

    pickup_windows = repository.list_pickup_windows()

    assert [window.pickup_window_id for window in pickup_windows] == [
        "friday-afternoon",
        "saturday-midday",
        "sunday-morning",
    ]


def test_static_pickup_window_repository_fetches_window_by_id() -> None:
    pickup_window = PickupWindow(
        "friday-afternoon",
        "Friday afternoon collection",
        1,
    )
    repository = StaticPickupWindowRepository([pickup_window])

    assert repository.get_pickup_window("friday-afternoon") == pickup_window


def test_static_pickup_window_repository_returns_none_for_missing_window() -> None:
    repository = StaticPickupWindowRepository([])

    assert repository.get_pickup_window("missing-window") is None


def test_static_pickup_window_repository_can_be_backed_by_seed_windows() -> None:
    repository = StaticPickupWindowRepository.from_seed()

    pickup_windows = repository.list_pickup_windows()

    assert [window.display_order for window in pickup_windows] == sorted(
        window.display_order for window in pickup_windows
    )
    assert len(pickup_windows) >= 3


def test_static_pickup_window_repository_satisfies_application_protocol() -> None:
    repository: PickupWindowRepository = StaticPickupWindowRepository.from_seed()

    assert repository.get_pickup_window("missing-window") is None


def test_seed_pickup_window_labels_avoid_live_capacity_or_exact_scheduling() -> None:
    repository = StaticPickupWindowRepository.from_seed()
    forbidden_terms = ("available", "capacity", "slot", "reservation", "at ")

    labels = [window.label.casefold() for window in repository.list_pickup_windows()]

    assert all(not any(term in label for term in forbidden_terms) for label in labels)


def test_in_memory_order_repository_creates_order_with_deterministic_id() -> None:
    repository = InMemoryOrderRepository(id_generator=lambda: "order-1")
    pickup_window = PickupWindow(
        "friday-afternoon",
        "Friday afternoon collection",
        1,
    )
    lines = make_order().lines

    order = repository.create_order(
        basket_id=BasketId("basket-1"),
        contact_details=ContactDetails(
            name="Giulia Rossi",
            email="giulia@example.com",
        ),
        pickup_window=pickup_window,
        lines=lines,
    )

    assert order.order_id == OrderId("order-1")
    assert order.pickup_window == pickup_window
    assert repository.get_order(OrderId("order-1")) == order


def test_in_memory_order_repository_fetches_missing_order_as_none() -> None:
    repository = InMemoryOrderRepository(id_generator=lambda: "order-1")

    assert repository.get_order(OrderId("missing-order")) is None


def test_in_memory_order_repository_saves_updated_order_state() -> None:
    repository = InMemoryOrderRepository(id_generator=lambda: "order-1")
    order = make_order("order-1")

    repository.save_order(order)

    assert repository.get_order(OrderId("order-1")) == order


def test_in_memory_order_repository_state_lasts_for_instance_lifetime() -> None:
    repository = InMemoryOrderRepository(id_generator=lambda: "order-1")
    order = make_order("order-1")

    repository.save_order(order)

    assert repository.get_order(order.order_id) == order


def test_in_memory_order_repository_uses_replaceable_id_generation() -> None:
    ids = iter(("order-1", "order-2"))
    repository = InMemoryOrderRepository(id_generator=lambda: next(ids))

    first = repository.create_order(
        basket_id=BasketId("basket-1"),
        contact_details=ContactDetails(
            name="Giulia Rossi",
            email="giulia@example.com",
        ),
        pickup_window=PickupWindow(
            "friday-afternoon",
            "Friday afternoon collection",
            1,
        ),
        lines=make_order().lines,
    )
    second = repository.create_order(
        basket_id=BasketId("basket-2"),
        contact_details=ContactDetails(
            name="Marco Bianchi",
            email="marco@example.com",
        ),
        pickup_window=PickupWindow(
            "saturday-midday",
            "Saturday midday collection",
            2,
        ),
        lines=make_order().lines,
    )

    assert first.order_id == OrderId("order-1")
    assert second.order_id == OrderId("order-2")


def test_in_memory_order_repository_satisfies_application_protocol() -> None:
    repository: OrderRepository = InMemoryOrderRepository(
        id_generator=lambda: "order-1"
    )

    assert repository.get_order(OrderId("missing-order")) is None
