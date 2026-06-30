# Architecture candidates

## Selected baseline

React local UI → FastAPI service → SQLite-backed deterministic stage runner →
typed adapters → SQLite + Qdrant + content-addressed cache → external tools.

Why:

- Clear state ownership and restart semantics.
- Python matches media/ML ecosystem.
- Tool processes isolate dependency/VRAM failures.
- React can arrive after CLI/core contracts stabilize.

## Candidate A — Native FFmpeg renderer

Status: selected mandatory baseline.

Build scenes into explicit filter graphs/segments. Persist command args, probe
data, intermediate hashes, and encode metadata. Benefits: smallest runtime,
direct control, good Windows availability. Cost: complex rich animation and
preview authoring.

## Candidate B — Revideo renderer

Status: optional, benchmark required in Sprint 8.

Run as Node worker receiving Miller scene JSON and emitting progress/artifact
manifest. Benefits: declarative TypeScript scenes, preview, reusable effects.
Costs: Puppeteer/Chromium/Vite lifecycle, ports, memory, packaging. Failure must
fall back to native renderer where scene features permit.

## Candidate C — MoneyPrinterTurbo-derived application

Status: rejected.

Adapting its monolithic task service would front-load migration debt. Miller
needs per-stage hashes, invalidation, immutable attempts, scene alternatives,
locks, partial repair, and comic provenance from first principles.

## Candidate D — StoryToolkitAI-derived application

Status: rejected.

Useful editorial/search ideas, but GPL-3.0 and JSON/thread-oriented queue/project
state conflict with core ownership and transactional requirements.

## Process boundaries

- **Core process:** FastAPI, schemas, SQLite transitions, scheduling.
- **GPU worker:** one expensive model at a time; explicit load/unload.
- **Renderer worker:** FFmpeg subprocess; optional Node/Revideo process.
- **Vector service:** local Qdrant; rebuildable from SQLite/artifacts.
- **Optional GPL worker:** user-installed/pinned external tool only after proof
  and distribution review.

## Stage-state invariant

Only core transitions stage state. Workers emit proposals/events. Core validates
artifact existence, hash, schema, and expected attempt ID before committing
completion. Stale worker output never overwrites current state.

## Sprint 1 schema direction

Minimum entities:

- `Project`
- `Artifact`
- `StageDefinition`
- `StageRun`
- `StageDependency`
- `Event`
- `ToolInvocation`

Minimum states:

`pending`, `running`, `completed`, `failed`, `skipped`, `invalidated`,
`cancelled`.
