# Miller handoff

Status: **`ARC-001`, `ARC-003`, `AUD-001`, `SEC-001`, `SEC-002` implemented and locally verified; pending owner/independent review**
Planning revision: `2026-07-21-definitive`  
Active sprint: `QAE-001` (recommended next — the only sprint in the entire 55-card plan not currently blocked)

## What was completed

- repository and evidence-level assessment;
- preserved architecture direction;
- 13-layer roadmap and critical path;
- 55 permanent Gemma-sized sprint cards;
- machine-readable state and blocker fallbacks;
- external research/project decisions;
- board reviews and final architecture council;
- context/agent protocols;
- evaluation, test, risk, security, release, and owner-decision controls;
- first local Windows acceptance procedure;
- planning validator.
- synthetic no-OCR/OCR MP4 acceptance, capability manifest, hashes, FFprobe, and SQLite integrity report;
- `docs/INV-003-AUDIT.md` versioned dependency/data/license audit;
- `DOC-001` control-document reconciliation, planning validation, and independent local review;
- `ARC-001` ordered database migrations, preflight backup, integrity checks, and a restore drill in `src/miller/db.py`.
- `ENV-002` (comic portion only): a 10-issue real comic fixture manifest from the owner's `V:\Media\Comics` library
  (hashes only, gitignored, never committed). Discovered a real edge case: several `.cbz` files in the owner's
  library are actually mislabeled 7-Zip/RAR archives.
- `ARC-003` versioned worker protocol, lease/heartbeat, a stale-result guard, cooperative cancellation, timeout
  detection, typed error classes, and single-GPU admission in `src/miller/{db,models,workers}.py`.
- `AUD-001` a new standalone, isolated alignment worker process (`src/miller/audio/worker/align_worker.py`) plus a
  pinned environment spec, and CPU-fallback auto-device resolution in `ExternalAlignmentWorker.align()`.
- `SEC-001` 34 adversarial security tests (`tests/test_security.py`): CBZ/path/image fuzzing, localhost-boundary
  verification, log-secret-sanitization confirmation, subprocess-failure-surface tests. Fixed an XSS-prone unescaped
  interpolation in the embedded web editor and a missing structured-error extraction in `embedding_worker.py`.
- `SEC-002` ran `uv audit --locked` (0 vulnerabilities across 45 packages), generated `docs/SBOM.json` from real
  installed-package metadata (48 packages, no GPL-family license found), captured the real FFmpeg build
  configuration on this machine (a GPL v3 build — fine under the current subprocess architecture, but a bundling
  caveat is now recorded as `RISKS.md` RSK-025), and wrote `docs/NOTICES.md` and a supply-chain policy in
  `docs/SEC-002-AUDIT.md`. No production code was changed.
- Repository housekeeping: quarantined a stray duplicated `Miller/.head-chef/` directory; added `.gemma/`,
  `.head-chef/`, and `_quarantine/` to `.gitignore`; committed the previously-untracked `docs/INV-003-AUDIT.md`,
  `sprints/SPRINTS.json`, and the pre-existing-but-uncommitted `DOC-001` documentation reconciliation.

For `ARC-001`, `ARC-003`, `AUD-001`, and `SEC-001`: Ruff, strict Mypy, the full Pytest suite (129 passed, 1 skip),
and the wheel/sdist build all passed locally. `SEC-002` changed no production code (docs/reports only); the
existing gate was re-confirmed green. A local Head Chef analysis-station review independently checked each diff/
report against every acceptance criterion for its sprint (`ARC-001`: run `run-1ffb0cf91e2875eb`; `ARC-003`: run
`run-c324ccef4c5699b9`; `AUD-001`: run `run-0bdcc2fd2eaad650`; `SEC-001`: run `run-2aead45e6598cf9c`; `SEC-002`: run
`run-5a83e4b732d0a1ba`); the coordinator recorded an `accepted` verdict on each run, correcting citation errors and
several false-negative verdicts each time — see each run's review note for specifics.

## What was not done

- no crash-mid-operation interruption drill for `ARC-001`, `ARC-003`, or `AUD-001` — deferred to `ENV-004`;
- `ARC-003`'s new protocol is not yet wired into the actual external adapters — `ANL-005`/`RET-004` work;
- `AUD-001` did not install or run real WhisperX/stable-ts/torch — no model weights were downloaded;
- `SEC-002` did not resolve Miller's own software license (`OD-001`, owner decision) or model/data terms (blocked on
  actually installing model workers);
- no Windows long-path, antivirus, or RTX 3070 hardware-stress tests were run in this environment;
- no real comics, narration, model workers, or subjective video gates were tested;
- private comic paths/hashes were accessed (read-only) for the `ENV-002` manifest, but no script or narration fixture
  has been supplied or approved yet, so `ENV-002` is only partially satisfied and remains `blocked`;
- none of `ARC-001`, `ARC-003`, `AUD-001`, `SEC-001`, or `SEC-002` has had a human/owner review pass — only the
  coordinator (this session) and a local model reviewed each; the "independent reviewer accepts the result"
  acceptance criterion is only partially satisfied for all five.

## Exact next action

Owner/independent review of the `ARC-001`, `ARC-003`, `AUD-001`, `SEC-001`, and `SEC-002` evidence above.
`SPRINT_STATE.json`'s dependency graph currently has exactly **one** sprint whose prerequisites are fully satisfied
and not itself blocked: `QAE-001` (human quality rubric and acceptance records, deps `DOC-002` — complete). Every
other `ready`-status sprint (`ARC-002`, `ARC-004`, `ANL-005`, `RET-001`, `RET-004`, `STO-001`, `VID-003`, `UX-001`)
transitively depends on `ANL-001`/`ARC-002`/`ENV-003`, all of which are blocked on the still-missing script/narration
half of `ENV-002`. `REL-001` stays blocked behind `ENV-004`/`VID-004`/`UX-004` even with both `SEC-001` and
`SEC-002` now complete. In short: **after `QAE-001`, further sprint-card progress genuinely requires either the
owner supplying/approving a script + edited narration fixture, or an explicit owner decision to install real model
workers (WhisperX, embedding, VLM) — this is not a scope-discipline artifact, it is the real state of the
dependency graph.**

## Do not redo

Do not re-audit the repository or redesign the core before `ENV-001`. Use `CURRENT_STATE.md` as the accepted
inventory and open a correction card only if local evidence contradicts it. Do not re-implement `ARC-001`'s
migration/backup/restore mechanism, `ARC-003`'s worker protocol/lease mechanism, `AUD-001`'s worker
environment/CPU-fallback mechanism, `SEC-001`'s fuzz-test coverage, or `SEC-002`'s SBOM/notices; open a correction
card only if local evidence contradicts the implementation.

## Safe fallback cards

`QAE-001` is the only currently-unblocked card requiring no additional owner input.

## Context startup

Read `PROJECT_CHARTER.md`, the executive section of `CURRENT_STATE.md`, `SPRINT_STATE.json`, the `ENV-001` card, this
handoff, and Git status. Do not load all sprint cards into Gemma context.
