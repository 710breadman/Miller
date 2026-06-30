# Project status

Updated: 2026-06-29

## Current

Sprint 0 complete. Roadmap decomposed into small, independently verifiable
sub-sprints. Active checkpoint: `1.1 — Python package skeleton`. No production
application code exists yet.

## Decisions

- Core owns state and orchestration; no upstream app becomes source of truth.
- Implement deterministic SQLite stage runner in Sprint 1.
- Keep FFmpeg as mandatory render backend. Benchmark Revideo later.
- Wrap WhisperX public Python API behind a process-capable adapter.
- Adapt BallonsTranslator concepts/interfaces first; GPL code stays external
  unless project licensing decision explicitly permits reuse.
- Study StoryToolkitAI concepts only; do not copy GPL code.
- Use Qdrant Python client behind a vector-store protocol; local mode is
  acceptable for tests only.
- Benchmark OpenCLIP and SigLIP 2 on comic-specific labeled data.
- Keep SAM 2 and Depth Anything V2 optional, selective workers.
- Use OpenTimelineIO only for optional interchange.

## Risks

- Project license remains unset.
- Comic/model dataset rights require separate review from source-code licenses.
- RTX 3070 VRAM requires model lifecycle control and low-memory profiles.
- BallonsTranslator headless extraction may be costly because orchestration is
  coupled to Qt threads/config.
- Revideo proof must measure deterministic output, startup cost, memory, and
  FFmpeg escape hatches.

## Next

Execute only `1.1 — Python package skeleton`: add packaging/layout/test config;
verify clean install plus import smoke test. Do not begin schemas or DB.
