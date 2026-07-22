import math
import shutil
import struct
import wave
from pathlib import Path

import pytest
from PIL import Image

from miller.analysis import NormalizedPoint
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
from miller.video import (
    FFmpegRenderer,
    ManualVideoSpec,
    MotionPreset,
    RenderProfile,
    Scene,
    TransitionEffect,
    storyboard_to_video_spec,
)


def write_tone(path: Path, frequency: float, duration: float, rate: int = 16_000) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        samples = (
            struct.pack(
                "<h",
                int(3500 * math.sin(2 * math.pi * frequency * index / rate)),
            )
            for index in range(int(duration * rate))
        )
        output.writeframes(b"".join(samples))


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="FFmpeg unavailable",
)
def test_transition_music_ducking_and_subtitle_stream(tmp_path: Path) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGB", (640, 360), (20, 40, 80)).save(first)
    Image.new("RGB", (640, 360), (110, 30, 20)).save(second)
    narration = tmp_path / "narration.wav"
    music = tmp_path / "music.wav"
    write_tone(narration, 440, 1.5)
    write_tone(music, 220, 0.8)
    subtitles = tmp_path / "captions.srt"
    subtitles.write_text(
        "1\n00:00:00,000 --> 00:00:00,750\nFirst scene\n\n"
        "2\n00:00:00,750 --> 00:00:01,500\nSecond scene\n",
        encoding="utf-8",
    )
    spec = ManualVideoSpec(
        scenes=(
            Scene(
                id="scene_1",
                image_path=str(first),
                duration_seconds=0.75,
                motion=MotionPreset.PAN_RIGHT,
                transition_to_next=TransitionEffect.CROSSFADE,
                transition_duration_seconds=0.2,
            ),
            Scene(
                id="scene_2",
                image_path=str(second),
                duration_seconds=0.75,
                motion=MotionPreset.SLOW_PULL,
            ),
        ),
        narration_path=str(narration),
        music_path=str(music),
        subtitle_path=str(subtitles),
        profile=RenderProfile(width=320, height=240, fps=12, threads=1),
    )
    result = FFmpegRenderer().render(spec, tmp_path / "advanced.mp4")
    stream_types = [stream["codec_type"] for stream in result.probe["streams"]]
    assert stream_types.count("video") == 1
    assert stream_types.count("audio") == 1
    assert stream_types.count("subtitle") == 1
    duration = float(result.probe["format"]["duration"])
    assert duration == pytest.approx(1.5, abs=0.12)


def test_storyboard_conversion_preserves_timing_motion_and_assets(tmp_path: Path) -> None:
    asset_a = "page_" + "a" * 64
    asset_b = "page_" + "b" * 64
    candidate_score = SceneScore(
        lexical=1,
        character=1,
        theme=1,
        continuity=1,
        quality=1,
        reuse_penalty=0,
        total=1,
    )
    plan = StoryboardPlan(
        scope=SearchScope(characters=("Hero",)),
        scenes=(
            StoryboardScene(
                id="scene_0001",
                beat_id="beat_0001",
                start=0,
                end=2,
                narration="A hero rises.",
                intent="A hero rises.",
                primary_asset=asset_a,
                candidates=(
                    SceneCandidate(
                        asset_id=asset_a,
                        source_locator="Series/1/a.png",
                        score=candidate_score,
                    ),
                ),
                camera=CameraPlan(
                    preset=CameraPreset.PAN_LEFT,
                    focus=NormalizedPoint(x=0.4, y=0.6),
                ),
                transition=TransitionPreset.CUT,
            ),
            StoryboardScene(
                id="scene_0002",
                beat_id="beat_0002",
                start=2,
                end=5,
                narration="The city answers.",
                intent="The city answers.",
                primary_asset=asset_b,
                candidates=(
                    SceneCandidate(
                        asset_id=asset_b,
                        source_locator="Series/1/b.png",
                        score=candidate_score,
                    ),
                ),
                camera=CameraPlan(preset=CameraPreset.SLOW_PUSH),
                transition=TransitionPreset.DIP_BLACK,
            ),
        ),
    )
    first = tmp_path / "a.png"
    second = tmp_path / "b.png"
    Image.new("RGB", (20, 20), "black").save(first)
    Image.new("RGB", (20, 20), "white").save(second)
    spec = storyboard_to_video_spec(plan, {asset_a: first, asset_b: second})
    assert [scene.duration_seconds for scene in spec.scenes] == [2, 3]
    assert spec.scenes[0].motion == MotionPreset.PAN_LEFT
    assert spec.scenes[0].transition_to_next == TransitionEffect.DIP_BLACK
    assert spec.scenes[0].focus_x == 0.4
