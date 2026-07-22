"""Quality findings, scores, and bounded repair actions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QualityModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKING = "blocking"


class FindingCategory(StrEnum):
    MISSING_MEDIA = "missing_media"
    STREAM_LAYOUT = "stream_layout"
    DURATION_MISMATCH = "duration_mismatch"
    BLACK_FRAMES = "black_frames"
    AUDIO_CLIPPING = "audio_clipping"
    DUPLICATE_ASSET = "duplicate_asset"
    WEAK_MATCH = "weak_match"
    STATIC_RUN = "static_run"
    MOTION_REPETITION = "motion_repetition"
    CONTINUITY_SHIFT = "continuity_shift"


class QualityFinding(QualityModel):
    id: str = Field(pattern=r"^finding_[0-9]{4}$")
    category: FindingCategory
    severity: FindingSeverity
    scene_ids: tuple[str, ...] = ()
    message: str = Field(min_length=1)
    evidence: dict[str, str | int | float | bool] = Field(default_factory=dict)
    suggested_action: str = Field(default="review", min_length=1)


class QualityReport(QualityModel):
    pass_index: int = Field(ge=0)
    score: float = Field(ge=0.0, le=1.0)
    findings: tuple[QualityFinding, ...]

    @field_validator("findings")
    @classmethod
    def validate_findings(
        cls, value: tuple[QualityFinding, ...]
    ) -> tuple[QualityFinding, ...]:
        expected = [f"finding_{index:04d}" for index in range(1, len(value) + 1)]
        if [finding.id for finding in value] != expected:
            raise ValueError("finding IDs must be ordered and contiguous")
        return value


class RepairActionKind(StrEnum):
    REPLACE_ASSET = "replace_asset"
    CHANGE_MOTION = "change_motion"
    RERENDER = "rerender"
    REVIEW = "review"


class RepairAction(QualityModel):
    id: str = Field(pattern=r"^repair_[0-9]{4}$")
    kind: RepairActionKind
    scene_id: str = Field(min_length=1)
    reason_finding_id: str = Field(pattern=r"^finding_[0-9]{4}$")
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)


class RepairPlan(QualityModel):
    pass_index: int = Field(ge=1)
    maximum_passes: int = Field(ge=0, le=20)
    actions: tuple[RepairAction, ...]
    blocked_scene_ids: tuple[str, ...] = ()

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, value: tuple[RepairAction, ...]) -> tuple[RepairAction, ...]:
        expected = [f"repair_{index:04d}" for index in range(1, len(value) + 1)]
        if [action.id for action in value] != expected:
            raise ValueError("repair IDs must be ordered and contiguous")
        return value
