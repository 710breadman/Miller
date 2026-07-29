# Miller handoff

Status: **`ARC-001`, `ARC-003`, `AUD-001`, `SEC-001`, `SEC-002`, `QAE-001` implemented and locally verified; pending owner/independent review**
Planning revision: `2026-07-21-definitive`  
Active sprint: **none** — every remaining sprint is blocked on an owner decision (see "Exact next action")

## What was completed

- repository and evidence-level assessment, roadmap, sprint cards, machine-readable state, decisions, protocols,
  evaluation/test/risk/security/release/owner-decision controls, first local Windows acceptance procedure, planning
  validator, `docs/INV-003-AUDIT.md`, `DOC-001` control-document reconciliation (all prior sessions);
- `ARC-001` ordered database migrations, preflight backup, `PRAGMA integrity_check`-based corruption detection, and
  a restore drill in `src/miller/db.py`;
- `ENV-002` (comic portion only): a 10-issue real comic fixture manifest from the owner's `V:\Media\Comics` library
  (hashes only, gitignored, never committed); discovered a real edge case — several `.cbz` files in the owner's
  library are actually mislabeled 7-Zip/RAR archives;
- `ARC-003` versioned worker protocol, lease/heartbeat, a stale-result guard, cooperative cancellation, timeout
  detection, typed error classes, and single-GPU admission in `src/miller/{db,models,workers}.py`;
- `AUD-001` a new standalone, isolated alignment worker process (`src/miller/audio/worker/align_worker.py`) plus a
  pinned environment spec, and CPU-fallback auto-device resolution in `ExternalAlignmentWorker.align()`;
- `SEC-001` 34 adversarial security tests (`tests/test_security.py`): CBZ/path/image fuzzing, localhost-boundary
  verification, log-secret-sanitization confirmation, subprocess-failure-surface tests; fixed an XSS-prone
  unescaped interpolation in the embedded web editor and a missing structured-error extraction in
  `embedding_worker.py`;
- `SEC-002` ran `uv audit --locked` (0 vulnerabilities across 45 packages), generated `docs/SBOM.json` from real
  installed-package metadata (no GPL-family license found), captured the real FFmpeg build configuration (a GPL v3
  build — recorded as `RISKS.md` RSK-025 for future release-bundling decisions), and wrote `docs/NOTICES.md` and a
  supply-chain policy;
- `QAE-001` finalized the human quality rubric (`EVALUATION_PLAN.md`): visual and audio dimensions alongside the
  existing narrative ones, reviewer roles with clear authority, numeric scoring thresholds
  (`accepted`/`needs_repair`/`rejected`), a disagreement-handling process, and an immutable content-addressed E5
  acceptance-record format with a schema, a synthetic example, and a committed verification script
  (`docs/schemas/verify_e5_example.py`) that recomputes and confirms the content hash;
- Repository housekeeping: quarantined a stray duplicated `Miller/.head-chef/` directory; added `.gemma/`,
  `.head-chef/`, and `_quarantine/` to `.gitignore`; committed the previously-untracked `docs/INV-003-AUDIT.md`,
  `sprints/SPRINTS.json`, and the pre-existing-but-uncommitted `DOC-001` documentation reconciliation.

For `ARC-001`, `ARC-003`, `AUD-001`, and `SEC-001`: Ruff, strict Mypy, the full Pytest suite (129 passed, 1 skip for
missing symlink privilege), and the wheel/sdist build all passed locally. `SEC-002` and `QAE-001` changed no
production code; the same gate was re-confirmed green after each. A local Head Chef analysis-station review
independently checked each diff/report against every acceptance criterion for its sprint (`ARC-001`: run
`run-1ffb0cf91e2875eb`; `ARC-003`: run `run-c324ccef4c5699b9`; `AUD-001`: run `run-0bdcc2fd2eaad650`; `SEC-001`: run
`run-2aead45e6598cf9c`; `SEC-002`: run `run-5a83e4b732d0a1ba`; `QAE-001`: run `run-cbcbbb59c020276d`); the
coordinator recorded an `accepted` verdict on each run, correcting citation errors and several false-negative
verdicts each time (and, for `QAE-001`, adding a genuinely stronger verification script in direct response to one
fair local-review point) — see each run's review note for specifics.

## What was not done

- no crash-mid-operation interruption drill for `ARC-001`, `ARC-003`, or `AUD-001` — deferred to `ENV-004`;
- `ARC-003`'s new protocol is not yet wired into the actual external adapters — `ANL-005`/`RET-004` work;
- `AUD-001` did not install or run real WhisperX/stable-ts/torch — no model weights were downloaded;
- `SEC-002` did not resolve Miller's own software license (`OD-001`) or model/data terms;
- `QAE-001`'s rubric has not been exercised against any real rendered project — no real render exists yet;
- no Windows long-path, antivirus, or RTX 3070 hardware-stress tests were run in this environment;
- no real comics, narration, model workers, or subjective video gates were tested;
- private comic paths/hashes were accessed (read-only) for the `ENV-002` manifest, but no script or narration
  fixture has been supplied or approved yet, so `ENV-002` is only partially satisfied and remains `blocked`;
- none of the six sprints completed this session has had a human/owner review pass — only the coordinator (this
  session) and a local model reviewed each; the "independent reviewer accepts the result" acceptance criterion is
  only partially satisfied for all six.

## Exact next action

**This is a genuine stopping point, not a scope-discipline artifact.** Owner/independent review of the six sprints'
evidence above is the first step. After that, per `SPRINT_STATE.json`'s dependency graph, every remaining
`ready`-status sprint (`ARC-002`, `ARC-004`, `ANL-005`, `RET-001`, `RET-004`, `STO-001`, `VID-003`, `UX-001`)
transitively depends on the still-missing script/narration half of `ENV-002`, or on an explicit decision to install
a real model worker. Concretely, one of the following must happen before further bounded sprint-card work is
possible:

1. The owner supplies or approves a script + edited narration recording for at least one of the 10 comic fixtures
   already recorded in `.miller/acceptance/ENV-002-fixture-manifest.json` — this unblocks `ANL-001` and, through it,
   most of the `ANL`/`RET`/`STO` roadmap items.
2. The owner explicitly authorizes installing a real model worker (WhisperX/stable-ts per `AUD-001`'s pinned spec,
   an embedding model, or a VLM) — heavy, multi-GB downloads that were deliberately not done without that
   authorization (`OD-007`).
3. The owner makes the `OD-001` software-license decision, which unblocks meaningful progress on `REL-002`.

## Do not redo

Do not re-audit the repository or redesign the core before `ENV-001`. Use `CURRENT_STATE.md` as the accepted
inventory and open a correction card only if local evidence contradicts it. Do not re-implement any of `ARC-001`'s
migration/backup/restore mechanism, `ARC-003`'s worker protocol/lease mechanism, `AUD-001`'s worker
environment/CPU-fallback mechanism, `SEC-001`'s fuzz-test coverage, `SEC-002`'s SBOM/notices, or `QAE-001`'s rubric/
schema; open a correction card only if local evidence contradicts the implementation.

## Safe fallback cards

None remain unblocked without additional owner input (script/narration fixture, model-install authorization, or the
license decision) — see "Exact next action" above.

## Context startup

Read `PROJECT_CHARTER.md`, the executive section of `CURRENT_STATE.md`, `SPRINT_STATE.json`, the `ENV-001` card, this
handoff, and Git status. Do not load all sprint cards into Gemma context.
