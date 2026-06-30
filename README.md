# Miller

Local-first pipeline for producing comic-first YouTube videos from research,
scripts, edited narration, and an indexed comic library.

Status: Sprint 0 source audit complete. Active checkpoint: sub-sprint `1.1`
(Python package skeleton). Application implementation has not started. See
[STATUS.md](STATUS.md) and
[docs/TOOL_AUDIT.md](docs/TOOL_AUDIT.md).

## Product constraints

- Local web app: React UI + FastAPI service
- Deterministic, resumable SQLite-backed stages
- Read-only comic sources; content-addressed derived assets
- RTX 3070-compatible defaults
- One video project uses GPU at a time
- Native FFmpeg render path remains mandatory
- Optional integrations stay replaceable

## Current decision

Begin Sprint 1 with a narrow vertical foundation: typed project/stage schemas,
SQLite persistence, artifact hashing, deterministic failure/resume, and CLI.
No React UI, retrieval model, or renderer until that foundation passes.

## Repository map

- `docs/PRODUCT_SPEC.md` — full product outline
- `SPRINTS.md` — roadmap and sprint acceptance gates
- `SPRINT_STATE.json` — machine-readable active sub-sprint/progress
- `docs/SUB_SPRINT_TEMPLATE.md` — context-safe checkpoint format
- `docs/TOOL_AUDIT.md` — pinned upstream findings
- `docs/REUSE_MATRIX.md` — call/adapt/port/recreate/reject decisions
- `docs/LICENSE_MATRIX.md` — integration license boundaries
- `docs/CAPABILITY_MATRIX.md` — capability ownership
- `docs/ARCHITECTURE_CANDIDATES.md` — evaluated architecture choices
- `experiments/` — non-production proofs and audit verification

## Development

Project license has not been selected. Do not copy upstream source into this
public repository until project licensing and attribution policy are explicit.
