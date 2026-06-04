import type { CatalogCategoryId } from "./catalog";

export type BasketLine = {
  sku_id: string;
  name: string;
  category_id: CatalogCategoryId;
  category_label: string;
  unit_label: string;
  quantity: number;
  unit_price_minor: number;
  line_total_minor: number;
  currency: string;
  image_id: string;
};

type BasketBase = {
  basket_id: string;
  total_minor: number;
  currency: string;
  item_count: number;
  line_count: number;
};

export type EmptyBasket = BasketBase & {
  lines: [];
};

export type PopulatedBasket = BasketBase & {
  lines: [BasketLine, ...BasketLine[]];
};

export type BasketResponse = EmptyBasket | PopulatedBasket;

export type Basket = BasketResponse;

export type AddBasketLineRequest = {
  sku_id: string;
  quantity: number;
};

export type SetBasketLineQuantityRequest = {
  quantity: number;
};
