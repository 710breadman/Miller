# Project status

Updated: **2026-07-21**  
Planning revision: `2026-07-21-definitive`

## Current

Miller has an E2-verified software foundation and synthetic no-AI video baseline. It does not yet have target-Windows, real-comic, real-model, retrieval-winner, human-quality, or clean-release acceptance.

Active sprint: **`ENV-001 — Windows checkout and capability proof`**.

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
- database migrations and worker leases need hardening;
- panel/OCR/semantic analysis and retrieval lack real-corpus proof;
- storyboard choices are lexical/greedy rather than globally optimized;
- real alignment, cleanup, UI, partial render, Windows packaging, and licensing remain open.

## Next

Run `docs/LOCAL_ACCEPTANCE_TEST.md`, preserve evidence, and update state only after independent review. The full plan is indexed by `docs/PLANNING_INDEX.md`.
