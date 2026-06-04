import subprocess
import sys


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
    script = """
import importlib
import sys

catalog = importlib.import_module("tavola.domain.catalog")
leaked_modules = sorted(
    name
    for name in sys.modules
    if name == "tavola.api"
    or name.startswith("tavola.api.")
    or name == "tavola.infrastructure"
    or name.startswith("tavola.infrastructure.")
)

if leaked_modules:
    print("\\n".join(leaked_modules))
    raise SystemExit(1)

assert catalog.CatalogSku.__module__ == "tavola.domain.catalog"
assert [category.category_id for category in catalog.catalog_categories()] == [
    "antipasti",
    "primi",
    "desserts",
    "drinks",
    "pantry",
]
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout or result.stderr
