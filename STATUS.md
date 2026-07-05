# Project status

Updated: 2026-07-05

## Current

Sub-sprint `1.1 — Python package skeleton` is implemented on this branch and
remains the active checkpoint until branch CI and review complete.

## Implemented

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

## Gate

Run the package install, lint, strict typing, tests, build, and clean import.
After review, mark `1.1` complete and advance once to `1.2`.
