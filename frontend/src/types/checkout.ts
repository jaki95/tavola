import type { BasketLine, BasketResponse } from "./basket";

export type PickupWindow = {
  pickup_window_id: string;
  label: string;
  display_order: number;
};

export type PickupWindowsResponse = {
  pickup_windows: PickupWindow[];
};

export type OrderLine = BasketLine;

export type Order = {
  order_id: string;
  basket_id: string;
  contact_name: string;
  contact_email: string;
  pickup_window: PickupWindow;
  lines: OrderLine[];
  total_minor: number;
  currency: string;
  item_count: number;
  line_count: number;
};

export type CheckoutRequest = {
  basket_id: string;
  contact_name: string;
  contact_email: string;
  pickup_window_id: string;
};

export type CheckoutResponse = {
  order: Order;
  basket: BasketResponse;
};
