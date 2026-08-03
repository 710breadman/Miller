# Miller current-state assessment

Assessment date: **2026-08-02**
Repository: `710breadman/Miller`  
Inspected branch: `codex/env-001` at pre-`ARC-002` checkpoint `f349a18`; active control sprint: `ARC-004`

## Executive assessment

Miller is **not a blank project**. It has a coherent Python foundation, strong ownership boundaries, typed contracts, SQLite state, safe CBZ handling, a deterministic stage runner, optional worker boundaries, lexical retrieval, storyboard contracts, revisioned editing, FFmpeg rendering, packaging scripts, and a useful synthetic test suite.

It is also **not yet a proven comic-understanding or production-quality video system**. The current end-to-end baseline uses filename/OCR text, simple white-gutter panel heuristics, uniform audio timing, and greedy lexical scene selection. It now has one real 70-second E3 run, but that run exposed page-level crops, visible lettering, an ad/tag selection, reuse, and no clear OCR relevance gain. Most model-backed integrations remain contracts without a shipped worker environment or quantitative real-corpus evidence. The local web interface is a minimal inline prototype.

The baseline now uses the durable DAG. The correct next move is atomic output promotion and recovery, then comic-analysis and retrieval benchmarks on owner-approved labels. ENV-001 synthetic, ENV-003 real baseline, and ARC-002 real DAG execution reached E3; quantitative real-corpus and human gates remain open.

## Evidence levels

| Code | Meaning | Current examples |
|---|---|---|
| E0 | Documented intent only | React product UI, advanced character re-ID |
| E1 | Typed contract or scaffold | WhisperX and embedding subprocess adapters |
| E2 | Automated synthetic test | 64-test suite, generated tone and tiny images |
| E3 | Local hardware pass | ENV-001 synthetic no-OCR/OCR baseline, RTX 3070, FFmpeg/Tesseract, hashes, and SQLite integrity |
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
- Source distributions explicitly exclude local workspaces, caches, owner scripts/media, and quarantine directories;
  a clean `uv build` archive inspection found no private/runtime paths.
- `ENV-002` has an owner-approved, gitignored local fixture: 10 real comics plus a 3,524-word Green Lantern script
  and 28:15.219 edited narration WAV. Source hashes and AU4 SQLite integrity were verified before/after managed
  conversion on Windows; this is E3 fixture/integrity evidence, not render-quality evidence.
- `ENV-003` produced real no-OCR and OCR H.264/AAC baselines from a 70-second managed excerpt. Both fully decoded,
  had no detected black segment over 0.5 seconds, preserved source hashes, and stored complete project documents in
  an integrity-checked SQLite database. Visual quality needs repair; this remains E3, not E4/E5.
- `ARC-002` routes the baseline through five durable `PipelineRunner` stages. Automated tests prove abandoned-render
  recovery, dependency reuse, and missing-output invalidation (E2). A real Windows run took 165.671 seconds; the
  identical restart took 2.527 seconds with five cache hits and the same fully decoded MP4 hash (E3 execution).

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
| Project/state database | authoritative projects, stages, attempts, queue, documents, events | implemented foundation | `src/miller/db.py`, `models.py`, `transitions.py` | E3 transaction/recovery tests plus ordered migrations, preflight backup, integrity checks, restore drill, and real baseline DAG persistence (`ARC-001`, `ARC-002`) | process-kill and large-project restart acceptance | `ENV-004` |
| Artifact store | immutable content-addressed outputs and hashes | implemented foundation | `artifacts.py`, `runtime/cache.py` | E2 cache/invalidation tests | large-cache performance and Windows path proof | `ENV-004`, `VID-004` |
| Pipeline runner | deterministic DAG, cache, cancellation, retries | integrated with baseline | `runner.py`, `pipeline/baseline.py` | E2 interruption/restart automation plus E3 real five-stage execution and cache reuse (`ARC-002`) | process-kill, partial-output, and concurrent-run proof | `ARC-004`, `ENV-004` |
| Queue | persistent bounded work | implemented foundation | `workers.py`, DB queue tables | E3 versioned protocol, lease/heartbeat, stale-result guard, cancellation, timeout, error classes, and one-GPU admission (`ARC-003`, local Windows run) | priority scheduling across a single lease-holding item, real external-worker adapter integration | `ANL-005`, `RET-004`, `AUD-001` |
| Folder/CBZ ingest | safe read-only source inventory | strong implementation | `comics/` | E3 archive/path/image adversarial fuzzing (`SEC-001`, local Windows run) plus prior changed-source tests | CBR/PDF (real CBR files exist in the owner's library per `ENV-002`), double-page semantics | `ENV-002` |
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
| Alignment | word/beat timing | external contract + uniform fallback | `audio/whisper_worker.py`, `audio/worker/align_worker.py`, `uniform.py` | E2 worker contract, versioned probe, unload, CPU fallback | exact torch/stable-ts pins, installed environment, real accuracy and drift measurement | `AUD-001`, `AUD-002` |
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
| Licensing | allow safe distribution | Miller's own license still unresolved; dependency layer audited | `docs/LICENSE_DECISION.md`, matrices, `docs/SBOM.json`, `docs/NOTICES.md` | E3 SBOM + vulnerability scan + FFmpeg build/license record (`SEC-002`, local Windows run) | owner license decision (`OD-001`), model/data terms once installed, release-time re-scan | `REL-002` |

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

### Implemented contracts with remaining external validation

- portable project packaging;
- Qdrant persisted/local behavior;
- OTIO export against an actual editor.

The Windows installer/launcher and synthetic FFmpeg baseline reached E3 during
`ENV-001`; clean-machine, real-media, long-path, and human-quality gates remain
open.

`ARC-001` reached E3 on this local Windows machine: ordered schema migrations,
a verified preflight backup taken before any migration, `PRAGMA
integrity_check`-based corruption detection, and a restore drill (corrupt the
live file, restore from the verified backup, confirm data and integrity) are
implemented in `src/miller/db.py` and covered by `tests/test_db.py`.
Interruption/crash-mid-migration, very large real project databases, and
Windows long-path/AV interaction remain open (`ENV-004`).

`ARC-003` reached E3 on this local Windows machine: a versioned worker
protocol (items declare `protocol_version`; a worker rejects an unsupported
version before ever invoking its handler), lease/heartbeat with a
stale-result guard (`Database.claim_next`, `heartbeat_queue_item`, the
`lease_token` check in `_finish_queue_item`), cooperative cancellation
(`request_cancel_queue_item`, `WorkerContext.raise_if_cancelled`), lease-based
timeout detection (`reclaim_expired_leases`), typed error classification
(`WorkerErrorClass`), and single-GPU admission (`requires_gpu` +
`gpu_capacity` in `claim_next`) are implemented in `src/miller/db.py`,
`models.py`, and `workers.py`, preserving every pre-existing caller's call
signature (`cli.py`'s queue commands, the original `QueueWorker(database,
kind, handler)` construction). Ruff, strict Mypy across 82 files, the full
Pytest suite (87 tests, 16 new), and the wheel/sdist build all passed
locally. The existing external worker adapters (`audio/whisper_worker.py`,
`retrieval/embedding_worker.py`) do not yet route through this protocol --
that integration is `ANL-005`/`AUD-001`/`RET-004` work.

`SEC-001` reached E3 on this local Windows machine: adversarial tests in `tests/test_security.py` fuzz CBZ
archive/path/image inputs (path traversal, absolute paths, Windows drive-letter paths, duplicate case-insensitive
paths, encrypted entries via real ZIP-header byte patching, oversized/zero-byte entries, total-size limits, a
zip-bomb-style compression ratio, entry-count limits, corrupted images, invalid archives), verify the localhost-only
boundary at both the CLI argparse layer (`--host` `choices`) and the `MillerSettings` validator layer, confirm
`attempt_guard`/`lease_token` secrets are never written to project logs or DB events, exercise missing-binary and
malformed-JSON failure surfaces for both external worker adapters, and statically confirm no `shell=True`/`os.system`
usage anywhere in the core package. Found and fixed two real issues along the way: untrusted scene data is now
assigned through DOM text/value properties and event listeners rather than inline JavaScript attributes, and a missing
structured-error-message extraction in `retrieval/embedding_worker.py` (now matches the pattern `whisper_worker.py`
gained in `AUD-001`). Also discovered, and documented in the tests themselves, that Python's `zipfile` module
normalizes a literal backslash in a member name to a forward slash on *read* regardless of raw header bytes, meaning
Miller's own `"\\" in name` rejection in `comics/cbz.py` can never actually be reached via any `ZipFile`-mediated
read — defensive dead code in practice, kept in case that platform/version behavior ever changes.

`SEC-002` reached E3 on this local Windows machine: ran `uv audit --locked` (an experimental built-in `uv`
subcommand, no new tool installed) against the resolved dependency set — `Found no known vulnerabilities and no
adverse project statuses in 45 packages`; generated `docs/SBOM.json`, a machine-readable SBOM from
`importlib.metadata` over all 48 actually-installed packages (47 resolved a license via each package's PEP 639
`License-Expression` field or classifier; the 48th is Miller's own package), confirming no GPL-family license among
them; captured the real, full `ffmpeg -version` build configuration on this machine and identified that the
installed `gyan.dev` "full" build is licensed **GPL v3** (`--enable-gpl --enable-version3`), which is fine under the
current subprocess-invocation architecture but would carry bundling obligations if a future release packages that
binary directly (new `RISKS.md` RSK-025); and wrote `docs/NOTICES.md` and a supply-chain policy in
`docs/SEC-002-AUDIT.md`. No production code was changed. Remaining: owner license decision (`OD-001`), model/data
terms once model workers are actually installed, and a fresh scan at release time (vulnerability databases and
dependency versions change).

`QAE-001` reached E2 (automated/contract-level, not a hardware-capability observation): finalized the human quality
rubric in `EVALUATION_PLAN.md` with
concrete visual and audio dimensions (crop/composition safety, text-free cleanliness, motion/transition
appropriateness, visual variety; narration clarity, music/narration balance, music transition smoothness, A/V sync)
alongside the pre-existing narrative dimensions; defined reviewer roles (primary reviewer with final authority,
optional secondary reviewer, AI self-review as advisory-only); defined numeric scoring thresholds (`overall_score`
≥4.0 → `accepted`, ≥3.0 → `needs_repair`, <3.0 → `rejected`, with a per-dimension floor rule); defined a
disagreement-handling process (record both score sets, discuss against rubric text, preserve dissent permanently if
unresolved); and specified an immutable, content-addressed E5 acceptance-record format
(`docs/schemas/e5-acceptance-record.schema.json`, a synthetic example, and `docs/schemas/verify_e5_example.py` --
a runnable script that validates record shape and cross-field rules, then recomputes `content_hash`/`record_id`
from the example's own content and confirms byte-for-byte reproducibility). Remaining: this rubric has not yet
been exercised against a real rendered project — that requires the `ENV-002` script/narration fixture and an actual
render.

### Partially implemented

- durable end-to-end orchestration;
- external worker adapters routed through the new versioned protocol/lease queue (core protocol done in `ARC-003`; adapters themselves not yet updated);
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
- release-packaging migration/rollback ledger for distributed installs (`REL-002`; the core database migration/backup/restore system itself is implemented, see `ARC-001`).

### Blocked

- real-corpus and subjective gates require owner-approved comics and narration;
- representative model and real-media GPU measurements remain unrecorded;
- distribution requires owner license choice;
- Resolve compatibility requires supported Resolve installation.

## Technical debt with highest leverage

1. Baseline bypasses the durable DAG, so resume claims are broader than current end-to-end behavior.
2. ~~Schema upgrades are additive initialization rather than a formal migration ledger with pre-migration backup.~~ Resolved in `ARC-001`: ordered migrations, preflight backup, integrity checks, and a restore drill.
3. Evidence claims are spread across status, reports, and sprint state without a shared evidence level.
4. Legacy `SPRINTS.md` numbering differs from the definitive control-card IDs; `SPRINT_STATE.json` is authoritative.
5. The legacy roadmap compresses major model, integration, validation, and recovery work into broad items unsuitable for bounded local-worker tasks.
6. The HTML editor is embedded in Python and cannot yet support the intended visual workflow.
7. Retrieval is page-centric and greedy; the product needs panel/page mixed candidates and global continuity.
8. Model adapters validate JSON shape but need process lifecycle, version manifests, resource isolation, and retry/cancel semantics. `ARC-003` built the core-owned protocol version check, lease/heartbeat, stale-result guard, cancellation, timeout, error classification, and one-GPU admission in `db.py`/`workers.py`; the external adapters themselves (`audio/whisper_worker.py`, `retrieval/embedding_worker.py`) still call a bare subprocess without going through this queue/lease machinery.
9. Real quality acceptance has no stable owner rubric or golden project.
10. Product-duration and checkout-path documents contain stale values.

## Recommended immediate action

`ARC-002` is accepted: five durable baseline stages, E2 automated interruption/restart proof, and E3 real Windows
execution/cache reuse. `ARC-004` is active: make output promotion atomic and prove recovery without overwriting
existing files. `ANL-001`, `ENV-004`, and `QAE-002` remain ready alternatives. Visual E4/E5 remains open.
