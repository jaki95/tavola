from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from tavola.api.dependencies import (
    get_basket_repository,
    get_catalog_repository,
    get_order_repository,
    get_pickup_window_repository,
)
from tavola.api.schemas.basket import BasketResponse
from tavola.api.schemas.checkout import (
    CheckoutRequest,
    CheckoutResponse,
    OrderResponse,
    PickupWindowResponse,
    PickupWindowsResponse,
)
from tavola.application.basket import BasketRepository
from tavola.application.catalog import CatalogRepository
from tavola.application.checkout import (
    CheckoutApplicationError,
    CheckoutBasketNotFound,
    CheckoutBasketQuantityInvalid,
    CheckoutContactInvalid,
    CheckoutEmptyBasket,
    CheckoutPickupWindowNotFound,
    CheckoutSkuNotFound,
    CheckoutSkuUnavailable,
    CreateCheckoutOrder,
    ListPickupWindows,
    OrderRepository,
    PickupWindowRepository,
)

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.get("/pickup-windows", response_model=PickupWindowsResponse)
def list_pickup_windows(
    repository: Annotated[
        PickupWindowRepository,
        Depends(get_pickup_window_repository),
    ],
) -> PickupWindowsResponse:
    pickup_windows = ListPickupWindows(repository)()
    return PickupWindowsResponse(
        pickup_windows=[
            PickupWindowResponse.from_domain(window) for window in pickup_windows
        ]
    )


@router.post("", response_model=CheckoutResponse)
def create_checkout_order(
    request: CheckoutRequest,
    basket_repository: Annotated[BasketRepository, Depends(get_basket_repository)],
    catalog_repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
    pickup_window_repository: Annotated[
        PickupWindowRepository,
        Depends(get_pickup_window_repository),
    ],
    order_repository: Annotated[OrderRepository, Depends(get_order_repository)],
) -> CheckoutResponse:
    try:
        result = CreateCheckoutOrder(
            basket_repository=basket_repository,
            catalog_repository=catalog_repository,
            pickup_window_repository=pickup_window_repository,
            order_repository=order_repository,
        )(
            request.basket_id,
            contact_name=request.contact_name,
            contact_email=request.contact_email,
            pickup_window_id=request.pickup_window_id,
        )
    except CheckoutApplicationError as error:
        raise _checkout_http_exception(error) from error

    return CheckoutResponse(
        order=OrderResponse.from_domain(result.order),
        basket=BasketResponse.from_domain(result.basket),
    )


def _checkout_http_exception(error: CheckoutApplicationError) -> HTTPException:
    if isinstance(error, CheckoutBasketNotFound):
        return HTTPException(status_code=404, detail=error.message)
    if isinstance(error, CheckoutEmptyBasket):
        return _validation_exception(
            "basket_id",
            "Basket is empty.",
            error.code,
        )
    if isinstance(error, CheckoutPickupWindowNotFound):
        return _validation_exception(
            "pickup_window_id",
            "Pickup window was not found.",
            error.code,
        )
    if isinstance(error, CheckoutContactInvalid):
        message = (
            "Contact email must include text before and after @."
            if error.field == "contact_email"
            else "Contact name is required."
        )
        return _validation_exception(error.field, message, error.code)
    if isinstance(error, CheckoutSkuNotFound):
        return _validation_exception(
            "basket_id",
            "Basket contains a SKU that is no longer available.",
            error.code,
            {"sku_id": error.sku_id},
        )
    if isinstance(error, CheckoutSkuUnavailable):
        return _validation_exception(
            "basket_id",
            "Basket contains an unavailable SKU.",
            error.code,
            {"sku_id": error.sku_id},
        )
    if isinstance(error, CheckoutBasketQuantityInvalid):
        return _validation_exception(
            "basket_id",
            "Basket contains an invalid quantity.",
            error.code,
            {"sku_id": error.sku_id},
        )

    return HTTPException(status_code=422, detail=error.message)


def _validation_exception(
    field: str,
    message: str,
    error_type: str,
    context: dict[str, Any] | None = None,
) -> HTTPException:
    error_detail: dict[str, Any] = {
        "loc": ["body", field],
        "msg": message,
        "type": error_type,
    }
    if context is not None:
        error_detail["ctx"] = context
    return HTTPException(status_code=422, detail=[error_detail])
