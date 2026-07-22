import io
import math
import shutil
import struct
import wave
from pathlib import Path

import pytest
from PIL import Image

from miller.artifacts import sha256_file
from miller.video import FFmpegRenderer, ManualVideoSpec, MotionPreset, RenderProfile, Scene


def write_image(path: Path, color: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (640, 360), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    path.write_bytes(buffer.getvalue())


def write_tone(path: Path, duration: float = 1.0, rate: int = 16_000) -> None:
    frames = int(duration * rate)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        samples = (
            struct.pack("<h", int(4000 * math.sin(2 * math.pi * 440 * index / rate)))
            for index in range(frames)
        )
        output.writeframes(b"".join(samples))


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="FFmpeg unavailable",
)
def test_manual_video_render_is_reproducible_at_decoded_frame_level(tmp_path: Path) -> None:
    first_image = tmp_path / "first.png"
    second_image = tmp_path / "second.png"
    narration = tmp_path / "narration.wav"
    write_image(first_image, (30, 50, 90))
    write_image(second_image, (100, 30, 20))
    write_tone(narration)
    source_hashes = {
        first_image: sha256_file(first_image),
        second_image: sha256_file(second_image),
        narration: sha256_file(narration),
    }

    spec = ManualVideoSpec(
        scenes=(
            Scene(
                id="scene_1",
                image_path=str(first_image),
                duration_seconds=0.5,
                motion=MotionPreset.STATIC,
            ),
            Scene(
                id="scene_2",
                image_path=str(second_image),
                duration_seconds=0.5,
                motion=MotionPreset.SLOW_PUSH,
            ),
        ),
        narration_path=str(narration),
        profile=RenderProfile(width=320, height=240, fps=12, threads=1),
    )
    renderer = FFmpegRenderer()
    first = renderer.render(spec, tmp_path / "first.mp4")
    second = renderer.render(spec, tmp_path / "second.mp4")

    video_streams = [stream for stream in first.probe["streams"] if stream["codec_type"] == "video"]
    audio_streams = [stream for stream in first.probe["streams"] if stream["codec_type"] == "audio"]
    assert len(video_streams) == 1
    assert len(audio_streams) == 1
    assert int(video_streams[0]["width"]) == 320
    assert int(video_streams[0]["height"]) == 240
    assert renderer.frame_md5(first.output_path) == renderer.frame_md5(second.output_path)
    assert {path: sha256_file(path) for path in source_hashes} == source_hashes
