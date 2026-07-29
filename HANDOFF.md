# Miller handoff

Status: **`ARC-001` and `ARC-003` implemented and locally verified; pending owner/independent review**
Planning revision: `2026-07-21-definitive`  
Active sprint: `AUD-001` (recommended next; see "Exact next action")

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
  restore drill in `src/miller/db.py` (`_MIGRATIONS`, `create_backup`, `restore_from_backup`, `verify_integrity`), with
  9 new/updated tests in `tests/test_db.py`. Migration version boundaries (1/2/3) were reconstructed by feature area,
  not replayed from history, because the schema was published in a single commit with no prior per-version diff — see
  `DECISIONS.md` D-004 and the note at the top of `_MIGRATIONS` in `db.py`.
- `ENV-002` (comic portion only): owner pointed at a real local library, `V:\Media\Comics` (Daredevil, Green Lantern,
  Hawkman, Hulk, Punisher; ~4,700 issue files). Read-only survey selected 10 varied real `.cbz` issues across all 5
  series (roughly 1962–2024) and recorded path/size/sha256/zip-entry-count for each in
  `.miller/acceptance/ENV-002-fixture-manifest.json` (gitignored via `.miller/`, never committed; see policy notes in
  the manifest itself). Nothing under the source library was modified, copied, or extracted. Discovered and logged a
  real edge case along the way: most sampled Green Lantern `.cbz` files (and one Hawkman file) are actually 7-Zip/RAR
  archives with a `.cbz` extension — Miller's ingest only opens true ZIP-format CBZ today, so these would fail; three
  originally-picked fixtures were swapped for genuinely valid ones, and the rejected ones plus the sampling evidence
  are recorded in the manifest's `rejected_candidates`/`known_data_issues` for `SEC-001`/ingest-hardening later.
- `ARC-003` versioned worker protocol, lease/heartbeat, a stale-result guard, cooperative cancellation, lease-based
  timeout detection, typed error classes (`WorkerErrorClass`), and single-GPU admission in `src/miller/db.py`,
  `models.py`, and `workers.py` (`claim_next`, `heartbeat_queue_item`, `reclaim_expired_leases`,
  `request_cancel_queue_item`, `WorkerContext`, `WorkerError` subclasses), with 16 new tests across
  `tests/test_queue.py` (10) and `tests/test_workers.py` (6). Every pre-existing caller's call signature still works
  unchanged (`cli.py`'s `queue-*` commands, the original `QueueWorker(database, kind, handler)` construction, bare
  `complete_queue_item(item_id)`/`fail_queue_item(item_id, error)` calls) — the new lease/protocol machinery is
  additive and opt-in for callers that pass the new parameters. `requires_gpu` lives on the queue item (set via
  `enqueue`), not the worker; `gpu_capacity` on `QueueWorker`/`claim_next` bounds concurrently running GPU items
  system-wide, across all `QueueKind`s.
- Repository housekeeping: quarantined a stray duplicated `Miller/.head-chef/` directory (empty boilerplate from a
  past misrooted invocation) into `_quarantine/2026-07-29_cleanup/`; added `.gemma/`, `.head-chef/`, and
  `_quarantine/` to `.gitignore` (machine-local orchestration runtime state, same treatment as the existing `.miller/`
  entry); committed the previously-untracked `docs/INV-003-AUDIT.md` and `sprints/SPRINTS.json`, and the
  pre-existing-but-uncommitted `DOC-001` documentation reconciliation, as their own coherent commits.

For both `ARC-001` and `ARC-003`: Ruff, strict Mypy (82 files), the full Pytest suite (87 passed), and the wheel/sdist
build all passed locally on this Windows machine. A local Head Chef analysis-station review independently checked
each diff against every acceptance criterion for its sprint and agreed (`ARC-001`: `qwen3.5:4b`, run
`run-1ffb0cf91e2875eb`; `ARC-003`: `qwen3.5:9b`, run `run-c324ccef4c5699b9`); the coordinator recorded an `accepted`
verdict on each run.

## What was not done

- no crash-mid-migration/mid-claim interruption drill (kill the process mid-operation) for either `ARC-001` or
  `ARC-003` — deferred to `ENV-004`;
- no restore drill against a large, real, multi-project database — only synthetic fixtures in `tests/test_db.py`;
- `ARC-003`'s external worker adapters (`audio/whisper_worker.py`, `retrieval/embedding_worker.py`) do not yet route
  through the new versioned protocol/lease queue — that integration is `ANL-005`/`AUD-001`/`RET-004` work, not done
  here (those files are outside `ARC-003`'s allowed-file scope);
- no Windows long-path, antivirus, or RTX 3070 hardware-stress tests were run in this environment;
- no real comics, narration, model workers, or subjective video gates were tested (a read-only comic-fixture survey
  was done for `ENV-002`, see above, but no analysis/retrieval/render pipeline ran against real media);
- private comic paths/hashes were accessed (read-only) for the `ENV-002` manifest, but no script or narration fixture
  has been supplied or approved yet, so `ENV-002` is only partially satisfied and remains `blocked`;
- no license decision was made for the owner;
- neither `ARC-001` nor `ARC-003` has had a human/owner review pass — only the coordinator (this session) and a local
  model reviewed each; the "independent reviewer accepts the result" acceptance criterion is only partially satisfied
  for both.

## Exact next action

Owner/independent review of the `ARC-001` and `ARC-003` evidence above. Per `SPRINT_STATE.json`'s dependency graph,
`AUD-001` (pinned alignment worker environments) is the only direct `ARC-003` successor whose prerequisites are now
fully satisfied (`ARC-003` complete, `ENV-001` complete); `ANL-005`/`RET-004`/`VID-002` remain blocked behind
`ANL-001`/`VID-001`, which need the script+narration half of `ENV-002`. `SEC-001`, `SEC-002`, and `QAE-001` are also
unblocked and available as fallback work. `ENV-002` itself stays `blocked`: it still needs an approved script +
edited narration recording for at least one of the 10 comic fixtures before it and its direct dependents (`ANL-001`,
`RET-002`, `AUD-002`, `ENV-003`) can move; keep license/model/data decisions explicit.

## Do not redo

Do not re-audit the repository or redesign the core before `ENV-001`. Use `CURRENT_STATE.md` as the accepted
inventory and open a correction card only if local evidence contradicts it. Do not re-implement `ARC-001`'s
migration/backup/restore mechanism or `ARC-003`'s worker protocol/lease mechanism; open a correction card only if
local evidence contradicts the implementation.

## Safe fallback cards

`AUD-001`, `SEC-001`, `SEC-002`, and `QAE-001` can proceed when their prerequisites are satisfied without the
private script/narration fixture.

## Context startup

Read `PROJECT_CHARTER.md`, the executive section of `CURRENT_STATE.md`, `SPRINT_STATE.json`, the `ENV-001` card, this
handoff, and Git status. Do not load all sprint cards into Gemma context.
