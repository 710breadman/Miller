# Miller

Local-first pipeline for producing comic-first YouTube videos from research,
scripts, edited narration, and an indexed comic library.

## Branch status

This branch establishes the first executable foundation:

- installable `src/` Python package;
- Pydantic project, stage, attempt, artifact, and event records;
- strict Ruff, Mypy, Pytest, and build configuration;
- import smoke test;
- lightweight core dependencies only.

Heavy OCR, audio alignment, retrieval, rendering, and local-model dependencies
will remain outside the core package behind replaceable worker interfaces.

## Verify

```powershell
uv sync --extra dev
uv run ruff check .
uv run mypy src
uv run pytest
uv build
```

See `STATUS.md` and `SPRINT_STATE.json` for the next checkpoint.
