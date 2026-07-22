"""Portable Miller project manifest."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..models import Artifact, Event, Project, ProjectDocument, StageDefinition, StageRun


class PortableModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class PortableProjectManifest(PortableModel):
    schema_version: int = Field(default=1, ge=1)
    project: Project
    stage_definitions: tuple[StageDefinition, ...] = ()
    stage_runs: tuple[StageRun, ...] = ()
    artifacts: tuple[Artifact, ...] = ()
    documents: tuple[ProjectDocument, ...] = ()
    document_history: tuple[ProjectDocument, ...] = ()
    events: tuple[Event, ...] = ()
