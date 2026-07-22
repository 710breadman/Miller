# Miller decisions

Decision log revision: **2026-07-21-definitive**

## Accepted decisions

| ID | Decision | Rationale | Consequence | Revisit gate |
|---|---|---|---|---|
| D-001 | Preserve the Python core, FastAPI boundary, SQLite authority, immutable artifacts, and native FFmpeg renderer. | Existing implementation and E2 tests are coherent and align with local-first safety. | Work extends rather than rewrites the foundation. | A measured failure that cannot be corrected without replacement. |
| D-002 | Define evidence levels E0–E6 and attach the highest passed level to every capability claim. | Existing documents blur contract, synthetic, hardware, corpus, and human evidence. | Status and sprint completion require named evidence. | Never; vocabulary may expand. |
| D-003 | Make the end-to-end baseline execute through the durable DAG. | Current baseline calls subsystems directly, so full resume/restart is not proven. | `ARC-002` is on the minimum-usable critical path. | After restart acceptance. |
| D-004 | Add formal ordered migrations and verified pre-migration backups. | SQLite is authoritative user data and current additive initialization is insufficient for long-lived evolution. | Schema changes require migration tests and rollback evidence. | Never remove; implementation may evolve. |
| D-005 | Keep heavy AI tools in isolated, versioned worker environments. | RTX 3070 constraints and dependency conflicts require load/unload and failure isolation. | JSON protocol v2, probes, timeouts, resource records, and cancellation. | Only if a dependency becomes lightweight and conflict-free. |
| D-006 | Store versioned observations rather than one mutable page description. | Different detectors and models can disagree and improve. | Reanalysis is non-destructive and reproducible. | Never remove. |
| D-007 | Keep BM25 as the mandatory retrieval floor and select semantic models only through private comic labels. | Generic benchmarks do not establish comic-scene relevance. | No permanent embedding model until `RET-007`. | After each major model-generation change. |
| D-008 | Benchmark Qdrant against sqlite-vec; do not make either irreplaceable. | Qdrant is capable but adds a service; sqlite-vec is simpler but pre-v1. | Vector store remains an adapter and rebuildable. | `RET-006`. |
| D-009 | Use a candidate lattice and global sequence optimization for final storyboards. | Greedy per-beat selection cannot reliably manage continuity, repetition, and pacing. | Storyboard build becomes a deterministic optimization stage. | After golden-project evidence. |
| D-010 | Native FFmpeg remains mandatory; Revideo is optional and must win a measured comparison. | FFmpeg already works and has fewer packaging/runtime surfaces. | Revideo cannot block v1. | `VID-006`. |
| D-011 | Prefer crop/alternate selection before inpainting. | Generative cleanup can damage art and is expensive. | Text-free planning has a conservative fallback ladder. | Human visual evidence. |
| D-012 | Owner-approved labels and edits may improve ranking, but Miller will not silently train on user media. | Privacy, reproducibility, and feedback quality. | Active learning is opt-in and post-v1. | Owner approval plus `ADV` sprint. |
| D-013 | Build the UI around stable APIs after workflow contracts, not before. | The current embedded HTML is sufficient as a prototype; premature framework work would churn. | UX starts with information architecture and endpoints. | `UX-001`. |
| D-014 | Use Gemma 4 12B for bounded implementation, not unsupervised architecture decisions. | 64K local context is sufficient for small sprints but vulnerable to scope drift. | Every sprint lists files, tests, escalation, and Codex review. | When local model capability materially changes. |
| D-015 | Default video duration is 13–18 minutes, with content-fit exceptions and deep-dive mode. | Latest owner preference supersedes older 8–12 minute planning. | `docs/PRODUCT_SPEC.md` requires reconciliation. | Owner decision `OD-002`. |

## Deferred decisions

| ID | Decision required | Safe default until decided | Blocking |
|---|---|---|---|
| OD-001 | Project license: Apache-2.0, MIT, or another owner-approved license. | No external source copying; GPL tools stay external; no public packaged release. | `REL-002`. |
| OD-002 | Confirm 13–18 minute default and deep-dive range. | Use content-fit 13–18 and record exceptions. | Documentation consistency only. |
| OD-003 | Confirm canonical local checkout and data roots. | Detect paths; use `V:\AI\Miller` only as owner-reported, not hardcoded. | `ENV-001`. |
| OD-004 | Approve a private representative comic/narration corpus and storage policy. | Synthetic/public-domain fixtures only. | E4/E5 analysis, retrieval, storyboard, and render gates. |
| OD-005 | Subtitle default. | Off by default; optional export. | UI wording only. |
| OD-006 | Preferred professional interchange target. | OTIO generic export first; Resolve is optional. | `ADV-003`. |
| OD-007 | Whether model weights may be auto-downloaded. | Explicit install action with license/size display; never silent. | Packaging. |
| OD-008 | Commercial/public distribution intent. | Local private development only. | License, notices, model/data terms. |

## Superseded or rejected

- The old active roadmap pointer `4.2` is superseded by `ENV-001`; the retrieval label blocker remains, but it no longer blocks unrelated acceptance and architecture work.
- “Implemented ahead” is not a completion category. It becomes a status plus evidence level.
- The current hardcoded `D:\_Codex\Miller` handoff path is not authoritative.
- A React UI is not automatically required; it must follow `UX-001`.
- Qdrant is not automatically the v1 production winner.
