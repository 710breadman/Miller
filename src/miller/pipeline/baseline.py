"""Usable no-AI comic-to-video baseline pipeline."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from ..analysis import ComicAnalysisPipeline, ComicAnalysisResult
from ..audio import AlignmentResult, AudioTools, BeatPlan, build_beat_plan, uniform_alignment
from ..db import Database
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
        project_root = self.workspace / "projects" / project_id
        project_root.mkdir(parents=True, exist_ok=True)
        analysis = ComicAnalysisPipeline(self.workspace).analyze(
            comic_source,
            language=language,
            use_ocr=use_ocr,
            index_path=project_root / "analysis.sqlite3",
        )
        metadata = AudioTools().inspect(narration_path)
        alignment = uniform_alignment(
            script,
            metadata.duration_seconds,
            language=language[:2],
        )
        beats = build_beat_plan(script, alignment)
        scope = propose_search_scope(
            script,
            analysis.pages,
            steering_keywords=steering_keywords,
            exclusions=exclusions,
        )
        storyboard = StoryboardBuilder(analysis.pages).build(beats, scope)
        spec = storyboard_to_video_spec(
            storyboard,
            analysis.asset_paths,
            narration_path=narration_path,
            music_path=music_path,
            subtitle_path=subtitle_path,
            profile=profile,
        )
        render = FFmpegRenderer().render(spec, output_path)
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
