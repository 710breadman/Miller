"""Typed comic-source and ingestion records."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ComicModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ComicSourceKind(StrEnum):
    IMAGE_FOLDER = "image_folder"
    CBZ = "cbz"


class ComicSource(ComicModel):
    id: str = Field(pattern=r"^source_[0-9a-f]{64}$")
    kind: ComicSourceKind
    path: str = Field(min_length=1)
    display_name: str = Field(min_length=1)

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: str) -> str:
        return str(Path(value).expanduser().resolve())


class ComicPage(ComicModel):
    id: str = Field(pattern=r"^page_[0-9a-f]{64}$")
    index: int = Field(ge=0)
    locator: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    mode: str = Field(min_length=1)
    extension: str = Field(pattern=r"^\.[a-z0-9]+$")


class ComicInventory(ComicModel):
    source: ComicSource
    issue_id: str = Field(pattern=r"^issue_[0-9a-f]{64}$")
    fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    pages: tuple[ComicPage, ...]

    @field_validator("pages")
    @classmethod
    def validate_page_order(cls, value: tuple[ComicPage, ...]) -> tuple[ComicPage, ...]:
        indexes = [page.index for page in value]
        if indexes != list(range(len(value))):
            raise ValueError("comic page indexes must be contiguous and zero-based")
        if len({page.locator.casefold() for page in value}) != len(value):
            raise ValueError("comic page locators must be unique")
        return value


class CachedPage(ComicModel):
    page_id: str = Field(pattern=r"^page_[0-9a-f]{64}$")
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0)


class ThumbnailArtifact(ComicModel):
    page_id: str = Field(pattern=r"^page_[0-9a-f]{64}$")
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class InventoryReconciliation(ComicModel):
    unchanged: tuple[str, ...] = ()
    changed: tuple[str, ...] = ()
    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
