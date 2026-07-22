from pathlib import Path

from miller.analysis import NormalizedPoint
from miller.quality import (
    FindingCategory,
    RenderQualityEvaluator,
    RepairPlanner,
    StoryboardQualityEvaluator,
)
from miller.storyboard import (
    CameraPlan,
    CameraPreset,
    SceneCandidate,
    SceneScore,
    SearchScope,
    StoryboardPlan,
    StoryboardScene,
    TransitionPreset,
)
from miller.video import ManualVideoSpec, RenderProfile, RenderResult, Scene


def candidate(asset_id: str, score: float, locator: str = "Series/1/page.png") -> SceneCandidate:
    return SceneCandidate(
        asset_id=asset_id,
        source_locator=locator,
        score=SceneScore(
            lexical=score,
            character=score,
            theme=score,
            continuity=1,
            quality=0.8,
            reuse_penalty=0,
            total=score,
        ),
    )


def scene(
    index: int,
    primary: str,
    alternatives: tuple[str, ...],
    *,
    locked: bool = False,
    score: float = 0.2,
) -> StoryboardScene:
    all_assets = (primary, *alternatives)
    return StoryboardScene(
        id=f"scene_{index:04d}",
        beat_id=f"beat_{index:04d}",
        start=(index - 1) * 2,
        end=index * 2,
        narration=f"Beat {index}",
        intent=f"Beat {index}",
        primary_asset=primary,
        alternatives=alternatives,
        candidates=tuple(
            candidate(asset, score if asset == primary else 0.8)
            for asset in all_assets
        ),
        camera=CameraPlan(
            preset=CameraPreset.STATIC,
            focus=NormalizedPoint(x=0.5, y=0.5),
        ),
        transition=TransitionPreset.CUT,
        locked=locked,
    )


def test_editorial_findings_and_bounded_repairs_respect_locks() -> None:
    repeated = "page_" + "a" * 64
    alternatives = tuple("page_" + letter * 64 for letter in ("b", "c", "d", "e"))
    plan = StoryboardPlan(
        scope=SearchScope(series=("Series",)),
        scenes=tuple(
            scene(
                index,
                repeated,
                (alternatives[index - 1],),
                locked=index == 1,
            )
            for index in range(1, 5)
        ),
    )
    report = StoryboardQualityEvaluator().evaluate(plan)
    categories = {finding.category for finding in report.findings}
    assert FindingCategory.DUPLICATE_ASSET in categories
    assert FindingCategory.WEAK_MATCH in categories
    assert FindingCategory.STATIC_RUN in categories

    planner = RepairPlanner()
    repairs = planner.plan(report, plan, pass_index=1, maximum_passes=2)
    assert "scene_0001" in repairs.blocked_scene_ids
    assert all(action.scene_id != "scene_0001" for action in repairs.actions)
    repaired = planner.apply(plan, repairs)
    assert repaired.scenes[0] == plan.scenes[0]
    assert any(
        current.primary_asset != previous.primary_asset
        for previous, current in zip(plan.scenes[1:], repaired.scenes[1:], strict=True)
    )
    assert planner.plan(report, plan, pass_index=3, maximum_passes=2).actions == ()


def test_render_quality_finds_stream_and_duration_problems(tmp_path: Path) -> None:
    output = tmp_path / "render.mp4"
    output.write_bytes(b"not-a-real-video")
    result = RenderResult(
        output_path=str(output),
        output_sha256="a" * 64,
        ffmpeg_version="fixture",
        command=("ffmpeg",),
        probe={
            "streams": [{"codec_type": "video"}],
            "format": {"duration": "3.5"},
        },
        source_hashes={},
        duration_seconds=4,
    )
    spec = ManualVideoSpec(
        scenes=(
            Scene(
                id="scene_1",
                image_path=str(tmp_path / "image.png"),
                duration_seconds=4,
            ),
        ),
        narration_path=str(tmp_path / "narration.wav"),
        profile=RenderProfile(width=320, height=240, fps=12),
    )
    report = RenderQualityEvaluator(ffmpeg="").evaluate(result, spec)
    categories = {finding.category for finding in report.findings}
    assert FindingCategory.STREAM_LAYOUT in categories
    assert FindingCategory.DURATION_MISMATCH in categories
