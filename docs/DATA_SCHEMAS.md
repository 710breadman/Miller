# Current data schemas

Executable definitions live under `src/miller/`. Persisted records are strict,
immutable Pydantic models unless they represent an explicit revision or queue state.

## Authoritative SQLite records

- Projects, stage definitions/runs, immutable attempts, artifacts, events
- Revisioned project documents for analyses, storyboards, scripts, and renders
- Durable script/video/library queue items and restart recovery state

## Comic and analysis records

- Read-only comic sources, ordered pages, inventories, cached pages, thumbnails
- Normalized boxes, panel candidates, OCR spans/results, text masks
- Page descriptions and deterministic technical-quality measurements
- Reconciliation records and searchable analysis documents

## Retrieval records

- Labeled evaluation queries and relevance judgments
- Ranked assets, run configuration, latency, Recall@K, MRR, and nDCG
- External embedding-worker results
- Rebuildable vector points/matches with scalar filter payloads

## Audio and storyboard records

- Media probe and normalized-audio artifacts
- Words, mismatch operations, timed sections, and visual beats
- Search scope, candidate scores, alternatives, scene locks, camera/motion,
  transitions, music state, warnings, and review status

## Video, quality, and editing records

- Manual render requests/profiles and FFmpeg manifests
- Cached scene segments and final assembly manifests
- Technical/editorial findings and bounded repair proposals
- Revisioned editor commands with optimistic-concurrency checks

## Script/export/runtime records

- Evidence sources/claims, framing, outline, draft, verification, and final script
- Portable-project and OpenTimelineIO export manifests
- Capabilities, GPUs, hardware profiles, settings, and cache plans

Persisted schema changes require migration or an explicit artifact schema version.
Never silently reinterpret old data.
