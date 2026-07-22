"""Content-addressed scene clips and scoped partial rerendering."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..artifacts import canonical_json_bytes, sha256_bytes, sha256_file
from .ffmpeg import FFmpegRenderer, RenderFailure, RenderResult
from .models import ManualVideoSpec, Scene, TransitionEffect


class SceneClip(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scene_id: str = Field(min_length=1)
    fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    duration_seconds: float = Field(gt=0.0)
    cache_hit: bool


class SegmentedRenderResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    render: RenderResult
    clips: tuple[SceneClip, ...]
    warnings: tuple[str, ...] = ()


class SegmentedFFmpegRenderer:
    """Cache scene clips and assemble a hard-cut final render."""

    def __init__(
        self,
        workspace: Path | str,
        ffmpeg: str | None = None,
        ffprobe: str | None = None,
    ) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.renderer = FFmpegRenderer(ffmpeg=ffmpeg, ffprobe=ffprobe)
        self.ffmpeg = self.renderer.ffmpeg

    def render(self, spec: ManualVideoSpec, output: Path | str) -> SegmentedRenderResult:
        clips = tuple(self._scene_clip(scene, spec) for scene in spec.scenes)
        output_path = Path(output).expanduser().resolve()
        if output_path.exists():
            raise FileExistsError(f"render output already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        warnings = tuple(
            "segmented backend uses hard cuts; rich transition retained only in full renderer"
            for scene in spec.scenes[:-1]
            if scene.transition_to_next != TransitionEffect.CUT
        )
        with tempfile.TemporaryDirectory(prefix="miller-segments-", dir=self._tmp_root()) as temp:
            temporary_root = Path(temp)
            video_only = temporary_root / "video-only.mp4"
            self._concat(clips, video_only)
            command = self._mux_command(spec, video_only, output_path)
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=max(120, int(sum(scene.duration_seconds for scene in spec.scenes) * 8)),
            )
            if result.returncode != 0:
                output_path.unlink(missing_ok=True)
                raise RenderFailure(
                    f"segmented final assembly failed: {result.stderr[-4000:]}"
                )
        total_duration = sum(scene.duration_seconds for scene in spec.scenes)
        render = RenderResult(
            output_path=str(output_path),
            output_sha256=sha256_file(output_path),
            ffmpeg_version=self.renderer.version(),
            command=tuple(command),
            probe=self.renderer.probe(output_path),
            source_hashes=self._source_hashes(spec),
            duration_seconds=total_duration,
        )
        return SegmentedRenderResult(render=render, clips=clips, warnings=warnings)

    def _scene_clip(self, scene: Scene, spec: ManualVideoSpec) -> SceneClip:
        source_hash = sha256_file(Path(scene.image_path))
        fingerprint_digest = sha256_bytes(
            canonical_json_bytes(
                {
                    "scene": scene.model_dump(mode="json"),
                    "source_sha256": source_hash,
                    "profile": spec.profile.model_dump(mode="json"),
                    "backend": "segmented-scene-v1",
                }
            )
        )
        target = (
            self.workspace
            / "cache"
            / "video"
            / "scenes"
            / fingerprint_digest[:2]
            / f"{fingerprint_digest}.mp4"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        self._assert_managed(target)
        cache_hit = target.is_file() and target.stat().st_size > 0
        if not cache_hit:
            temporary = target.with_suffix(".partial.mp4")
            temporary.unlink(missing_ok=True)
            isolated = scene.model_copy(
                update={
                    "transition_to_next": TransitionEffect.CUT,
                }
            )
            self.renderer.render(
                ManualVideoSpec(scenes=(isolated,), profile=spec.profile),
                temporary,
            )
            os.replace(temporary, target)
        return SceneClip(
            scene_id=scene.id,
            fingerprint=f"sha256:{fingerprint_digest}",
            path=str(target),
            sha256=sha256_file(target),
            duration_seconds=scene.duration_seconds,
            cache_hit=cache_hit,
        )

    def _concat(self, clips: tuple[SceneClip, ...], output: Path) -> None:
        list_path = output.with_suffix(".concat.txt")
        lines = [f"file '{self._concat_escape(Path(clip.path))}'" for clip in clips]
        list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = subprocess.run(
            [
                self.ffmpeg,
                "-hide_banner",
                "-y",
                "-v",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                "-map_metadata",
                "-1",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        if result.returncode != 0:
            raise RenderFailure(f"scene concatenation failed: {result.stderr[-3000:]}")

    def _mux_command(
        self,
        spec: ManualVideoSpec,
        video_only: Path,
        output: Path,
    ) -> list[str]:
        total_duration = sum(scene.duration_seconds for scene in spec.scenes)
        command = [self.ffmpeg, "-hide_banner", "-y", "-v", "error", "-i", str(video_only)]
        next_input = 1
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
        output_audio = self.renderer._audio_filters(  # noqa: SLF001
            spec,
            narration_index,
            music_index,
            total_duration,
            filters,
        )
        if filters:
            command.extend(["-filter_complex", ";".join(filters)])
        command.extend(["-map", "0:v:0", "-c:v", "copy"])
        if output_audio is not None:
            command.extend(
                [
                    "-map",
                    output_audio,
                    "-c:a",
                    "aac",
                    "-b:a",
                    spec.profile.audio_bitrate,
                ]
            )
        if subtitle_index is not None:
            command.extend(["-map", f"{subtitle_index}:s:0", "-c:s", "mov_text"])
        command.extend(
            [
                "-map_metadata",
                "-1",
                "-movflags",
                "+faststart",
                "-t",
                self.renderer._number(total_duration),  # noqa: SLF001
                str(output),
            ]
        )
        return command

    def _source_hashes(self, spec: ManualVideoSpec) -> dict[str, str]:
        paths = [Path(scene.image_path) for scene in spec.scenes]
        paths.extend(
            Path(path)
            for path in (spec.narration_path, spec.music_path, spec.subtitle_path)
            if path is not None
        )
        return {str(path): sha256_file(path) for path in paths}

    def _tmp_root(self) -> str:
        root = self.workspace / "tmp"
        root.mkdir(parents=True, exist_ok=True)
        self._assert_managed(root)
        return str(root)

    def _assert_managed(self, path: Path) -> None:
        try:
            path.resolve().relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError(f"segmented render path escapes workspace: {path}") from exc

    @staticmethod
    def _concat_escape(path: Path) -> str:
        return str(path.resolve()).replace("'", "'\\''")
