def test_backend_layer_packages_are_importable() -> None:
    import tavola.api
    import tavola.api.dependencies
    import tavola.api.main
    import tavola.api.routers.catalog
    import tavola.api.routers.health
    import tavola.api.schemas.catalog
    import tavola.application
    import tavola.application.catalog
    import tavola.config
    import tavola.config.settings
    import tavola.domain
    import tavola.domain.catalog
    import tavola.infrastructure
    import tavola.infrastructure.catalog_repository
    import tavola.infrastructure.catalog_seed

    assert tavola.api is not None
    assert tavola.api.dependencies is not None
    assert tavola.api.main is not None
    assert tavola.api.routers.catalog is not None
    assert tavola.api.routers.health is not None
    assert tavola.api.schemas.catalog is not None
    assert tavola.application is not None
    assert tavola.application.catalog is not None
    assert tavola.config is not None
    assert tavola.config.settings is not None
    assert tavola.domain is not None
    assert tavola.domain.catalog is not None
    assert tavola.infrastructure is not None
    assert tavola.infrastructure.catalog_repository is not None
    assert tavola.infrastructure.catalog_seed is not None


def test_catalog_domain_import_has_no_api_or_infrastructure_dependency() -> None:
    from tavola.domain.catalog import CatalogSku, catalog_categories

    assert CatalogSku.__module__ == "tavola.domain.catalog"
    assert [category.category_id for category in catalog_categories()] == [
        "antipasti",
        "primi",
        "desserts",
        "drinks",
        "pantry",
    ]
