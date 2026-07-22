# Test plan

## Every change

```text
uv sync --frozen --extra dev --extra web --extra export --extra retrieval
uv run ruff check .
uv run mypy src
uv run pytest
uv build
```

## Automated coverage

The suite currently covers 64 tests across:

- Schemas, transitions, transactions, attempts, recovery, queues, and documents
- Content-addressed artifacts, scoped invalidation, and CLI restart/resume
- Comic discovery, archive safety, stable IDs, cache, thumbnails, and reconciliation
- Page/panel/OCR/mask/quality records and searchable analysis storage
- BM25 metrics, hybrid fusion, embedding-worker and Qdrant contracts
- Audio probing/normalization, mismatch diagnostics, timing, and beats
- Storyboard scope, ranking, exclusions, alternatives, reuse, locks, and coverage
- Derived crops/masks/inpainting fallback and source integrity
- FFmpeg streams, motion, transitions, subtitles, music ducking, determinism,
  scene caching, and partial rerender
- Quality findings, repair bounds, revisioned editor, web API, and stale-edit rejection
- Script stages, durable workers, project portability, OTIO export, runtime settings,
  cache pruning, and no-AI comic-to-MP4 execution

## Required local/manual suites

- Windows junctions, long paths, antivirus/file-lock behavior, and installer rollback
- Large private libraries and interrupted indexing
- Real OCR, OpenCLIP/SigLIP, WhisperX, inpainting, Ollama, and GPU lifecycle tests
- Visual/audio acceptance on representative projects
- Revideo and Resolve compatibility
- Final wheel clean-install, notices, and distribution review
