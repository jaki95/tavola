from tavola.infrastructure.catalog_repository import StaticCatalogRepository
from tavola.infrastructure.planner_mcp_server import (
    create_catalog_candidate_tool_handlers,
    run_stdio_server,
)


def main() -> None:
    run_stdio_server(
        create_catalog_candidate_tool_handlers(StaticCatalogRepository.from_seed())
    )


if __name__ == "__main__":
    main()
