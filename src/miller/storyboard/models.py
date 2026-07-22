"""Typed automatic storyboard and scene records."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..analysis import NormalizedPoint


class StoryboardModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SearchScope(StoryboardModel):
    characters: tuple[str, ...] = ()
    series: tuple[str, ...] = ()
    arcs: tuple[str, ...] = ()
    eras: tuple[str, ...] = ()
    continuities: tuple[str, ...] = ()
    moods: tuple[str, ...] = ()
    steering_keywords: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()

    @field_validator(
        "characters",
        "series",
        "arcs",
        "eras",
        "continuities",
        "moods",
        "steering_keywords",
        "exclusions",
    )
    @classmethod
    def unique_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if len({item.casefold() for item in cleaned}) != len(cleaned):
            raise ValueError("scope values must be unique ignoring case")
        return cleaned


class SceneScore(StoryboardModel):
    lexical: float = Field(ge=0.0, le=1.0)
    character: float = Field(ge=0.0, le=1.0)
    theme: float = Field(ge=0.0, le=1.0)
    continuity: float = Field(ge=0.0, le=1.0)
    quality: float = Field(ge=0.0, le=1.0)
    reuse_penalty: float = Field(ge=0.0, le=1.0)
    total: float = Field(ge=0.0, le=1.0)


class SceneCandidate(StoryboardModel):
    asset_id: str = Field(min_length=1)
    source_locator: str = Field(min_length=1)
    score: SceneScore
    reasons: tuple[str, ...] = ()


class CameraPreset(StrEnum):
    STATIC = "static"
    SLOW_PUSH = "slow_push"
    SLOW_PULL = "slow_pull"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"


class TransitionPreset(StrEnum):
    CUT = "cut"
    CROSSFADE = "crossfade"
    DIP_BLACK = "dip_black"


class CameraPlan(StoryboardModel):
    preset: CameraPreset
    focus: NormalizedPoint = Field(default_factory=lambda: NormalizedPoint(x=0.5, y=0.5))
    intensity: float = Field(default=0.25, ge=0.0, le=1.0)


class StoryboardScene(StoryboardModel):
    id: str = Field(pattern=r"^scene_[0-9]{4}$")
    beat_id: str = Field(pattern=r"^beat_[0-9]{4}$")
    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)
    narration: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    mood: str = Field(default="neutral", min_length=1)
    primary_asset: str = Field(min_length=1)
    alternatives: tuple[str, ...] = ()
    candidates: tuple[SceneCandidate, ...]
    camera: CameraPlan
    transition: TransitionPreset = TransitionPreset.CUT
    music_state: str = Field(default="neutral", min_length=1)
    locked: bool = False
    review_status: str = Field(default="automatic", min_length=1)

    @model_validator(mode="after")
    def validate_scene(self) -> StoryboardScene:
        if self.end <= self.start:
            raise ValueError("scene end must be after start")
        candidate_ids = [candidate.asset_id for candidate in self.candidates]
        if self.primary_asset not in candidate_ids:
            raise ValueError("primary asset must be present in candidates")
        if any(asset_id == self.primary_asset for asset_id in self.alternatives):
            raise ValueError("primary asset cannot also be an alternative")
        if any(asset_id not in candidate_ids for asset_id in self.alternatives):
            raise ValueError("alternatives must be present in candidates")
        return self


class StoryboardPlan(StoryboardModel):
    schema_version: int = Field(default=1, ge=1)
    scope: SearchScope
    scenes: tuple[StoryboardScene, ...]
    warnings: tuple[str, ...] = ()

    @field_validator("scenes")
    @classmethod
    def validate_scenes(cls, value: tuple[StoryboardScene, ...]) -> tuple[StoryboardScene, ...]:
        if not value:
            raise ValueError("storyboard requires scenes")
        expected_ids = [
            f"scene_{index:04d}" for index in range(1, len(value) + 1)
        ]
        if [scene.id for scene in value] != expected_ids:
            raise ValueError("scene IDs must be ordered and contiguous")
        for previous, current in zip(value, value[1:], strict=False):
            if abs(current.start - previous.end) > 0.05:
                raise ValueError("storyboard contains a timing gap or overlap")
        return value
