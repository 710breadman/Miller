# Project status

Updated: 2026-07-05

## Current

Sub-sprint `1.1 — Python package skeleton` is complete on this branch. The next
checkpoint is `1.2 — Core domain schemas`.

## Completed

- `pyproject.toml` with a `src/` package layout
- Python 3.11+ package metadata
- Lightweight Pydantic and Pillow core dependencies
- Ruff, strict Mypy, Pytest, and wheel-build configuration
- Package version and import smoke test
- Initial immutable domain records for projects, stages, attempts, artifacts,
  and events

## Boundary

CUDA, PyTorch, OCR, WhisperX, retrieval models, Node, and local language models
are intentionally excluded from the core environment. They will use replaceable
worker interfaces later.

## Next

Complete `1.2`: add explicit stage transition rules, schema round-trip tests,
and invalid-state tests. Do not begin SQLite persistence or CLI execution in
that checkpoint.
