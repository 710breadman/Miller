# License matrix

Not legal advice. This is an engineering gate. Project license is currently
unset; copying upstream source is therefore prohibited by project policy.

| Component | Observed license | Approved use now | Conditions / risk |
|---|---|---|---|
| MoneyPrinterTurbo | MIT | Study, call, adapt concepts | Preserve notices if code is later copied |
| BallonsTranslator | GPL-3.0 | Study; separate user-installed process proof | No in-core copy/bundle until distribution analysis |
| StoryToolkitAI | GPL-3.0 | Study only | No source copy or linked dependency |
| Revideo | MIT | Package/process proof | Preserve license notices when distributed |
| WhisperX | BSD-2-Clause | Package/process adapter | Preserve copyright/license notice |
| OpenTimelineIO | Apache-2.0 | Python dependency | Preserve NOTICE/license obligations if distributed |
| OpenCLIP code | MIT | Benchmark dependency | Check each model card/weights separately |
| Big Vision SigLIP 2 code | Apache-2.0 | Reference/benchmark | Model/material licensing tracked separately |
| Qdrant client/server | Apache-2.0 | Dependency/service | Preserve notices when distributed |
| SAM 2 code/checkpoints | Apache-2.0 | Optional benchmark | Third-party demo assets have separate licenses |
| Depth Anything V2 Small | Apache-2.0 | Optional benchmark/use | Track code and weight provenance |
| Depth Anything V2 Base/Large/Giant | CC-BY-NC-4.0 weights | Evaluation only; not default | Non-commercial restriction |
| FFmpeg | LGPL/GPL varies by build/config | External executable | Record build/config; avoid assuming one license |
| Ollama/models | Tool + model-specific | API use | Every model has independent terms |
| Comic/user media | User-provided rights | Read-only processing | Do not imply ownership or redistribution rights |

## Distribution gates

1. Select Miller project license.
2. Generate dependency SBOM with exact versions.
3. Record model-card and weight licenses separately from source code.
4. Record FFmpeg build configuration and codecs.
5. Decide whether optional GPL tools are user-installed external programs or
   distributed components; obtain legal review before bundling/linking.
6. Include attribution/notices in packaged builds.
