"""Replaceable vector-store records and protocol.

SQLite remains authoritative for asset identity and provenance. Vector stores
contain only rebuildable embeddings and filter payloads.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Protocol, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator

PayloadScalar: TypeAlias = str | int | float | bool | None
Payload: TypeAlias = dict[str, PayloadScalar]
FilterValues: TypeAlias = Mapping[str, str | int | bool]


class VectorModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class VectorPoint(VectorModel):
    """One rebuildable embedding record."""

    id: str = Field(min_length=1, max_length=512)
    vector: tuple[float, ...]
    payload: Payload = Field(default_factory=dict)

    @field_validator("vector")
    @classmethod
    def validate_vector(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        if not value:
            raise ValueError("vector cannot be empty")
        if any(not math.isfinite(component) for component in value):
            raise ValueError("vector components must be finite")
        return value

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: Payload) -> Payload:
        if "_miller_id" in value:
            raise ValueError("payload key _miller_id is reserved")
        return value


class VectorMatch(VectorModel):
    """Normalized vector search result."""

    id: str = Field(min_length=1, max_length=512)
    score: float
    payload: Payload = Field(default_factory=dict)


class VectorStore(Protocol):
    """Small metadata-aware vector-store contract."""

    def ensure_collection(self, name: str, vector_size: int) -> None: ...

    def upsert(self, collection: str, points: Sequence[VectorPoint]) -> None: ...

    def query(
        self,
        collection: str,
        vector: Sequence[float],
        *,
        limit: int = 20,
        filters: FilterValues | None = None,
    ) -> tuple[VectorMatch, ...]: ...

    def delete_collection(self, name: str) -> bool: ...
