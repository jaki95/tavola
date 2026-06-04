from typing import Annotated

from pydantic import BaseModel, StrictInt, StringConstraints

from tavola.domain.basket import Basket, BasketLine

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class BasketLineMutationRequest(BaseModel):
    sku_id: NonBlankString
    quantity: StrictInt


class BasketLineQuantityRequest(BaseModel):
    quantity: StrictInt


class BasketLineResponse(BaseModel):
    sku_id: str
    name: str
    category_id: str
    category_label: str
    unit_label: str
    quantity: int
    unit_price_minor: int
    line_total_minor: int
    currency: str
    image_id: str

    @classmethod
    def from_domain(cls, line: BasketLine) -> "BasketLineResponse":
        return cls(
            sku_id=line.sku.sku_id,
            name=line.sku.name,
            category_id=line.sku.category.category_id,
            category_label=line.sku.category.label,
            unit_label=line.sku.unit_label,
            quantity=line.quantity,
            unit_price_minor=line.sku.price.amount_minor,
            line_total_minor=line.line_total.amount_minor,
            currency=line.sku.price.currency,
            image_id=line.sku.image_id,
        )


class BasketResponse(BaseModel):
    basket_id: str
    lines: list[BasketLineResponse]
    total_minor: int
    currency: str
    item_count: int
    line_count: int

    @classmethod
    def from_domain(cls, basket: Basket) -> "BasketResponse":
        return cls(
            basket_id=basket.basket_id.value,
            lines=[BasketLineResponse.from_domain(line) for line in basket.lines],
            total_minor=basket.total.amount_minor,
            currency=basket.total.currency,
            item_count=basket.item_count,
            line_count=basket.line_count,
        )
