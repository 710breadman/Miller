"""Convert Miller storyboards into native render specifications."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..storyboard import CameraPreset, StoryboardPlan, TransitionPreset
from .models import ManualVideoSpec, MotionPreset, RenderProfile, Scene, TransitionEffect

_MOTION = {
    CameraPreset.STATIC: MotionPreset.STATIC,
    CameraPreset.SLOW_PUSH: MotionPreset.SLOW_PUSH,
    CameraPreset.SLOW_PULL: MotionPreset.SLOW_PULL,
    CameraPreset.PAN_LEFT: MotionPreset.PAN_LEFT,
    CameraPreset.PAN_RIGHT: MotionPreset.PAN_RIGHT,
}

_TRANSITION = {
    TransitionPreset.CUT: TransitionEffect.CUT,
    TransitionPreset.CROSSFADE: TransitionEffect.CROSSFADE,
    TransitionPreset.DIP_BLACK: TransitionEffect.DIP_BLACK,
}


def storyboard_to_video_spec(
    plan: StoryboardPlan,
    asset_paths: Mapping[str, Path | str],
    *,
    narration_path: Path | str | None = None,
    music_path: Path | str | None = None,
    subtitle_path: Path | str | None = None,
    profile: RenderProfile | None = None,
) -> ManualVideoSpec:
    scenes: list[Scene] = []
    for index, storyboard_scene in enumerate(plan.scenes):
        if storyboard_scene.primary_asset not in asset_paths:
            raise KeyError(f"missing path for asset: {storyboard_scene.primary_asset}")
        next_transition = (
            plan.scenes[index + 1].transition
            if index + 1 < len(plan.scenes)
            else TransitionPreset.CUT
        )
        scenes.append(
            Scene(
                id=storyboard_scene.id,
                image_path=str(asset_paths[storyboard_scene.primary_asset]),
                duration_seconds=storyboard_scene.end - storyboard_scene.start,
                motion=_MOTION[storyboard_scene.camera.preset],
                focus_x=storyboard_scene.camera.focus.x,
                focus_y=storyboard_scene.camera.focus.y,
                transition_to_next=_TRANSITION[next_transition],
            )
        )
    return ManualVideoSpec(
        scenes=tuple(scenes),
        narration_path=str(narration_path) if narration_path is not None else None,
        music_path=str(music_path) if music_path is not None else None,
        subtitle_path=str(subtitle_path) if subtitle_path is not None else None,
        profile=profile or RenderProfile(),
    )
