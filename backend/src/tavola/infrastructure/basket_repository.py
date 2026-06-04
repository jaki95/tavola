from collections.abc import Callable
from uuid import uuid4

from tavola.domain.basket import Basket, BasketId


class InMemoryBasketRepository:
    def __init__(self, id_generator: Callable[[], str] | None = None) -> None:
        self._id_generator = id_generator or (lambda: uuid4().hex)
        self._baskets_by_id: dict[BasketId, Basket] = {}

    def create_basket(self) -> Basket:
        basket = Basket.empty(BasketId(self._id_generator()))
        self.save_basket(basket)
        return basket

    def get_basket(self, basket_id: BasketId) -> Basket | None:
        return self._baskets_by_id.get(basket_id)

    def save_basket(self, basket: Basket) -> None:
        self._baskets_by_id[basket.basket_id] = basket
