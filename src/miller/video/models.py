"""Typed contracts for native video rendering."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class VideoModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MotionPreset(StrEnum):
    STATIC = "static"
    SLOW_PUSH = "slow_push"
    SLOW_PULL = "slow_pull"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"


class TransitionEffect(StrEnum):
    CUT = "cut"
    CROSSFADE = "crossfade"
    DIP_BLACK = "dip_black"


class Scene(VideoModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    image_path: str = Field(min_length=1)
    duration_seconds: float = Field(gt=0, le=120)
    motion: MotionPreset = MotionPreset.SLOW_PUSH
    focus_x: float = Field(default=0.5, ge=0, le=1)
    focus_y: float = Field(default=0.5, ge=0, le=1)
    transition_to_next: TransitionEffect = TransitionEffect.CUT
    transition_duration_seconds: float = Field(default=0.35, ge=0.05, le=2.0)

    @field_validator("image_path")
    @classmethod
    def normalize_image_path(cls, value: str) -> str:
        return str(Path(value).expanduser().resolve())


class RenderProfile(VideoModel):
    width: int = Field(default=1920, ge=320, le=7680)
    height: int = Field(default=1080, ge=240, le=4320)
    fps: int = Field(default=30, ge=12, le=120)
    codec: str = Field(default="libx264", pattern=r"^[A-Za-z0-9_.-]+$")
    crf: int = Field(default=18, ge=0, le=51)
    preset: str = Field(default="medium", pattern=r"^[A-Za-z0-9_.-]+$")
    threads: int = Field(default=1, ge=1, le=64)
    audio_bitrate: str = Field(default="192k", pattern=r"^[0-9]+k$")

    @model_validator(mode="after")
    def validate_even_dimensions(self) -> RenderProfile:
        if self.width % 2 or self.height % 2:
            raise ValueError("render dimensions must be even")
        return self


class ManualVideoSpec(VideoModel):
    scenes: tuple[Scene, ...]
    narration_path: str | None = None
    music_path: str | None = None
    subtitle_path: str | None = None
    narration_volume: float = Field(default=1.0, ge=0.0, le=4.0)
    music_volume: float = Field(default=0.18, ge=0.0, le=1.0)
    profile: RenderProfile = Field(default_factory=RenderProfile)

    @field_validator("narration_path", "music_path", "subtitle_path")
    @classmethod
    def normalize_optional_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(Path(value).expanduser().resolve())

    @field_validator("scenes")
    @classmethod
    def validate_scenes(cls, value: tuple[Scene, ...]) -> tuple[Scene, ...]:
        if not value:
            raise ValueError("video requires at least one scene")
        ids = [scene.id for scene in value]
        if len(ids) != len(set(ids)):
            raise ValueError("scene IDs must be unique")
        return value
