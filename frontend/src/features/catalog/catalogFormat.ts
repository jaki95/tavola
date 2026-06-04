import type {
  CatalogCategoryId,
  DietaryFacets,
  Money
} from "../../types/catalog";

const CATALOG_CATEGORY_LABELS: Record<CatalogCategoryId, string> = {
  antipasti: "Antipasti",
  primi: "Primi",
  desserts: "Desserts",
  drinks: "Drinks",
  pantry: "Pantry"
};

type DietaryFacetField =
  | "is_vegetarian"
  | "is_vegan"
  | "is_gluten_free"
  | "contains_alcohol";

const DIETARY_FACET_BADGE_LABELS: ReadonlyArray<{
  field: DietaryFacetField;
  label: string;
}> = [
  { field: "is_vegetarian", label: "Vegetarian" },
  { field: "is_vegan", label: "Vegan" },
  { field: "is_gluten_free", label: "Gluten-free" },
  { field: "contains_alcohol", label: "Contains alcohol" }
];

export function formatMoney(
  money: Money,
  locale: Intl.LocalesArgument = "en-GB"
): string {
  const formatter = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: money.currency
  });
  const fractionDigits = formatter.resolvedOptions().maximumFractionDigits ?? 2;
  const majorUnits = money.amount_minor / 10 ** fractionDigits;

  return formatter.format(majorUnits);
}

export function formatCatalogCategoryLabel(
  categoryId: CatalogCategoryId
): string {
  return CATALOG_CATEGORY_LABELS[categoryId];
}

export function formatDietaryFacetBadges(facets: DietaryFacets): string[] {
  return DIETARY_FACET_BADGE_LABELS.flatMap(({ field, label }) =>
    facets[field] ? [label] : []
  );
}
