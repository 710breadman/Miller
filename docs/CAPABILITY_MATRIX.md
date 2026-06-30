# Capability matrix

| Capability | Miller owns | Adapter/tool | V1 status | Acceptance gate |
|---|---|---|---|---|
| Projects/jobs/stages | Schema, DB, invariants | SQLite | Sprint 1 | Fail/restart/resume deterministically |
| Artifact cache | Hashes, manifests, invalidation | Filesystem | Sprint 1 | Only dependents invalidate |
| Comic ingest | IDs, provenance, cache | CBZ/images | Sprint 2 | Changed issue only reprocesses changes |
| Text regions | Normalized masks/regions | BallonsTranslator proof + fallback | Sprint 3/7 | Sources untouched; reproducible outputs |
| OCR | Normalized text/coordinates | Candidate engines | Sprint 3 | Fixture searchable by OCR |
| Retrieval | Labels, hybrid rank, metrics | OpenCLIP/SigLIP 2 + Qdrant | Sprint 4 | Labeled benchmark winner |
| Narration timing | Script comparison schema | WhisperX | Sprint 5 | Reliable word/beat timestamps |
| Storyboard | Scene intent/scores/locks | Retrieval + rules + Ollama | Sprint 6 | Complete two-minute plan |
| Render | Scene render contract | FFmpeg; Revideo optional | Sprint 8 | Deterministic repeated render |
| Music/audio | Section states/mix policy | FFmpeg | Sprint 8 | Loudness/sync checks pass |
| Quality repair | Metrics, pass history, rollback | FFmpeg/probes/models | Sprint 9 | Improves only affected scenes |
| Scene editor | Overrides/locks | React | Sprint 10 | Partial fix/rerender |
| Script factory | Evidence/provenance/stages | Ollama + sources | Sprint 11 | Sourced repeatable script |
| Timeline export | Mapping/manifest | OpenTimelineIO | Sprint 12 | External timing/media round-trip |
| Subject masks | Selection/fallback | SAM 2 optional | Later proof | Fits hardware; no base dependency |
| Depth/parallax | Selection/fallback | Depth Anything V2 Small | Later proof | Fits hardware; visual benefit measured |

## Cross-cutting contracts

Every adapter returns:

- normalized typed output;
- exact tool/model/version;
- input/output hashes;
- structured warnings/errors;
- deterministic config;
- cancellation and timeout behavior;
- capability probe result.
