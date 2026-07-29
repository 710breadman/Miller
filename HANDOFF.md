# Miller handoff

Status: **ARC-001 implemented and locally verified; pending owner/independent review; ARC-003 active**
Planning revision: `2026-07-21-definitive`  
Active sprint: `ARC-003`

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
  9 new/updated tests in `tests/test_db.py`. Ruff, strict Mypy (82 files), the full Pytest suite (71 passed), and the
  wheel/sdist build all passed locally on this Windows machine. A local Head Chef analysis-station review
  (`qwen3.5:4b`, run `run-1ffb0cf91e2875eb`) independently checked the diff against every acceptance criterion and
  agreed; the coordinator recorded an `accepted` verdict on that run. Migration version boundaries (1/2/3) were
  reconstructed by feature area, not replayed from history, because the schema was published in a single commit with
  no prior per-version diff — see `DECISIONS.md` D-004 and the note at the top of `_MIGRATIONS` in `db.py`.
- `ENV-002` (comic portion only): owner pointed at a real local library, `V:\Media\Comics` (Daredevil, Green Lantern,
  Hawkman, Hulk, Punisher; ~4,700 issue files). Read-only survey selected 10 varied real `.cbz` issues across all 5
  series (roughly 1962–2024) and recorded path/size/sha256/zip-entry-count for each in
  `.miller/acceptance/ENV-002-fixture-manifest.json` (gitignored via `.miller/`, never committed; see policy notes in
  the manifest itself). Nothing under the source library was modified, copied, or extracted. Discovered and logged a
  real edge case along the way: most sampled Green Lantern `.cbz` files (and one Hawkman file) are actually 7-Zip/RAR
  archives with a `.cbz` extension — Miller's ingest only opens true ZIP-format CBZ today, so these would fail; three
  originally-picked fixtures were swapped for genuinely valid ones, and the rejected ones plus the sampling evidence
  are recorded in the manifest's `rejected_candidates`/`known_data_issues` for `SEC-001`/ingest-hardening later.

## What was not done

- product code (`src/miller/db.py`, `tests/test_db.py`) *was* changed this session for `ARC-001` — see above; this is
  the first sprint in this planning revision to touch product code rather than only control documents;
- no crash-mid-migration or interruption drill (kill the process while a migration is applying) — deferred to
  `ARC-003`/`ENV-004`;
- no restore drill against a large, real, multi-project database — only synthetic fixtures in `tests/test_db.py`;
- no Windows long-path, antivirus, or RTX 3070 hardware tests were run in this environment;
- no real comics, narration, model workers, or subjective video gates were tested (a read-only comic-fixture survey
  was done for `ENV-002`, see above, but no analysis/retrieval/render pipeline ran against real media);
- private comic paths/hashes were accessed (read-only) for the `ENV-002` manifest, but no script or narration fixture
  has been supplied or approved yet, so `ENV-002` is only partially satisfied and remains `blocked`;
- no license decision was made for the owner;
- `ARC-001`'s evidence has not yet had a human/owner review pass — only the coordinator (this session) and a local
  model reviewed it; the sprint's "independent reviewer accepts the result" criterion is only partially satisfied.

## Exact next action

Owner/independent review of the `ARC-001` evidence above. Then run `ARC-003` (worker protocol, lease, and resource
hardening) from `docs/sprints/ARC-003.md`. `ENV-002` stays `blocked`: the comic half of its fixture is now recorded
(`.miller/acceptance/ENV-002-fixture-manifest.json`), but it still needs an approved script + edited narration
recording for at least one of the 10 fixtures before the sprint and its dependents (`ANL-001`, `RET-002`, `AUD-002`,
`ENV-003`) can move; keep license/model/data decisions explicit.

## Do not redo

Do not re-audit the repository or redesign the core before `ENV-001`. Use `CURRENT_STATE.md` as the accepted inventory and open a correction card only if local evidence contradicts it. Do not re-implement `ARC-001`'s migration/backup/restore mechanism; open a correction card only if local evidence contradicts the implementation.

## Housekeeping noticed but out of `ARC-001` scope

- `Miller/` at the repository root is an untracked, apparently duplicated nested `.head-chef` state directory (looks
  like a past "wrong project root" dispatch, similar to what `_quarantine/2026-07-26_cleanup/head-chef-wrong-root`
  already captured once). Left untouched — not in `ARC-001`'s allowed files and safer for a human or a dedicated
  cleanup card to confirm before moving/deleting.
- `SPRINT_STATE.json`'s `next_unblocked` list still contains `ENV-001` and `INV-003`, which are already in
  `completed_sprints`; this redundancy predates this session and is out of `ARC-001`'s scope to fully audit.

## Safe fallback cards

`INV-003`, `ARC-003`, `SEC-001`, `SEC-002`, and `QAE-001` can proceed when their prerequisites are satisfied without the private fixture.

## Context startup

Read `PROJECT_CHARTER.md`, the executive section of `CURRENT_STATE.md`, `SPRINT_STATE.json`, the `ENV-001` card, this handoff, and Git status. Do not load all sprint cards into Gemma context.
