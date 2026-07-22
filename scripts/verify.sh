#!/usr/bin/env sh
set -eu

uv sync --frozen --extra dev --extra web --extra export --extra retrieval
uv run ruff check .
uv run mypy src
uv run pytest
uv build

printf '%s\n' 'Miller verification passed.'
