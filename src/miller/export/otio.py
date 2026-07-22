"""Optional OpenTimelineIO export and referenced-media packaging."""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import opentimelineio as otio  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field

from ..artifacts import sha256_file
from ..storyboard import StoryboardPlan


class ExportModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class PackagedMedia(ExportModel):
    source_path: str
    packaged_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class TimelineExportResult(ExportModel):
    timeline_path: str
    media: tuple[PackagedMedia, ...]
    fps: float = Field(gt=0)
    scene_count: int = Field(ge=1)


class TimelineExporter:
    def __init__(self, *, fps: float = 30.0) -> None:
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.fps = fps

    def build(
        self,
        storyboard: StoryboardPlan,
        asset_paths: Mapping[str, Path | str],
        *,
        narration_path: Path | str | None = None,
        music_path: Path | str | None = None,
        subtitle_path: Path | str | None = None,
    ) -> Any:
        timeline = otio.schema.Timeline(name="Miller Storyboard")
        video_track = otio.schema.Track(name="Comic Visuals", kind=otio.schema.TrackKind.Video)
        for scene in storyboard.scenes:
            source = asset_paths.get(scene.primary_asset)
            if source is None:
                raise KeyError(f"missing asset path for {scene.primary_asset}")
            duration = otio.opentime.RationalTime(
                round((scene.end - scene.start) * self.fps),
                self.fps,
            )
            clip = otio.schema.Clip(
                name=scene.id,
                media_reference=otio.schema.ExternalReference(
                    target_url=Path(source).expanduser().resolve().as_uri(),
                    available_range=otio.opentime.TimeRange(
                        start_time=otio.opentime.RationalTime(0, self.fps),
                        duration=duration,
                    ),
                ),
                source_range=otio.opentime.TimeRange(
                    start_time=otio.opentime.RationalTime(0, self.fps),
                    duration=duration,
                ),
                metadata={
                    "miller": {
                        "scene_id": scene.id,
                        "beat_id": scene.beat_id,
                        "narration": scene.narration,
                        "intent": scene.intent,
                        "mood": scene.mood,
                        "primary_asset": scene.primary_asset,
                        "alternatives": list(scene.alternatives),
                        "camera": scene.camera.model_dump(mode="json"),
                        "transition": scene.transition.value,
                        "music_state": scene.music_state,
                        "locked": scene.locked,
                    }
                },
            )
            video_track.append(clip)
        timeline.tracks.append(video_track)
        self._append_audio_track(timeline, "Narration", narration_path, storyboard)
        self._append_audio_track(timeline, "Music", music_path, storyboard)
        if subtitle_path is not None:
            timeline.metadata["miller_subtitles"] = str(
                Path(subtitle_path).expanduser().resolve()
            )
        timeline.metadata["miller_schema_version"] = storyboard.schema_version
        return timeline

    def export(
        self,
        storyboard: StoryboardPlan,
        asset_paths: Mapping[str, Path | str],
        output: Path | str,
        *,
        narration_path: Path | str | None = None,
        music_path: Path | str | None = None,
        subtitle_path: Path | str | None = None,
    ) -> TimelineExportResult:
        target = Path(output).expanduser().resolve()
        if target.exists():
            raise FileExistsError(f"timeline output already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        timeline = self.build(
            storyboard,
            asset_paths,
            narration_path=narration_path,
            music_path=music_path,
            subtitle_path=subtitle_path,
        )
        otio.adapters.write_to_file(timeline, str(target))
        return TimelineExportResult(
            timeline_path=str(target),
            media=(),
            fps=self.fps,
            scene_count=len(storyboard.scenes),
        )

    def export_package(
        self,
        storyboard: StoryboardPlan,
        asset_paths: Mapping[str, Path | str],
        directory: Path | str,
        *,
        narration_path: Path | str | None = None,
        music_path: Path | str | None = None,
        subtitle_path: Path | str | None = None,
    ) -> TimelineExportResult:
        root = Path(directory).expanduser().resolve()
        media_root = root / "media"
        media_root.mkdir(parents=True, exist_ok=True)
        packaged: list[PackagedMedia] = []
        rewritten_assets: dict[str, Path] = {}
        for asset_id, source_value in asset_paths.items():
            item = self._package_file(Path(source_value), media_root, asset_id)
            packaged.append(item)
            rewritten_assets[asset_id] = Path(item.packaged_path)
        packaged_narration = self._optional_package(
            narration_path, media_root, "narration", packaged
        )
        packaged_music = self._optional_package(music_path, media_root, "music", packaged)
        packaged_subtitle = self._optional_package(
            subtitle_path, media_root, "captions", packaged
        )
        timeline_path = root / "timeline.otio"
        self.export(
            storyboard,
            rewritten_assets,
            timeline_path,
            narration_path=packaged_narration,
            music_path=packaged_music,
            subtitle_path=packaged_subtitle,
        )
        return TimelineExportResult(
            timeline_path=str(timeline_path),
            media=tuple(packaged),
            fps=self.fps,
            scene_count=len(storyboard.scenes),
        )

    def _append_audio_track(
        self,
        timeline: Any,
        name: str,
        source: Path | str | None,
        storyboard: StoryboardPlan,
    ) -> None:
        if source is None:
            return
        duration_seconds = storyboard.scenes[-1].end - storyboard.scenes[0].start
        duration = otio.opentime.RationalTime(round(duration_seconds * self.fps), self.fps)
        track = otio.schema.Track(name=name, kind=otio.schema.TrackKind.Audio)
        track.append(
            otio.schema.Clip(
                name=name,
                media_reference=otio.schema.ExternalReference(
                    target_url=Path(source).expanduser().resolve().as_uri()
                ),
                source_range=otio.opentime.TimeRange(
                    start_time=otio.opentime.RationalTime(0, self.fps),
                    duration=duration,
                ),
            )
        )
        timeline.tracks.append(track)

    @staticmethod
    def _optional_package(
        source: Path | str | None,
        media_root: Path,
        label: str,
        records: list[PackagedMedia],
    ) -> Path | None:
        if source is None:
            return None
        item = TimelineExporter._package_file(Path(source), media_root, label)
        records.append(item)
        return Path(item.packaged_path)

    @staticmethod
    def _package_file(source: Path, media_root: Path, label: str) -> PackagedMedia:
        resolved = source.expanduser().resolve()
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        digest = sha256_file(resolved)
        safe_label = "".join(character if character.isalnum() else "_" for character in label)
        target = media_root / f"{safe_label}_{digest[:12]}{resolved.suffix.casefold()}"
        if target.exists():
            if sha256_file(target) != digest:
                raise RuntimeError(f"packaged media collision: {target}")
        else:
            shutil.copyfile(resolved, target)
        return PackagedMedia(
            source_path=str(resolved),
            packaged_path=str(target),
            sha256=digest,
        )
