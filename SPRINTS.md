# Development sprints

## Sprint 0 — Source audit

Status: complete.

Goal: classify relevant upstream capabilities as call, adapt, port, recreate,
study, or reject before application implementation.

Deliverables:

- `docs/TOOL_AUDIT.md`
- `docs/REUSE_MATRIX.md`
- `docs/LICENSE_MATRIX.md`
- `docs/CAPABILITY_MATRIX.md`
- `docs/ARCHITECTURE_CANDIDATES.md`
- `docs/upstream-lock.json`
- minimal proof/audit scripts in `experiments/`

Acceptance:

- Exact upstream revisions recorded.
- Core capability and license boundaries classified.
- Renderer, comic text cleanup, alignment, retrieval, vector store, optional
  segmentation/depth, and timeline export choices have explicit next actions.
- No upstream code copied into core.

## Sprint 1 — Project foundation

Build Pydantic schemas, SQLite DB, artifact hashing, project directories,
deterministic stage state machine, structured logs, cancellation/resume, CLI.

Stop when a fake project can fail, restart, resume, and complete
deterministically while unchanged outputs keep stable hashes.

## Sprint 2 — Comic ingestion

CBZ/image-folder ingestion, read-only source policy, extraction cache, stable
IDs, thumbnails, file-change detection, incremental updates.

Stop when a changed issue reprocesses only changed material.

## Sprint 3 — Comic understanding

Panel candidates, OCR/text masks, balloon regions, descriptions, metadata,
quality scores, full-page preservation.

Stop when a test comic is searchable by OCR and metadata.

## Sprint 4 — Retrieval benchmark

Benchmark OpenCLIP/SigLIP 2, pages/panels, OCR/embeddings, hybrid ranking.

Stop when a reproducible labeled comic benchmark selects a configuration.

## Sprint 5 — Narration alignment

WhisperX adapter, script/audio comparison, word timing, sections/beats,
mismatch warnings.

Stop when narration beats reliably map to timestamps.

## Sprint 6 — Automatic storyboard

Scope proposal, steering, retrieval, continuity/reuse scoring, alternatives,
scene JSON.

Stop when a two-minute script creates a complete storyboard automatically.

## Sprint 7 — Text removal and derived assets

Clean-crop preference, masks, inpainting adapter, derived cache, fallback.

Stop when source pages remain untouched and outputs reproduce by hash.

## Sprint 8 — Renderer

Native FFmpeg renderer, Revideo comparison, camera presets, transitions,
subtitles, narration, music, draft/final profiles.

Stop when same project renders deterministically twice.

## Sprint 9 — Quality repair loop

Preview analysis, scene scoring, repair planning, partial renders, pass
comparison, bounded loops.

Stop when flawed fixture improves without rerendering unaffected scenes.

## Sprint 10 — Simple editor

Scene cards, replacement/alternatives, crop/focus, motion, music, scene locks,
partial rerender.

Stop when weak scene can be fixed without a professional editor.

## Sprint 11 — Script factory

Research modes, evidence ledger, framing, outline/draft, verification,
humanization, read-aloud checks, script queue.

Stop when one topic produces a sourced script through repeatable stages.

## Sprint 12 — Optional export

OTIO, media package, captions, metadata, Resolve interchange experiment.

Stop when an external editor opens a test project with correct timing/media.

## Sprint 13 — Packaging

Tool detection, config UI, hardware profile, cache management, portable
projects, Windows launcher, docs.
