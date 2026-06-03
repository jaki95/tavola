def test_backend_layer_packages_are_importable() -> None:
    import tavola.api
    import tavola.application
    import tavola.config
    import tavola.domain
    import tavola.infrastructure

    assert tavola.api is not None
    assert tavola.application is not None
    assert tavola.config is not None
    assert tavola.domain is not None
    assert tavola.infrastructure is not None
