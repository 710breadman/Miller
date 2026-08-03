# Miller handoff

Status: **`ARC-002` accepted with E2 restart and E3 real-run evidence; `ARC-004` active; visual quality needs repair**
Planning revision: `2026-07-21-definitive`  
Active sprint: **`ARC-004` — Atomic output and artifact audit**

## What was completed

- repository and evidence-level assessment, roadmap, sprint cards, machine-readable state, decisions, protocols,
  evaluation/test/risk/security/release/owner-decision controls, first local Windows acceptance procedure, planning
  validator, `docs/INV-003-AUDIT.md`, `DOC-001` control-document reconciliation (all prior sessions);
- `ARC-001` ordered database migrations, preflight backup, `PRAGMA integrity_check`-based corruption detection, and
  a restore drill in `src/miller/db.py`;
- `ENV-002`: an owner-approved, gitignored private fixture with 10 real comic issues, a 3,524-word Green Lantern
  script, the edited AU4 narration project, and a managed 28:15.219 mono 44.1 kHz PCM WAV. Source hashes were
  rechecked unchanged, AU4 SQLite integrity passed, and conversion provenance is recorded. No private media was
  committed. Several library `.cbz` files are actually mislabeled 7-Zip/RAR archives;
- `ENV-003`: real no-OCR and OCR 70-second H.264/AAC videos from a managed excerpt of the approved Green Lantern
  fixture. Both fully decode, have no detected black segment over 0.5 seconds, preserve all source hashes, and store
  complete documents in an integrity-checked SQLite database. No-OCR took 114.324 seconds; OCR took about 140.9
  seconds and produced 1,199 regions. Manual review found page-level crops, visible lettering, an OCR-selected
  ad/tag page, reuse, and no clear relevance improvement, so quality is `needs_repair` and E4/E5 remain open;
- `ARC-002`: the existing baseline API now executes five durable `PipelineRunner` stages for ingest, analysis and
  derived assets, uniform alignment, retrieval/storyboard, and render. Focused tests prove cache reuse,
  missing-output invalidation, project-scoped abandoned-attempt recovery, and restart without recomputing completed
  predecessors, plus reconstruction of a missing managed cache artifact (18 passed). A real 70-second Green Lantern
  run took 165.671 seconds; an identical restart took 2.527 seconds with five cache hits, the same fully decoded MP4
  hash, and SQLite `quick_check=ok`;
- `ARC-003` versioned worker protocol, lease/heartbeat, a stale-result guard, cooperative cancellation, timeout
  detection, typed error classes, and single-GPU admission in `src/miller/{db,models,workers}.py`;
- `AUD-001` produced a standalone alignment worker contract, probe/unload operations, and CPU-fallback auto-device
  resolution; independent review found its `torch>=2.1` and `stable-ts>=2.16` ranges do not satisfy the pinned,
  reproducible-environment objective, so the card is blocked rather than complete;
- `SEC-001` adversarial security tests (`tests/test_security.py`): CBZ/path/image fuzzing, localhost-boundary
  verification, log-secret-sanitization confirmation, subprocess-failure-surface tests; independent review fixed a
  residual DOM injection flaw by removing untrusted scene values from inline JavaScript handlers, and retained the
  structured-error extraction in `embedding_worker.py`;
- `SEC-002` ran `uv audit --locked` (0 vulnerabilities across 45 packages), generated `docs/SBOM.json` from real
  installed-package metadata (no GPL-family license found), captured the real FFmpeg build configuration (a GPL v3
  build — recorded as `RISKS.md` RSK-025 for future release-bundling decisions), and wrote `docs/NOTICES.md` and a
  supply-chain policy;
- `QAE-001` finalized the human quality rubric (`EVALUATION_PLAN.md`): visual and audio dimensions alongside the
  existing narrative ones, reviewer roles with clear authority, numeric scoring thresholds
  (`accepted`/`needs_repair`/`rejected`), a disagreement-handling process, and an immutable content-addressed E5
  acceptance-record format with a schema, a synthetic example, and a verification script
  (`docs/schemas/verify_e5_example.py`) that now enforces record shape, reviewer roles, score/threshold rules,
  disagreement detail, and reproducible content identity;
- Repository housekeeping: quarantined a stray duplicated `Miller/.head-chef/` directory; added `.gemma/`,
  `.head-chef/`, and `_quarantine/` to `.gitignore`; committed the previously-untracked `docs/INV-003-AUDIT.md`,
  `sprints/SPRINTS.json`, and the pre-existing-but-uncommitted `DOC-001` documentation reconciliation.
- Build safety: `pyproject.toml` now explicitly excludes local runtime/cache/media/quarantine paths from source
  distributions. A prior 186 MB sdist containing ignored `.miller` artifacts was moved intact to
  `.miller/quarantine/sdist-private-artifact-20260802-1800/`; the replacement sdist is 326,877 bytes and its 264
  paths contain none of the excluded directories.

Independent Codex review on 2026-08-02 inspected all six commits, artifacts, requirements, and current source. After
the bounded SEC-001/QAE-001 corrections: `uv sync --frozen --extra dev --extra web --extra export --extra retrieval`,
Ruff, strict Mypy, Pytest (133 passed, 1 skipped for missing symlink privilege), wheel/sdist build, planning validator,
E5 verifier, embedded-JavaScript syntax check, and `git diff --check` all passed. Earlier Head Chef review runs
checked each diff/report against every acceptance criterion for its sprint (`ARC-001`: run
`run-1ffb0cf91e2875eb`; `ARC-003`: run `run-c324ccef4c5699b9`; `AUD-001`: run `run-0bdcc2fd2eaad650`; `SEC-001`: run
`run-2aead45e6598cf9c`; `SEC-002`: run `run-5a83e4b732d0a1ba`; `QAE-001`: run `run-cbcbbb59c020276d`); the
coordinator recorded an `accepted` verdict on each run, correcting citation errors and several false-negative
verdicts each time (and, for `QAE-001`, adding a stronger verification script in direct response to one fair review
point) — see each run's review note for specifics. Current independent verdict supersedes those coordinator-only
verdicts where they conflict.

Later on 2026-08-02, the owner supplied the missing `ENV-002` script and edited narration. Codex inspected the
private manifest and source files, exported narration only from a byte-identical managed AU4 copy, verified the WAV
probe/hash/levels, and rechecked source hashes unchanged. This closes `BLK-002` and advances `ENV-002` to E3.

`ENV-003` then passed its bounded E3 technical objective. The report and contact sheet are under
`.miller/acceptance/`. A Head Chef vision worker's false PASS was rejected after coordinator inspection found the
visible ad and repeated art. A separate dedicated RTX 3070 text/evidence review accepted only the E3 technical
claim and explicitly kept E4/E5 unproven. Final gate passed: frozen sync, Ruff, strict Mypy, 133 passed/1 Windows
symlink skip, sdist/wheel build, planning validator (55 cards; active `ARC-002`), and `git diff --check`.

`ARC-002` then passed its bounded objective. The implementation and tests stay within the card's allowed files and
preserve the public baseline/CLI result contract. Content-addressed stage artifacts and dependency/config hashes
make completed work reusable; the render cache also verifies the external MP4 path and SHA-256. Synthetic
interruption proof is E2; the real Windows DAG/cache run is E3. The acceptance report is
`.miller/acceptance/ARC-002-report.json`. A dedicated RTX 3070 `qwen3.5:9b` review returned `ACCEPT`; Codex rejected
its speculative concerns about read-only source access and managed artifact paths. Atomic output promotion and a
real process-kill drill remain explicitly assigned to `ARC-004` and `ENV-004`.

## What was not done

- no crash-mid-operation interruption drill for `ARC-001`, `ARC-003`, or `AUD-001` — deferred to `ENV-004`;
- `ARC-002` restart recovery is automated/synthetic; a real process-kill and partial-output recovery drill remains;
- `ARC-003`'s new protocol is not yet wired into the actual external adapters — `ANL-005`/`RET-004` work;
- `AUD-001` did not produce a fully pinned environment or install/run real WhisperX/stable-ts/torch — no model
  weights were downloaded;
- `SEC-002` did not resolve Miller's own software license (`OD-001`) or model/data terms;
- `QAE-001`'s full E5 rubric has not been exercised against a real rendered project; the ENV-003 contact-sheet
  inspection is technical evidence plus quality findings, not owner acceptance;
- no Windows long-path, antivirus, or RTX 3070 hardware-stress tests were run in this environment;
- no pinned production model worker or subjective E5 video gate has passed;
- owner acceptance now exists for the private `ENV-002` fixture, but not for model installation, software license,
  or real-video quality;

## Exact next action

Execute `ARC-004`: audit all artifact and external render writes, implement atomic output promotion without
overwriting existing files, and prove recovery from an interrupted render. Preserve ARC-002 stage/cache behavior.

## Do not redo

Do not re-audit the repository or redesign the core before `ENV-001`. Use `CURRENT_STATE.md` as the accepted
inventory and open a correction card only if local evidence contradicts it. Do not re-implement any of `ARC-001`'s
migration/backup/restore mechanism, `ARC-003`'s worker protocol/lease mechanism, `SEC-001`'s fuzz-test coverage,
`SEC-002`'s SBOM/notices, or `QAE-001`'s rubric/schema. Preserve `AUD-001`'s worker protocol/CPU fallback, but do not
call its environment pinned or complete until exact locks install and probe successfully.

## Safe fallback cards

`ANL-001`, `ENV-004`, and `QAE-002` are ready. `AUD-001` still needs explicit authorization for a fully pinned
heavy model environment; `OD-001` remains owner-only.

## Context startup

Read `PROJECT_CHARTER.md`, the executive section of `CURRENT_STATE.md`, `SPRINT_STATE.json`, the `ARC-004` card, this
handoff, and Git status. Do not load all sprint cards into Gemma context.
