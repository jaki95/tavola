import beefRaguLasagneImage from "../../assets/catalog/beef-ragu-lasagne-serves-2.jpg";
import aranciataSparklingImage from "../../assets/catalog/aranciata-sparkling-330ml.jpg";
import burrataPuglieseImage from "../../assets/catalog/burrata-pugliese-125g.jpg";
import cannoliSicilianiImage from "../../assets/catalog/cannoli-siciliani-two-pack.jpg";
import cantucciBiscottiImage from "../../assets/catalog/cantucci-biscotti-200g.jpg";
import caponataSicilianaImage from "../../assets/catalog/caponata-siciliana-300g.jpg";
import chiantiClassicoImage from "../../assets/catalog/chianti-classico-750ml.jpg";
import extraVirginOliveOilImage from "../../assets/catalog/extra-virgin-olive-oil-500ml.jpg";
import finocchionaSalamiImage from "../../assets/catalog/finocchiona-salami-100g.jpg";
import freshTagliatelleImage from "../../assets/catalog/fresh-tagliatelle-250g.jpg";
import grilledArtichokesImage from "../../assets/catalog/grilled-artichokes-200g.jpg";
import limonataSparklingImage from "../../assets/catalog/limonata-sparkling-330ml.jpg";
import marinatedNocellaraOlivesImage from "../../assets/catalog/marinated-nocellara-olives-250g.jpg";
import parmigianaMelanzaneImage from "../../assets/catalog/parmigiana-melanzane-serves-2.jpg";
import pecorinoToscanoImage from "../../assets/catalog/pecorino-toscano-200g.jpg";
import pestoGenoveseImage from "../../assets/catalog/pesto-genovese-180g.jpg";
import pinotGrigioDelleVenezieImage from "../../assets/catalog/pinot-grigio-delle-venezie-750ml.jpg";
import potatoGnocchiImage from "../../assets/catalog/potato-gnocchi-500g.jpg";
import prosciuttoDiParmaImage from "../../assets/catalog/prosciutto-di-parma-100g.jpg";
import pumpkinSageTortelloniImage from "../../assets/catalog/pumpkin-sage-tortelloni-300g.jpg";
import ricottaSpinachRavioliImage from "../../assets/catalog/ricotta-spinach-ravioli-300g.jpg";
import ribollitaToscanaImage from "../../assets/catalog/ribollita-toscana-500g.jpg";
import rosemaryFocacciaImage from "../../assets/catalog/rosemary-focaccia-piece.jpg";
import sugoPomodoroImage from "../../assets/catalog/sugo-pomodoro-500g.jpg";
import tiramisuCupImage from "../../assets/catalog/tiramisu-cup-single.jpg";
import tortaDellaNonnaImage from "../../assets/catalog/torta-della-nonna-slice.jpg";
import fallbackImage from "../../assets/catalog/catalog-fallback.svg";
import type { CatalogImageAsset } from "../../types/catalog";

const catalogImageDimensions = {
  width: 960,
  height: 720
} as const;

export const catalogImageIds = [
  "burrata-pugliese-125g",
  "marinated-nocellara-olives-250g",
  "caponata-siciliana-300g",
  "prosciutto-di-parma-100g",
  "grilled-artichokes-200g",
  "rosemary-focaccia-piece",
  "finocchiona-salami-100g",
  "fresh-tagliatelle-250g",
  "ricotta-spinach-ravioli-300g",
  "beef-ragu-lasagne-serves-2",
  "parmigiana-melanzane-serves-2",
  "potato-gnocchi-500g",
  "pumpkin-sage-tortelloni-300g",
  "ribollita-toscana-500g",
  "tiramisu-cup-single",
  "cannoli-siciliani-two-pack",
  "torta-della-nonna-slice",
  "cantucci-biscotti-200g",
  "aranciata-sparkling-330ml",
  "limonata-sparkling-330ml",
  "chianti-classico-750ml",
  "pinot-grigio-delle-venezie-750ml",
  "sugo-pomodoro-500g",
  "pesto-genovese-180g",
  "extra-virgin-olive-oil-500ml",
  "pecorino-toscano-200g"
] as const;

type CatalogImageId = (typeof catalogImageIds)[number];
type CatalogImageBase = Omit<CatalogImageAsset, "alt">;

const catalogImages: Record<CatalogImageId, CatalogImageBase> = {
  "burrata-pugliese-125g": withDimensions(burrataPuglieseImage),
  "marinated-nocellara-olives-250g": withDimensions(
    marinatedNocellaraOlivesImage
  ),
  "caponata-siciliana-300g": withDimensions(caponataSicilianaImage),
  "prosciutto-di-parma-100g": withDimensions(prosciuttoDiParmaImage),
  "grilled-artichokes-200g": withDimensions(grilledArtichokesImage),
  "rosemary-focaccia-piece": withDimensions(rosemaryFocacciaImage),
  "finocchiona-salami-100g": withDimensions(finocchionaSalamiImage),
  "fresh-tagliatelle-250g": withDimensions(freshTagliatelleImage),
  "ricotta-spinach-ravioli-300g": withDimensions(ricottaSpinachRavioliImage),
  "beef-ragu-lasagne-serves-2": withDimensions(beefRaguLasagneImage),
  "parmigiana-melanzane-serves-2": withDimensions(parmigianaMelanzaneImage),
  "potato-gnocchi-500g": withDimensions(potatoGnocchiImage),
  "pumpkin-sage-tortelloni-300g": withDimensions(pumpkinSageTortelloniImage),
  "ribollita-toscana-500g": withDimensions(ribollitaToscanaImage),
  "tiramisu-cup-single": withDimensions(tiramisuCupImage),
  "cannoli-siciliani-two-pack": withDimensions(cannoliSicilianiImage),
  "torta-della-nonna-slice": withDimensions(tortaDellaNonnaImage),
  "cantucci-biscotti-200g": withDimensions(cantucciBiscottiImage),
  "aranciata-sparkling-330ml": withDimensions(aranciataSparklingImage),
  "limonata-sparkling-330ml": withDimensions(limonataSparklingImage),
  "chianti-classico-750ml": withDimensions(chiantiClassicoImage),
  "pinot-grigio-delle-venezie-750ml": withDimensions(
    pinotGrigioDelleVenezieImage
  ),
  "sugo-pomodoro-500g": withDimensions(sugoPomodoroImage),
  "pesto-genovese-180g": withDimensions(pestoGenoveseImage),
  "extra-virgin-olive-oil-500ml": withDimensions(extraVirginOliveOilImage),
  "pecorino-toscano-200g": withDimensions(pecorinoToscanoImage)
};

const fallbackCatalogImage = withDimensions(fallbackImage);

export function getCatalogImageAsset(
  imageId: string,
  productName: string
): CatalogImageAsset {
  const image = catalogImages[imageId as CatalogImageId] ?? fallbackCatalogImage;

  return {
    ...image,
    alt: `${productName} product image`
  };
}

function withDimensions(src: string): CatalogImageBase {
  return {
    src,
    ...catalogImageDimensions
  };
}
