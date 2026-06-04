from dataclasses import dataclass

from tavola.domain.catalog import SUPPORTED_CURRENCY, CatalogSku, Money

MAX_BASKET_LINE_QUANTITY = 10


class BasketValidationError(ValueError):
    """Raised when basket quantities or identifiers break domain rules."""


class BasketQuantityNotIntegerError(BasketValidationError):
    """Raised when a basket quantity is not an integer."""


class BasketQuantityNotPositiveError(BasketValidationError):
    """Raised when a basket quantity is zero or negative."""


class BasketQuantityExceededError(BasketValidationError):
    """Raised when a basket quantity exceeds the per-line maximum."""

    def __init__(self, max_quantity: int) -> None:
        self.max_quantity = max_quantity
        super().__init__(f"quantity cannot exceed {max_quantity}")


class BasketLineNotFoundError(LookupError):
    """Raised when a requested basket line is not present."""


@dataclass(frozen=True, slots=True)
class BasketId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("basket_id is required")


@dataclass(frozen=True, slots=True)
class BasketLine:
    sku: CatalogSku
    quantity: int

    def __post_init__(self) -> None:
        _validate_quantity(self.quantity)

    @property
    def line_total(self) -> Money:
        return Money(
            amount_minor=self.sku.price.amount_minor * self.quantity,
            currency=self.sku.price.currency,
        )


@dataclass(frozen=True, slots=True)
class Basket:
    basket_id: BasketId
    lines: tuple[BasketLine, ...]

    def __post_init__(self) -> None:
        sku_ids = [line.sku.sku_id for line in self.lines]
        if len(sku_ids) != len(set(sku_ids)):
            raise BasketValidationError("basket lines must be unique by SKU")

    @classmethod
    def empty(cls, basket_id: BasketId) -> "Basket":
        return cls(basket_id=basket_id, lines=())

    @property
    def total(self) -> Money:
        return Money(
            amount_minor=sum(line.line_total.amount_minor for line in self.lines),
            currency=self.currency,
        )

    @property
    def currency(self) -> str:
        if not self.lines:
            return SUPPORTED_CURRENCY
        return self.lines[0].sku.price.currency

    @property
    def item_count(self) -> int:
        return sum(line.quantity for line in self.lines)

    @property
    def line_count(self) -> int:
        return len(self.lines)

    def add_line(self, sku: CatalogSku, *, quantity: int) -> "Basket":
        _validate_quantity(quantity)

        existing = self._find_line(sku.sku_id)
        if existing is None:
            return Basket(
                basket_id=self.basket_id,
                lines=(*self.lines, BasketLine(sku=sku, quantity=quantity)),
            )

        return self._replace_line(
            sku.sku_id,
            BasketLine(sku=sku, quantity=existing.quantity + quantity),
        )

    def set_line_quantity(self, sku_id: str, *, quantity: int) -> "Basket":
        _validate_quantity(quantity)
        line = self._find_line(sku_id)
        if line is None:
            raise BasketLineNotFoundError("basket line not found")

        return self._replace_line(
            sku_id,
            BasketLine(sku=line.sku, quantity=quantity),
        )

    def remove_line(self, sku_id: str) -> "Basket":
        if self._find_line(sku_id) is None:
            raise BasketLineNotFoundError("basket line not found")

        return Basket(
            basket_id=self.basket_id,
            lines=tuple(line for line in self.lines if line.sku.sku_id != sku_id),
        )

    def _find_line(self, sku_id: str) -> BasketLine | None:
        return next((line for line in self.lines if line.sku.sku_id == sku_id), None)

    def _replace_line(self, sku_id: str, replacement: BasketLine) -> "Basket":
        return Basket(
            basket_id=self.basket_id,
            lines=tuple(
                replacement if line.sku.sku_id == sku_id else line
                for line in self.lines
            ),
        )


def _validate_quantity(quantity: int) -> None:
    if type(quantity) is not int:
        raise BasketQuantityNotIntegerError("quantity must be an integer")
    if quantity <= 0:
        raise BasketQuantityNotPositiveError("quantity must be positive")
    if quantity > MAX_BASKET_LINE_QUANTITY:
        raise BasketQuantityExceededError(MAX_BASKET_LINE_QUANTITY)
