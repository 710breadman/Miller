# Project status

Updated: 2026-07-05

## Current

Miller now has a usable no-AI local pipeline and substantial framework coverage
for later AI-assisted stages. The canonical roadmap is paused at `4.2 — Comic
evaluation set`, because a meaningful 100–300-query benchmark requires a
user-approved real comic corpus and human relevance labels.

The Windows target folder is `D:\_Codex\Miller`. This environment cannot mount
that drive, so a defensive installer applies and verifies the completed package
there in one command.

## Implemented

- Deterministic SQLite projects, stages, immutable attempts, events, documents,
  durable queues, cancellation, restart recovery, and scoped invalidation
- Content-addressed artifacts, atomic writes, integrity verification, safe cache
  pruning, and portable project round-trips
- Safe comic ingestion, page cache, thumbnails, incremental reconciliation,
  analysis schemas, conservative panel candidates, OCR contracts, masks,
  descriptions, quality metrics, and searchable local analysis storage
- Retrieval benchmark formats and metrics, BM25 baseline, external embedding
  workers, hybrid fusion, and Qdrant vector-store contract
- Audio inspection/normalization, WhisperX worker contract, script comparison,
  fallback word timing, and beat segmentation
- Automatic storyboard scope, search, ranking, alternatives, continuity/reuse
  handling, scene locks, timing, motion, and transitions
- Reproducible derived crops/masks/inpainting fallback chain
- FFmpeg rendering with narration, subtitles, looped music/ducking, transitions,
  manifests, scene cache, and partial rerendering
- Deterministic quality findings, repair plans, revisioned scene editing, and
  localhost-only FastAPI editor
- Evidence-led script factory, Ollama structured-output adapter, bounded queue
  workers, OpenTimelineIO export, and no-AI end-to-end video command
- Runtime capability/GPU profiles, typed settings, Windows installer, verifier,
  launcher, examples, and locked optional dependency groups

## Verification

```text
uv sync --frozen --extra dev --extra web --extra export --extra retrieval
uv run ruff check .
uv run mypy src
uv run pytest
uv build
```

Current result: **64 tests passed**; Ruff passed; strict Mypy passed across 82
source files; source distribution and wheel built successfully.

## Requires the local Windows machine or user decisions

- Apply and run the package at `D:\_Codex\Miller`
- Validate Windows junctions, long paths, GPU drivers, FFmpeg build, and RTX 3070
  memory/performance
- Create the real 100–300-query comic retrieval evaluation set
- Run measured OpenCLIP versus SigLIP 2 benchmarks on that corpus
- Run a pinned WhisperX model and verify real narration alignment
- Prove the pinned BallonsTranslator external adapter on representative pages
- Compare Revideo against native FFmpeg on the same two-minute fixture
- Test Resolve interchange with an installed Resolve version
- Select Miller's software license and approve private-corpus fixture policy
- Review subjective visual pacing, inpainting quality, and music/style preferences

## Recommended next action

Run `Install-Miller.cmd`, then execute `miller capabilities` and one
`baseline-video` project using a small real comic and narration sample. Preserve
that project as the first local acceptance fixture.
