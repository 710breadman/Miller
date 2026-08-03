# Miller risk register

Scores: probability (P) and impact (I), 1–5. Priority = P × I.

| ID | Risk | P | I | Priority | Mitigation | Trigger / owner |
|---|---|---:|---:|---:|---|---|
| RSK-001 | Documentation overstates model/product completion | 4 | 5 | 20 | evidence taxonomy, validator, acceptance records | any “complete” claim without level; director |
| RSK-002 | Baseline bypasses durable DAG and cannot truly resume | 4 | 5 | 20 | `ARC-002`, crash/restart E2/E3 | direct pipeline path persists; architect |
| RSK-003 | Database schema change loses or corrupts projects | 3 | 5 | 15 | ordered migrations, preflight backup, restore tests | schema version bump; data engineer |
| RSK-004 | Private comics are copied, logged, or committed | 2 | 5 | 10 | fixture policy, paths/hashes only, Git ignore audit | corpus work; security/licensing |
| RSK-005 | Learned detector/model trained on restricted data becomes distributable dependency | 3 | 5 | 15 | separate code/weights/data terms, external download | candidate selection; licensing |
| RSK-006 | 8 GB VRAM is insufficient or model processes fragment memory | 4 | 4 | 16 | isolated workers, one GPU task, unload, CPU fallback, measured batches | OOM/repeat failures; local-AI engineer |
| RSK-007 | Comic panel/OCR/VLM accuracy is poor across styles | 4 | 5 | 20 | stratified corpus, fallback/full-page, human alternatives | E4 misses targets; comic/CV leads |
| RSK-008 | Retrieval benchmark leaks labels or overfits | 3 | 4 | 12 | held-out queries, fixed manifests, per-query results | repeated tuning; IR lead |
| RSK-009 | Greedy scene selection creates incoherent videos | 4 | 4 | 16 | global optimizer and sequence A/B | E5 continuity/reuse scores; narrative/editor |
| RSK-010 | Text removal damages art | 4 | 4 | 16 | alternate/crop first, masks, preview, source immutable | artifacts fail visual review; video lead |
| RSK-011 | Render cancellation leaves valid-looking partial output | 3 | 5 | 15 | temp output, probe/hash, atomic promotion | killed process; systems/video |
| RSK-012 | Windows scripts assume stale drive/path/tool state | 4 | 4 | 16 | parameterize, capability manifest, clean-machine test | `ENV-001`; deployment lead |
| RSK-013 | Inline prototype UI is mistaken for completed product UX | 4 | 3 | 12 | IA/usability gates and visual workflow | owner cannot complete task; UX lead |
| RSK-014 | Optional dependency becomes mandatory through imports | 3 | 4 | 12 | optional-boundary tests and worker processes | clean core import fails; architect |
| RSK-015 | Qdrant service complicates installation/recovery | 3 | 3 | 9 | rebuildable vectors, sqlite-vec benchmark | service errors dominate; data/IR |
| RSK-016 | Revideo/Node adds complexity without visible benefit | 3 | 3 | 9 | same-fixture comparison and kill criterion | no material E5 benefit; video/product |
| RSK-017 | Agent expands scope or rewrites working code | 4 | 4 | 16 | allowed files, forbidden files, one sprint/commit, Codex review | unrelated diff; director |
| RSK-018 | Context reset loses active state | 4 | 4 | 16 | startup/close protocol, machine JSON, exact next action | handoff missing; project manager |
| RSK-019 | AI output invents provenance/characters/events | 4 | 5 | 20 | typed observations, confidence, evidence refs, human review | unsupported assertion; comic/narrative |
| RSK-020 | Feedback loop silently learns bad/private preferences | 2 | 5 | 10 | owner-approved labels only, versioned datasets, rollback | automatic training proposal; director/security |
| RSK-021 | Dependency supply-chain compromise | 2 | 5 | 10 | lockfiles, hashes, provenance, isolated workers, SBOM | new package/model; security |
| RSK-022 | Long videos exceed time/disk or fail late | 4 | 4 | 16 | proxies, scene cache, preflight disk/time, partial render | production fixture; performance/video |
| RSK-023 | Music/quotes/copyright create distribution concerns | 3 | 4 | 12 | user-supplied assets, provenance, no bundled copyrighted media | release/content decision; owner |
| RSK-024 | Plan becomes too large for Gemma 12B | 3 | 4 | 12 | one card, narrow files, compact handoff, split high-context cards | context pressure; sprint planner |
| RSK-025 | Bundling the installed FFmpeg binary into a release would carry GPLv3 obligations (confirmed `--enable-gpl --enable-version3` build, `SEC-002`) | 2 | 3 | 6 | keep FFmpeg subprocess-invoked and system-installed, not bundled; rebuild LGPL-only if bundling is ever desired | release packaging decision; `REL-001`/`REL-002` |

## Risk acceptance

Only the owner may accept a risk involving public licensing, private corpus handling, destructive data migration, or a permanent quality/capability tradeoff. Other risks may be provisionally accepted by Codex with rationale and expiry.
