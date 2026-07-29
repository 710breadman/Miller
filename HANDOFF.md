# Miller handoff

Status: **`ARC-001`, `ARC-003`, `AUD-001` implemented and locally verified; pending owner/independent review**
Planning revision: `2026-07-21-definitive`  
Active sprint: `SEC-001` (recommended next; see "Exact next action")

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
  Migration version boundaries (1/2/3) were reconstructed by feature area, not replayed from history, because the
  schema was published in a single commit with no prior per-version diff — see `DECISIONS.md` D-004.
- `ENV-002` (comic portion only): owner pointed at a real local library, `V:\Media\Comics` (Daredevil, Green Lantern,
  Hawkman, Hulk, Punisher; ~4,700 issue files). Read-only survey selected 10 varied real `.cbz` issues across all 5
  series (roughly 1962–2024) and recorded path/size/sha256/zip-entry-count for each in
  `.miller/acceptance/ENV-002-fixture-manifest.json` (gitignored, never committed). Discovered and logged a real edge
  case: most sampled Green Lantern `.cbz` files (and one Hawkman file) are actually 7-Zip/RAR archives with a `.cbz`
  extension — Miller's ingest only opens true ZIP-format CBZ today. Recorded in the manifest's
  `rejected_candidates`/`known_data_issues` for `SEC-001` (next).
- `ARC-003` versioned worker protocol, lease/heartbeat, a stale-result guard, cooperative cancellation, lease-based
  timeout detection, typed error classes (`WorkerErrorClass`), and single-GPU admission in `src/miller/db.py`,
  `models.py`, and `workers.py` (`claim_next`, `heartbeat_queue_item`, `reclaim_expired_leases`,
  `request_cancel_queue_item`, `WorkerContext`, `WorkerError` subclasses). Every pre-existing caller's call signature
  still works unchanged. `requires_gpu` lives on the queue item (set via `enqueue`); `gpu_capacity` bounds
  concurrently running GPU items system-wide, across all `QueueKind`s.
- `AUD-001` a new standalone, isolated alignment worker process (`src/miller/audio/worker/align_worker.py`, no
  dependency on the `miller` package) implementing `probe`/`align`/`unload` for WhisperX and stable-ts, plus a pinned
  environment spec (`src/miller/audio/worker/requirements.txt`; WhisperX pinned to the exact revision already in
  `docs/upstream-lock.json`, stable-ts pinned only by minimum version pending a confirmed revision). `probe` honestly
  reports today's real state on this machine (torch/whisperx/stable-ts all absent) — a genuine, not simulated, check.
  `ExternalAlignmentWorker.align()` in `whisper_worker.py` now defaults to `device="auto"`, probing first and falling
  back to CPU (`int8`) when CUDA is unavailable; an explicit `device`/`compute_type` still bypasses that resolution.
  No heavy ML dependency was installed or downloaded — that remains explicit, owner-gated work (`OD-007`, `AUD-002`).
- Repository housekeeping: quarantined a stray duplicated `Miller/.head-chef/` directory into
  `_quarantine/2026-07-29_cleanup/`; added `.gemma/`, `.head-chef/`, and `_quarantine/` to `.gitignore`; committed the
  previously-untracked `docs/INV-003-AUDIT.md`, `sprints/SPRINTS.json`, and the pre-existing-but-uncommitted `DOC-001`
  documentation reconciliation, each as their own coherent commits.

For `ARC-001`, `ARC-003`, and `AUD-001`: Ruff, strict Mypy, the full Pytest suite (95 passed), and the wheel/sdist
build all passed locally on this Windows machine. A local Head Chef analysis-station review independently checked
each diff against every acceptance criterion for its sprint and agreed (`ARC-001`: `qwen3.5:4b`, run
`run-1ffb0cf91e2875eb`; `ARC-003`: `qwen3.5:9b`, run `run-c324ccef4c5699b9`; `AUD-001`:
`hf.co/arbazsiddiqui/Ozan-v1-12B-GGUF:Q4_K_M`, run `run-0bdcc2fd2eaad650`); the coordinator recorded an `accepted`
verdict on each run, correcting minor citation errors each time (see each run's review note).

## What was not done

- no crash-mid-operation interruption drill (kill the process mid-migration/mid-claim/mid-align) for `ARC-001`,
  `ARC-003`, or `AUD-001` — deferred to `ENV-004`;
- `ARC-003`'s new protocol is not yet wired into the actual external adapters (`audio/whisper_worker.py`,
  `retrieval/embedding_worker.py` still call a bare subprocess directly, not through the queue/lease machinery) —
  that integration is `ANL-005`/`RET-004` work;
- `AUD-001` did not install or run real WhisperX/stable-ts/torch — no model weights were downloaded, no GPU inference
  was attempted; the pinned environment is a specification only, confirmed accurate only up to what git/PyPI record,
  not by actually building it;
- no Windows long-path, antivirus, or RTX 3070 hardware-stress tests were run in this environment;
- no real comics, narration, model workers, or subjective video gates were tested;
- private comic paths/hashes were accessed (read-only) for the `ENV-002` manifest, but no script or narration fixture
  has been supplied or approved yet, so `ENV-002` is only partially satisfied and remains `blocked`;
- no license decision was made for the owner;
- none of `ARC-001`, `ARC-003`, or `AUD-001` has had a human/owner review pass — only the coordinator (this session)
  and a local model reviewed each; the "independent reviewer accepts the result" acceptance criterion is only
  partially satisfied for all three.

## Exact next action

Owner/independent review of the `ARC-001`, `ARC-003`, and `AUD-001` evidence above. Per `SPRINT_STATE.json`'s
dependency graph, `AUD-001`'s direct successor `AUD-002` stays blocked behind `ENV-002`'s missing script/narration
half. `SEC-001` (archive/file/API/worker security tests, deps `ARC-003` — satisfied) is the recommended next sprint:
it directly follows up on the mislabeled-7z/RAR-archive finding logged during `ENV-002`. `SEC-002` and `QAE-001` are
also unblocked fallback options. `ENV-002` itself stays `blocked`: it still needs an approved script + edited
narration recording before it and its direct dependents (`ANL-001`, `RET-002`, `AUD-002`, `ENV-003`) can move; keep
license/model/data decisions explicit.

## Do not redo

Do not re-audit the repository or redesign the core before `ENV-001`. Use `CURRENT_STATE.md` as the accepted
inventory and open a correction card only if local evidence contradicts it. Do not re-implement `ARC-001`'s
migration/backup/restore mechanism, `ARC-003`'s worker protocol/lease mechanism, or `AUD-001`'s worker
environment/CPU-fallback mechanism; open a correction card only if local evidence contradicts the implementation.

## Safe fallback cards

`SEC-001`, `SEC-002`, and `QAE-001` can proceed when their prerequisites are satisfied without the private
script/narration fixture.

## Context startup

Read `PROJECT_CHARTER.md`, the executive section of `CURRENT_STATE.md`, `SPRINT_STATE.json`, the `ENV-001` card, this
handoff, and Git status. Do not load all sprint cards into Gemma context.
