# Tavola Backend

FastAPI backend scaffold for the Tavola demonstrator.

## Local Setup

Install dependencies:

```sh
uv sync
```

Validate the package layout:

```sh
uv run python -c "import tavola.api, tavola.domain"
```

Run tests:

```sh
uv run pytest
```

Run quality checks:

```sh
uv run ruff check .
uv run ruff format --check .
```
