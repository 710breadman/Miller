# Project status

Updated: **2026-07-29**
Planning revision: `2026-07-21-definitive`

## Current

Miller has an E2-verified software foundation plus E3 synthetic/local Windows acceptance, now including ordered database migrations/backup/restore (`ARC-001`); a versioned worker protocol with lease/heartbeat, a stale-result guard, cancellation, timeout, error classes, and one-GPU admission (`ARC-003`); a reproducible, isolated alignment worker environment spec with probe/unload/CPU-fallback (`AUD-001`); adversarial archive/path/image fuzzing, localhost-boundary and log-sanitization verification (`SEC-001`); and a dependency SBOM, vulnerability scan, and FFmpeg build/license record (`SEC-002`) — all five pending owner/independent review. It does not yet have real-comic, real-model, retrieval-winner, human-quality, or clean-release acceptance.

Active sprint: **`QAE-001 — Human quality rubric and acceptance records`** — currently the only sprint in the plan not blocked on `ENV-002`'s missing script/narration fixture or a real model-worker installation.

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

Owner/independent review of `ARC-001`, `ARC-003`, `AUD-001`, `SEC-001`, and
`SEC-002` evidence, then implement and verify `QAE-001` (human quality
rubric and acceptance records). After that, further sprint progress needs
either the `ENV-002` script/narration fixture or an owner decision to
install real model workers. The full plan is indexed by
`docs/PLANNING_INDEX.md`.
