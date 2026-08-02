# Miller blockers and fallback work

A blocker stops only the dependent sprint. It never stops unrelated work.

| ID | Blocker | Affects | Owner action | Safe fallback work | Clear condition |
|---|---|---|---|---|---|
| BLK-001 | Actual Windows checkout/path not confirmed | local acceptance and packaging | confirm current repo/workspace locations | `INV-003`, `DOC-001`, `ARC-001`, `SEC-002` | `ENV-001` capability report stored |
| BLK-002 | Comic portion resolved (10-issue manifest, `.miller/acceptance/ENV-002-fixture-manifest.json`, gitignored); script + edited narration for the same fixture still not supplied | real analysis/retrieval/visual tests | approve/supply a matching script + edited narration recording | schemas, synthetic fixtures, worker contracts | script + narration fixture manifest and hashes also exist |
| BLK-003 | Human relevance labels absent | retrieval winner | label 100–300 queries | build label UI, BM25 fixture, embedding workers | validator reports target labels and coverage |
| BLK-004 | RTX 3070 access required | VLM/embedding/alignment/NVENC benchmarks | run local benchmark jobs | CPU/fake worker contracts, test harnesses | report includes driver, VRAM, latency, peak memory |
| BLK-005 | Alignment worker contract exists, but `torch>=2.1` and `stable-ts>=2.16` are not reproducible pins; environment/model absent | `AUD-001`, word-level alignment | authorize platform/CUDA selection and heavy install | uniform fallback and synthetic worker tests | locked environment installs, probes, unloads, and records exact versions |
| BLK-006 | Text removal model checkout absent | inpainting proof | install approved external worker | text-free crop policy and masks | fixture outputs and license manifest accepted |
| BLK-007 | Owner license unresolved | public distribution | choose MIT or Apache-2.0 after review | keep private/internal, create SBOM/notices draft | `LICENSE` committed and dependency review passed |
| BLK-008 | Resolve not installed/supported | Resolve round-trip | install supported Resolve or waive | OTIO structural round-trip only | external timeline opens with media/timing |
| BLK-009 | Video duration conflict: older 8–12 vs newer 13–18 minutes | defaults/pacing/performance | choose default and deep-dive ranges | make duration configurable, no hardcoded acceptance | owner decision in `DECISIONS.md` |
| BLK-010 | Comic corpus redistribution rights | public fixtures/CI | approve synthetic or licensed fixture policy | keep private hashes/manifests out of Git | fixture policy signed off |
| BLK-011 | Current model/data licenses may change | release | re-audit pinned artifacts | keep model download separate from core | release license matrix current |
| BLK-012 | Real visual quality is subjective | storyboard/render acceptance | complete rubric review | automated technical checks only, marked provisional | E5 review by owner or delegated reviewer |

## Escalation rule

Escalate to Codex/owner when a blocker requires architecture, stored-data migration, public API change, new license obligation, proprietary software, or quality tradeoff. Otherwise record the default and continue the next unblocked card.
