# Miller test matrix

| Area | Unit | Integration | End-to-end | Windows/hardware | Human | Required before |
|---|---|---|---|---|---|---|
| Database/migrations | transitions, SQL helpers | v1/v2/v3/current migration, rollback | interrupted migration/restore | file locks, antivirus | — | schema change merge |
| Artifacts/cache | hashing, paths, eviction | DB/artifact consistency | crash during write | NTFS/junction/long path/low disk | — | core completion |
| Queue/workers | claim/lease/heartbeat/cancel | worker death and stale result rejection | multi-stage restart | process tree/GPU admission | — | model worker adoption |
| CBZ/folder ingest | path and limits | cache/reconcile | real issue import | network/drive/long path | spot review | minimum usable |
| Panel/text/order | geometry and schemas | detector worker | corpus analysis | GPU/CPU throughput | annotation review | strong v1 |
| OCR | normalization/preprocessing | engine workers | searchable corpus | model/tool lifecycle | transcription review | strong v1 |
| VLM | schema/guard/confidence | external worker | corpus reanalysis | VRAM/load/unload | semantic rubric | strong v1 |
| Retrieval | tokenization/fusion/metrics | index/backends | labeled benchmark | latency/indexing/VRAM | relevance labels | winner ADR |
| Audio | normalization/timing | WhisperX/stable-ts workers | real narration | GPU/CPU/failure | timing review | strong v1 |
| Storyboard | scoring/constraints | retrieval + global plan | golden project | performance | narrative A/B | strong v1 |
| Derived visuals | crops/masks/provenance | inpaint worker | text-free project | VRAM/fallback | artifact review | polished v1 |
| Render | filter/manifest/probe | scene cache/audio mix | complete video | CPU/NVENC/cancel | visual/audio rubric | every release |
| Editor/API | commands/revisions/auth boundary | API + rerender | complete review workflow | browser/service restart | usability | polished v1 |
| Script factory | evidence IDs/schema | provider queue | sourced script | Ollama lifecycle | style/fact review | optional feature |
| Portable/export | manifest/path mapping | archive/OTIO roundtrip | cross-machine project | Resolve proof | NLE review | release/advanced |
| Security | path validation/fuzz | dependency scan | malicious fixture suite | Windows subprocess | privacy review | release |
| Packaging | config/parser | installed wheel/scripts | clean machine | Windows matrix | install usability | E6 release |

## Mandatory command tiers

### Focused sprint gate

Run the smallest relevant tests and inspect generated artifacts.

### Full repository gate

```powershell
uv sync --frozen --extra dev --extra web --extra export --extra retrieval
uv run ruff check .
uv run mypy src
uv run pytest
uv build
uv run python scripts/validate_planning.py
```

### Release gate

Repeat the full gate from a clean extracted source tree, install the built wheel into a clean environment, run CLI/API smoke tests, and perform `docs/LOCAL_ACCEPTANCE_TEST.md` on Windows.

## Evidence storage

Store machine-readable reports under the Miller-managed workspace or `verification/` release artifact. Git may contain compact non-copyrighted summaries. Every report records commit, config, dependency lock, model/tool versions, input fixture manifest, command, timestamps, and result class.
