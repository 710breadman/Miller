"""Derived comic asset records."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from ..analysis import NormalizedBox


class DerivedModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DerivedMethod(StrEnum):
    CLEAN_CROP = "clean_crop"
    EXTERNAL_INPAINT = "external_inpaint"
    SIMPLE_FILL = "simple_fill"
    ORIGINAL_FALLBACK = "original_fallback"


class CropCandidate(DerivedModel):
    box: NormalizedBox
    text_coverage: float = Field(ge=0.0, le=1.0)
    aspect_penalty: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0, le=1.0)
    source: str = Field(min_length=1)


class DerivedAsset(DerivedModel):
    source_path: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_path: str = Field(min_length=1)
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    method: DerivedMethod
    crop: NormalizedBox
    mask_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    tool: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    warnings: tuple[str, ...] = ()
