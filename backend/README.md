# Tavola Backend

FastAPI backend scaffold for the Tavola demonstrator.

## Local Setup

Install dependencies:

```sh
uv sync
```

Run the development API server:

```sh
uv run uvicorn tavola.api.main:app --reload
```

The API is available at `http://localhost:8000` by default. The scaffold health
endpoint is `GET /api/health`.

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

Apply formatting:

```sh
uv run ruff format .
```
