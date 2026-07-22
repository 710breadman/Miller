# Miller authoritative architecture

Architecture revision: **2026-07-21-definitive**

## Decision summary

Preserve the existing **Python + FastAPI + SQLite + content-addressed artifacts + external worker + FFmpeg** foundation. Do not replace it with an orchestration framework, desktop shell, Node renderer, hosted vector service, or monolithic AI process before evidence requires that change.

The architecture must be strengthened in four places:

1. formal evidence levels and migration safety;
2. true end-to-end stage orchestration and worker lifecycle;
3. comic-specific observations and benchmarked retrieval;
4. global storyboard selection and visual review.

## Layered architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Local UI                                                            │
│ project wizard · queue · progress · visual storyboard · preview     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ versioned local API
┌──────────────────────────────▼──────────────────────────────────────┐
│ Application services                                                │
│ projects · library · pipeline · editor · evaluation · export        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ commands / immutable results
┌──────────────────────────────▼──────────────────────────────────────┐
│ Deterministic pipeline core                                         │
│ DAG · stage fingerprints · attempts · cancellation · invalidation   │
└──────────────┬───────────────────────────────┬──────────────────────┘
               │                               │
┌──────────────▼───────────────┐   ┌──────────▼──────────────────────┐
│ Miller-owned deterministic   │   │ Isolated optional workers       │
│ ingest, schemas, retrieval   │   │ OCR · VLM · embeddings          │
│ fusion, storyboard, FFmpeg   │   │ alignment · inpainting          │
└──────────────┬───────────────┘   └──────────┬──────────────────────┘
               │                               │ typed JSON protocol
┌──────────────▼───────────────────────────────▼──────────────────────┐
│ Data plane                                                          │
│ SQLite authority · immutable artifacts · rebuildable vector index  │
└─────────────────────────────────────────────────────────────────────┘
```

## Ownership boundaries

### SQLite owns

- projects and project configuration;
- library source identities and current fingerprints;
- stage definitions, runs, attempts, state transitions, and cancellation;
- document revisions and edit history;
- queue and worker lease state;
- normalized page/panel/region/observation records;
- provenance, model/tool versions, prompt versions, and evidence levels;
- evaluation labels and approved feedback;
- render manifests and release evidence.

### Immutable artifact store owns

- extracted/normalized source copies;
- page, panel, crop, mask, cleaned-image, and proxy files;
- alignment, analysis, retrieval, storyboard, render, and evaluation JSON;
- logs and benchmark outputs;
- content hashes.

### Rebuildable vector storage owns

- embeddings and filter payloads only;
- no irreplaceable project state;
- collection/model/schema version in every record.

### External workers own nothing authoritative

Workers receive a bounded request and return a proposal. Core verifies:

- protocol version;
- request/attempt guard;
- exact model/tool revision;
- source hashes;
- output schema and bounds;
- output file existence and hashes;
- warning/error structure;
- cancellation/timeout outcome.

## Canonical data flow

1. **Inventory**
   - identify source without mutation;
   - reject unsafe archives;
   - hash pages and record locators.
2. **Derive**
   - create managed page assets;
   - preserve orientation, spreads, and source provenance.
3. **Observe**
   - panels, balloons, text, reading order, OCR, visual semantics, quality;
   - observations are versioned and appendable, not silently overwritten.
4. **Index**
   - normalized text index;
   - image/text embeddings;
   - metadata filters;
   - rebuildable vector collections.
5. **Interpret**
   - narration alignment;
   - script beats and scene intent;
   - search scope and constraints.
6. **Retrieve**
   - BM25 + embedding candidates;
   - fusion and optional top-N rerank;
   - retain scores and alternatives.
7. **Plan**
   - global storyboard optimization;
   - continuity, relevance, quality, reuse, and pacing constraints;
   - user locks are hard constraints.
8. **Prepare visuals**
   - select page/panel/crop;
   - avoid text first; mask/inpaint only when needed;
   - composition-aware focus and safe motion.
9. **Render**
   - render to a temporary managed output;
   - probe, quality-check, hash, then atomically promote;
   - never overwrite.
10. **Review and revise**
    - show candidates, evidence, and preview;
    - invalidate only affected dependents;
    - partial rerender.
11. **Export**
    - final MP4 plus deterministic manifest;
    - optional OTIO/Resolve interchange.

## Observation model

A page must not have one unqualified “AI description.” Store independent observations:

- `panel_detection`;
- `text_region_detection`;
- `balloon_detection`;
- `reading_order`;
- `ocr_transcript`;
- `visual_caption`;
- `character_occurrence`;
- `location_action_emotion`;
- `quality_measurement`;
- `scene_relation`.

Each observation records:

- source asset ID and geometry;
- detector/model/tool and exact revision;
- prompt/config version;
- confidence and uncertainty;
- evidence level;
- input/output hashes;
- creation time;
- superseded-by relationship;
- warnings;
- human approval state.

This allows reanalysis without destroying earlier results.

## Panel and page identity

- A page ID remains content-derived.
- A panel ID is derived from page ID + detector version + normalized geometry.
- Reanalysis creates a new panel-observation set; it does not silently reuse an old panel ID when geometry changes.
- Editorial references use stable source page plus explicit crop geometry and analysis revision.
- Whole-page candidates remain valid for splash pages or failed segmentation.

## Retrieval architecture

### Baselines

- BM25 remains mandatory and becomes the floor.
- Candidate embeddings: SigLIP 2 NaFlex base, OpenCLIP baseline, and Qwen3-VL-Embedding-2B.
- Vector backends: current Qdrant adapter and sqlite-vec proof.
- Fusion starts with reciprocal-rank fusion; score calibration is optional only when labels support it.
- Reranking is top-N only and must justify latency/VRAM.

### Query classes

Evaluate separately:

- concrete character/action;
- location/object;
- dialogue/OCR;
- abstract emotion/theme;
- continuity/sequence;
- costume/era/series constraints;
- negative/exclusion queries.

### Selection

Do not pick each beat greedily in isolation. Build a candidate lattice and optimize the sequence with:

- relevance;
- source scope;
- character continuity;
- visual continuity;
- emotional fit;
- technical quality;
- text-removal cost;
- recent-use and whole-video reuse penalties;
- page-order coherence where appropriate;
- locked scenes.

## Audio architecture

- Edited narration is authoritative.
- WhisperX is the primary candidate, isolated in a pinned environment.
- stable-ts is the fallback benchmark.
- Uniform timing remains an explicit provisional fallback, never a word-alignment pass.
- Alignment stores word coverage, confidence, unmatched script/audio spans, drift, and review state.

## Rendering architecture

Native FFmpeg remains mandatory.

Required hardening:

- temporary output in the same destination filesystem;
- FFprobe and stream validation before promotion;
- atomic rename/promotion;
- cancellation and progress events;
- scene-level cache and partial render;
- deterministic manifest;
- CPU default and measured NVENC option;
- subtitles off by default;
- source, crop, mask, motion, transition, audio, and tool provenance.

Revideo remains an optional comparison, not a dependency.

## UI architecture

The current inline editor is a prototype. The product UI should be a local web client over stable APIs.

Order:

1. define information architecture and API contracts;
2. project/import wizard;
3. queue/progress/recovery;
4. visual storyboard timeline with thumbnails and alternatives;
5. scene preview and partial rerender;
6. only then choose whether React materially improves maintenance.

Do not introduce Tauri/Electron before the full workflow passes in a browser.

## Migration and recovery architecture

- `schema_migrations` table with one immutable row per migration;
- ordered migration files/functions;
- preflight integrity check;
- backup before a migration that changes persisted user data;
- one transaction where SQLite supports it;
- application version compatibility check;
- post-migration integrity and data invariants;
- rollback by restoring verified backup, not reverse SQL by default;
- cache/vector rebuild procedure separate from authoritative DB restore.

## Dependency map

```text
Evidence taxonomy + local acceptance
         │
         ├── migration safety ──┐
         ├── baseline DAG ──────┼── reliable minimum usable milestone
         └── approved fixtures ─┘
                         │
       comic labels + analysis benchmark
                         │
       retrieval benchmark and winner ADR
                         │
       real alignment + beat intent
                         │
       global storyboard optimizer
                         │
       text-free visual prep + renderer hardening
                         │
       visual editor + human rubric + golden project
                         │
       clean Windows package + release evidence
```

## Critical path

1. `ENV-001` local environment truth.
2. `ENV-002` approved fixture.
3. `ARC-001` migration safety.
4. `ARC-002` durable baseline DAG.
5. `ENV-003` and `ENV-004` minimum-usable acceptance.
6. `ANL-001` observation/evaluation schema.
7. `RET-001` and `RET-002` real relevance labels.
8. `ANL-002`–`ANL-006` measured comic analysis.
9. `RET-003`–`RET-007` measured retrieval winner.
10. `AUD-001`–`AUD-002` real timing.
11. `STO-001`–`STO-005` coherent storyboard.
12. `VID-001`–`VID-005` polished visual/render loop.
13. `UX-001`–`UX-004`, `QAE-001`–`QAE-003`.
14. `REL-001`–`REL-002`.

## Parallel work

- license/SBOM work can run beside local acceptance;
- UI information architecture can run after API/data contracts stabilize, before model selection completes;
- alignment worker setup can run beside retrieval labels;
- archive fuzzing can run beside analysis benchmarks;
- OTIO/Resolve remains outside the critical path;
- advanced character re-ID and parallax remain post-v1.

## Rejected architectural directions

- replacing SQLite authority with Qdrant;
- using LangGraph/CrewAI/AutoGen as the pipeline state machine;
- making Revideo, Node, Chromium, Ollama, CUDA, or Qdrant service mandatory;
- storing only one mutable AI result per page;
- greedy per-beat selection as the final storyboard algorithm;
- embedding the future product UI permanently inside one Python string;
- self-modifying or self-training behavior without approved labels;
- rebuilding the foundation before local evidence shows it is inadequate.
