# Project status

Updated: **2026-07-29**
Planning revision: `2026-07-21-definitive`

## Current

Miller has an E2-verified software foundation plus E3 synthetic/local Windows acceptance, now including ordered database migrations/backup/restore (`ARC-001`); a versioned worker protocol with lease/heartbeat, a stale-result guard, cancellation, timeout, error classes, and one-GPU admission (`ARC-003`); a reproducible, isolated alignment worker environment spec with probe/unload/CPU-fallback (`AUD-001`); adversarial archive/path/image fuzzing, localhost-boundary and log-sanitization verification (`SEC-001`); a dependency SBOM, vulnerability scan, and FFmpeg build/license record (`SEC-002`); and a finalized human quality rubric with reviewer roles, scoring thresholds, and an immutable E5 acceptance-record schema (`QAE-001`) — all six pending owner/independent review. It does not yet have real-comic, real-model, retrieval-winner, human-quality, or clean-release acceptance.

**Every sprint whose prerequisites were satisfiable without further owner input is now done.** `active_sprint` points at `ARC-002 — Durable baseline DAG integration` as the next architectural item, but it cannot actually start: its dependency `ENV-003` is blocked, and every other remaining `ready`-status sprint has the same shape of blocker. See `HANDOFF.md` "Exact next action" for the three concrete unblocking options.

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
- the new worker protocol/lease queue is not yet wired into the actual external adapters (WhisperX, embedding);
- panel/OCR/semantic analysis and retrieval lack real-corpus proof;
- storyboard choices are lexical/greedy rather than globally optimized;
- real alignment, cleanup, UI, partial render, Windows packaging, and licensing remain open.

## Next

Owner/independent review of `ARC-001`, `ARC-003`, `AUD-001`, `SEC-001`,
`SEC-002`, and `QAE-001` evidence. Further sprint progress needs one of:
the owner supplying/approving the `ENV-002` script/narration fixture; an
owner decision to install a real model worker (WhisperX, embedding, or
VLM); or the `OD-001` software-license decision. The full plan is indexed
by `docs/PLANNING_INDEX.md`.
