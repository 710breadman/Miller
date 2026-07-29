# Miller handoff

Status: **`ARC-001`, `ARC-003`, `AUD-001`, `SEC-001` implemented and locally verified; pending owner/independent review**
Planning revision: `2026-07-21-definitive`  
Active sprint: `SEC-002` (recommended next; see "Exact next action")

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
- `ARC-001` ordered database migrations, preflight backup, `PRAGMA integrity_check`-based corruption detection, and a
  restore drill in `src/miller/db.py` (`_MIGRATIONS`, `create_backup`, `restore_from_backup`, `verify_integrity`).
- `ENV-002` (comic portion only): owner pointed at a real local library, `V:\Media\Comics` (Daredevil, Green Lantern,
  Hawkman, Hulk, Punisher; ~4,700 issue files). Read-only survey selected 10 varied real `.cbz` issues across all 5
  series (roughly 1962–2024) and recorded path/size/sha256/zip-entry-count for each in
  `.miller/acceptance/ENV-002-fixture-manifest.json` (gitignored, never committed). Discovered a real edge case:
  most sampled Green Lantern `.cbz` files (and one Hawkman file) are actually 7-Zip/RAR archives with a `.cbz`
  extension — Miller's ingest only opens true ZIP-format CBZ today.
- `ARC-003` versioned worker protocol, lease/heartbeat, a stale-result guard, cooperative cancellation, lease-based
  timeout detection, typed error classes (`WorkerErrorClass`), and single-GPU admission in `src/miller/db.py`,
  `models.py`, and `workers.py`. Every pre-existing caller's call signature still works unchanged.
- `AUD-001` a new standalone, isolated alignment worker process (`src/miller/audio/worker/align_worker.py`, no
  dependency on the `miller` package) implementing `probe`/`align`/`unload` for WhisperX and stable-ts, plus a pinned
  environment spec. `ExternalAlignmentWorker.align()` now defaults to `device="auto"`, probing first and falling back
  to CPU when CUDA is unavailable. No heavy ML dependency was installed or downloaded.
- `SEC-001` 34 new adversarial tests in `tests/test_security.py`: CBZ archive/path/image fuzzing (path traversal,
  absolute/Windows-drive paths, case-insensitive duplicates, encrypted entries via real ZIP-header byte patching,
  oversized/zero-byte entries, total-size and compression-ratio zip-bomb limits, entry-count limits, corrupted
  images, invalid archives), localhost-only boundary verification (CLI argparse `choices` + `MillerSettings`
  validator), confirmation that `attempt_guard`/`lease_token` secrets never reach logs or DB events, subprocess
  missing-binary/malformed-JSON/structured-error-body tests for both worker adapters, and a static no-`shell=True`
  check. Found and fixed two real issues: an XSS-prone unescaped `scene.id` interpolation into `onclick`/`onchange`
  JS-attribute strings in `web/app.py`'s embedded editor, and a missing structured-error-message extraction in
  `retrieval/embedding_worker.py` (now matches `whisper_worker.py`'s `AUD-001` pattern). Also discovered and
  documented that Python's `zipfile` normalizes a literal backslash to a forward slash on *read*, meaning Miller's
  own `"\\"`-rejection check in `comics/cbz.py` is defensive dead code in practice (kept for platform-behavior
  safety, not currently reachable).
- Repository housekeeping: quarantined a stray duplicated `Miller/.head-chef/` directory; added `.gemma/`,
  `.head-chef/`, and `_quarantine/` to `.gitignore`; committed the previously-untracked `docs/INV-003-AUDIT.md`,
  `sprints/SPRINTS.json`, and the pre-existing-but-uncommitted `DOC-001` documentation reconciliation.

For `ARC-001`, `ARC-003`, `AUD-001`, and `SEC-001`: Ruff, strict Mypy, the full Pytest suite (129 passed, 1 skip for
missing symlink privilege), and the wheel/sdist build all passed locally on this Windows machine. A local Head Chef
analysis-station review independently checked each diff against every acceptance criterion for its sprint (`ARC-001`:
run `run-1ffb0cf91e2875eb`; `ARC-003`: run `run-c324ccef4c5699b9`; `AUD-001`: run `run-0bdcc2fd2eaad650`; `SEC-001`:
run `run-2aead45e6598cf9c`); the coordinator recorded an `accepted` verdict on each run, correcting citation errors
(and one false-negative verdict on `SEC-001`'s CBZ-fuzzing criterion) each time — see each run's review note for
specifics.

## What was not done

- no crash-mid-operation interruption drill for `ARC-001`, `ARC-003`, or `AUD-001` — deferred to `ENV-004`;
- `ARC-003`'s new protocol is not yet wired into the actual external adapters — that integration is
  `ANL-005`/`RET-004` work;
- `AUD-001` did not install or run real WhisperX/stable-ts/torch — no model weights were downloaded;
- `SEC-001` did not fix CBR/PDF ingest support (out of scope; a distinct capability gap, not a security defect) —
  the mislabeled-archive finding from `ENV-002` is now formally covered by fuzz tests confirming Miller correctly
  refuses to open a non-ZIP file regardless of its `.cbz` extension, which is the correct/safe behavior;
- no Windows long-path, antivirus, or RTX 3070 hardware-stress tests were run in this environment;
- no real comics, narration, model workers, or subjective video gates were tested;
- private comic paths/hashes were accessed (read-only) for the `ENV-002` manifest, but no script or narration fixture
  has been supplied or approved yet, so `ENV-002` is only partially satisfied and remains `blocked`;
- no license decision was made for the owner;
- none of `ARC-001`, `ARC-003`, `AUD-001`, or `SEC-001` has had a human/owner review pass — only the coordinator
  (this session) and a local model reviewed each; the "independent reviewer accepts the result" acceptance criterion
  is only partially satisfied for all four.

## Exact next action

Owner/independent review of the `ARC-001`, `ARC-003`, `AUD-001`, and `SEC-001` evidence above. Per `SPRINT_STATE.json`'s
dependency graph, `SEC-001`'s direct successor `REL-001` stays blocked behind `ENV-004`/`SEC-002`/`VID-004`/`UX-004`.
`SEC-002` (dependency/model/data/SBOM/license review, deps `INV-003` — satisfied) is the recommended next sprint; it
directly extends `docs/INV-003-AUDIT.md`. `QAE-001` is also an unblocked fallback option. `ENV-002` itself stays
`blocked`: it still needs an approved script + edited narration recording before it and its direct dependents
(`ANL-001`, `RET-002`, `AUD-002`, `ENV-003`) can move; keep license/model/data decisions explicit.

## Do not redo

Do not re-audit the repository or redesign the core before `ENV-001`. Use `CURRENT_STATE.md` as the accepted
inventory and open a correction card only if local evidence contradicts it. Do not re-implement `ARC-001`'s
migration/backup/restore mechanism, `ARC-003`'s worker protocol/lease mechanism, `AUD-001`'s worker
environment/CPU-fallback mechanism, or `SEC-001`'s fuzz-test coverage; open a correction card only if local evidence
contradicts the implementation.

## Safe fallback cards

`SEC-002` and `QAE-001` can proceed when their prerequisites are satisfied without the private script/narration
fixture.

## Context startup

Read `PROJECT_CHARTER.md`, the executive section of `CURRENT_STATE.md`, `SPRINT_STATE.json`, the `ENV-001` card, this
handoff, and Git status. Do not load all sprint cards into Gemma context.
