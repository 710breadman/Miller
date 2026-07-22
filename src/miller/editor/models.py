"""Typed editor commands and snapshots."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..analysis import NormalizedPoint
from ..storyboard import CameraPreset, StoryboardPlan, TransitionPreset


class EditorModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class StoryboardSnapshot(EditorModel):
    revision: int = Field(ge=1)
    storyboard: StoryboardPlan


class SaveStoryboardCommand(EditorModel):
    expected_revision: int = Field(ge=0)
    storyboard: StoryboardPlan


class SceneCommand(EditorModel):
    expected_revision: int = Field(ge=1)
    scene_id: str = Field(pattern=r"^scene_[0-9]{4}$")


class ReplaceAssetCommand(SceneCommand):
    asset_id: str = Field(min_length=1)


class SetMotionCommand(SceneCommand):
    preset: CameraPreset


class SetFocusCommand(SceneCommand):
    focus: NormalizedPoint


class SetTransitionCommand(SceneCommand):
    transition: TransitionPreset


class SetLockCommand(SceneCommand):
    locked: bool


class SetMusicCommand(SceneCommand):
    music_state: str = Field(min_length=1, max_length=100)
