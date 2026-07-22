"""Comic ingestion orchestration, extraction cache, and thumbnails."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Final

from PIL import Image, ImageOps

from ..artifacts import sha256_bytes, sha256_file
from .cbz import inventory_cbz, read_cbz_page
from .common import ComicSourceError, atomic_write
from .discovery import inventory_image_folder
from .models import (
    CachedPage,
    ComicInventory,
    ComicPage,
    ComicSourceKind,
    InventoryReconciliation,
    ThumbnailArtifact,
)

_DEFAULT_THUMBNAIL_SIZE: Final[tuple[int, int]] = (512, 512)


class ComicIngestor:
    """Read comic sources and write only content-addressed derived cache files."""

    def __init__(self, workspace: Path | str) -> None:
        self.workspace = Path(workspace).expanduser().resolve()

    def inventory(self, source: Path | str) -> ComicInventory:
        path = Path(source).expanduser().resolve()
        if path.is_dir():
            return inventory_image_folder(path)
        if path.is_file() and path.suffix.casefold() == ".cbz":
            return inventory_cbz(path)
        raise ComicSourceError(f"unsupported comic source: {path}")

    def read_page(self, inventory: ComicInventory, page: ComicPage) -> bytes:
        if page not in inventory.pages:
            raise ValueError("page does not belong to inventory")
        if inventory.source.kind == ComicSourceKind.CBZ:
            return read_cbz_page(inventory, page)
        root = Path(inventory.source.path).resolve()
        path = (root / page.locator).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ComicSourceError(f"page path escapes source root: {page.locator}") from exc
        if not path.is_file():
            raise ComicSourceError(f"page no longer exists: {page.locator}")
        payload = path.read_bytes()
        if len(payload) != page.size_bytes or sha256_bytes(payload) != page.sha256:
            raise ComicSourceError(f"page changed after inventory: {page.locator}")
        return payload

    def cache_page(self, inventory: ComicInventory, page: ComicPage) -> CachedPage:
        payload = self.read_page(inventory, page)
        target = (
            self.workspace
            / "cache"
            / "comics"
            / "pages"
            / page.sha256[:2]
            / f"{page.sha256}{page.extension}"
        )
        self._assert_managed(target)
        if target.exists():
            if sha256_file(target) != page.sha256:
                raise RuntimeError(f"cached page failed integrity check: {target}")
        else:
            atomic_write(target, payload)
        return CachedPage(
            page_id=page.id,
            relative_path=target.relative_to(self.workspace).as_posix(),
            sha256=page.sha256,
            size_bytes=len(payload),
        )

    def create_thumbnail(
        self,
        inventory: ComicInventory,
        page: ComicPage,
        *,
        max_size: tuple[int, int] = _DEFAULT_THUMBNAIL_SIZE,
    ) -> ThumbnailArtifact:
        payload = self.read_page(inventory, page)
        try:
            with Image.open(io.BytesIO(payload)) as opened:
                image = ImageOps.exif_transpose(opened)
                image = (
                    image.convert("RGB")
                    if image.mode not in {"RGB", "RGBA"}
                    else image.copy()
                )
                image.thumbnail(max_size, Image.Resampling.LANCZOS, reducing_gap=3.0)
                output = io.BytesIO()
                image.save(output, format="PNG", optimize=False, compress_level=9)
                thumbnail = output.getvalue()
                width, height = image.size
        except Exception as exc:
            raise ComicSourceError(
                f"thumbnail generation failed for {page.locator}: {exc}"
            ) from exc

        digest = sha256_bytes(thumbnail)
        target = (
            self.workspace
            / "cache"
            / "comics"
            / "thumbnails"
            / digest[:2]
            / f"{digest}.png"
        )
        self._assert_managed(target)
        if target.exists():
            if sha256_file(target) != digest:
                raise RuntimeError(f"thumbnail failed integrity check: {target}")
        else:
            atomic_write(target, thumbnail)
        return ThumbnailArtifact(
            page_id=page.id,
            relative_path=target.relative_to(self.workspace).as_posix(),
            sha256=digest,
            width=width,
            height=height,
        )

    def cache_inventory(
        self, inventory: ComicInventory
    ) -> tuple[tuple[CachedPage, ThumbnailArtifact], ...]:
        return tuple(
            (self.cache_page(inventory, page), self.create_thumbnail(inventory, page))
            for page in inventory.pages
        )

    def _assert_managed(self, path: Path) -> None:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError(f"cache path escapes managed workspace: {resolved}") from exc


def reconcile_inventories(
    previous: ComicInventory, current: ComicInventory
) -> InventoryReconciliation:
    old = {page.locator: page for page in previous.pages}
    new = {page.locator: page for page in current.pages}
    shared = old.keys() & new.keys()
    unchanged = tuple(sorted(locator for locator in shared if old[locator].id == new[locator].id))
    changed = tuple(sorted(locator for locator in shared if old[locator].id != new[locator].id))
    added = tuple(sorted(new.keys() - old.keys()))
    removed = tuple(sorted(old.keys() - new.keys()))
    return InventoryReconciliation(
        unchanged=unchanged,
        changed=changed,
        added=added,
        removed=removed,
    )
