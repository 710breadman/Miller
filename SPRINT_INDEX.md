# Miller sprint index

Permanent IDs never change. Status is controlled by `SPRINT_STATE.json`.

| ID | Title | Roadmap | Status | Prerequisites |
|---|---|---|---|---|
| `INV-001` | Repository inventory and evidence map | R1 | completed | — |
| `INV-002` | Evidence taxonomy and completion rules | R1 | completed | `INV-001` |
| `INV-003` | Dependency, data, and license audit | R1 | ready | `INV-001` |
| `DOC-001` | Reconcile product vision and stale claims | R1 | ready | `INV-001`, `INV-002` |
| `DOC-002` | Canonical project-control documents | R1 | completed | `INV-001`, `INV-002` |
| `ENV-001` | Windows checkout and capability proof | R2 | active | `DOC-002` |
| `ENV-002` | Approved local acceptance fixture | R2 | blocked | `ENV-001` |
| `ENV-003` | Real no-AI baseline acceptance | R2 | blocked | `ENV-002` |
| `ENV-004` | Restart, long-path, and large-source acceptance | R2 | blocked | `ENV-003` |
| `ARC-001` | Ordered database migrations and restore | R3 | ready | `DOC-002` |
| `ARC-002` | Durable baseline DAG integration | R3 | ready | `ARC-001`, `ENV-003` |
| `ARC-003` | Worker protocol, lease, and resource hardening | R3 | ready | `ARC-001` |
| `ARC-004` | Atomic output and artifact audit | R3 | ready | `ARC-002` |
| `ANL-001` | Corpus, annotation, and observation schema | R4 | blocked | `ENV-002`, `ARC-001` |
| `ANL-002` | Panel, balloon, and text detector benchmark | R4 | blocked | `ANL-001` |
| `ANL-003` | Reading-order detection and evaluation | R4 | blocked | `ANL-001`, `ANL-002` |
| `ANL-004` | OCR preprocessing and engine selection | R4 | blocked | `ANL-001`, `ANL-002` |
| `ANL-005` | Structured VLM worker implementation | R4 | ready | `ARC-003`, `ANL-001` |
| `ANL-006` | VLM comic benchmark and selection | R4 | blocked | `ANL-005`, `ANL-001` |
| `ANL-007` | Character occurrence and identity model | R4 | blocked | `ANL-002`, `ANL-006` |
| `ANL-008` | Scene and sequence representation | R4 | blocked | `ANL-003`, `ANL-006` |
| `RET-001` | Human relevance label tool and schema | R5 | ready | `ANL-001` |
| `RET-002` | Create 100–300 query evaluation set | R5 | blocked | `RET-001`, `ENV-002` |
| `RET-003` | BM25 and metadata baseline report | R5 | blocked | `RET-002`, `ANL-004` |
| `RET-004` | Embedding worker candidate implementations | R5 | ready | `ARC-003`, `ANL-001` |
| `RET-005` | Embedding retrieval benchmark | R5 | blocked | `RET-002`, `RET-004` |
| `RET-006` | Vector backend operational benchmark | R5 | blocked | `RET-004`, `ENV-001` |
| `RET-007` | Fusion, reranking, and retrieval winner | R5 | blocked | `RET-003`, `RET-005`, `RET-006` |
| `AUD-001` | Pinned alignment worker environments | R7 | ready | `ARC-003`, `ENV-001` |
| `AUD-002` | Real narration alignment acceptance | R7 | blocked | `AUD-001`, `ENV-002` |
| `STO-001` | Structured beat intent and uncertainty | R6 | ready | `ARC-002` |
| `STO-002` | Mixed page/panel candidate lattice | R6 | blocked | `STO-001`, `RET-007` |
| `STO-003` | Global sequence optimizer | R6 | blocked | `STO-002` |
| `STO-004` | Composition-aware crop and motion plan | R6 | blocked | `STO-003`, `ANL-002` |
| `STO-005` | Narrative and editorial acceptance | R6 | blocked | `STO-004`, `QAE-001` |
| `VID-001` | Text-free alternate, crop, and mask policy | R7 | blocked | `ANL-002`, `STO-004` |
| `VID-002` | External inpainting proof and fallback | R7 | blocked | `VID-001`, `ARC-003` |
| `VID-003` | Render progress, cancellation, and promotion | R7 | ready | `ARC-004` |
| `VID-004` | Scene cache and partial rerender acceptance | R7 | blocked | `VID-003`, `STO-004` |
| `VID-005` | CPU and NVENC target benchmark | R9 | blocked | `VID-003`, `ENV-002` |
| `VID-006` | Revideo same-fixture comparison | R13 | blocked | `VID-004` |
| `UX-001` | Product information architecture and API map | R8 | ready | `DOC-001`, `ARC-002` |
| `UX-002` | Project, import, queue, and progress UI | R8 | blocked | `UX-001`, `ARC-003` |
| `UX-003` | Visual storyboard and scene editor | R8 | blocked | `UX-002`, `STO-004` |
| `UX-004` | Preview, partial rerender, and recovery UX | R8 | blocked | `UX-003`, `VID-004` |
| `QAE-001` | Human quality rubric and acceptance records | R11 | ready | `DOC-002` |
| `QAE-002` | Golden projects and regression suite | R11 | blocked | `ENV-003`, `QAE-001` |
| `QAE-003` | Evidence dashboard and final repeated reviews | R11 | blocked | `QAE-002` |
| `SEC-001` | Archive, file, API, and worker security tests | R10 | ready | `ARC-003` |
| `SEC-002` | Dependency, model, data, SBOM, and license review | R12 | ready | `INV-003` |
| `REL-001` | Clean Windows installation and portability | R12 | blocked | `ENV-004`, `SEC-001`, `SEC-002`, `VID-004`, `UX-004` |
| `REL-002` | Polished v1 release candidate | R12 | blocked | `REL-001`, `QAE-003` |
| `ADV-001` | Advanced character re-identification | R13 | blocked | `ANL-007`, `QAE-002` |
| `ADV-002` | Selective masks and depth parallax | R13 | blocked | `VID-004`, `QAE-001` |
| `ADV-003` | OTIO and Resolve interchange proof | R13 | blocked | `REL-001` |

## Categories

- Investigation/documentation: `INV-*`, `DOC-*`
- Local environment and fixtures: `ENV-*`
- Architecture/core: `ARC-*`
- Comic analysis: `ANL-*`
- Retrieval: `RET-*`
- Audio: `AUD-*`
- Storyboard: `STO-*`
- Video/render: `VID-*`
- User experience: `UX-*`
- Quality/evaluation: `QAE-*`
- Security/release: `SEC-*`, `REL-*`
- Advanced experiments: `ADV-*`

## Scheduling rule

Only one sprint is active per branch/worker. Parallel work uses separate worktrees and non-overlapping file scopes. A blocked card does not become active; choose a dependency-valid ready card from `next_unblocked`.
