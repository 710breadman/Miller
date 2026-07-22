# External project decisions

Decision date: **2026-07-21**  
Ratings: **adopt**, **adapt**, **benchmark**, **monitor**, or **reject**.

| Project | Purpose | License / activity | Strengths | Weaknesses / dependency risk | Integration difficulty | Miller decision |
|---|---|---|---|---|---|---|
| FFmpeg/FFprobe | render, probe, normalize, mix | LGPL/GPL varies by build; active | mature, deterministic CLI, broad codecs | command complexity; build/codec license must be recorded | medium | **adopt** as mandatory backend |
| Tesseract | OCR baseline | Apache-2.0; maintained | lightweight, offline, simple | weak on stylized lettering and layout | low | **adopt** as baseline/fallback |
| manga-ocr | Japanese manga OCR | Apache-2.0; current | manga-tuned text recognition | Japanese focus; model environment | medium | **benchmark/adapt** external worker |
| PaddleOCR | multilingual OCR | Apache-2.0; active | detection/recognition breadth | large dependency and GPU environment | medium/high | **benchmark** |
| comic-text-detector | comic text/balloon masks | GPL-3.0 | comic-specific, useful masks | GPL and training-data provenance | medium | **benchmark**, external only |
| BallonsTranslator | OCR/removal/inpainting app | GPL-3.0; active | proven comic cleanup flow | Qt/GUI coupling, unstable headless boundary | high | **adapt concepts**, external proof |
| MAGI | comic page understanding | research restrictions | broad comic tasks and relationships | not appropriate as distributable core; operational complexity | high | **reject core**, benchmark/inspire |
| Qwen3-VL-2B | structured visual semantics | Apache-2.0 model card; current | small modern VLM, structured output candidate | real comic accuracy and 8 GB fit unproven | medium | **benchmark first** |
| Qwen3-VL-Embedding-2B | multimodal retrieval | Apache-2.0; current | unified multimodal retrieval | runtime/VRAM can exceed apparent model size | high | **benchmark** |
| SigLIP 2 NaFlex | image-text retrieval | Apache-2.0; current | variable aspect, strong retrieval family | must validate comic and panel performance | medium | **priority benchmark** |
| OpenCLIP | image-text retrieval | MIT code; checkpoint terms vary | many checkpoints, mature ecosystem | dataset/checkpoint licensing and generic-image bias | medium | **benchmark** exact checkpoints |
| Qdrant | vector store | Apache-2.0; active | metadata filters, service parity | extra service/packaging/backup surface | medium | **retain adapter**, optional production backend |
| sqlite-vec | embedded vector search | MIT/Apache; active pre-1.0 | simple local deployment | API/migration stability and scale unproven | medium | **benchmark/monitor** |
| WhisperX | word alignment | BSD-2-Clause; active | word timestamps and alignment | model downloads, PyTorch/CUDA complexity | high | **adopt** pinned external worker after proof |
| stable-ts | timestamp/alignment alternative | MIT; active | practical fallback and corrections | overlapping dependency stack | medium | **benchmark fallback** |
| Revideo | programmatic video | MIT; active | reusable declarative motion and preview | Node/Chromium/Vite memory, packaging, determinism surfaces | high | **benchmark**, optional only |
| Remotion | programmatic video | tiered/custom licensing | mature React video ecosystem | license and Node complexity conflict with local simple core | high | **reject core** |
| OpenTimelineIO | timeline interchange | Apache-2.0; active | standard editorial model | Resolve adapters/version compatibility vary | low/medium | **adopt optional export** |
| StoryToolkitAI | story/transcript/Resolve | GPL-3.0; active | useful workflow and Resolve lessons | incompatible core reuse and different state model | high | **inspire only** |
| MoneyPrinterTurbo | automated video workflow | MIT; active | practical task/media patterns | stock-first assumptions and weaker provenance/resume | medium | **adapt patterns**, not foundation |
| SAM 2 | subject segmentation | Apache-2.0 code/model terms vary | high-quality masks | CUDA/build/VRAM overhead | high | **monitor/optional benchmark** |
| Depth Anything V2 Small | depth/parallax | Apache-2.0 for Small; larger weights restricted | selective visual depth | limited product value, possible artifacts | medium | **optional later** |
| CVAT | annotation platform | MIT; active | powerful review/annotation | heavy deployment and generic workflow | high | **optional**, build focused Miller label UI first |

## Dependency acceptance checklist

Before an item becomes **adopted**, its sprint must record:

1. exact repository/tag/commit and package version;
2. code, model-weight, dataset, and transitive license terms;
3. install and capability probe on Windows;
4. isolated failure, timeout, cancellation, and unavailable-tool behavior;
5. input/output schema and hashes;
6. peak RAM/VRAM and disk use;
7. benchmark or user benefit over the current fallback;
8. rollback and data migration strategy;
9. notices/SBOM entry.

No project becomes Miller’s source of truth.
