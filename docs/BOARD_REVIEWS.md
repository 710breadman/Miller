# Miller board of directors reviews

Each review was conducted against the repository assessment and current product mission. Confidence reflects evidence available now, not confidence in future model quality.

## 1. Product director

**Findings:** Miller’s identity is an automatic comic-first video production workflow, not a collection of disconnected AI demos. The simple path must accept script + edited narration + comics and produce a reviewable video; deep research, advanced motion, and complex export are optional.  
**Risks:** architecture work can outrun visible user value; old 8–12 minute defaults conflict with newer 13–18 minute intent.  
**Missing evidence:** a real owner project completed without hand-editing internals.  
**Recommendations:** prioritize local acceptance, semantic retrieval, coherent storyboard, visual review, and recovery.  
**Rejected:** rebuilding the UI or renderer before the real baseline.  
**Highest priority:** `ENV-003`.  
**Confidence:** high.

## 2. Systems architect

**Findings:** Python, SQLite, typed contracts, content-addressed artifacts, external workers, and FFmpeg are sound. `PipelineRunner` is stronger than the direct baseline path.  
**Risks:** two orchestration paths, informal migrations, weak worker lifecycle, and partial output promotion.  
**Missing evidence:** end-to-end DAG restart.  
**Recommendations:** `ARC-001`–`ARC-004`; stable service APIs before frontend separation.  
**Rejected:** Temporal/Prefect/LangGraph replacement.  
**Highest priority:** route baseline through the durable DAG.  
**Confidence:** high.

## 3. Comic-analysis specialist

**Findings:** current full-page/white-gutter/Tesseract baseline is useful but not comic understanding. Reading order, balloon/text types, panel relationships, sound effects, spreads, and character occurrences are absent or weak.  
**Risks:** full-page fallback may be counted as success; OCR dialogue can be assigned to the wrong panel/speaker.  
**Missing evidence:** representative annotated pages.  
**Recommendations:** observation schema, stratified corpus, panel/text/order/OCR gates before character re-ID.  
**Rejected:** adopting a research monolith as source of truth.  
**Highest priority:** `ANL-001` and `ANL-002`.  
**Confidence:** high.

## 4. Computer-vision specialist

**Findings:** detector and worker abstractions are appropriate; model selection is premature. Qwen3-VL-2B, SigLIP 2 NaFlex, OpenCLIP, and current comic detectors are candidates.  
**Risks:** 8 GB VRAM, training-data restrictions, stylized-art domain shift, hallucinated VLM semantics.  
**Missing evidence:** measured accuracy/VRAM on owner pages.  
**Recommendations:** isolated workers, small batches, explicit uncertainty, compare against deterministic baselines.  
**Rejected:** mandatory SAM/depth/inpainting on every scene.  
**Highest priority:** `ANL-005` worker contract after corpus schemas.  
**Confidence:** medium-high.

## 5. Information-retrieval specialist

**Findings:** BM25 and metric infrastructure are a good floor. Current min-max fusion and page-only greedy use are not enough.  
**Risks:** no labels, score scale instability, overfitting, missing hard negatives, weak query taxonomy.  
**Missing evidence:** 100–300 labels and panel IDs.  
**Recommendations:** label tool, fixed corpus, BM25 report, embedding comparison, RRF/rerank, one winner ADR.  
**Rejected:** selecting Qdrant/model from generic benchmarks.  
**Highest priority:** `RET-001` and `RET-002`.  
**Confidence:** high.

## 6. Video editor and motion designer

**Findings:** native FFmpeg path is technically useful; current crop/motion cycles are generic and can cut off composition. Scene cache and revision concepts are promising.  
**Risks:** repetitive Ken Burns motion, unsafe center crops, damaged lettering removal, late failures on long renders.  
**Missing evidence:** frame-level review of real projects.  
**Recommendations:** composition-aware safe boxes, preview proxies, text-free alternatives, atomic/partial render, restrained transitions.  
**Rejected:** effects-heavy motion as default.  
**Highest priority:** `STO-004` and `VID-003`.  
**Confidence:** high.

## 7. Narrative editor

**Findings:** beat text is currently used almost directly as search intent. Emotional and thematic continuity are not represented globally.  
**Risks:** technically relevant panels can undermine the point, era, or emotional escalation; actual quotes require provenance and careful use.  
**Missing evidence:** owner-rated storyboards and failure examples.  
**Recommendations:** structured beat intent, candidate reasons, global sequence cost, owner locks, narrative rubric.  
**Rejected:** an LLM choosing final scenes without alternatives/evidence.  
**Highest priority:** `STO-001`–`STO-003`.  
**Confidence:** high.

## 8. Local-AI optimization engineer

**Findings:** process boundaries and small core are correct for RTX 3070 8 GB. Gemma 4 12B can implement narrow cards but should not own architecture or subjective acceptance.  
**Risks:** model process fragmentation, oversized prompts, concurrent GPU jobs, dependency conflicts.  
**Missing evidence:** local model throughput and context behavior by task.  
**Recommendations:** one GPU worker, explicit unload, compact card context, schemas/tests first, 32K target despite 64K maximum.  
**Rejected:** loading the entire repository for each sprint.  
**Highest priority:** `ARC-003` plus the context protocol.  
**Confidence:** medium-high.

## 9. Windows deployment engineer

**Findings:** install/repair scripts are defensive but target a stale hardcoded path and have not been accepted on the owner machine.  
**Risks:** Winget IDs, environment refresh, ExecutionPolicy, long paths, junctions, antivirus locks, drive availability, process cleanup.  
**Missing evidence:** current checkout and clean-machine logs.  
**Recommendations:** capability-first install, parameterized roots, no implicit Git branch/stash surprises, deterministic repair.  
**Rejected:** packaging model runtimes into the first core installer.  
**Highest priority:** `ENV-001`.  
**Confidence:** high.

## 10. Database and data-integrity engineer

**Findings:** transactions, immutable attempts, documents, history, and SQLite authority are strong. Additive initialization is not a sufficient long-lived migration system.  
**Risks:** version bump without backup, partial migration, artifact/DB divergence, stale worker completion.  
**Missing evidence:** migration/restore and corruption drills.  
**Recommendations:** ordered migrations, checksums, preflight backup, post-migration integrity, stale attempt guards, audit command.  
**Rejected:** making Qdrant authoritative.  
**Highest priority:** `ARC-001`.  
**Confidence:** high.

## 11. QA and evaluation lead

**Findings:** 64 synthetic tests prove useful contracts, not product quality. The repository needs a test taxonomy and immutable acceptance reports.  
**Risks:** status inflation, fixture leakage, only averages reported, subjective claims by agents.  
**Missing evidence:** E3–E6.  
**Recommendations:** golden projects, stratified labels, per-case reports, human rubric, evidence dashboard.  
**Rejected:** “appears to work” completion.  
**Highest priority:** `ENV-002` and `QAE-001`.  
**Confidence:** high.

## 12. Security and privacy reviewer

**Findings:** archive checks and read-only media boundaries are strong. External worker/model supply chain and private-corpus handling need operational controls.  
**Risks:** malicious archives/images, subprocess path injection, model remote code, copyrighted media in Git/logs, localhost exposure.  
**Missing evidence:** fuzzing, dependency scan, local bind verification, corpus policy.  
**Recommendations:** `SEC-001`, pinned workers, no `trust_remote_code` without review, redact media/text from logs.  
**Rejected:** automatic remote upload or web exposure.  
**Highest priority:** private fixture policy before labels.  
**Confidence:** high.

## 13. UX designer

**Findings:** revisioned API operations are a solid backend; the inline HTML is an engineering console, not the intended product.  
**Risks:** requiring project IDs, filenames instead of images, unclear errors/progress, no visual crop/preview.  
**Missing evidence:** owner task walkthrough.  
**Recommendations:** project wizard, queue/progress, visual alternatives, timeline, preview, recovery; disclose advanced options progressively.  
**Rejected:** a complex NLE interface.  
**Highest priority:** `UX-001` after current pipeline APIs are mapped.  
**Confidence:** high.

## 14. Open-source and licensing reviewer

**Findings:** current “external GPL, no copied source” boundary is prudent. Dataset/model rights are as important as code licenses.  
**Risks:** Manga109-derived weights, GPL in-process integration, checkpoint-specific OpenCLIP terms, FFmpeg codec build, unselected Miller license.  
**Missing evidence:** complete dependency/model/data inventory.  
**Recommendations:** Apache-2.0 or MIT owner choice, SBOM/notices, separate optional downloads, exact revisions.  
**Rejected:** redistribution before license review.  
**Highest priority:** `SEC-002`.  
**Confidence:** high.

## 15. Skeptical technical reviewer

**Findings:** many “implemented ahead” items are data models and happy-path tests. The baseline is not stage-resumable, semantic descriptions are mostly OCR/filenames, and UI/render quality remain unproven.  
**Risks:** a large plan can become paperwork; advanced models can distract from one useful video.  
**Missing evidence:** the first real video and owner review.  
**Recommendations:** time-box research, require a fallback baseline in every lane, kill candidates that do not beat it materially.  
**Rejected:** hundreds of tiny no-value sprints and speculative feature branches.  
**Highest priority:** produce and inspect the short golden project.  
**Confidence:** high.

# Final architecture council

## Resolved disagreements

- **Native FFmpeg versus Revideo:** FFmpeg remains mandatory. Revideo receives one same-fixture comparison; no preemptive migration.
- **Qdrant versus embedded vectors:** SQLite remains authoritative. Qdrant and sqlite-vec are rebuildable candidates selected by operational benchmark.
- **React now versus later:** stable API and information architecture first. Separate frontend only when the prototype demonstrably cannot meet the visual workflow.
- **Model sophistication versus hardware:** benchmark capable small models; retain fallbacks and process isolation. Do not lower the product goal silently.
- **Character re-ID timing:** defer until panel/text/semantic observations and IDs are reliable.
- **Roadmap size:** 55 permanent cards are sufficient coverage; split only when a card actually exceeds context or reviewability.

## Authoritative combined direction

1. Complete local acceptance and evidence control.
2. Strengthen migrations, DAG, workers, and atomic outputs.
3. Build a private evaluation corpus and comic-specific observations.
4. Select retrieval components by the same labels and target hardware.
5. Optimize the storyboard globally and preserve human alternatives/locks.
6. Add polished visual/audio stages and a simple visual editor.
7. Package only after clean-machine, security, and license gates.
8. Keep advanced character/motion/export features optional.

## Necessities versus optional work

**Necessary:** Windows acceptance, source safety, migrations, durable DAG, labels, comic observations, retrieval benchmark, real alignment, coherent storyboard, atomic/partial render, visual review, recovery, clean package.  
**Optional:** Revideo, SAM 2, depth parallax, advanced re-ID, Resolve, cloud workers, distributed orchestration.
