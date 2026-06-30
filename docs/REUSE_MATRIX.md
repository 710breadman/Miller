# Reuse matrix

Terms:

- **Call** — use supported API/CLI/package through adapter.
- **Adapt** — implement Miller-owned interface based on proven concepts.
- **Port** — copy/translate source after explicit license approval.
- **Recreate** — implement behavior from requirements, not source.
- **Study** — learn only.
- **Reject** — keep outside selected architecture.

| Source | Capability | Decision | Boundary / reason |
|---|---|---|---|
| FFmpeg/FFprobe | Probe, render, mix, encode | Call | Mandatory subprocess adapter; JSON/progress parsing |
| Ollama | Local LLM/embeddings | Call | HTTP adapter; structured outputs validated |
| SQLite | Project/stage state | Call | Core source of truth |
| MoneyPrinterTurbo | Task API/config patterns | Adapt | Useful vocabulary/validation |
| MoneyPrinterTurbo | App/task architecture | Reject | Cannot meet hash-DAG/resume/repair ownership |
| MoneyPrinterTurbo | FFmpeg cases | Study, then recreate | Keep Miller scene model/backend |
| BallonsTranslator | Detector/OCR/inpaint contracts | Adapt | Strong interfaces and fallback concepts |
| BallonsTranslator | Implementations | Call externally first | GPL boundary; unstable headless internals |
| BallonsTranslator | Qt orchestration/UI | Reject | Wrong runtime boundary |
| StoryToolkitAI | Search/story/Resolve concepts | Study | GPL; concepts inform Miller models |
| StoryToolkitAI | Queue/project state | Reject | JSON/thread model weaker than SQLite invariants |
| Revideo | Rich scene renderer | Call candidate | Node worker; pass benchmark before adoption |
| Revideo | Primary/only renderer | Reject | Chromium/Vite cannot be single point of failure |
| WhisperX | ASR + word alignment | Call | Isolated typed worker; normalize result |
| OpenTimelineIO | Optional edit export | Call | Export-only; Miller remains authoritative |
| OpenCLIP | Comic retrieval | Call candidate | Benchmark pinned inference model |
| SigLIP 2 | Comic retrieval | Call candidate | Benchmark B-class model on RTX 3070 |
| Qdrant | Vector/filter index | Call | Rebuildable index; SQLite owns identity |
| FAISS | Lightweight benchmark | Call candidate | No primary metadata DB |
| SAM 2 | Subject masks | Call optional | Selective scenes only |
| Depth Anything V2 Small | Depth maps | Call optional | Apache-2.0 weights; selective scenes |
| Depth Anything V2 Base+ | Default depth | Reject | CC-BY-NC-4.0 weights conflict with broad use |
| ComfyUI | Difficult cleanup/effects | Call optional | Never basic-render dependency |
| Temporal/Prefect/LangGraph/agents | Orchestration | Reject initially | Deterministic local state machine is sufficient |

No upstream source is approved for **Port** yet. Project license must be chosen
first, followed by file-level provenance and notice requirements.
