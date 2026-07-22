"""Native FFmpeg renderer with deterministic scene, transition, and audio manifests."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..artifacts import sha256_file
from .models import ManualVideoSpec, MotionPreset, Scene, TransitionEffect


class RenderFailure(RuntimeError):
    """Raised when FFmpeg or FFprobe fails."""


class RenderResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    output_path: str
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    ffmpeg_version: str
    command: tuple[str, ...]
    probe: dict[str, Any]
    source_hashes: dict[str, str]
    duration_seconds: float = Field(gt=0.0)


class FFmpegRenderer:
    def __init__(self, ffmpeg: str | None = None, ffprobe: str | None = None) -> None:
        self.ffmpeg = ffmpeg or shutil.which("ffmpeg") or ""
        self.ffprobe = ffprobe or shutil.which("ffprobe") or ""
        if not self.ffmpeg or not self.ffprobe:
            raise RenderFailure("FFmpeg and FFprobe must both be installed")

    def render(self, spec: ManualVideoSpec, output: Path | str) -> RenderResult:
        output_path = Path(output).expanduser().resolve()
        if output_path.exists():
            raise FileExistsError(f"render output already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        source_hashes = self._validate_sources(spec)
        command = self._build_command(spec, output_path)
        total_duration = sum(scene.duration_seconds for scene in spec.scenes)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=max(120, int(total_duration * 12)),
        )
        if result.returncode != 0:
            output_path.unlink(missing_ok=True)
            raise RenderFailure(
                f"FFmpeg failed with exit {result.returncode}: {result.stderr[-4000:]}"
            )
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise RenderFailure("FFmpeg reported success but produced no output")
        probe = self.probe(output_path)
        return RenderResult(
            output_path=str(output_path),
            output_sha256=sha256_file(output_path),
            ffmpeg_version=self.version(),
            command=tuple(command),
            probe=probe,
            source_hashes=source_hashes,
            duration_seconds=total_duration,
        )

    def version(self) -> str:
        result = subprocess.run(
            [self.ffmpeg, "-version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if result.returncode != 0:
            raise RenderFailure("unable to query FFmpeg version")
        return result.stdout.splitlines()[0].strip()

    def probe(self, path: Path | str) -> dict[str, Any]:
        result = subprocess.run(
            [
                self.ffprobe,
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 0:
            raise RenderFailure(f"FFprobe failed: {result.stderr[-2000:]}")
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RenderFailure("FFprobe returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise RenderFailure("FFprobe result must be an object")
        return value

    def frame_md5(self, path: Path | str) -> str:
        """Return decoded-frame checksums for golden tests."""

        result = subprocess.run(
            [
                self.ffmpeg,
                "-v",
                "error",
                "-i",
                str(path),
                "-map",
                "0:v:0",
                "-f",
                "framemd5",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        if result.returncode != 0:
            raise RenderFailure(f"frame checksum failed: {result.stderr[-2000:]}")
        return result.stdout

    def _validate_sources(self, spec: ManualVideoSpec) -> dict[str, str]:
        hashes: dict[str, str] = {}
        paths = [Path(scene.image_path) for scene in spec.scenes]
        paths.extend(
            Path(path)
            for path in (spec.narration_path, spec.music_path, spec.subtitle_path)
            if path is not None
        )
        for path in paths:
            if not path.is_file():
                raise RenderFailure(f"render input does not exist: {path}")
            hashes[str(path)] = sha256_file(path)
        return hashes

    def _build_command(self, spec: ManualVideoSpec, output: Path) -> list[str]:
        profile = spec.profile
        total_duration = sum(scene.duration_seconds for scene in spec.scenes)
        boundary_durations = [
            self._transition_duration(scene, profile.fps)
            for scene in spec.scenes[:-1]
        ]
        command = [self.ffmpeg, "-hide_banner", "-y", "-v", "error"]
        for index, scene in enumerate(spec.scenes):
            extra = boundary_durations[index] if index < len(boundary_durations) else 0.0
            command.extend(
                [
                    "-framerate",
                    str(profile.fps),
                    "-loop",
                    "1",
                    "-t",
                    self._number(scene.duration_seconds + extra),
                    "-i",
                    scene.image_path,
                ]
            )
        next_input = len(spec.scenes)
        narration_index: int | None = None
        music_index: int | None = None
        subtitle_index: int | None = None
        if spec.narration_path:
            narration_index = next_input
            next_input += 1
            command.extend(["-i", spec.narration_path])
        if spec.music_path:
            music_index = next_input
            next_input += 1
            command.extend(["-stream_loop", "-1", "-i", spec.music_path])
        if spec.subtitle_path:
            subtitle_index = next_input
            command.extend(["-i", spec.subtitle_path])

        filters: list[str] = []
        video_labels: list[str] = []
        for index, scene in enumerate(spec.scenes):
            extra = boundary_durations[index] if index < len(boundary_durations) else 0.0
            label = f"v{index}"
            video_labels.append(label)
            filters.append(
                self._scene_filter(
                    index,
                    label,
                    scene,
                    spec,
                    scene.duration_seconds + extra,
                )
            )
        output_video = self._join_video_filters(
            spec,
            video_labels,
            boundary_durations,
            filters,
        )
        output_audio = self._audio_filters(
            spec,
            narration_index,
            music_index,
            total_duration,
            filters,
        )
        command.extend(["-filter_complex", ";".join(filters), "-map", output_video])
        if output_audio is not None:
            command.extend(["-map", output_audio, "-c:a", "aac", "-b:a", profile.audio_bitrate])
        if subtitle_index is not None:
            command.extend(["-map", f"{subtitle_index}:s:0", "-c:s", "mov_text"])
        command.extend(
            [
                "-c:v",
                profile.codec,
                "-preset",
                profile.preset,
                "-crf",
                str(profile.crf),
                "-pix_fmt",
                "yuv420p",
                "-threads",
                str(profile.threads),
                "-map_metadata",
                "-1",
                "-movflags",
                "+faststart",
                "-t",
                self._number(total_duration),
                str(output),
            ]
        )
        return command

    def _join_video_filters(
        self,
        spec: ManualVideoSpec,
        labels: list[str],
        boundary_durations: list[float],
        filters: list[str],
    ) -> str:
        if len(labels) == 1:
            return f"[{labels[0]}]"
        previous = labels[0]
        cumulative = spec.scenes[0].duration_seconds
        for boundary_index, next_label in enumerate(labels[1:]):
            scene = spec.scenes[boundary_index]
            transition = {
                TransitionEffect.CUT: "fade",
                TransitionEffect.CROSSFADE: "fade",
                TransitionEffect.DIP_BLACK: "fadeblack",
            }[scene.transition_to_next]
            duration = boundary_durations[boundary_index]
            output_label = f"vx{boundary_index + 1}"
            filters.append(
                f"[{previous}][{next_label}]xfade=transition={transition}:"
                f"duration={self._number(duration)}:offset={self._number(cumulative)}"
                f"[{output_label}]"
            )
            previous = output_label
            cumulative += spec.scenes[boundary_index + 1].duration_seconds
        return f"[{previous}]"

    def _audio_filters(
        self,
        spec: ManualVideoSpec,
        narration_index: int | None,
        music_index: int | None,
        total_duration: float,
        filters: list[str],
    ) -> str | None:
        if narration_index is None and music_index is None:
            return None
        if narration_index is not None and music_index is not None:
            filters.extend(
                [
                    f"[{narration_index}:a]aresample=48000,"
                    f"volume={spec.narration_volume:.6f},asplit=2[narr][side]",
                    f"[{music_index}:a]aresample=48000,"
                    f"atrim=duration={self._number(total_duration)},"
                    f"volume={spec.music_volume:.6f}[music]",
                    "[music][side]sidechaincompress="
                    "threshold=0.02:ratio=8:attack=20:release=500[ducked]",
                    "[narr][ducked]amix=inputs=2:duration=first:normalize=0[aout]",
                ]
            )
            return "[aout]"
        if narration_index is not None:
            filters.append(
                f"[{narration_index}:a]aresample=48000,"
                f"volume={spec.narration_volume:.6f}[aout]"
            )
            return "[aout]"
        assert music_index is not None
        filters.append(
            f"[{music_index}:a]aresample=48000,"
            f"atrim=duration={self._number(total_duration)},"
            f"volume={spec.music_volume:.6f}[aout]"
        )
        return "[aout]"

    def _scene_filter(
        self,
        input_index: int,
        label: str,
        scene: Scene,
        spec: ManualVideoSpec,
        render_duration: float,
    ) -> str:
        profile = spec.profile
        width = profile.width
        height = profile.height
        common = (
            f"[{input_index}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1,"
        )
        total_frames = max(1, round(render_duration * profile.fps))
        if scene.motion == MotionPreset.STATIC:
            motion = ""
        elif scene.motion in {MotionPreset.SLOW_PUSH, MotionPreset.SLOW_PULL}:
            if scene.motion == MotionPreset.SLOW_PUSH:
                zoom = f"1+0.08*on/{total_frames}"
            else:
                zoom = f"1.08-0.08*on/{total_frames}"
            x = f"(iw-iw/zoom)*{scene.focus_x:.6f}"
            y = f"(ih-ih/zoom)*{scene.focus_y:.6f}"
            motion = (
                f"zoompan=z='{zoom}':x='{x}':y='{y}':d=1:"
                f"s={width}x{height}:fps={profile.fps},"
            )
        else:
            direction = "on" if scene.motion == MotionPreset.PAN_RIGHT else f"{total_frames}-on"
            x = f"(iw-iw/1.05)*({direction})/{total_frames}"
            y = f"(ih-ih/1.05)*{scene.focus_y:.6f}"
            motion = (
                f"zoompan=z='1.05':x='{x}':y='{y}':d=1:"
                f"s={width}x{height}:fps={profile.fps},"
            )
        return f"{common}{motion}format=yuv420p[{label}]"

    @staticmethod
    def _transition_duration(scene: Scene, fps: int) -> float:
        if scene.transition_to_next == TransitionEffect.CUT:
            return 1 / fps
        return min(scene.transition_duration_seconds, scene.duration_seconds / 2)

    @staticmethod
    def _number(value: float) -> str:
        return f"{value:.6f}".rstrip("0").rstrip(".")
