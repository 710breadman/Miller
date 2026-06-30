# Development roadmap

Each sub-sprint is one bounded Codex checkpoint. Execute only
`active_sub_sprint` from `SPRINT_STATE.json`, verify its gate, update state and
status, then stop. Never batch adjacent sub-sprints.

Common completion requirements:

1. Scope contains one cohesive outcome.
2. Relevant tests pass.
3. Generated artifacts are inspected.
4. Decisions/failures are recorded in `STATUS.md` or an ADR.
5. `SPRINT_STATE.json` advances exactly one sub-sprint.
6. Worktree stops at a stable, reviewable checkpoint.

Use [`docs/SUB_SPRINT_TEMPLATE.md`](docs/SUB_SPRINT_TEMPLATE.md) when adding or
splitting work.

## Sprint 0 — Source audit

Status: complete.

### 0.1 — Repository bootstrap

Outcome: repo, product spec, instructions, roadmap, status, and state files.

Gate: clean repo structure exists and project goal/safety rules are explicit.

### 0.2 — Primary upstream audit

Outcome: MoneyPrinterTurbo, BallonsTranslator, StoryToolkitAI, Revideo,
WhisperX, and OpenTimelineIO inspected at pinned revisions.

Gate: architecture, interfaces, limits, tests, and licenses recorded.

### 0.3 — ML/storage audit

Outcome: OpenCLIP, SigLIP 2, Qdrant, SAM 2, and Depth Anything V2 inspected.

Gate: retrieval/storage/optional-worker candidates classified.

### 0.4 — Architecture decision pack

Outcome: reuse, license, capability, and architecture matrices plus audit
verification scripts.

Gate: every relevant capability classified; no upstream code copied.

## Sprint 1 — Project foundation

### 1.1 — Python package skeleton

Outcome: `pyproject.toml`, package layout, test layout, lint/test config.

Gate: fresh env installs project; empty test suite and import smoke test pass.

Exclude: domain schemas, DB, CLI behavior.

### 1.2 — Core domain schemas

Outcome: typed project, artifact, stage definition/run, event, tool invocation,
and status-transition schemas.

Gate: schema round-trips and invalid transition tests pass.

Exclude: persistence and execution.

### 1.3 — SQLite persistence

Outcome: DB schema/migrations and repositories for Sprint 1 entities.

Gate: create/read/update transaction tests pass; illegal transitions roll back.

Exclude: stage execution.

### 1.4 — Project directories and artifact hashing

Outcome: safe managed project layout, atomic writes, SHA-256 artifact manifests.

Gate: source inputs remain untouched; repeated content gets stable hashes.

Exclude: pipeline scheduling.

### 1.5 — Deterministic stage runner

Outcome: single-process dependency runner with pending/running/completed/failed
states and input-hash invalidation.

Gate: fake DAG completes deterministically; changed input invalidates only
dependents.

Exclude: cancellation, process workers, UI.

### 1.6 — Cancellation, resume, and structured logs

Outcome: cooperative cancellation, stale-run recovery, retries, JSONL events.

Gate: killed fake run restarts and resumes without corrupting completed stages.

Exclude: production media tools.

### 1.7 — Foundation CLI acceptance

Outcome: CLI creates, inspects, runs, cancels, and resumes fake projects.

Gate: subprocess acceptance test performs fail → restart → resume → complete;
unchanged outputs retain hashes.

Exclude: web API/UI.

## Sprint 2 — Comic ingestion

### 2.1 — Comic source contracts

Outcome: typed comic source/issue/page records and enforced read-only policy.

Gate: traversal, unsupported type, and attempted source-write tests fail safely.

### 2.2 — Image-folder discovery

Outcome: deterministic recursive image discovery and natural page ordering.

Gate: fixture folder produces stable ordered inventory across runs.

### 2.3 — CBZ inventory

Outcome: safe ZIP inspection with path, size, compression, and image validation.

Gate: valid fixture inventories; zip-slip/bomb-like fixtures reject safely.

### 2.4 — Extraction cache and stable IDs

Outcome: content-addressed page extraction with stable issue/page IDs.

Gate: same source reuses cache; renamed unchanged file preserves content ID.

### 2.5 — Thumbnail artifacts

Outcome: deterministic bounded-size thumbnails with orientation/color handling.

Gate: golden fixture dimensions/hashes pass; original pages unchanged.

### 2.6 — Incremental ingestion acceptance

Outcome: source fingerprinting and changed/added/removed page reconciliation.

Gate: edited issue reprocesses only affected page artifacts.

## Sprint 3 — Comic understanding

### 3.1 — Page-analysis records

Outcome: normalized analysis schema for pages, panels, text regions, OCR,
descriptions, and quality metrics.

Gate: versioned fixture round-trips; coordinates validate.

### 3.2 — Panel candidate baseline

Outcome: conservative panel candidates while always preserving full page.

Gate: fixture emits valid non-overlapping/flagged candidates and full-page
fallback.

### 3.3 — OCR adapter contract and baseline

Outcome: replaceable OCR protocol plus first local implementation.

Gate: adapter contract tests normalize text, confidence, language, polygons,
and failures.

### 3.4 — Text and balloon masks

Outcome: text-region masks, balloon-region hints, and mask artifact provenance.

Gate: visual golden fixtures and coordinate/mask consistency checks pass.

### 3.5 — Descriptions and quality scores

Outcome: structured page/panel descriptions and deterministic technical quality
scores.

Gate: invalid AI output rejects; scores reproduce from fixed inputs/config.

### 3.6 — Understanding index acceptance

Outcome: persist page/panel/OCR/metadata records for query.

Gate: fixture comic searchable by OCR and metadata with source locators.

## Sprint 4 — Retrieval benchmark

### 4.1 — Benchmark schema and runner

Outcome: query, relevance, hard-negative, run-config, metric, and result formats.

Gate: synthetic ranking computes reproducible Recall@K, MRR, nDCG, latency.

### 4.2 — Comic evaluation set

Outcome: 100–300 labeled queries spanning action, emotion, art style, costume,
era, page/panel, and hard negatives.

Gate: validator finds no missing locators, duplicate IDs, or label leakage.

### 4.3 — Lexical/OCR baseline

Outcome: metadata + OCR retrieval baseline.

Gate: benchmark report saved with exact config and index hash.

### 4.4 — OpenCLIP benchmark adapter

Outcome: pinned OpenCLIP image/text embedding run.

Gate: report includes quality, VRAM, indexing speed, and query latency.

### 4.5 — SigLIP 2 benchmark adapter

Outcome: pinned RTX 3070-compatible SigLIP 2 embedding run.

Gate: same metrics/corpus/config discipline as OpenCLIP.

### 4.6 — Hybrid winner selection

Outcome: compare lexical, models, pages/panels, and hybrid weights.

Gate: reproducible winner config chosen with failure/rollback notes.

## Sprint 5 — Narration alignment

### 5.1 — Audio inspection

Outcome: FFprobe-backed audio metadata, validation, and non-destructive working
format conversion.

Gate: valid fixtures normalize; corrupt/unsupported audio fails clearly.

### 5.2 — WhisperX capability worker

Outcome: isolated WhisperX probe/load/transcribe/align worker contract.

Gate: unavailable GPU/model reports structured failure; worker can unload.

### 5.3 — Word-timing normalization

Outcome: normalize WhisperX segments/words into Miller schema.

Gate: timestamps monotonic, bounded, confidence/warnings preserved.

### 5.4 — Script/audio comparison

Outcome: supplied-script mapping with omissions, insertions, substitutions, and
pickup markers.

Gate: controlled mismatch fixtures produce expected diagnostics.

### 5.5 — Section and beat timing

Outcome: deterministic section/visual-beat ranges from script plus word timing.

Gate: two-minute fixture maps all narration without overlaps/gaps beyond
configured tolerance.

## Sprint 6 — Automatic storyboard

### 6.1 — Scene schema and invariants

Outcome: scenes, candidates, scores, source locators, locks, camera, transition,
music, and review fields.

Gate: invalid timing/assets/scores reject; valid storyboard round-trips.

### 6.2 — Search-scope proposal

Outcome: structured character/series/arc/era/continuity scope with user steering.

Gate: proposal validates; exclusions and user overrides always win.

### 6.3 — Beat query and candidate retrieval

Outcome: each timed beat generates traceable queries and candidate pool.

Gate: every beat has candidates or explicit no-match diagnostic.

### 6.4 — Candidate ranking

Outcome: semantic, character, theme, continuity, quality, and reuse scoring.

Gate: locked/excluded assets obeyed; reuse penalty verified.

### 6.5 — Scene timing and motion plan

Outcome: convert ranked beats into scene durations, primary/alternatives,
camera presets, and transitions.

Gate: complete audio coverage and valid asset references.

### 6.6 — Two-minute storyboard acceptance

Outcome: end-to-end automatic storyboard fixture and report.

Gate: all scenes trace to narration, queries, scores, and comic source.

## Sprint 7 — Text removal and derived assets

### 7.1 — Clean-crop preference

Outcome: score text-free crops before any destructive-looking derivation.

Gate: valid clean crops win; subject-safe constraints hold.

### 7.2 — Inpaint mask artifacts

Outcome: derived masks limited to selected text regions with provenance.

Gate: mask never modifies source; visual/debug artifacts inspectable.

### 7.3 — BallonsTranslator adapter proof

Outcome: pinned external-process detector/inpaint proof on fixture pages.

Gate: structured result captures masks, regions, model IDs, outputs, errors.

### 7.4 — Inpainting fallback chain

Outcome: clean crop → primary inpainter → safe alternate/unclean fallback.

Gate: every failure ends with usable asset or explicit blocked scene.

### 7.5 — Derived-asset acceptance

Outcome: content-addressed reproducible cleaned panels.

Gate: repeated run matches hashes; source tree byte hashes unchanged.

## Sprint 8 — Renderer

### 8.1 — Render contract and profiles

Outcome: typed render request/manifest plus draft/final hardware profiles.

Gate: configs validate and record tool versions/args.

### 8.2 — Single-scene FFmpeg render

Outcome: render one still/page crop to exact video dimensions/duration.

Gate: FFprobe verifies stream, duration, frame rate, pixel format.

### 8.3 — Camera and transition presets

Outcome: deterministic pan/push/pull/crop plus cut/crossfade/dip presets.

Gate: visual golden/tolerance tests pass without out-of-bounds frames.

### 8.4 — Narration, subtitles, and music mix

Outcome: mux narration, SRT, section music, loudness control, and ducking.

Gate: sync/loudness/subtitle timing checks pass.

### 8.5 — Multi-scene FFmpeg pipeline

Outcome: assemble complete storyboard with progress/cancellation.

Gate: two-minute fixture renders; manifest traces each segment.

### 8.6 — Revideo comparison proof

Outcome: same fixture rendered through pinned Revideo worker.

Gate: report compares determinism, time, RAM/VRAM, size, cancellation, sync,
and Windows packaging.

### 8.7 — Renderer acceptance

Outcome: select default/optional backend policy and rerender proof.

Gate: identical project/config renders twice within documented hash/tolerance.

## Sprint 9 — Quality repair loop

### 9.1 — Quality metric schema

Outcome: scene/project findings, severity, evidence, score, repair proposal.

Gate: malformed or unsupported findings reject.

### 9.2 — Technical media checks

Outcome: detect black frames, missing media, clipping, corruption, timing, and
music loudness.

Gate: seeded broken fixtures trigger expected findings.

### 9.3 — Visual/editorial checks

Outcome: detect duplicates, weak match, bad crop, static runs, motion repetition,
and continuity warnings.

Gate: seeded storyboard defects trigger expected findings.

### 9.4 — Repair planner

Outcome: bounded repair actions respecting locks and affected-scene scope.

Gate: locked scenes untouched; no proposal exceeds pass limit.

### 9.5 — Partial rerender and comparison

Outcome: rerender affected scenes; compare new/old score and retain winner.

Gate: worse repair rolls back; unaffected artifact hashes stay stable.

### 9.6 — Repair-loop acceptance

Outcome: configurable 0/1/2/3/5-pass loop with early stop and history.

Gate: flawed project improves within limit without unrelated rerenders.

## Sprint 10 — Simple editor

### 10.1 — Editor API read model

Outcome: API returns scene cards, assets, alternatives, scores, locks, status.

Gate: project snapshot endpoint contract passes.

### 10.2 — Override command API

Outcome: validated panel, crop/focus, motion, music, and lock commands.

Gate: commands are atomic, auditable, and invalidate only dependents.

### 10.3 — React app shell

Outcome: local app bootstrap, routing, API client, error/loading states.

Gate: production build and smoke test pass.

### 10.4 — Scene card timeline

Outcome: ordered scene cards with timing, thumbnail, warnings, and lock state.

Gate: fixture project renders accurately at desktop target.

### 10.5 — Alternative and panel replacement

Outcome: browse/filter alternatives and replace primary asset.

Gate: replacement persists and triggers scoped rerender.

### 10.6 — Crop, motion, music, and lock controls

Outcome: focused controls with previews and reset.

Gate: each edit round-trips through command API.

### 10.7 — Editor acceptance

Outcome: user repairs seeded weak scene through UI.

Gate: only affected scene rerenders; final project retains edit history.

## Sprint 11 — Script factory

### 11.1 — Evidence ledger schemas

Outcome: sources, claims, locators, excerpts, confidence, and section usage.

Gate: provenance required; unsupported claims cannot become verified.

### 11.2 — Research provider contracts

Outcome: closed-source, local-first, broad, and custom-set provider interfaces.

Gate: each mode enforces source boundaries and normalized results.

### 11.3 — Framing discovery

Outcome: structured thesis/angle candidates from briefing and evidence.

Gate: candidates cite evidence and expose uncertainty.

### 11.4 — Outline generation

Outcome: selected framing becomes sectioned outline with claim assignments.

Gate: every factual section maps to evidence or explicit research gap.

### 11.5 — Draft generation

Outcome: style-configured draft with target length/pacing.

Gate: structured stage artifact saved with prompt/model/version.

### 11.6 — Fact and lore verification

Outcome: claim coverage report and corrected verified draft.

Gate: unsupported claims removed, qualified, or flagged.

### 11.7 — Humanization passes

Outcome: theme, structure, read-aloud, repetition, robotic-language, and length
passes.

Gate: diff/history preserved; no new unsupported claims.

### 11.8 — Script queue acceptance

Outcome: sequential, resumable script-stage queue.

Gate: one topic produces sourced final script across restart.

## Sprint 12 — Optional export

### 12.1 — OTIO mapping

Outcome: map storyboard scenes, timing, refs, captions, and metadata to OTIO.

Gate: OTIO round-trip preserves clip order/timing.

### 12.2 — Media package

Outcome: portable referenced-media package with narration/music/captions.

Gate: manifest has no missing refs and does not mutate originals.

### 12.3 — Resolve interchange proof

Outcome: test supported OTIO/plugin or alternate interchange path.

Gate: documented Resolve version opens basic timing/media correctly.

### 12.4 — Export acceptance

Outcome: optional export command plus compatibility report.

Gate: external editor opens fixture; normal render workflow has no dependency.

## Sprint 13 — Packaging

### 13.1 — Tool capability detection

Outcome: versioned probes for FFmpeg, FFprobe, Ollama, Node, GPU, and adapters.

Gate: missing/incompatible tools produce actionable diagnostics.

### 13.2 — Hardware profiles

Outcome: RTX 3070 default plus CPU/degraded config and model lifecycle limits.

Gate: selected profile validates against detected capability.

### 13.3 — Configuration UI

Outcome: typed settings editor with secrets separation and validation.

Gate: safe config round-trip; secrets never enter logs/project manifests.

### 13.4 — Cache management

Outcome: inspect/prune/rebuild managed cache without deleting user sources.

Gate: dry run and protected-path tests pass.

### 13.5 — Portable projects

Outcome: export/import project state and managed assets with integrity checks.

Gate: round-trip opens on clean test location with identical manifest hashes.

### 13.6 — Windows launcher

Outcome: personal launcher starts services, opens browser, and shuts down cleanly.

Gate: clean-machine checklist passes without manual shell commands.

### 13.7 — Documentation and V1 acceptance

Outcome: install, operate, recover, backup, troubleshoot, and license docs plus
golden end-to-end project.

Gate: V1 required scope passes on target hardware; exclusions remain excluded.
