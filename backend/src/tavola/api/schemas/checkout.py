from typing import Annotated

from pydantic import BaseModel, StringConstraints

from tavola.api.schemas.basket import BasketResponse
from tavola.domain.checkout import Order, OrderLine, PickupWindow

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class PickupWindowResponse(BaseModel):
    pickup_window_id: str
    label: str
    display_order: int

    @classmethod
    def from_domain(cls, pickup_window: PickupWindow) -> "PickupWindowResponse":
        return cls(
            pickup_window_id=pickup_window.pickup_window_id,
            label=pickup_window.label,
            display_order=pickup_window.display_order,
        )


class PickupWindowsResponse(BaseModel):
    pickup_windows: list[PickupWindowResponse]


class CheckoutRequest(BaseModel):
    basket_id: NonBlankString
    contact_name: NonBlankString
    contact_email: NonBlankString
    pickup_window_id: NonBlankString


class OrderLineResponse(BaseModel):
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
    def from_domain(cls, line: OrderLine) -> "OrderLineResponse":
        return cls(
            sku_id=line.sku_id,
            name=line.name,
            category_id=line.category_id,
            category_label=line.category_label,
            unit_label=line.unit_label,
            quantity=line.quantity,
            unit_price_minor=line.unit_price.amount_minor,
            line_total_minor=line.line_total.amount_minor,
            currency=line.currency,
            image_id=line.image_id,
        )


class OrderResponse(BaseModel):
    order_id: str
    basket_id: str
    contact_name: str
    contact_email: str
    pickup_window: PickupWindowResponse
    lines: list[OrderLineResponse]
    total_minor: int
    currency: str
    item_count: int
    line_count: int

    @classmethod
    def from_domain(cls, order: Order) -> "OrderResponse":
        return cls(
            order_id=order.order_id.value,
            basket_id=order.basket_id.value,
            contact_name=order.contact.name,
            contact_email=order.contact.email,
            pickup_window=PickupWindowResponse.from_domain(order.pickup_window),
            lines=[OrderLineResponse.from_domain(line) for line in order.lines],
            total_minor=order.total.amount_minor,
            currency=order.currency,
            item_count=order.item_count,
            line_count=order.line_count,
        )


class CheckoutResponse(BaseModel):
    order: OrderResponse
    basket: BasketResponse
