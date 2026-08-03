# Miller development roadmap

This file preserves the original capability roadmap and its historical sprint
numbering. `SPRINT_STATE.json` is the machine-readable source for the current
control sprint and supersedes any "active" label below. Later roadmap work may
have software implemented ahead of the canonical order, but no control sprint is
declared complete until its required acceptance evidence exists.

## Common completion gate

1. One bounded outcome with typed inputs/outputs.
2. Relevant tests and the full quality gate pass.
3. Generated artifacts/manifests are inspected.
4. Sources remain unchanged and managed outputs pass integrity checks.
5. Decisions, failures, versions, and remaining real-world validation are recorded.
6. Only the active canonical checkpoint advances.

## Sprint 0 — Source audit — complete

Upstream architecture, reuse boundaries, exact revisions, licenses, storage,
retrieval, alignment, rendering, and optional-worker candidates are documented.
No upstream application owns Miller state.

## Sprint 1 — Project foundation — complete

Package, schemas, SQLite persistence, immutable attempts, artifact store,
deterministic stage runner, cancellation, restart recovery, structured logs,
and CLI acceptance.

## Sprint 2 — Comic ingestion — complete

Read-only image-folder/CBZ inventory, archive safety controls, content IDs,
extraction cache, thumbnails, and incremental reconciliation.

## Sprint 3 — Comic understanding — complete

Versioned page/panel/OCR/mask/description/quality records, conservative panel
candidates, Tesseract adapter, deterministic analysis, and searchable local index.

## Sprint 4 — Retrieval benchmark — historical active sprint; currently evidence-blocked

### 4.1 Benchmark schema and runner — complete

Reproducible ranking, latency, Recall@K, MRR, and nDCG.

### 4.2 Real comic evaluation set — blocked on local data

Create 100–300 human-labeled narration queries using an approved corpus. Cover
characters, action, mood, costume, era, art style, pages/panels, and hard negatives.
The validator must find no missing locators, duplicate IDs, or label leakage.

### 4.3 Lexical/OCR baseline — framework complete ahead

BM25/metadata/OCR retrieval and exact index/run configuration are implemented.
A real report awaits the 4.2 corpus.

### 4.4 OpenCLIP benchmark — worker contract complete; real run blocked

Requires pinned model/weights, the same corpus, RTX 3070 VRAM/indexing/latency
measurements, and exact model licensing.

### 4.5 SigLIP 2 benchmark — worker contract complete; real run blocked

Same evidence discipline as OpenCLIP.

### 4.6 Hybrid winner selection — blocked

Select only from measured lexical/OpenCLIP/SigLIP page/panel/hybrid results.
Qdrant stores rebuildable vectors; SQLite remains authoritative.

## Sprint 5 — Narration alignment — implemented ahead; real model validation pending

FFprobe inspection, non-destructive normalization, WhisperX process contract,
word normalization, script mismatches, sections, beats, and deterministic fallback
timing are implemented. Completion requires representative local WhisperX runs.

## Sprint 6 — Automatic storyboard — implemented ahead

Scene schema, scope steering, traceable queries, ranking, alternatives, continuity,
reuse penalties, locks, timing, motion, transitions, and complete audio coverage.

## Sprint 7 — Text removal and derived assets — partially validated

Clean-crop preference, mask artifacts, deterministic fallback assets, provenance,
and source-integrity checks are implemented. The pinned BallonsTranslator external
process proof remains blocked on a local checkout and representative pages.

## Sprint 8 — Renderer — native path implemented; comparison blocked

Typed profiles, still/pan/push/pull scenes, cuts/crossfades/dips, narration,
subtitles, music ducking, multi-scene rendering, manifests, and scene-level cache
are implemented. Revideo comparison and final backend policy require local proof.

## Sprint 9 — Quality repair loop — implemented ahead

Technical/editorial findings, repair proposals, scene locks, bounded passes,
partial rerender, unchanged-scene cache retention, and rollback-oriented records.
Subjective quality still requires real projects.

## Sprint 10 — Simple editor — implemented ahead

Local API/read model, revisioned commands, alternatives, asset replacement, focus,
motion, transition, music/lock controls, history, optimistic locking, and scoped
rerender foundations.

## Sprint 11 — Script factory — partially implemented ahead

Evidence ledger, local research provider, framing, outline, draft, verification,
humanization, Ollama structured-output adapter, persistence, and durable queue are
implemented. Broad web research and lore-specific acceptance remain.

## Sprint 12 — Optional export — partially implemented ahead

OpenTimelineIO mapping and referenced-media packages are implemented. Resolve
interchange remains blocked on an installed supported Resolve version.

## Sprint 13 — Packaging — partially implemented ahead

Capabilities, GPU profiles, typed settings, cache management, portable projects,
Windows installer/launcher/verifier, CI, and documentation are implemented. Final
acceptance requires the target Windows/RTX 3070 machine, license decision, notices,
and real golden project.
