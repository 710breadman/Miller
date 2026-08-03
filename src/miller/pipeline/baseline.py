"""Usable no-AI comic-to-video baseline pipeline."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..analysis import ComicAnalysisPipeline, ComicAnalysisResult
from ..artifacts import ArtifactStore, sha256_file
from ..audio import AlignmentResult, AudioTools, BeatPlan, build_beat_plan, uniform_alignment
from ..comics import ComicIngestor, ComicInventory
from ..db import Database
from ..models import Artifact, StageDefinition
from ..runner import PipelineRunner, RuntimeStage, StageContext
from ..storyboard import (
    StoryboardBuilder,
    StoryboardPlan,
    propose_search_scope,
)
from ..video import FFmpegRenderer, RenderProfile, RenderResult
from ..video.storyboard import storyboard_to_video_spec


class BaselineVideoResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    analysis: ComicAnalysisResult
    alignment: AlignmentResult
    beats: BeatPlan
    storyboard: StoryboardPlan
    render: RenderResult


class BaselineVideoPipeline:
    def __init__(self, database: Database, workspace: Path | str) -> None:
        self.database = database
        self.workspace = Path(workspace).expanduser().resolve()

    def run(
        self,
        project_id: str,
        *,
        comic_source: Path | str,
        script: str,
        narration_path: Path | str,
        output_path: Path | str,
        steering_keywords: tuple[str, ...] = (),
        exclusions: tuple[str, ...] = (),
        language: str = "eng",
        use_ocr: bool = True,
        music_path: Path | str | None = None,
        subtitle_path: Path | str | None = None,
        profile: RenderProfile | None = None,
    ) -> BaselineVideoResult:
        self.database.get_project(project_id)
        self.database.recover_abandoned(project_id)
        comic_path = Path(comic_source).expanduser().resolve()
        narration = Path(narration_path).expanduser().resolve()
        output = Path(output_path).expanduser().resolve()
        music = self._optional_resolved_path(music_path)
        subtitles = self._optional_resolved_path(subtitle_path)
        render_profile = profile or RenderProfile()
        inventory = ComicIngestor(self.workspace).inventory(comic_path)
        runner = self._runner(project_id)
        outputs = runner.run(
            project_id,
            configs={
                "baseline.ingest": {
                    "comic_source": str(comic_path),
                    "source_fingerprint": inventory.fingerprint,
                },
                "baseline.analysis": {
                    "comic_source": str(comic_path),
                    "language": language,
                    "use_ocr": use_ocr,
                },
                "baseline.alignment": {
                    "script": script,
                    "narration_path": str(narration),
                    "narration_sha256": sha256_file(narration),
                    "language": language,
                },
                "baseline.storyboard": {
                    "script": script,
                    "steering_keywords": tuple(steering_keywords),
                    "exclusions": tuple(exclusions),
                },
                "baseline.render": {
                    "output_path": str(output),
                    "narration_path": str(narration),
                    "narration_sha256": sha256_file(narration),
                    "music_path": str(music) if music is not None else None,
                    "music_sha256": sha256_file(music) if music is not None else None,
                    "subtitle_path": str(subtitles) if subtitles is not None else None,
                    "subtitle_sha256": (
                        sha256_file(subtitles) if subtitles is not None else None
                    ),
                    "profile": render_profile.model_dump(mode="json"),
                },
            },
        )
        analysis = ComicAnalysisResult.model_validate(
            self._read_artifact(outputs["baseline.analysis"], runner.artifacts)
        )
        alignment = AlignmentResult.model_validate(
            self._read_artifact(outputs["baseline.alignment"], runner.artifacts)
        )
        planning = self._read_artifact(outputs["baseline.storyboard"], runner.artifacts)
        beats = BeatPlan.model_validate(planning["beats"])
        storyboard = StoryboardPlan.model_validate(planning["storyboard"])
        render = RenderResult.model_validate(
            self._read_artifact(outputs["baseline.render"], runner.artifacts)
        )
        self._save(project_id, "comic.inventory", analysis.inventory.model_dump(mode="json"))
        self._save(
            project_id,
            "comic.analysis",
            {"pages": [page.model_dump(mode="json") for page in analysis.pages]},
        )
        self._save(project_id, "audio.alignment", alignment.model_dump(mode="json"))
        self._save(project_id, "audio.beats", beats.model_dump(mode="json"))
        self._save(project_id, "storyboard", storyboard.model_dump(mode="json"))
        self._save(project_id, "render.last", render.model_dump(mode="json"))
        return BaselineVideoResult(
            analysis=analysis,
            alignment=alignment,
            beats=beats,
            storyboard=storyboard,
            render=render,
        )

    def _runner(self, project_id: str) -> PipelineRunner:
        project_root = self.workspace / "projects" / project_id
        project_root.mkdir(parents=True, exist_ok=True)

        def ingest(context: StageContext) -> dict[str, Any]:
            inventory = ComicIngestor(self.workspace).inventory(
                str(context.config["comic_source"])
            )
            expected = str(context.config["source_fingerprint"])
            if inventory.fingerprint != expected:
                raise RuntimeError("comic source changed after baseline preflight inventory")
            return inventory.model_dump(mode="json")

        def analyze(context: StageContext) -> dict[str, Any]:
            expected = ComicInventory.model_validate(
                self._read_artifact(context.dependency_artifacts[0], context.artifact_store)
            )
            result = ComicAnalysisPipeline(self.workspace).analyze(
                str(context.config["comic_source"]),
                language=str(context.config["language"]),
                use_ocr=bool(context.config["use_ocr"]),
                index_path=project_root / "analysis.sqlite3",
            )
            if result.inventory.fingerprint != expected.fingerprint:
                raise RuntimeError("comic source changed between ingest and analysis")
            return result.model_dump(mode="json")

        def align(context: StageContext) -> dict[str, Any]:
            metadata = AudioTools().inspect(str(context.config["narration_path"]))
            alignment = uniform_alignment(
                str(context.config["script"]),
                metadata.duration_seconds,
                language=str(context.config["language"])[:2],
            )
            return alignment.model_dump(mode="json")

        def storyboard(context: StageContext) -> dict[str, Any]:
            analysis = ComicAnalysisResult.model_validate(
                self._read_artifact(context.dependency_artifacts[0], context.artifact_store)
            )
            alignment = AlignmentResult.model_validate(
                self._read_artifact(context.dependency_artifacts[1], context.artifact_store)
            )
            script = str(context.config["script"])
            beats = build_beat_plan(script, alignment)
            scope = propose_search_scope(
                script,
                analysis.pages,
                steering_keywords=tuple(context.config["steering_keywords"]),
                exclusions=tuple(context.config["exclusions"]),
            )
            plan = StoryboardBuilder(analysis.pages).build(beats, scope)
            return {
                "beats": beats.model_dump(mode="json"),
                "storyboard": plan.model_dump(mode="json"),
            }

        def render(context: StageContext) -> dict[str, Any]:
            analysis = ComicAnalysisResult.model_validate(
                self._read_artifact(context.dependency_artifacts[0], context.artifact_store)
            )
            planning = self._read_artifact(
                context.dependency_artifacts[1], context.artifact_store
            )
            plan = StoryboardPlan.model_validate(planning["storyboard"])
            spec = storyboard_to_video_spec(
                plan,
                analysis.asset_paths,
                narration_path=str(context.config["narration_path"]),
                music_path=self._optional_config_path(context.config, "music_path"),
                subtitle_path=self._optional_config_path(context.config, "subtitle_path"),
                profile=RenderProfile.model_validate(context.config["profile"]),
            )
            result = FFmpegRenderer().render(spec, str(context.config["output_path"]))
            return result.model_dump(mode="json")

        return PipelineRunner(
            self.database,
            self.workspace,
            [
                RuntimeStage(
                    StageDefinition(
                        id="baseline.ingest", name="Baseline comic ingest", version="1"
                    ),
                    ingest,
                ),
                RuntimeStage(
                    StageDefinition(
                        id="baseline.analysis",
                        name="Baseline comic analysis and derived assets",
                        version="1",
                        dependencies=("baseline.ingest",),
                    ),
                    analyze,
                ),
                RuntimeStage(
                    StageDefinition(
                        id="baseline.alignment", name="Baseline uniform alignment", version="1"
                    ),
                    align,
                ),
                RuntimeStage(
                    StageDefinition(
                        id="baseline.storyboard",
                        name="Baseline retrieval and storyboard",
                        version="1",
                        dependencies=("baseline.analysis", "baseline.alignment"),
                    ),
                    storyboard,
                ),
                RuntimeStage(
                    StageDefinition(
                        id="baseline.render",
                        name="Baseline render",
                        version="1",
                        dependencies=("baseline.analysis", "baseline.storyboard"),
                    ),
                    render,
                    self._validate_render_cache,
                ),
            ],
        )

    @staticmethod
    def _read_artifact(artifact: Artifact, store: ArtifactStore) -> Any:
        return json.loads(store.resolve(artifact).read_text(encoding="utf-8"))

    @staticmethod
    def _optional_resolved_path(value: Path | str | None) -> Path | None:
        return Path(value).expanduser().resolve() if value is not None else None

    @staticmethod
    def _optional_config_path(config: Mapping[str, Any], key: str) -> str | None:
        value = config.get(key)
        return str(value) if value is not None else None

    @classmethod
    def _validate_render_cache(
        cls,
        artifact: Artifact,
        config: Mapping[str, Any],
        store: ArtifactStore,
    ) -> bool:
        result = RenderResult.model_validate(cls._read_artifact(artifact, store))
        output = Path(result.output_path)
        expected = Path(str(config["output_path"])).expanduser().resolve()
        return (
            output == expected
            and output.is_file()
            and sha256_file(output) == result.output_sha256
        )

    def _save(self, project_id: str, kind: str, document: dict[str, object]) -> None:
        try:
            revision = self.database.get_document(project_id, kind).revision
        except KeyError:
            revision = 0
        self.database.put_document(
            project_id,
            kind,
            document,
            expected_revision=revision,
        )
