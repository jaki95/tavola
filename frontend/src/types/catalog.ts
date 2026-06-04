export const catalogCategoryIds = [
  "antipasti",
  "primi",
  "desserts",
  "drinks",
  "pantry"
] as const;

export type CatalogCategoryId = (typeof catalogCategoryIds)[number];

export type Money = {
  amount_minor: number;
  currency: string;
};

export type DietaryFacets = {
  is_vegetarian: boolean;
  is_vegan: boolean;
  is_gluten_free: boolean;
  contains_alcohol: boolean;
};

export type CatalogCategory = {
  category_id: CatalogCategoryId;
  label: string;
};

export type CatalogProductSummary = DietaryFacets & {
  sku_id: string;
  name: string;
  category_id: CatalogCategoryId;
  category_label: string;
  unit_label: string;
  unit_price_minor: number;
  currency: string;
  short_description: string;
  image_id: string;
};

export type CatalogProductDetail = CatalogProductSummary & {
  detail_description: string;
};

export type CatalogFilters = {
  category_id: CatalogCategoryId | null;
  query: string;
};

export type CatalogListResponse = {
  categories: CatalogCategory[];
  products: CatalogProductSummary[];
};
