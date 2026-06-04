from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from tavola.api.dependencies import get_basket_repository, get_catalog_repository
from tavola.api.schemas.basket import (
    BasketLineMutationRequest,
    BasketLineQuantityRequest,
    BasketResponse,
)
from tavola.application.basket import (
    AddBasketLine,
    BasketApplicationError,
    BasketLineNotFound,
    BasketNotFound,
    BasketQuantityExceeded,
    BasketQuantityInvalid,
    BasketRepository,
    BasketSkuNotFound,
    BasketSkuUnavailable,
    CreateBasket,
    GetBasket,
    RemoveBasketLine,
    SetBasketLineQuantity,
)
from tavola.application.catalog import CatalogRepository

router = APIRouter(prefix="/baskets", tags=["baskets"])


@router.post("", response_model=BasketResponse, status_code=status.HTTP_201_CREATED)
def create_basket(
    repository: Annotated[BasketRepository, Depends(get_basket_repository)],
) -> BasketResponse:
    basket = CreateBasket(repository)()
    return BasketResponse.from_domain(basket)


@router.get("/{basket_id}", response_model=BasketResponse)
def get_basket(
    basket_id: str,
    repository: Annotated[BasketRepository, Depends(get_basket_repository)],
) -> BasketResponse:
    try:
        basket = GetBasket(repository)(basket_id)
    except BasketApplicationError as error:
        raise _basket_http_exception(error) from error

    return BasketResponse.from_domain(basket)


@router.post("/{basket_id}/lines", response_model=BasketResponse)
def add_basket_line(
    basket_id: str,
    request: BasketLineMutationRequest,
    basket_repository: Annotated[BasketRepository, Depends(get_basket_repository)],
    catalog_repository: Annotated[CatalogRepository, Depends(get_catalog_repository)],
) -> BasketResponse:
    try:
        basket = AddBasketLine(basket_repository, catalog_repository)(
            basket_id,
            sku_id=request.sku_id,
            quantity=request.quantity,
        )
    except BasketApplicationError as error:
        raise _basket_http_exception(error) from error

    return BasketResponse.from_domain(basket)


@router.patch("/{basket_id}/lines/{sku_id}", response_model=BasketResponse)
def set_basket_line_quantity(
    basket_id: str,
    sku_id: str,
    request: BasketLineQuantityRequest,
    repository: Annotated[BasketRepository, Depends(get_basket_repository)],
) -> BasketResponse:
    try:
        basket = SetBasketLineQuantity(repository)(
            basket_id,
            sku_id=sku_id,
            quantity=request.quantity,
        )
    except BasketApplicationError as error:
        raise _basket_http_exception(error) from error

    return BasketResponse.from_domain(basket)


@router.delete("/{basket_id}/lines/{sku_id}", response_model=BasketResponse)
def remove_basket_line(
    basket_id: str,
    sku_id: str,
    repository: Annotated[BasketRepository, Depends(get_basket_repository)],
) -> BasketResponse:
    try:
        basket = RemoveBasketLine(repository)(basket_id, sku_id=sku_id)
    except BasketApplicationError as error:
        raise _basket_http_exception(error) from error

    return BasketResponse.from_domain(basket)


def _basket_http_exception(error: BasketApplicationError) -> HTTPException:
    if isinstance(error, (BasketNotFound, BasketLineNotFound)):
        return HTTPException(status_code=404, detail=error.message)

    if isinstance(error, BasketSkuNotFound):
        return _validation_exception("sku_id", "SKU not found.", error.code)
    if isinstance(error, BasketSkuUnavailable):
        return _validation_exception("sku_id", "SKU is unavailable.", error.code)
    if isinstance(error, BasketQuantityInvalid):
        return _validation_exception(
            "quantity",
            "Quantity must be positive.",
            error.code,
        )
    if isinstance(error, BasketQuantityExceeded):
        return _validation_exception(
            "quantity",
            f"Quantity cannot exceed {error.max_quantity}.",
            error.code,
            {"max_quantity": error.max_quantity},
        )

    return HTTPException(status_code=422, detail=error.message)


def _validation_exception(
    field: str,
    message: str,
    error_type: str,
    context: dict[str, int] | None = None,
) -> HTTPException:
    error_detail = {
        "loc": ["body", field],
        "msg": message,
        "type": error_type,
    }
    if context is not None:
        error_detail["ctx"] = context
    return HTTPException(status_code=422, detail=[error_detail])
