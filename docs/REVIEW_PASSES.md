# Definitive plan review passes

## Pass 1 — Coverage

**Found:** migration safety, baseline/DAG split, worker leases, reading order, panel identity, private fixture policy, visual editor, and clean-machine acceptance were underrepresented.  
**Changes:** added architecture, analysis, security, UX, and release cards plus the subsystem inventory and test matrix.

## Pass 2 — Feasibility

**Found:** several previous milestones bundled real models, GPU setup, labels, implementation, and subjective acceptance.  
**Changes:** separated environment, worker, benchmark, selection, and acceptance cards. Advanced character re-ID and parallax moved out of v1 critical path.

## Pass 3 — Context efficiency

**Found:** the old roadmap required rereading broad milestones and allowed “implemented ahead” ambiguity.  
**Changes:** 55 permanent cards, explicit allowed/forbidden files, compact startup packet, ≤32K normal Gemma target, machine JSON, next-unblocked options.

## Pass 4 — Product coherence

**Found:** research/script/export capability could distract from the primary script+narration→comic-video path.  
**Changes:** local baseline, comic observations, retrieval, storyboard coherence, visual review, and recovery placed first. Script factory expansion and advanced export are optional/later.

## Pass 5 — Risk and failure analysis

**Found:** status inflation, corpus leakage, migrations, partial render, model licensing, GPU OOM, stale workers, and Windows paths were major hazards.  
**Changes:** evidence levels, risk register, private corpus rules, atomic promotion, worker guards, migration backups, blocker fallbacks, security/release cards.

## Pass 6 — Simplification

**Removed/deferred:** distributed orchestrators, mandatory Qdrant service, mandatory Revideo/React/Tauri, always-on SAM/depth/inpainting, multiple concurrent GPU projects, cloud requirements, CBR/PDF for v1, and automatic silent learning.

## Pass 7 — Final board review

The board accepted the preserved Python/SQLite/FFmpeg architecture and the evidence-first sequence. Final corrections:

- explicitly mark synthetic tests E2;
- make `ENV-001` active rather than a blocked label sprint;
- keep BM25 and no-AI paths as permanent fallbacks;
- require one winner ADR per benchmark family;
- require owner approval for duration, license, corpus policy, and quality preferences;
- require independent verification before state advancement.

## Completion claim

This planning package is complete as a control system, not as implementation evidence. Local Windows, corpus, model, visual, and release gates remain intentionally open.
