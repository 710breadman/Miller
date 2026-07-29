# Project status

Updated: **2026-07-29**
Planning revision: `2026-07-21-definitive`

## Current

Miller has an E2-verified software foundation plus E3 synthetic/local Windows acceptance, now including ordered database migrations, preflight backup, integrity checks, and a restore drill (`ARC-001`, pending owner/independent review). It does not yet have real-comic, real-model, retrieval-winner, human-quality, or clean-release acceptance.

Active sprint: **`ARC-003 — Worker protocol, lease, and resource hardening`**.

## Preserved strengths

- read-only safe comic ingestion;
- SQLite authority, immutable attempts, document revisions, and artifact hashes;
- deterministic runner and optional external worker contracts;
- BM25 baseline and rebuildable vector adapter;
- storyboard/edit/render data contracts;
- native FFmpeg render path;
- synthetic tests and package verification.

## Highest gaps

- the direct baseline does not yet use the durable DAG;
- worker leases and resource hardening need work (`ARC-003`);
- panel/OCR/semantic analysis and retrieval lack real-corpus proof;
- storyboard choices are lexical/greedy rather than globally optimized;
- real alignment, cleanup, UI, partial render, Windows packaging, and licensing remain open.

## Next

Owner/independent review of `ARC-001` evidence, then implement and verify
`ARC-003` (worker protocol, lease, and resource hardening). The full plan is
indexed by `docs/PLANNING_INDEX.md`.
