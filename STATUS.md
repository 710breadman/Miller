# Project status

Updated: **2026-08-02**
Planning revision: `2026-07-21-definitive`

## Current

Miller has an E2-verified software foundation plus E3 synthetic/local Windows acceptance. Independent Codex review accepted `ARC-001`, `ARC-003`, `SEC-001`, `SEC-002`, and `QAE-001`; review corrections removed unsafe inline-JavaScript interpolation from the editor and made E5 record validation enforce roles, scores, thresholds, disagreements, and hashes. `AUD-001` remains E2/incomplete: its worker contract works, but `torch>=2.1` and `stable-ts>=2.16` are not reproducible pins and no real environment was installed. Miller still lacks real-comic, real-model, retrieval-winner, human-quality, and clean-release acceptance.

No remaining critical-path sprint can start without owner input. `active_sprint` points at `ARC-002 — Durable baseline DAG integration`, but dependency `ENV-003` needs the missing script/narration fixture. `AUD-001` also needs explicit authorization for platform/CUDA selection and heavy worker installation.

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

Independent review is complete. Further sprint progress needs one of: owner-supplied/approved `ENV-002`
script/narration; authorization to pin and install a real model worker (WhisperX, embedding, or VLM); or the
`OD-001` software-license decision. The full plan is indexed by `docs/PLANNING_INDEX.md`.
