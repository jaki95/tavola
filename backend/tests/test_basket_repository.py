from tavola.application.basket import BasketRepository
from tavola.domain.basket import BasketId
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.infrastructure.basket_repository import InMemoryBasketRepository


def make_sku() -> CatalogSku:
    return CatalogSku(
        sku_id="fresh-tagliatelle-250g",
        name="Fresh Tagliatelle",
        category=CatalogCategory("primi", "Primi", 2),
        unit_label="250g",
        price=Money(amount_minor=425, currency="GBP"),
        short_description="Egg pasta cut fresh each morning.",
        detail_description="Silky ribbons of egg pasta for a quick supper.",
        tags=("pasta", "fresh"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id="fresh-tagliatelle-250g",
        display_order=1,
        is_available=True,
    )


def test_in_memory_basket_repository_creates_basket_with_deterministic_id() -> None:
    repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")

    basket = repository.create_basket()

    assert basket.basket_id == BasketId("basket-1")
    assert basket.lines == ()
    assert repository.get_basket(BasketId("basket-1")) == basket


def test_in_memory_basket_repository_fetches_missing_basket_as_none() -> None:
    repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")

    assert repository.get_basket(BasketId("missing-basket")) is None


def test_in_memory_basket_repository_saves_updated_basket_state() -> None:
    repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket = repository.create_basket()
    updated = basket.add_line(make_sku(), quantity=2)

    repository.save_basket(updated)

    assert repository.get_basket(BasketId("basket-1")) == updated


def test_in_memory_basket_repository_uses_replaceable_id_generation() -> None:
    ids = iter(("basket-1", "basket-2"))
    repository = InMemoryBasketRepository(id_generator=lambda: next(ids))

    first = repository.create_basket()
    second = repository.create_basket()

    assert first.basket_id == BasketId("basket-1")
    assert second.basket_id == BasketId("basket-2")


def test_in_memory_basket_repository_satisfies_application_protocol() -> None:
    repository: BasketRepository = InMemoryBasketRepository(
        id_generator=lambda: "basket-1"
    )

    assert repository.get_basket(BasketId("missing-basket")) is None
