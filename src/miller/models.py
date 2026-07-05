"""Typed domain models owned by Miller core."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AttemptStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ABANDONED = "abandoned"


class Project(FrozenModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=200)
    workspace: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class StageDefinition(FrozenModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=100)
    dependencies: tuple[str, ...] = ()

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, value: tuple[str, ...], info: Any) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("stage dependencies must be unique")
        stage_id = info.data.get("id")
        if stage_id and stage_id in value:
            raise ValueError("a stage cannot depend on itself")
        return value


class StageRun(FrozenModel):
    id: str = Field(min_length=1, max_length=128)
    project_id: str = Field(min_length=1, max_length=128)
    stage_id: str = Field(min_length=1, max_length=128)
    status: StageStatus = StageStatus.PENDING
    input_fingerprint: str | None = None
    output_artifact_id: str | None = None
    active_attempt_id: str | None = None
    cancel_requested: bool = False
    error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_state(self) -> StageRun:
        if self.status == StageStatus.RUNNING and not self.active_attempt_id:
            raise ValueError("running stage must have an active attempt")
        if self.status != StageStatus.RUNNING and self.active_attempt_id:
            raise ValueError("only running stages may have an active attempt")
        if self.status == StageStatus.COMPLETED and not self.output_artifact_id:
            raise ValueError("completed stage must reference an output artifact")
        return self


class StageAttempt(FrozenModel):
    id: str = Field(min_length=1, max_length=128)
    stage_run_id: str = Field(min_length=1, max_length=128)
    number: int = Field(ge=1)
    status: AttemptStatus
    attempt_guard: str = Field(min_length=16, max_length=256)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    error: str | None = None

    @model_validator(mode="after")
    def validate_terminal_timestamp(self) -> StageAttempt:
        terminal = self.status != AttemptStatus.RUNNING
        if terminal != (self.completed_at is not None):
            raise ValueError("terminal attempt status and completed_at must agree")
        return self


class Artifact(FrozenModel):
    id: str = Field(pattern=r"^artifact_[0-9a-f]{64}$")
    content_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    project_id: str = Field(min_length=1, max_length=128)
    stage_run_id: str | None = Field(default=None, max_length=128)
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    media_type: str = Field(default="application/octet-stream", min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class Event(FrozenModel):
    id: str = Field(min_length=1, max_length=128)
    project_id: str = Field(min_length=1, max_length=128)
    kind: str = Field(min_length=1, max_length=100)
    stage_run_id: str | None = Field(default=None, max_length=128)
    attempt_id: str | None = Field(default=None, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
