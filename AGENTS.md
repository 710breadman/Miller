# Project instructions

## Goal

Build a local-first automatic YouTube production system that creates comic-first
videos from scripts, narration, research, and an indexed comic library.

## Ownership and safety

- Miller owns authoritative project, queue, provenance, storyboard, edit, repair,
  and render state in SQLite.
- Comic libraries, scripts, narration, music, and user media are read-only inputs.
- Derived data belongs only in Miller-managed project/cache directories.
- Never overwrite an existing output or delete a user file.
- External commands use argument arrays; never construct a shell command from input.
- Caches and Qdrant are rebuildable and never the sole copy of project state.
- Every worker result remains a proposal until schema, attempt guard, provenance,
  file existence, and hashes are validated by core.
- Keep loops bounded. Default repair limit is two passes.

## Dependency boundaries

- Core must remain usable without CUDA, PyTorch, Node, downloaded models, Ollama,
  Qdrant service, or OpenTimelineIO.
- OCR, WhisperX, embedding, inpainting, and LLM environments remain replaceable.
- Record exact executable, package, model, weight, prompt, and configuration versions.
- Keep GPL implementations external unless an explicit distribution decision permits
  otherwise.

## Source study

Before implementing a significant external capability:

1. Search this repository for existing work.
2. Inspect an approved upstream implementation and its exact revision.
3. Record interfaces, limits, tests, dependencies, licenses, and reusable concepts.
4. Prefer a typed adapter or proven design without inheriting an upstream app's state.
5. Add contract tests and a safe unavailable-tool failure path.

## Required verification

```text
uv sync --frozen --extra dev --extra web --extra export --extra retrieval
uv run ruff check .
uv run mypy src
uv run pytest
uv build
```

For release checkpoints, extract the package into a clean directory, repeat the
full gate, install the built wheel in a clean environment, and import `miller`.

## Codex procedure

1. Read `AGENTS.md`, `STATUS.md`, and `SPRINT_STATE.json`.
2. Respect the active canonical sub-sprint and recorded hardware/data blockers.
3. Inspect existing code and tests before changing behavior.
4. Keep source inputs untouched and preserve backward-compatible persisted data.
5. Implement a bounded, reviewable outcome.
6. Run the full gate and inspect generated media/manifests.
7. Update status, state, decisions, and exact local validation still required.
8. Stop at a stable checkpoint; never claim a real-model or visual gate passed
   without its actual evidence.
