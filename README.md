# Miller

Miller is a local-first comic-to-video production system. It can safely inspect
and analyze comic folders or CBZ files, align narration, build a traceable
storyboard, render an MP4, preserve revisions, and resume durable work after a
restart. AI tools improve individual stages but are not required for the basic
pipeline.

## What works now

- Read-only image-folder and CBZ ingestion with archive safety limits
- Stable page IDs, extraction cache, thumbnails, incremental reconciliation
- Page/panel records, conservative panel detection, OCR adapter, text masks,
  descriptions, technical quality scores, and searchable analysis storage
- BM25 retrieval benchmarks, metric calculation, embedding-worker contracts,
  hybrid score fusion, and a rebuildable Qdrant adapter
- Audio probing/normalization, WhisperX worker boundary, mismatch diagnostics,
  and deterministic fallback timing
- Automatic storyboard construction with scope steering, exclusions, continuity,
  reuse control, alternatives, locks, motion, and transitions
- Text-free crop preference, mask provenance, external inpainting boundary, and
  deterministic local fallback assets
- FFmpeg rendering with narration, subtitles, music ducking, transitions, and
  scene-level caching for partial rerenders
- Technical/editorial quality findings and bounded repair proposals
- Revisioned scene editor with optimistic locking and a localhost-only web UI
- Durable script/video/library queues and restart recovery
- Evidence-led script stages with local Ollama structured-output support
- Portable project archives and optional OpenTimelineIO export
- Capability detection, RTX 3070/low-memory/CPU profiles, safe cache pruning,
  Windows install/verify/launch scripts, and a no-AI end-to-end command

## Install from the current checkout

Extract the release archive anywhere, then double-click:

```powershell
.\Install-Miller.cmd
```

Or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\APPLY_TO_D_CODEX_MILLER.ps1
```

The installer detects its checkout/workspace paths, creates a backup outside the Git
worktree, preserves dirty Git work, creates a new branch when possible, copies
without deleting user files, installs locked dependencies from public PyPI, and
runs the complete verification gate.

If an earlier installer stopped while downloading dependencies, run:

```powershell
.\Repair-Miller-Install.cmd
```

The repair resumes the existing installation; it does not recopy or remove user files.

## Verify or launch

```powershell
.\VERIFY_MILLER.ps1
.\RUN_MILLER.ps1
```

The editor opens on `http://127.0.0.1:8765` by default.

## Produce a basic video without AI

```powershell
uv run miller --db .miller\miller.sqlite3 baseline-video `
  --project-id project_demo `
  --workspace .miller\workspace `
  --comic "D:\Comics\Example.cbz" `
  --script "D:\Scripts\example.txt" `
  --narration "D:\Audio\example.wav" `
  --output "D:\Renders\example.mp4"
```

Add `--no-ocr` when Tesseract is unavailable. Use `--steering`, `--exclude`,
`--music`, and `--subtitles` as needed.

## Development

```powershell
uv sync --frozen --extra dev --extra web --extra export --extra retrieval
uv run ruff check .
uv run mypy src
uv run pytest
uv build
```

## Important boundaries

- Comic libraries, scripts, narration, music, and user media are never overwritten.
- Render/export commands refuse to overwrite existing outputs.
- Derived files stay below a Miller-managed workspace.
- SQLite owns authoritative state; Qdrant and caches are rebuildable.
- External tools receive argument arrays rather than shell command strings.
- AI output remains a proposal until schema and provenance validation pass.
- Heavy model environments remain replaceable and separate from the core package.
- Miller's software license is still an owner decision; upstream source has not
  been copied into the project.

See `STATUS.md`, `SPRINT_STATE.json`, `docs/IMPLEMENTATION_REPORT.md`, and
`docs/LOCAL_WINDOWS_SETUP.md`.
