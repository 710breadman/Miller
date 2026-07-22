# Miller definitive roadmap

Roadmap revision: **2026-07-21-definitive**  
Authority: `PROJECT_CHARTER.md`, `CURRENT_STATE.md`, and this file.  
Execution details: `SPRINT_INDEX.md` and `docs/SPRINT_CARDS.md`.

## Roadmap rules

- Preserve proven behavior; replace only after measured evidence.
- A capability's status names its evidence level: E0 intent, E1 contract, E2 synthetic automation, E3 target-hardware pass, E4 real-corpus quantitative pass, E5 human acceptance, E6 clean-machine release.
- The critical path is allowed to be blocked. Independent fallback work continues.
- Model, detector, database, renderer, and UI choices are benchmark decisions, not preferences.
- Every migration, model output, edit, and render is traceable and reversible.

## Milestones

| Milestone | Outcome | Exit gate |
|---|---|---|
| Minimum usable | A real comic and narration produce a safe, reviewable no-AI video on the owner’s Windows machine | E3 baseline, source hashes unchanged, restart/retry recorded |
| Strong v1 | Comic-specific analysis, labeled retrieval winner, real alignment, global storyboard, partial rerender, visual review | E4 retrieval/analysis plus E5 two golden projects |
| Polished v1 | Simple project UI, reliable recovery, clean Windows package, notices and license | E6 clean-machine release candidate |
| Long-term | Character/scene intelligence, approved feedback loop, optional advanced motion/export | Advanced gates remain optional and measured |

## R1 — Immediate stabilization

**Goal:** establish trustworthy local state before adding capability.

- Validate the actual checkout, branch, dependencies, FFmpeg/Tesseract/Ollama/GPU, and locked quality gate.
- Reconcile stale path/duration/status claims.
- Introduce the evidence taxonomy and a planning validator.
- Preserve the current code as the reference baseline.

**User benefit:** the project can be resumed without guessing what is real.

**Definition of done:** `ENV-001`–`ENV-004`, `DOC-001`, and `INV-003` have evidence; no source media changed.

## R2 — Local acceptance testing

**Goal:** turn the synthetic baseline into a real owner-machine proof.

- Build a small approved fixture containing varied page layouts and 30–90 seconds of narration.
- Run without OCR, then with OCR.
- Stop/restart mid-work and verify durable recovery.
- Record speed, memory, output probe, hashes, warnings, and manual observations.

**User benefit:** a usable video exists now, while later quality work proceeds.

**Rollback:** preserve the current synthetic baseline and fixture manifest; do not alter source media.

## R3 — Core pipeline completion

**Goal:** make real end-to-end work use the durable DAG rather than direct function calls.

- Add ordered, backed-up database migrations.
- Route baseline stages through `PipelineRunner`.
- Add worker protocol versioning, leases/heartbeats, structured failure classes, cancellation, and resource admission.
- Render to managed temporary outputs, verify, then atomically promote.

**User benefit:** interrupted work resumes safely and only affected stages rerun.

**Gemma difficulty:** medium/high; Codex reviews every schema, public interface, and orchestration change.

## R4 — Comic-analysis quality

**Goal:** build versioned, comic-specific observations rather than one weak page description.

- Define corpus, annotation, panel/page/region identity, and observation schemas.
- Benchmark deterministic and learned panel/balloon/text detectors.
- Add reading-order evaluation.
- Compare OCR preprocessing and engines by language.
- Implement a process-isolated structured VLM worker, beginning with a small permissively licensed candidate.
- Add character occurrences and scene relationships only after base observations are reliable.

**User benefit:** Miller can find what a page shows, not merely what its filename or OCR says.

**Test data:** private owner-approved comics; public datasets are benchmark references only when their terms permit.

## R5 — Retrieval quality

**Goal:** select visuals by measured relevance.

- Build a simple human-label tool and 100–300 query evaluation set.
- Establish BM25 as the mandatory floor.
- Benchmark SigLIP 2, OpenCLIP checkpoints, and Qwen3-VL-Embedding-2B where hardware permits.
- Compare Qdrant and sqlite-vec operationally.
- Evaluate score calibration, reciprocal-rank fusion, metadata constraints, and a bounded top-N reranker.

**Definition of done:** one ADR names the winning page/panel/hybrid configuration with Recall@K, MRR, nDCG, latency, VRAM, failure behavior, license, and rollback.

## R6 — Storyboard and narrative quality

**Goal:** convert beat intent and retrieval candidates into a coherent sequence.

- Extract structured beat intent and uncertainty.
- Search both panels and full pages.
- Optimize the sequence globally for relevance, continuity, reuse, pacing, visual quality, and text-cleanup cost.
- Generate composition-aware crops and motion.
- Preserve alternatives and owner locks.

**User benefit:** scenes support the narration and emotional arc instead of acting as isolated keyword matches.

## R7 — Visual and audio polish

**Goal:** improve the final video without making optional AI mandatory.

- Prefer a clean alternate or crop before masking/inpainting.
- Validate WhisperX on edited narration; retain stable-ts and uniform fallback tiers.
- Add render progress, cooperative cancellation, partial rerender, and measured NVENC policy.
- Compare Revideo only on the same fixture; reject it if benefit does not outweigh complexity.
- Define music, pacing, crop safety, motion, and transition rubrics.

**User benefit:** polished output with bounded repair and no hidden destructive steps.

## R8 — User interface and workflow

**Goal:** make Miller simple to operate while exposing power when needed.

- Define project/import/queue/review information architecture.
- Keep FastAPI service boundaries stable.
- Add project creation, source selection, queue state, progress, errors, restart/retry, thumbnails, alternatives, visual timeline, scene preview, locks, and partial rerender.
- Adopt a separate frontend framework only if the inline prototype cannot meet measured UX needs.

**User benefit:** normal use is a guided workflow; advanced export remains optional.

## R9 — Performance optimization

**Goal:** fit Ryzen 7 3700X, RTX 3070 8 GB, and 32 GB RAM without sacrificing capability.

- Measure first-run and warm-cache time, peak RAM/VRAM, disk growth, model load/unload, batch size, and queue contention.
- Run one GPU-heavy worker at a time in v1.
- Use process isolation and unload between stages.
- Maintain CPU/fallback modes and explicit degraded-quality labels.

**Non-goal:** choosing a smaller model solely because it is easier to integrate.

## R10 — Reliability and recovery

**Goal:** survive crashes, context resets, file locks, model failures, and partial outputs.

- Migration backups and restore drills.
- Queue lease/heartbeat recovery.
- Source integrity and artifact audit commands.
- Atomic outputs, bounded retries, crash-safe logs, and exact next action.
- Large-library and low-disk tests.

## R11 — Evaluation and approved feedback

**Goal:** make quality improvement measurable and owner-controlled.

- Golden projects and regression fixtures.
- Automated, hardware, quantitative, and human gates recorded separately.
- Review rubric and comparison UI.
- Approved labels and edits can become training/evaluation data; no silent learning.
- Evidence dashboard prevents status inflation.

## R12 — Packaging and distribution

**Goal:** provide a safe Windows installation and portable project format.

- Parameterize checkout/workspace paths.
- Verify clean-machine install, repair, update, uninstall boundaries, shortcuts, logs, and antivirus/file locks.
- Select a project license.
- Generate notices, dependency/model inventory, SBOM, FFmpeg build/codec record, and release manifest.
- Prove final video and project archive round-trip.

## R13 — Advanced and experimental features

These do not block v1:

- cross-page character re-identification;
- subject masks and depth-assisted parallax;
- learned owner preference ranking;
- Revideo backend if it wins the comparison;
- Resolve interchange;
- complex multi-agent script research;
- CBR/PDF ingestion;
- optional cloud or remote workers.

Every experiment must have a kill criterion and leave the core usable without it.

## Critical path

```text
ENV-001 → ENV-002 → ENV-003
                   ├→ ARC-001 → ARC-002 → ARC-003 → ARC-004
                   ├→ ANL-001 → ANL-002 → ANL-003 → ANL-004
                   │             └────────→ ANL-005 → ANL-006
                   ├→ RET-001 → RET-002 → RET-003 → RET-004 → RET-005
                   │                                      └→ RET-006 → RET-007
                   ├→ AUD-001 → AUD-002
                   └→ STO-001 → STO-002 → STO-003 → STO-004 → STO-005
                                              │
                                              ▼
                  VID-001 → VID-002 → VID-003 → VID-004 → QAE-001 → QAE-002
                                                                      │
                  UX-001 → UX-002 → UX-003 → UX-004 ──────────────────┤
                                                                      ▼
                  SEC-001 → SEC-002 → REL-001 → REL-002
```

## Parallel lanes

- `INV-003`, `DOC-001`, `ARC-001`, and `SEC-002` can proceed while local media approval is pending.
- `ANL-002`, `ANL-003`, and `ANL-004` share the corpus but can benchmark in separate worktrees after `ANL-001`.
- `RET-003` can run as soon as labels exist; embedding/backend work can prepare contracts in parallel but cannot select a winner early.
- `UX-001` can proceed from contracts; visual UI implementation waits for stable storyboard/preview APIs.
- Advanced sprints remain outside the critical path.

## Explicit non-goals for v1

- replacing SQLite with a distributed database;
- running multiple GPU-heavy video projects concurrently;
- silently downloading or executing unpinned model code;
- copying GPL or research-only code into Miller core;
- automatic learning from every edit;
- mandatory Node, Chromium, ComfyUI, cloud APIs, or Resolve;
- a professional NLE replacement;
- publication or redistribution of private comic corpora.
