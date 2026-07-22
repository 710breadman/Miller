from pathlib import Path

import opentimelineio as otio

from miller.analysis import NormalizedPoint
from miller.export import TimelineExporter
from miller.storyboard import (
    CameraPlan,
    CameraPreset,
    SceneCandidate,
    SceneScore,
    SearchScope,
    StoryboardPlan,
    StoryboardScene,
)


def plan() -> StoryboardPlan:
    score = SceneScore(
        lexical=1,
        character=1,
        theme=1,
        continuity=1,
        quality=1,
        reuse_penalty=0,
        total=1,
    )
    candidate = SceneCandidate(asset_id="page_a", source_locator="a.png", score=score)
    return StoryboardPlan(
        scope=SearchScope(),
        scenes=(
            StoryboardScene(
                id="scene_0001",
                beat_id="beat_0001",
                start=0,
                end=2,
                narration="Narration",
                intent="Intent",
                primary_asset="page_a",
                candidates=(candidate,),
                camera=CameraPlan(
                    preset=CameraPreset.SLOW_PUSH,
                    focus=NormalizedPoint(x=0.5, y=0.5),
                ),
            ),
        ),
    )


def test_otio_round_trip_and_media_package(tmp_path: Path) -> None:
    image = tmp_path / "page.png"
    image.write_bytes(b"fixture image bytes")
    narration = tmp_path / "narration.wav"
    narration.write_bytes(b"fixture narration bytes")

    result = TimelineExporter(fps=24).export_package(
        plan(),
        {"page_a": image},
        tmp_path / "export",
        narration_path=narration,
    )
    timeline = otio.adapters.read_from_file(result.timeline_path)
    assert len(timeline.tracks) == 2
    assert timeline.tracks[0][0].name == "scene_0001"
    assert timeline.tracks[0][0].metadata["miller"]["primary_asset"] == "page_a"
    assert len(result.media) == 2
    assert all(Path(item.packaged_path).is_file() for item in result.media)
