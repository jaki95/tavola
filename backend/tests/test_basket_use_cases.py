import pytest

from tavola.application.basket import (
    AddBasketLine,
    BasketLineNotFound,
    BasketNotFound,
    BasketQuantityExceeded,
    BasketQuantityInvalid,
    BasketSkuNotFound,
    BasketSkuUnavailable,
    CreateBasket,
    GetBasket,
    RemoveBasketLine,
    SetBasketLineQuantity,
)
from tavola.domain.basket import MAX_BASKET_LINE_QUANTITY, BasketId
from tavola.domain.catalog import (
    CatalogCategory,
    CatalogSku,
    DietaryFacets,
    Money,
)
from tavola.infrastructure.basket_repository import InMemoryBasketRepository
from tavola.infrastructure.catalog_repository import StaticCatalogRepository


def make_sku(
    sku_id: str = "fresh-tagliatelle-250g",
    *,
    name: str = "Fresh Tagliatelle",
    category: CatalogCategory | None = None,
    amount_minor: int = 425,
    is_available: bool = True,
) -> CatalogSku:
    return CatalogSku(
        sku_id=sku_id,
        name=name,
        category=category or CatalogCategory("primi", "Primi", 2),
        unit_label="250g",
        price=Money(amount_minor=amount_minor, currency="GBP"),
        short_description="Egg pasta cut fresh each morning.",
        detail_description="Silky ribbons of egg pasta for a quick supper.",
        tags=("pasta", "fresh"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id=sku_id,
        display_order=1,
        is_available=is_available,
    )


def test_create_basket_returns_persisted_empty_basket() -> None:
    repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")

    basket = CreateBasket(repository)()

    assert basket.basket_id == BasketId("basket-1")
    assert basket.lines == ()
    assert repository.get_basket(BasketId("basket-1")) == basket


def test_get_basket_returns_known_basket() -> None:
    repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket = repository.create_basket()

    result = GetBasket(repository)("basket-1")

    assert result == basket


def test_get_basket_raises_typed_error_for_unknown_basket() -> None:
    repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")

    with pytest.raises(BasketNotFound) as error:
        GetBasket(repository)("missing-basket")

    assert error.value.code == "basket_not_found"


def test_get_basket_raises_typed_error_for_invalid_basket_id() -> None:
    repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")

    with pytest.raises(BasketNotFound) as error:
        GetBasket(repository)(" ")

    assert error.value.code == "basket_not_found"


def test_add_basket_line_adds_available_sku_and_persists_totals() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    catalog_repository = StaticCatalogRepository([make_sku()])
    basket_repository.create_basket()

    basket = AddBasketLine(basket_repository, catalog_repository)(
        "basket-1",
        sku_id="fresh-tagliatelle-250g",
        quantity=2,
    )

    assert basket.lines[0].sku.sku_id == "fresh-tagliatelle-250g"
    assert basket.lines[0].quantity == 2
    assert basket.total.amount_minor == 850
    assert basket_repository.get_basket(BasketId("basket-1")) == basket


def test_add_basket_line_merges_existing_sku_quantity() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    catalog_repository = StaticCatalogRepository([make_sku()])
    basket_repository.create_basket()
    add_line = AddBasketLine(basket_repository, catalog_repository)

    add_line("basket-1", sku_id="fresh-tagliatelle-250g", quantity=2)
    basket = add_line("basket-1", sku_id="fresh-tagliatelle-250g", quantity=3)

    assert len(basket.lines) == 1
    assert basket.lines[0].quantity == 5


def test_add_basket_line_raises_typed_error_for_missing_basket() -> None:
    catalog_repository = StaticCatalogRepository([make_sku()])

    with pytest.raises(BasketNotFound) as error:
        AddBasketLine(
            InMemoryBasketRepository(id_generator=lambda: "basket-1"),
            catalog_repository,
        )("missing-basket", sku_id="fresh-tagliatelle-250g", quantity=1)

    assert error.value.code == "basket_not_found"


def test_add_basket_line_raises_typed_error_for_missing_sku() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()

    with pytest.raises(BasketSkuNotFound) as error:
        AddBasketLine(basket_repository, StaticCatalogRepository([]))(
            "basket-1",
            sku_id="missing-sku",
            quantity=1,
        )

    assert error.value.code == "sku_not_found"


def test_add_basket_line_raises_typed_error_for_unavailable_sku() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()
    catalog_repository = StaticCatalogRepository([make_sku(is_available=False)])

    with pytest.raises(BasketSkuUnavailable) as error:
        AddBasketLine(basket_repository, catalog_repository)(
            "basket-1",
            sku_id="fresh-tagliatelle-250g",
            quantity=1,
        )

    assert error.value.code == "sku_unavailable"


def test_add_basket_line_raises_typed_error_for_non_positive_quantity() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()
    catalog_repository = StaticCatalogRepository([make_sku()])

    with pytest.raises(BasketQuantityInvalid) as error:
        AddBasketLine(basket_repository, catalog_repository)(
            "basket-1",
            sku_id="fresh-tagliatelle-250g",
            quantity=0,
        )

    assert error.value.code == "invalid_quantity"


@pytest.mark.parametrize("quantity", [1.5, "2", True])
def test_add_basket_line_raises_typed_error_for_non_integer_quantity(
    quantity: object,
) -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()
    catalog_repository = StaticCatalogRepository([make_sku()])

    with pytest.raises(BasketQuantityInvalid) as error:
        AddBasketLine(basket_repository, catalog_repository)(
            "basket-1",
            sku_id="fresh-tagliatelle-250g",
            quantity=quantity,  # type: ignore[arg-type]
        )

    assert error.value.code == "invalid_quantity"


def test_add_basket_line_raises_typed_error_for_merged_quantity_over_maximum() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()
    catalog_repository = StaticCatalogRepository([make_sku()])
    add_line = AddBasketLine(basket_repository, catalog_repository)

    add_line(
        "basket-1",
        sku_id="fresh-tagliatelle-250g",
        quantity=MAX_BASKET_LINE_QUANTITY,
    )

    with pytest.raises(BasketQuantityExceeded) as error:
        add_line("basket-1", sku_id="fresh-tagliatelle-250g", quantity=1)

    assert error.value.code == "quantity_exceeds_max"
    assert error.value.max_quantity == MAX_BASKET_LINE_QUANTITY


def test_set_basket_line_quantity_replaces_quantity_and_persists() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()
    catalog_repository = StaticCatalogRepository([make_sku()])
    AddBasketLine(basket_repository, catalog_repository)(
        "basket-1",
        sku_id="fresh-tagliatelle-250g",
        quantity=2,
    )

    basket = SetBasketLineQuantity(basket_repository)(
        "basket-1",
        sku_id="fresh-tagliatelle-250g",
        quantity=4,
    )

    assert basket.lines[0].quantity == 4
    assert basket.total.amount_minor == 1700
    assert basket_repository.get_basket(BasketId("basket-1")) == basket


def test_set_basket_line_quantity_raises_typed_errors() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()

    with pytest.raises(BasketNotFound):
        SetBasketLineQuantity(basket_repository)(
            "missing-basket",
            sku_id="fresh-tagliatelle-250g",
            quantity=1,
        )

    with pytest.raises(BasketLineNotFound) as missing_line:
        SetBasketLineQuantity(basket_repository)(
            "basket-1",
            sku_id="fresh-tagliatelle-250g",
            quantity=1,
        )

    with pytest.raises(BasketQuantityInvalid):
        SetBasketLineQuantity(basket_repository)(
            "basket-1",
            sku_id="fresh-tagliatelle-250g",
            quantity=0,
        )

    with pytest.raises(BasketQuantityExceeded) as over_max:
        SetBasketLineQuantity(basket_repository)(
            "basket-1",
            sku_id="fresh-tagliatelle-250g",
            quantity=MAX_BASKET_LINE_QUANTITY + 1,
        )

    assert missing_line.value.code == "line_not_found"
    assert over_max.value.max_quantity == MAX_BASKET_LINE_QUANTITY


def test_remove_basket_line_removes_line_and_persists_empty_basket() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()
    catalog_repository = StaticCatalogRepository([make_sku()])
    AddBasketLine(basket_repository, catalog_repository)(
        "basket-1",
        sku_id="fresh-tagliatelle-250g",
        quantity=1,
    )

    basket = RemoveBasketLine(basket_repository)(
        "basket-1",
        sku_id="fresh-tagliatelle-250g",
    )

    assert basket.lines == ()
    assert basket_repository.get_basket(BasketId("basket-1")) == basket


def test_remove_basket_line_raises_typed_errors() -> None:
    basket_repository = InMemoryBasketRepository(id_generator=lambda: "basket-1")
    basket_repository.create_basket()

    with pytest.raises(BasketNotFound):
        RemoveBasketLine(basket_repository)(
            "missing-basket",
            sku_id="fresh-tagliatelle-250g",
        )

    with pytest.raises(BasketLineNotFound) as error:
        RemoveBasketLine(basket_repository)(
            "basket-1",
            sku_id="fresh-tagliatelle-250g",
        )

    assert error.value.code == "line_not_found"
