"""Command-line entry point for the Miller foundation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .comics import ComicIngestor
from .db import Database
from .models import StageDefinition
from .runner import PipelineRunner, RuntimeStage, StageContext, StageExecutionError
from .video import FFmpegRenderer, ManualVideoSpec


def _emit(value: Any) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def _demo_stages() -> list[RuntimeStage]:
    def prepare(context: StageContext) -> dict[str, Any]:
        if context.config.get("fail"):
            raise RuntimeError("intentional prepare failure")
        return {"stage": "prepare", "seed": context.config.get("seed", "default")}

    def transform(context: StageContext) -> dict[str, Any]:
        if context.config.get("fail"):
            raise RuntimeError("intentional transform failure")
        return {
            "stage": "transform",
            "inputs": [artifact.id for artifact in context.dependency_artifacts],
        }

    def finalize(context: StageContext) -> dict[str, Any]:
        if context.config.get("fail"):
            raise RuntimeError("intentional finalize failure")
        return {
            "stage": "finalize",
            "inputs": [artifact.id for artifact in context.dependency_artifacts],
            "result": "complete",
        }

    return [
        RuntimeStage(StageDefinition(id="prepare", name="Prepare", version="1"), prepare),
        RuntimeStage(
            StageDefinition(
                id="transform", name="Transform", version="1", dependencies=("prepare",)
            ),
            transform,
        ),
        RuntimeStage(
            StageDefinition(
                id="finalize", name="Finalize", version="1", dependencies=("transform",)
            ),
            finalize,
        ),
    ]


def _database(args: argparse.Namespace) -> Database:
    database = Database(Path(args.db))
    database.initialize()
    return database


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="miller")
    parser.add_argument("--db", default=".miller/miller.sqlite3", help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize the Miller database")

    create = subparsers.add_parser("project-create", help="Create a project")
    create.add_argument("--name", required=True)
    create.add_argument("--workspace", required=True)
    create.add_argument("--id")

    show = subparsers.add_parser("project-show", help="Show a project and stage state")
    show.add_argument("--project-id", required=True)

    run = subparsers.add_parser("demo-run", help="Run the deterministic demo pipeline")
    run.add_argument("--project-id", required=True)
    run.add_argument("--workspace", required=True)
    run.add_argument("--seed", default="default")
    run.add_argument("--fail-stage", choices=("prepare", "transform", "finalize"))

    cancel = subparsers.add_parser("cancel", help="Request cooperative stage cancellation")
    cancel.add_argument("--project-id", required=True)
    cancel.add_argument("--stage-id", required=True)
    cancel.add_argument("--workspace", required=True)

    events = subparsers.add_parser("events", help="List project events")
    events.add_argument("--project-id", required=True)

    recover = subparsers.add_parser("recover", help="Mark stale running attempts abandoned")
    recover.add_argument("--workspace", required=True)

    comic_inventory = subparsers.add_parser(
        "comic-inventory", help="Inspect an image folder or CBZ without modifying it"
    )
    comic_inventory.add_argument("--source", required=True)
    comic_inventory.add_argument("--workspace", required=True)

    comic_cache = subparsers.add_parser(
        "comic-cache", help="Create content-addressed page and thumbnail cache"
    )
    comic_cache.add_argument("--source", required=True)
    comic_cache.add_argument("--workspace", required=True)

    video_render = subparsers.add_parser(
        "video-render", help="Render a manual scene specification with FFmpeg"
    )
    video_render.add_argument("--spec", required=True)
    video_render.add_argument("--output", required=True)
    video_render.add_argument("--manifest")

    web = subparsers.add_parser("web", help="Run the local storyboard editor")
    web.add_argument(
        "--host",
        choices=("127.0.0.1", "localhost", "::1"),
        default="127.0.0.1",
        help="Local loopback address only",
    )
    web.add_argument("--port", type=int, default=8765)
    web.add_argument("--no-browser", action="store_true")

    capabilities = subparsers.add_parser(
        "capabilities", help="Probe local tools, GPU, and recommended profile"
    )
    capabilities.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    capabilities.add_argument("--qdrant-url", default="http://127.0.0.1:6333")

    config_show = subparsers.add_parser("config-show", help="Validate and display settings")
    config_show.add_argument("--path", default="config.toml")

    config_init = subparsers.add_parser("config-init", help="Create a default settings file")
    config_init.add_argument("--path", default="config.toml")
    config_init.add_argument("--force", action="store_true")

    cache_prune = subparsers.add_parser(
        "cache-prune", help="Inspect or prune only the Miller-managed cache"
    )
    cache_prune.add_argument("--workspace", required=True)
    cache_prune.add_argument("--target-gb", required=True, type=float)
    cache_prune.add_argument("--execute", action="store_true")

    queue_enqueue = subparsers.add_parser("queue-enqueue", help="Add a durable queue item")
    queue_enqueue.add_argument("--project-id", required=True)
    queue_enqueue.add_argument("--kind", required=True, choices=("script", "video", "library"))
    queue_enqueue.add_argument("--priority", type=int, default=100)
    queue_enqueue.add_argument("--payload", default="{}", help="JSON object")

    queue_list = subparsers.add_parser("queue-list", help="List durable queue items")
    queue_list.add_argument("--kind", choices=("script", "video", "library"))
    queue_list.add_argument(
        "--status", choices=("pending", "running", "completed", "failed", "cancelled")
    )

    queue_claim = subparsers.add_parser("queue-claim", help="Claim the next queue item")
    queue_claim.add_argument("--kind", required=True, choices=("script", "video", "library"))

    queue_finish = subparsers.add_parser("queue-finish", help="Complete or fail a queue item")
    queue_finish.add_argument("--item-id", required=True)
    queue_finish.add_argument("--error")

    subparsers.add_parser("queue-recover", help="Requeue work interrupted by a restart")

    script_worker = subparsers.add_parser(
        "worker-script", help="Process queued script jobs through local Ollama"
    )
    script_worker.add_argument("--model", required=True)
    script_worker.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    script_worker.add_argument("--max-items", type=int, default=100)

    video_worker = subparsers.add_parser("worker-video", help="Process queued FFmpeg video jobs")
    video_worker.add_argument("--max-items", type=int, default=100)

    project_export = subparsers.add_parser(
        "project-export", help="Create an integrity-checked portable project"
    )
    project_export.add_argument("--project-id", required=True)
    project_export.add_argument("--workspace", required=True)
    project_export.add_argument("--output", required=True)

    project_import = subparsers.add_parser(
        "project-import", help="Import a portable project into a clean workspace"
    )
    project_import.add_argument("--workspace", required=True)
    project_import.add_argument("--package", required=True)

    timeline = subparsers.add_parser(
        "timeline-export", help="Export storyboard JSON to OpenTimelineIO"
    )
    timeline.add_argument("--storyboard", required=True)
    timeline.add_argument("--asset-map", required=True, help="JSON map of asset IDs to paths")
    timeline.add_argument("--output")
    timeline.add_argument("--package-dir")
    timeline.add_argument("--fps", type=float, default=30.0)
    timeline.add_argument("--narration")
    timeline.add_argument("--music")
    timeline.add_argument("--subtitles")

    script_run = subparsers.add_parser(
        "script-run", help="Run the sourced script factory through local Ollama"
    )
    script_run.add_argument("--project-id", required=True)
    script_run.add_argument("--request", required=True, help="ScriptFactoryRequest JSON")
    script_run.add_argument("--model", required=True)
    script_run.add_argument("--ollama-url", default="http://127.0.0.1:11434")

    baseline = subparsers.add_parser(
        "baseline-video",
        help="Analyze a comic and render a complete no-AI baseline video",
    )
    baseline.add_argument("--project-id", required=True)
    baseline.add_argument("--project-name", default="Baseline video")
    baseline.add_argument("--workspace", required=True)
    baseline.add_argument("--comic", required=True)
    baseline.add_argument("--script", required=True)
    baseline.add_argument("--narration", required=True)
    baseline.add_argument("--output", required=True)
    baseline.add_argument("--music")
    baseline.add_argument("--subtitles")
    baseline.add_argument("--language", default="eng")
    baseline.add_argument("--no-ocr", action="store_true")
    baseline.add_argument("--steering", action="append", default=[])
    baseline.add_argument("--exclude", action="append", default=[])
    baseline.add_argument("--width", type=int, default=1920)
    baseline.add_argument("--height", type=int, default=1080)
    baseline.add_argument("--fps", type=int, default=30)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {"comic-inventory", "comic-cache"}:
        ingestor = ComicIngestor(args.workspace)
        inventory = ingestor.inventory(args.source)
        if args.command == "comic-inventory":
            _emit(inventory)
        else:
            cached = ingestor.cache_inventory(inventory)
            _emit(
                {
                    "inventory": inventory.model_dump(mode="json"),
                    "cached": [
                        {
                            "page": page.model_dump(mode="json"),
                            "thumbnail": thumbnail.model_dump(mode="json"),
                        }
                        for page, thumbnail in cached
                    ],
                }
            )
        return 0
    if args.command == "video-render":
        spec_path = Path(args.spec).expanduser().resolve()
        spec = ManualVideoSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))
        render_result = FFmpegRenderer().render(spec, args.output)
        render_manifest = render_result.model_dump_json(indent=2)
        if args.manifest:
            manifest_path = Path(args.manifest).expanduser().resolve()
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(render_manifest + "\n", encoding="utf-8")
        _emit(render_result)
        return 0
    if args.command == "web":
        import threading
        import webbrowser

        try:
            import uvicorn

            from .web import create_app
        except ImportError:
            print(
                "Web dependencies are unavailable. Run: uv sync --extra web",
                file=sys.stderr,
            )
            return 3
        address = f"http://{args.host}:{args.port}"
        if not args.no_browser:
            threading.Timer(0.8, lambda: webbrowser.open(address)).start()
        uvicorn.run(
            create_app(args.db),
            host=args.host,
            port=args.port,
            log_level="info",
        )
        return 0

    if args.command == "capabilities":
        from .runtime import probe_runtime

        _emit(probe_runtime(args.ollama_url, args.qdrant_url))
        return 0
    if args.command == "config-show":
        from .runtime import load_settings

        _emit(load_settings(args.path))
        return 0
    if args.command == "config-init":
        from .runtime import MillerSettings, save_settings

        config_path = Path(args.path)
        if config_path.exists() and not args.force:
            print(f"settings file already exists: {config_path}", file=sys.stderr)
            return 2
        save_settings(config_path, MillerSettings())
        _emit(MillerSettings())
        return 0
    if args.command == "cache-prune":
        from .runtime import CacheManager

        if args.target_gb < 0:
            print("--target-gb cannot be negative", file=sys.stderr)
            return 2
        target_bytes = round(args.target_gb * 1024**3)
        plan = CacheManager(args.workspace).prune(
            target_bytes,
            dry_run=not args.execute,
        )
        _emit(plan)
        return 0
    if args.command == "timeline-export":
        try:
            from .export import TimelineExporter
        except ImportError:
            print(
                "Timeline dependencies are unavailable. Run: uv sync --extra export",
                file=sys.stderr,
            )
            return 3
        from .storyboard import StoryboardPlan

        storyboard = StoryboardPlan.model_validate_json(
            Path(args.storyboard).read_text(encoding="utf-8")
        )
        asset_map_value = json.loads(Path(args.asset_map).read_text(encoding="utf-8"))
        if not isinstance(asset_map_value, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in asset_map_value.items()
        ):
            print("--asset-map must contain a JSON string-to-string object", file=sys.stderr)
            return 2
        exporter = TimelineExporter(fps=args.fps)
        if args.package_dir:
            timeline_result = exporter.export_package(
                storyboard,
                asset_map_value,
                args.package_dir,
                narration_path=args.narration,
                music_path=args.music,
                subtitle_path=args.subtitles,
            )
        elif args.output:
            timeline_result = exporter.export(
                storyboard,
                asset_map_value,
                args.output,
                narration_path=args.narration,
                music_path=args.music,
                subtitle_path=args.subtitles,
            )
        else:
            print("timeline-export requires --output or --package-dir", file=sys.stderr)
            return 2
        _emit(timeline_result)
        return 0

    database = _database(args)
    if args.command == "init":
        _emit({"database": str(database.path), "status": "initialized"})
        return 0
    if args.command == "project-create":
        project = database.create_project(args.name, args.workspace, args.id)
        _emit(project)
        return 0
    if args.command == "project-show":
        project = database.get_project(args.project_id)
        _emit(
            {
                "project": project.model_dump(mode="json"),
                "stages": [
                    run.model_dump(mode="json") for run in database.list_stage_runs(project.id)
                ],
            }
        )
        return 0
    if args.command == "events":
        _emit([event.model_dump(mode="json") for event in database.list_events(args.project_id)])
        return 0
    if args.command == "recover":
        recovered = database.recover_abandoned()
        _emit({"recovered": recovered})
        return 0
    if args.command == "queue-enqueue":
        from .models import QueueKind

        payload = json.loads(args.payload)
        if not isinstance(payload, dict):
            print("--payload must be a JSON object", file=sys.stderr)
            return 2
        _emit(
            database.enqueue(
                args.project_id,
                QueueKind(args.kind),
                payload,
                priority=args.priority,
            )
        )
        return 0
    if args.command == "queue-list":
        from .models import QueueKind, QueueStatus

        kind = QueueKind(args.kind) if args.kind else None
        status = QueueStatus(args.status) if args.status else None
        queue_items = database.list_queue(kind=kind, status=status)
        _emit([item.model_dump(mode="json") for item in queue_items])
        return 0
    if args.command == "queue-claim":
        from .models import QueueKind

        item = database.claim_next(QueueKind(args.kind))
        _emit(None if item is None else item.model_dump(mode="json"))
        return 0
    if args.command == "queue-finish":
        item = (
            database.fail_queue_item(args.item_id, args.error)
            if args.error
            else database.complete_queue_item(args.item_id)
        )
        _emit(item)
        return 0
    if args.command == "queue-recover":
        _emit({"recovered": database.recover_queue()})
        return 0
    if args.command == "worker-script":
        from .models import QueueKind
        from .script_factory import (
            OllamaGenerator,
            ScriptFactory,
            ScriptFactoryRequest,
            ScriptFactoryService,
        )
        from .workers import QueueWorker

        script_service = ScriptFactoryService(
            database,
            ScriptFactory(OllamaGenerator(args.model, url=args.ollama_url)),
        )

        def process_script(item: Any) -> dict[str, Any]:
            request_value = item.payload.get("request")
            if request_value is None and item.payload.get("request_path"):
                request_value = json.loads(
                    Path(item.payload["request_path"]).read_text(encoding="utf-8")
                )
            request = ScriptFactoryRequest.model_validate(request_value)
            package = script_service.run(item.project_id, request)
            return {"final_words": len(package.final.text.split())}

        results = QueueWorker(database, QueueKind.SCRIPT, process_script).run_until_empty(
            max_items=args.max_items
        )
        _emit([result.model_dump(mode="json") for result in results])
        return 0
    if args.command == "worker-video":
        from .models import QueueKind
        from .workers import QueueWorker

        def process_video(item: Any) -> dict[str, Any]:
            spec_value = item.payload.get("spec")
            if spec_value is None and item.payload.get("spec_path"):
                spec_value = json.loads(Path(item.payload["spec_path"]).read_text(encoding="utf-8"))
            spec = ManualVideoSpec.model_validate(spec_value)
            output = item.payload.get("output")
            if not isinstance(output, str) or not output:
                raise ValueError("video queue payload requires output path")
            render = FFmpegRenderer().render(spec, output)
            try:
                revision = database.get_document(item.project_id, "render.last").revision
            except KeyError:
                revision = 0
            database.put_document(
                item.project_id,
                "render.last",
                render.model_dump(mode="json"),
                expected_revision=revision,
            )
            return {"output": render.output_path, "sha256": render.output_sha256}

        results = QueueWorker(database, QueueKind.VIDEO, process_video).run_until_empty(
            max_items=args.max_items
        )
        _emit([result.model_dump(mode="json") for result in results])
        return 0
    if args.command == "project-export":
        from .portable import PortableProjectExporter

        exported_manifest = PortableProjectExporter(database, args.workspace).export(
            args.project_id, args.output
        )
        _emit(exported_manifest)
        return 0
    if args.command == "project-import":
        from .portable import PortableProjectImporter

        imported_manifest = PortableProjectImporter(database, args.workspace).import_package(
            args.package
        )
        _emit(imported_manifest)
        return 0
    if args.command == "script-run":
        from .script_factory import (
            OllamaGenerator,
            ScriptFactory,
            ScriptFactoryRequest,
            ScriptFactoryService,
        )

        request = ScriptFactoryRequest.model_validate_json(
            Path(args.request).read_text(encoding="utf-8")
        )
        service = ScriptFactoryService(
            database,
            ScriptFactory(OllamaGenerator(args.model, url=args.ollama_url)),
        )
        _emit(service.run(args.project_id, request))
        return 0
    if args.command == "baseline-video":
        from .pipeline import BaselineVideoPipeline
        from .video import RenderProfile

        try:
            database.get_project(args.project_id)
        except KeyError:
            database.create_project(
                args.project_name,
                args.workspace,
                args.project_id,
            )
        script = Path(args.script).read_text(encoding="utf-8")
        profile = RenderProfile(width=args.width, height=args.height, fps=args.fps)
        baseline_result = BaselineVideoPipeline(database, args.workspace).run(
            args.project_id,
            comic_source=args.comic,
            script=script,
            narration_path=args.narration,
            output_path=args.output,
            steering_keywords=tuple(args.steering),
            exclusions=tuple(args.exclude),
            language=args.language,
            use_ocr=not args.no_ocr,
            music_path=args.music,
            subtitle_path=args.subtitles,
            profile=profile,
        )
        _emit(baseline_result)
        return 0
    if args.command in {"demo-run", "cancel"}:
        runner = PipelineRunner(database, args.workspace, _demo_stages())
        if args.command == "cancel":
            runner.request_cancel(args.project_id, args.stage_id)
            _emit({"project_id": args.project_id, "stage_id": args.stage_id, "cancel": True})
            return 0
        database.recover_abandoned()
        configs: dict[str, dict[str, Any]] = {"prepare": {"seed": args.seed}}
        if args.fail_stage:
            configs.setdefault(args.fail_stage, {})["fail"] = True
        try:
            outputs = runner.run(args.project_id, configs=configs)
        except StageExecutionError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        _emit(
            {stage_id: artifact.model_dump(mode="json") for stage_id, artifact in outputs.items()}
        )
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
