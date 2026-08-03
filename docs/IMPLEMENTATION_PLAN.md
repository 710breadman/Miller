# Miller next phase: real-corpus comic understanding

Status: **`DOC-001` accepted; `ARC-001` implementation active**
Evidence now: E3 synthetic/local. Real-corpus work targets E4; human review targets E5.

## Outcome

Use owner-approved comics at `V:\Comics` as external, read-only test input. Build a private manifest and reproducible reports; improve panel/text/OCR/reading-order observations; establish lexical retrieval baseline; then compare approved external workers. Do not copy or commit source pages, narration, scripts, model weights, or derived copyrighted media.

## Execution order

### 1. Close `DOC-001` (control-document checkpoint)

Reconcile path, 13–18 minute duration, milestone wording, and stale “implemented ahead” claims. Run `uv run python scripts/validate_planning.py`. Update `CURRENT_STATE.md`, `HANDOFF.md`, and `SPRINT_STATE.json` once after review. Commit only the coherent control-document change with `DOC-001` in the message.

### 2. `ENV-002` — private local fixture manifest

Inspect `V:\Comics` read-only. Select a small stratified sample across the five folders: ordinary pages, covers, likely spreads, irregular layouts, ads, and varied resolutions. Record absolute source path, folder identity, page count, byte count, source SHA-256, file hashes, dimensions, extension, and access timestamp in a private manifest under `.miller/` or an owner-approved external evidence directory. Add no media to Git.

Required blocker check: script and edited narration are still absent from known context. If absent, complete comic-only inventory evidence and leave audio/video acceptance blocked; do not fabricate a full fixture.

Acceptance: source hashes before/after equal; no writes under `V:\Comics`; manifest parses; sample selection reproducible; rights/retention policy recorded.

### 3. `ANL-001` — corpus and observation schema

Define stable source/page/panel/region IDs derived from source identity and geometry, annotation provenance, detector version, confidence, coordinate space, reading direction, and uncertainty. Separate private labels from redistributable code. Add schema/contract tests only inside card scope.

Acceptance: same source/config regenerates identical IDs; changed source invalidates dependents; malformed/out-of-bounds observations reject; no source media enters artifacts.

### 4. `ENV-003` — real no-AI/OCR baseline

Run Miller baseline against a tiny approved sample. Preserve command line, environment, source/output hashes, FFprobe JSON, SQLite integrity, timing, warnings, and output paths. Produce no-OCR and OCR outputs only in managed external storage; never overwrite existing output.

Acceptance: direct process exit status, valid MP4, source unchanged, provenance complete. E4 only after quantitative report; E5 requires owner visual/audio review.

### 5. `ANL-002/003/004` — measured comic analysis

Benchmark current gutter detector, selected panel detectors, reading-order rules (LTR and RTL), and OCR preprocessing/engines on the same stratified pages. Report precision/recall or IoU, OCR CER/WER, reading-order accuracy, runtime, RAM/VRAM, failure buckets, and representative visual overlays. Keep external GPL/research tools process-isolated unless license decision changes.

### 6. `RET-001/002/003` — retrieval baseline

Create label tool/schema, then 100–300 narration/query labels with held-out queries and hard negatives. Measure BM25/metadata baseline using page/panel locators without leakage. Only then compare embedding workers on identical corpus/config and record the winner in an ADR.

### 7. `AUD-001/002`, `STO-001`, then video gates

Pin alignment worker; test real narration only when supplied/approved. Build beat intent and candidate lattice from measured observations. Defer text cleanup, Revideo, advanced masks, and NLE export until baseline relevance/timing evidence exists.

## First 48-hour slice

1. Finish `DOC-001` and checkpoint.
2. Generate private comic manifest from `V:\Comics`; report counts, sizes, hashes, dimensions, and representative sample IDs.
3. Run one tiny no-AI inventory/cache/analysis probe; inspect generated JSON/SQLite/artifacts.
4. Create `ENV-002` evidence record and exact blocker for missing script/narration.
5. Start `ANL-001` schema work; add focused contract tests.

## Evidence gates

- E2: synthetic tests and schema contracts.
- E3: local Windows/GPU/process/hash/SQLite proof.
- E4: real-corpus metrics with fixed manifest, versions, configs, and failure buckets.
- E5: owner review of rendered video/overlays/audio.
- E6: clean-machine install/recovery/release proof.

## Non-negotiable controls

- `V:\Comics` read-only; no copy, rename, delete, or in-place metadata injection.
- Public datasets remain access/license-gated: Manga109 academic/request access; COMICS/Text+ access and terms; SemanticComics/DCM772 item-level rights.
- Store IDs, paths, hashes, and reports; keep copyrighted pixels external.
- SQLite authoritative; caches/indexes rebuildable.
- Every claim needs command, exit code, artifact path, hash, version, and evidence level.

## Exact artifact paths

- `.miller/private/comic-fixture-manifest.json` — untracked/private.
- `.miller/private/reports/ENV-002-*.md` — untracked/private.
- `.miller/private/reports/ENV-003-*.md` — untracked/private.
- `docs/INV-003-AUDIT.md` — public dependency/data/license audit.
- `docs/adr/` — selected architecture/license decisions.
- `HANDOFF.md` — exact next action and blockers.
