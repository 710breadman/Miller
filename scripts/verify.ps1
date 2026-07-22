$ErrorActionPreference = 'Stop'

uv sync --frozen --extra dev --extra web --extra export --extra retrieval
uv run ruff check .
uv run mypy src
uv run pytest
uv build

Write-Host 'Miller verification passed.'
