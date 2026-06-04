from tavola.domain.catalog import CatalogCategory, CatalogSku, DietaryFacets, Money

ANTIPASTI = CatalogCategory("antipasti", "Antipasti", 1)
PRIMI = CatalogCategory("primi", "Primi", 2)
DESSERTS = CatalogCategory("desserts", "Desserts", 3)
DRINKS = CatalogCategory("drinks", "Drinks", 4)
PANTRY = CatalogCategory("pantry", "Pantry", 5)


SEED_CATALOG: tuple[CatalogSku, ...] = (
    CatalogSku(
        sku_id="burrata-pugliese-125g",
        name="Burrata Pugliese",
        category=ANTIPASTI,
        unit_label="125g",
        price=Money(amount_minor=495, currency="GBP"),
        short_description=(
            "Fresh burrata with a creamy centre and delicate milk sweetness."
        ),
        detail_description=(
            "Made in Puglia with a soft mozzarella shell and rich stracciatella"
            " centre. Serve with tomatoes, basil, and a drizzle of olive oil."
        ),
        tags=("burrata", "cheese", "creamy", "vegetarian"),
        facets=DietaryFacets(is_vegetarian=True, is_gluten_free=True),
        image_id="burrata-pugliese-125g",
        display_order=1,
        is_available=True,
    ),
    CatalogSku(
        sku_id="marinated-nocellara-olives-250g",
        name="Marinated Nocellara Olives",
        category=ANTIPASTI,
        unit_label="250g",
        price=Money(amount_minor=425, currency="GBP"),
        short_description="Buttery green olives marinated with citrus peel and herbs.",
        detail_description=(
            "Large Sicilian Nocellara olives are dressed with lemon, oregano,"
            " and extra virgin olive oil. They bring a bright, salty start to an"
            " aperitivo board."
        ),
        tags=("olives", "aperitivo", "vegan", "gluten-free"),
        facets=DietaryFacets(
            is_vegetarian=True,
            is_vegan=True,
            is_gluten_free=True,
        ),
        image_id="marinated-nocellara-olives-250g",
        display_order=2,
        is_available=True,
    ),
    CatalogSku(
        sku_id="caponata-siciliana-300g",
        name="Caponata Siciliana",
        category=ANTIPASTI,
        unit_label="300g",
        price=Money(amount_minor=650, currency="GBP"),
        short_description=(
            "Sweet-sour aubergine relish with capers, celery, and tomato."
        ),
        detail_description=(
            "A Sicilian antipasto of slow-cooked aubergine, tomato, celery, and"
            " capers. Spoon onto toasted bread or serve beside grilled fish."
        ),
        tags=("aubergine", "sicilian", "vegan", "antipasti"),
        facets=DietaryFacets(
            is_vegetarian=True,
            is_vegan=True,
            is_gluten_free=True,
        ),
        image_id="caponata-siciliana-300g",
        display_order=3,
        is_available=True,
    ),
    CatalogSku(
        sku_id="prosciutto-di-parma-100g",
        name="Prosciutto di Parma",
        category=ANTIPASTI,
        unit_label="100g",
        price=Money(amount_minor=775, currency="GBP"),
        short_description=(
            "Silky cured ham sliced thin for antipasti and sharing boards."
        ),
        detail_description=(
            "Aged Parma ham with gentle sweetness and a clean savoury finish."
            " Layer with melon, figs, or burrata for a classic deli plate."
        ),
        tags=("prosciutto", "cured-meat", "parma", "antipasti"),
        facets=DietaryFacets(is_gluten_free=True),
        image_id="prosciutto-di-parma-100g",
        display_order=4,
        is_available=True,
    ),
    CatalogSku(
        sku_id="grilled-artichokes-200g",
        name="Grilled Artichokes",
        category=ANTIPASTI,
        unit_label="200g",
        price=Money(amount_minor=625, currency="GBP"),
        short_description="Tender artichoke hearts grilled and packed in herb oil.",
        detail_description=(
            "Quartered artichokes are lightly charred, then preserved with"
            " parsley, garlic, and olive oil. Add them to antipasti boards,"
            " salads, or warm focaccia."
        ),
        tags=("artichoke", "grilled", "vegan", "antipasti"),
        facets=DietaryFacets(
            is_vegetarian=True,
            is_vegan=True,
            is_gluten_free=True,
        ),
        image_id="grilled-artichokes-200g",
        display_order=5,
        is_available=True,
    ),
    CatalogSku(
        sku_id="fresh-tagliatelle-250g",
        name="Fresh Tagliatelle",
        category=PRIMI,
        unit_label="250g",
        price=Money(amount_minor=425, currency="GBP"),
        short_description=(
            "Egg pasta ribbons cut fresh for rich sauces and quick suppers."
        ),
        detail_description=(
            "Silky tagliatelle made with durum wheat flour and free-range egg."
            " Toss with ragu, mushrooms, or a simple butter and sage sauce."
        ),
        tags=("pasta", "tagliatelle", "fresh", "vegetarian"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id="fresh-tagliatelle-250g",
        display_order=1,
        is_available=True,
    ),
    CatalogSku(
        sku_id="ricotta-spinach-ravioli-300g",
        name="Ricotta and Spinach Ravioli",
        category=PRIMI,
        unit_label="300g",
        price=Money(amount_minor=695, currency="GBP"),
        short_description="Fresh ravioli filled with ricotta, spinach, and nutmeg.",
        detail_description=(
            "Pillowy pasta parcels with a classic ricotta and spinach filling."
            " Finish with tomato sugo, brown butter, or grated pecorino."
        ),
        tags=("ravioli", "pasta", "ricotta", "vegetarian"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id="ricotta-spinach-ravioli-300g",
        display_order=2,
        is_available=True,
    ),
    CatalogSku(
        sku_id="beef-ragu-lasagne-serves-2",
        name="Beef Ragu Lasagne",
        category=PRIMI,
        unit_label="serves 2",
        price=Money(amount_minor=1295, currency="GBP"),
        short_description="Layered fresh pasta with slow beef ragu and bechamel.",
        detail_description=(
            "A ready-to-bake lasagne built with fresh pasta sheets, long-cooked"
            " beef ragu, and creamy bechamel. It is generous enough for two"
            " supper portions."
        ),
        tags=("lasagne", "beef", "bake", "primo"),
        facets=DietaryFacets(),
        image_id="beef-ragu-lasagne-serves-2",
        display_order=3,
        is_available=True,
    ),
    CatalogSku(
        sku_id="parmigiana-melanzane-serves-2",
        name="Parmigiana di Melanzane",
        category=PRIMI,
        unit_label="serves 2",
        price=Money(amount_minor=1150, currency="GBP"),
        short_description=(
            "Aubergine, tomato, basil, and mozzarella baked until bubbling."
        ),
        detail_description=(
            "Slices of aubergine are layered with tomato sugo, mozzarella, basil,"
            " and parmesan. Warm it through for a comforting vegetarian primo."
        ),
        tags=("aubergine", "bake", "vegetarian", "primo"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id="parmigiana-melanzane-serves-2",
        display_order=4,
        is_available=True,
    ),
    CatalogSku(
        sku_id="potato-gnocchi-500g",
        name="Potato Gnocchi",
        category=PRIMI,
        unit_label="500g",
        price=Money(amount_minor=525, currency="GBP"),
        short_description="Soft potato gnocchi ready for sauce, butter, or pesto.",
        detail_description=(
            "Light dumplings made with potato and wheat flour for a simple"
            " weeknight primo. Pan-fry after boiling for crisp edges."
        ),
        tags=("gnocchi", "potato", "pasta", "vegan"),
        facets=DietaryFacets(is_vegetarian=True, is_vegan=True),
        image_id="potato-gnocchi-500g",
        display_order=5,
        is_available=True,
    ),
    CatalogSku(
        sku_id="pumpkin-sage-tortelloni-300g",
        name="Pumpkin and Sage Tortelloni",
        category=PRIMI,
        unit_label="300g",
        price=Money(amount_minor=725, currency="GBP"),
        short_description="Fresh tortelloni filled with roasted pumpkin and sage.",
        detail_description=(
            "Large pasta parcels are filled with sweet roasted pumpkin,"
            " mascarpone, and sage. Serve with brown butter and toasted"
            " hazelnuts."
        ),
        tags=("tortelloni", "pumpkin", "sage", "vegetarian"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id="pumpkin-sage-tortelloni-300g",
        display_order=6,
        is_available=True,
    ),
    CatalogSku(
        sku_id="tiramisu-cup-single",
        name="Tiramisu Cup",
        category=DESSERTS,
        unit_label="single portion",
        price=Money(amount_minor=475, currency="GBP"),
        short_description="Classic tiramisu layered in a ready-to-serve dessert cup.",
        detail_description=(
            "Mascarpone cream, espresso-soaked sponge, and cocoa are layered in"
            " an individual cup. It is chilled, balanced, and ready for a dinner"
            " finish."
        ),
        tags=("tiramisu", "coffee", "dessert", "vegetarian"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id="tiramisu-cup-single",
        display_order=1,
        is_available=True,
    ),
    CatalogSku(
        sku_id="cannoli-siciliani-two-pack",
        name="Cannoli Siciliani",
        category=DESSERTS,
        unit_label="two pack",
        price=Money(amount_minor=550, currency="GBP"),
        short_description=(
            "Crisp pastry shells filled with sweet ricotta and pistachio."
        ),
        detail_description=(
            "Two Sicilian cannoli filled shortly before packing so the shells"
            " stay crisp. Ricotta cream, citrus zest, and pistachio make them"
            " bright and rich."
        ),
        tags=("cannoli", "ricotta", "pistachio", "dessert"),
        facets=DietaryFacets(is_vegetarian=True),
        image_id="cannoli-siciliani-two-pack",
        display_order=2,
        is_available=True,
    ),
    CatalogSku(
        sku_id="lemon-polenta-cake-slice",
        name="Lemon Polenta Cake",
        category=DESSERTS,
        unit_label="slice",
        price=Money(amount_minor=395, currency="GBP"),
        short_description="Moist lemon polenta cake with almond and citrus syrup.",
        detail_description=(
            "A bright cake slice made with polenta, almond, lemon zest, and"
            " syrup. It is naturally gluten-free and ideal with espresso."
        ),
        tags=("cake", "lemon", "almond", "gluten-free"),
        facets=DietaryFacets(is_vegetarian=True, is_gluten_free=True),
        image_id="lemon-polenta-cake-slice",
        display_order=3,
        is_available=True,
    ),
    CatalogSku(
        sku_id="san-pellegrino-aranciata-330ml",
        name="San Pellegrino Aranciata",
        category=DRINKS,
        unit_label="330ml",
        price=Money(amount_minor=225, currency="GBP"),
        short_description="Sparkling orange soda with a gently bitter citrus finish.",
        detail_description=(
            "A chilled Italian aranciata with bright orange flavour and fine"
            " bubbles. Pair it with salty antipasti or a casual lunch."
        ),
        tags=("aranciata", "orange", "soft-drink", "aperitivo"),
        facets=DietaryFacets(
            is_vegetarian=True,
            is_vegan=True,
            is_gluten_free=True,
        ),
        image_id="san-pellegrino-aranciata-330ml",
        display_order=1,
        is_available=True,
    ),
    CatalogSku(
        sku_id="limonata-sparkling-330ml",
        name="Limonata Sparkling Lemonade",
        category=DRINKS,
        unit_label="330ml",
        price=Money(amount_minor=225, currency="GBP"),
        short_description=(
            "Crisp sparkling lemonade with sharp Sicilian lemon character."
        ),
        detail_description=(
            "A refreshing lemon soda with lively acidity and a clean finish."
            " Serve cold with pastries, picnic food, or a light antipasto."
        ),
        tags=("limonata", "lemon", "soft-drink", "vegan"),
        facets=DietaryFacets(
            is_vegetarian=True,
            is_vegan=True,
            is_gluten_free=True,
        ),
        image_id="limonata-sparkling-330ml",
        display_order=2,
        is_available=True,
    ),
    CatalogSku(
        sku_id="chianti-classico-750ml",
        name="Chianti Classico",
        category=DRINKS,
        unit_label="750ml",
        price=Money(amount_minor=1595, currency="GBP"),
        short_description=(
            "Medium-bodied Tuscan red wine with cherry and savoury spice."
        ),
        detail_description=(
            "A food-friendly Chianti with red cherry, dried herbs, and gentle"
            " tannins. Pour with lasagne, cured meats, or tomato-led primi."
        ),
        tags=("wine", "chianti", "red", "tuscan"),
        facets=DietaryFacets(
            is_vegetarian=True,
            is_gluten_free=True,
            contains_alcohol=True,
        ),
        image_id="chianti-classico-750ml",
        display_order=3,
        is_available=True,
    ),
    CatalogSku(
        sku_id="sugo-pomodoro-500g",
        name="Sugo al Pomodoro",
        category=PANTRY,
        unit_label="jar 500g",
        price=Money(amount_minor=575, currency="GBP"),
        short_description="Slow tomato sugo with basil for pasta, gnocchi, and bakes.",
        detail_description=(
            "Italian tomatoes are cooked down with olive oil, basil, and a"
            " little garlic. Keep a jar ready for fresh pasta or a quick"
            " parmigiana."
        ),
        tags=("sugo", "tomato", "sauce", "vegan"),
        facets=DietaryFacets(
            is_vegetarian=True,
            is_vegan=True,
            is_gluten_free=True,
        ),
        image_id="sugo-pomodoro-500g",
        display_order=1,
        is_available=True,
    ),
    CatalogSku(
        sku_id="pesto-genovese-180g",
        name="Pesto Genovese",
        category=PANTRY,
        unit_label="jar 180g",
        price=Money(amount_minor=650, currency="GBP"),
        short_description=(
            "Basil pesto with pine nuts, parmesan, and extra virgin olive oil."
        ),
        detail_description=(
            "A fragrant Ligurian-style pesto for tossing through pasta or"
            " spooning over vegetables. The jar is sized for two generous pasta"
            " suppers."
        ),
        tags=("pesto", "basil", "sauce", "vegetarian"),
        facets=DietaryFacets(is_vegetarian=True, is_gluten_free=True),
        image_id="pesto-genovese-180g",
        display_order=2,
        is_available=True,
    ),
    CatalogSku(
        sku_id="extra-virgin-olive-oil-500ml",
        name="Extra Virgin Olive Oil",
        category=PANTRY,
        unit_label="500ml",
        price=Money(amount_minor=1195, currency="GBP"),
        short_description="Peppery extra virgin olive oil for finishing and dipping.",
        detail_description=(
            "A balanced Italian olive oil with grassy aroma and a clean peppery"
            " finish. Use it for bread, salads, vegetables, and final drizzles."
        ),
        tags=("olive-oil", "dipping", "vegan", "pantry"),
        facets=DietaryFacets(
            is_vegetarian=True,
            is_vegan=True,
            is_gluten_free=True,
        ),
        image_id="extra-virgin-olive-oil-500ml",
        display_order=3,
        is_available=True,
    ),
)
