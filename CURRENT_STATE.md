# Miller current-state assessment

Assessment date: **2026-07-21**  
Repository: `710breadman/Miller`  
Inspected branch: `main` at merge commit `4bf034d27e77ae3652ee5eed8ce96da21768513b`

## Executive assessment

Miller is **not a blank project**. It has a coherent Python foundation, strong ownership boundaries, typed contracts, SQLite state, safe CBZ handling, a deterministic stage runner, optional worker boundaries, lexical retrieval, storyboard contracts, revisioned editing, FFmpeg rendering, packaging scripts, and a useful synthetic test suite.

It is also **not yet a proven comic-understanding or production-quality video system**. The current end-to-end baseline uses filename/OCR text, simple white-gutter panel heuristics, uniform audio timing, greedy lexical scene selection, and synthetic media tests. Most model-backed integrations are contracts without a shipped worker environment or real-corpus evidence. The local web interface is a minimal inline prototype.

The correct next move is to preserve the foundation, formalize evidence levels, complete local Windows acceptance, make the baseline use the durable DAG, then benchmark comic analysis and retrieval on owner-approved labels.

## Evidence levels

| Code | Meaning | Current examples |
|---|---|---|
| E0 | Documented intent only | React product UI, advanced character re-ID |
| E1 | Typed contract or scaffold | WhisperX and embedding subprocess adapters |
| E2 | Automated synthetic test | 64-test suite, generated tone and tiny images |
| E3 | Local hardware pass | not yet recorded for current Windows/RTX target |
| E4 | Real-corpus quantitative pass | not yet recorded for retrieval, OCR, panel detection |
| E5 | Human visual/audio acceptance | not yet recorded |
| E6 | Clean-machine release acceptance | not yet recorded |

No capability may be called “complete and verified” without naming the highest evidence level reached.

## What is proven

- Python package builds and imports in the recorded Linux container.
- Ruff, strict mypy, pytest, and wheel/sdist verification passed in the recorded environment.
- SQLite stage, attempt, artifact, queue, document revision, invalidation, and abandoned-run recovery contracts have tests.
- CBZ inventory rejects unsafe paths, suspicious sizes, duplicate normalized paths, encrypted entries, and suspicious compression ratios.
- The source comic remains read-only; derived pages are copied to managed storage.
- The native FFmpeg renderer refuses an existing output, validates source files, records hashes and command data, probes the result, supports narration/music/subtitles, and renders deterministic scene motion contracts.
- Revisioned storyboard edits support locks, alternatives, optimistic conflict detection, history, and dependent-stage invalidation.
- A synthetic no-AI baseline reaches an MP4 when FFmpeg is available.
- Optional heavy dependencies are kept outside the core import path.

## What lacks proof

- the installer and launch scripts on the owner’s current `V:\AI\Miller` checkout;
- Windows long paths, drive letters, antivirus behavior, subprocess shutdown, and GPU recovery;
- real CBZ/folder collections with ads, double-page spreads, corrupt scans, irregular panels, borderless art, manga order, mixed file names, and very large issues;
- comic-specific panel, balloon, text, and reading-order accuracy;
- OCR accuracy on representative lettering;
- semantic VLM descriptions, characters, locations, actions, emotions, and scene relationships;
- real multimodal retrieval quality;
- real word-level narration alignment;
- global storyboard quality and emotional continuity;
- text removal and inpainting quality;
- product-grade visual editing and partial rerender;
- target-hardware speed/VRAM;
- clean-machine packaging and distribution license.

## System map

```text
User media (read-only)
  ├─ comic folders / CBZ
  ├─ script / brief / evidence
  ├─ narration
  └─ optional music
        │
        ▼
Safe ingest and immutable source inventory
        │
        ▼
Derived page/panel/region assets
        │
        ├─ OCR / text / balloon / reading order
        ├─ visual semantic observations
        ├─ character and scene observations
        └─ quality and provenance
        │
        ▼
SQLite authoritative metadata + rebuildable vector index
        │
        ▼
Beat interpretation → lexical/vector retrieval → rerank
        │
        ▼
Global storyboard plan + alternatives + locks
        │
        ▼
Audio alignment + shot/motion/text-free planning
        │
        ▼
FFmpeg render → quality checks → bounded repair
        │
        ├─ simple local editor and partial rerender
        └─ optional OTIO/Resolve export
```

## Subsystem inventory

| Subsystem | Intended purpose | Current status | Relevant files | Proven | Missing or weak | Next action |
|---|---|---|---|---|---|---|
| Project/state database | authoritative projects, stages, attempts, queue, documents, events | implemented foundation | `src/miller/db.py`, `models.py`, `transitions.py` | E2 transaction and recovery tests | explicit ordered migrations, backup/restore, corruption drills | `ARC-001` |
| Artifact store | immutable content-addressed outputs and hashes | implemented foundation | `artifacts.py`, `runtime/cache.py` | E2 cache/invalidation tests | large-cache performance and Windows path proof | `ENV-004`, `VID-004` |
| Pipeline runner | deterministic DAG, cache, cancellation, retries | implemented but not used by baseline | `runner.py` | E2 isolated DAG tests | baseline composition and real restart | `ARC-002` |
| Queue | persistent bounded work | partial | `workers.py`, DB queue tables | E2 claim/complete/fail contracts | leases/heartbeat, worker death, priorities, project/GPU policy | `ARC-003` |
| Folder/CBZ ingest | safe read-only source inventory | strong implementation | `comics/` | E2 archive safety and changed-source tests | CBR/PDF, malformed real archives, double-page semantics | `ENV-002`, `SEC-001` |
| Page derivation | managed source copies/crops/masks | implemented contracts | `derived/` | E2 deterministic output tests | production crop policy, panel asset identity across reanalysis | `ANL-001` |
| Panel detection | identify usable panels/regions | heuristic only | `analysis/panels.py` | E2 synthetic white-gutter cases | irregular/borderless panels, manga, splashes, spreads | `ANL-002` |
| Text/balloon detection | locate lettering and removable regions | scaffold/heuristic | `analysis/ocr.py`, `masks.py` | E2 geometry contracts | comic-trained detector and mask accuracy | `ANL-002`, `VID-001` |
| OCR | searchable text | Tesseract adapter/fallback | `analysis/ocr.py`, `pipeline.py` | E2 optional adapter behavior | measured comic OCR, preprocessing winner, language routing | `ANL-004` |
| Visual semantics | descriptions, characters, locations, actions, emotions | largely missing | normalized models exist in `analysis/models.py` | E1 schema | real VLM worker, evidence/confidence, reanalysis versioning | `ANL-005`, `ANL-006` |
| Character continuity | track occurrences/identity | missing/experimental | no production subsystem | E0 | detections, anchors, clustering, re-ID evaluation | `ANL-007`, `ADV-001` |
| Scene/sequence analysis | connect adjacent panels/pages | missing | no production subsystem | E0 | scene boundaries, speaker relationships, continuity graph | `ANL-008` |
| Lexical retrieval | BM25 text search | implemented baseline | `retrieval/lexical.py` | E2 ranking tests | tokenizer/language limits, panel records, real labels | `RET-003` |
| Embeddings | text-image semantic matching | contract only | `retrieval/embedding_worker.py` | E1 JSON validation | worker implementations and target-hardware measurements | `RET-004` |
| Vector store | rebuildable metadata-filtered vectors | Qdrant adapter | `retrieval/qdrant_store.py` | E2 memory/persisted tests | local service packaging, sqlite-vec comparison | `RET-006` |
| Hybrid ranking | combine lexical and vector scores | simple min-max fusion | `retrieval/hybrid.py` | E2 contract tests | calibration, RRF, rerank, query classes | `RET-007` |
| Retrieval evaluation | choose a winner by evidence | framework present | `retrieval/benchmark.py`, `metrics.py` | E2 metric calculations | 100–300 private labels and real runs | `RET-001`–`RET-007` |
| Audio probe/normalize | inspect and prepare narration | implemented contracts | `audio/probe.py`, `normalize.py` | E2 FFmpeg/synthetic tests | owner narration acceptance and failure handling | `AUD-002` |
| Alignment | word/beat timing | external contract + uniform fallback | `audio/whisper_worker.py`, `uniform.py` | E1 worker schema, E2 fallback | installed WhisperX/stable-ts, accuracy and drift | `AUD-001`, `AUD-002` |
| Beat segmentation | turn alignment/script into beats | implemented heuristics | `audio/beats.py` | E2 data tests | semantic beat intent and pacing validation | `STO-001` |
| Storyboard builder | choose candidates and scene timing | functional heuristic | `storyboard/builder.py` | E2 synthetic plan tests | semantic retrieval, panel selection, global sequence optimization | `STO-002`, `STO-003` |
| Shot/motion planning | focus, crop, movement, transitions | simple heuristics | `storyboard/builder.py`, `video/ffmpeg.py` | E2 command/render tests | composition-aware safe zones and emotional pacing | `STO-004` |
| Native render | deterministic MP4 | strongest media subsystem | `video/ffmpeg.py` | E2 render/probe/frame checksum | atomic promotion, progress/cancel, partial render, target speed | `ARC-004`, `VID-003`–`VID-005` |
| Music | quiet adaptive background and ducking | basic mix contract | `music/`, `video/ffmpeg.py` | E2 mix command tests | section-aware selection, loudness rubric, loop transitions | `QAE-001` |
| Quality/repair | detect and repair weak scenes | heuristic contract | `quality/` | E2 bounded repair tests | real quality signals, render loop integration, human proof | `QAE-001`–`QAE-003` |
| Storyboard editor | revisions, alternatives, locks | backend strong; UI prototype | `editor/`, `web/app.py` | E2 API/conflict tests | thumbnails, timeline, preview, undo UX, progress/retry | `UX-001`–`UX-004` |
| Script factory | sourced structured script stages | implemented contract | `script_factory/` | E2 claim-ID validation tests | real provider quality, research capture, owner style evaluation | after strong v1 |
| OTIO export | optional complex timeline | implemented adapter | `export/otio.py` | E2 optional roundtrip | Resolve compatibility on owner machine | `ADV-003` |
| Portable package | project export/import | implemented contract | `portable/` | E2 manifest checks | large project, missing optional assets, cross-machine proof | `REL-001` |
| Windows install/launch | simple local deployment | scripts exist | `*.ps1`, `*.cmd` | syntax/packaging evidence | actual current machine and path proof | `ENV-001`, `REL-001` |
| CI | repeatable quality gates | implemented | `.github/workflows/ci.yml` | Linux/Windows matrix configured | current run inspection and artifact retention policy | `QAE-003` |
| Licensing | allow safe distribution | unresolved | `docs/LICENSE_DECISION.md`, matrices | boundaries documented | owner license, dependency/model notices, SBOM | `SEC-002`, `REL-002` |

## Current gap classification

### Complete and verified to E2

- core package boundary;
- source-safe CBZ inventory;
- SQLite stage/document contracts;
- artifact hashing and dependency invalidation;
- basic lexical retrieval;
- storyboard data/revision contracts;
- native FFmpeg command/render contracts;
- optional dependency isolation;
- synthetic package and CLI baseline.

### Complete but not locally validated

- Windows installer/launcher;
- FFmpeg baseline on owner machine;
- portable project packaging;
- Qdrant persisted/local behavior;
- OTIO export against an actual editor.

### Partially implemented

- durable end-to-end orchestration;
- queue worker lifecycle;
- panel detection;
- OCR;
- hybrid retrieval;
- storyboard quality;
- quality repair;
- web editor;
- script factory.

### Scaffold only

- WhisperX worker;
- embedding worker;
- external inpainting/removal integrations;
- advanced model capability probes.

### Missing

- real VLM semantic analysis;
- character occurrence/identity and scene graph;
- human label workflow;
- calibrated multimodal retrieval winner;
- global storyboard optimization;
- product-grade UI;
- release-grade migration and backup system.

### Blocked

- real-corpus and subjective gates require owner-approved comics and narration;
- target GPU measurements require the Windows machine;
- distribution requires owner license choice;
- Resolve compatibility requires supported Resolve installation.

## Technical debt with highest leverage

1. Baseline bypasses the durable DAG, so resume claims are broader than current end-to-end behavior.
2. Schema upgrades are additive initialization rather than a formal migration ledger with pre-migration backup.
3. Evidence claims are spread across status, reports, and sprint state without a shared evidence level.
4. Current sprint state says the active item is also blocked; the state model needs separate active work and fallback-ready work.
5. `SPRINTS.md` compresses major model, integration, validation, and recovery work into broad items unsuitable for Gemma 4 12B.
6. The HTML editor is embedded in Python and cannot yet support the intended visual workflow.
7. Retrieval is page-centric and greedy; the product needs panel/page mixed candidates and global continuity.
8. Model adapters validate JSON shape but need process lifecycle, version manifests, resource isolation, and retry/cancel semantics.
9. Real quality acceptance has no stable owner rubric or golden project.
10. Product-duration and checkout-path documents contain stale values.

## Recommended immediate action

Run `ENV-001` from `docs/sprints/ENV-001.md`: verify the current Windows checkout, preserve Git state, run the locked quality gate, capture capabilities, and record exact local failures without changing product behavior.
