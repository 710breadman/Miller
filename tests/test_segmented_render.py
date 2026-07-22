import shutil
from pathlib import Path

import pytest
from PIL import Image

from miller.video import (
    ManualVideoSpec,
    MotionPreset,
    RenderProfile,
    Scene,
    SegmentedFFmpegRenderer,
)


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="FFmpeg unavailable",
)
def test_segmented_renderer_reuses_only_unchanged_scene_clips(tmp_path: Path) -> None:
    first_image = tmp_path / "first.png"
    second_image = tmp_path / "second.png"
    Image.new("RGB", (640, 360), "navy").save(first_image)
    Image.new("RGB", (640, 360), "maroon").save(second_image)
    spec = ManualVideoSpec(
        scenes=(
            Scene(
                id="scene_1",
                image_path=str(first_image),
                duration_seconds=0.5,
                motion=MotionPreset.SLOW_PUSH,
            ),
            Scene(
                id="scene_2",
                image_path=str(second_image),
                duration_seconds=0.5,
                motion=MotionPreset.PAN_LEFT,
            ),
        ),
        profile=RenderProfile(width=320, height=240, fps=12, threads=1),
    )
    renderer = SegmentedFFmpegRenderer(tmp_path / "workspace")
    first = renderer.render(spec, tmp_path / "first.mp4")
    assert [clip.cache_hit for clip in first.clips] == [False, False]

    second = renderer.render(spec, tmp_path / "second.mp4")
    assert [clip.cache_hit for clip in second.clips] == [True, True]
    first_clip_hash = second.clips[0].sha256

    Image.new("RGB", (640, 360), "darkgreen").save(second_image)
    changed = renderer.render(spec, tmp_path / "changed.mp4")
    assert [clip.cache_hit for clip in changed.clips] == [True, False]
    assert changed.clips[0].sha256 == first_clip_hash
    assert changed.clips[1].sha256 != second.clips[1].sha256
    assert float(changed.render.probe["format"]["duration"]) == pytest.approx(1.0, abs=0.12)
