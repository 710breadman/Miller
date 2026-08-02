# Miller handoff

Status: **`ENV-002` accepted at E3; `ENV-003` active; `ANL-001` ready; `AUD-001` remains incomplete/E2**
Planning revision: `2026-07-21-definitive`  
Active sprint: **`ENV-003` — Real no-AI baseline acceptance**

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

## What was not done

- no crash-mid-operation interruption drill for `ARC-001`, `ARC-003`, or `AUD-001` — deferred to `ENV-004`;
- `ARC-003`'s new protocol is not yet wired into the actual external adapters — `ANL-005`/`RET-004` work;
- `AUD-001` did not produce a fully pinned environment or install/run real WhisperX/stable-ts/torch — no model
  weights were downloaded;
- `SEC-002` did not resolve Miller's own software license (`OD-001`) or model/data terms;
- `QAE-001`'s rubric has not been exercised against any real rendered project — no real render exists yet;
- no Windows long-path, antivirus, or RTX 3070 hardware-stress tests were run in this environment;
- no real baseline video, model worker, or subjective video gate has been tested yet;
- owner acceptance now exists for the private `ENV-002` fixture, but not for model installation, software license,
  or real-video quality;

## Exact next action

Run `ENV-003` using a managed 30–90 second excerpt of the approved Green Lantern script/WAV and one recorded Green
Lantern comic fixture. Produce separate no-OCR and OCR MP4s, preserve commands/timing/hashes/ffprobe/warnings,
manually inspect both, and recheck every source hash. Do not alter production code if the acceptance run finds a
defect; record it and open the appropriate bounded card.

## Do not redo

Do not re-audit the repository or redesign the core before `ENV-001`. Use `CURRENT_STATE.md` as the accepted
inventory and open a correction card only if local evidence contradicts it. Do not re-implement any of `ARC-001`'s
migration/backup/restore mechanism, `ARC-003`'s worker protocol/lease mechanism, `SEC-001`'s fuzz-test coverage,
`SEC-002`'s SBOM/notices, or `QAE-001`'s rubric/schema. Preserve `AUD-001`'s worker protocol/CPU fallback, but do not
call its environment pinned or complete until exact locks install and probe successfully.

## Safe fallback cards

`ANL-001` is ready if `ENV-003` blocks. `AUD-001` still needs explicit authorization for a fully pinned heavy model
environment; `OD-001` remains owner-only.

## Context startup

Read `PROJECT_CHARTER.md`, the executive section of `CURRENT_STATE.md`, `SPRINT_STATE.json`, the `ENV-003` card, this
handoff, and Git status. Do not load all sprint cards into Gemma context.
