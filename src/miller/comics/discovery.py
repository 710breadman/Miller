"""Deterministic read-only image-folder inventory."""

from __future__ import annotations

from pathlib import Path

from ..artifacts import canonical_json_bytes, sha256_bytes
from .common import SUPPORTED_IMAGE_EXTENSIONS, ComicSourceError, inspect_image, natural_key
from .models import ComicInventory, ComicPage, ComicSource, ComicSourceKind

_DEFAULT_MAX_IMAGE_BYTES = 128 * 1024 * 1024


def inventory_image_folder(
    folder: Path | str,
    *,
    max_image_bytes: int = _DEFAULT_MAX_IMAGE_BYTES,
) -> ComicInventory:
    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise ComicSourceError(f"image folder does not exist: {root}")

    candidates: list[tuple[str, Path]] = []
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        if candidate.suffix.casefold() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ComicSourceError(f"image path escapes source root: {candidate}") from exc
        locator = candidate.relative_to(root).as_posix()
        candidates.append((locator, resolved))

    candidates.sort(key=lambda item: natural_key(item[0]))
    if not candidates:
        raise ComicSourceError(f"no supported images found in {root}")

    pages: list[ComicPage] = []
    for index, (locator, path) in enumerate(candidates):
        size = path.stat().st_size
        if size <= 0 or size > max_image_bytes:
            raise ComicSourceError(f"image size outside allowed range: {locator} ({size} bytes)")
        payload = path.read_bytes()
        width, height, mode = inspect_image(payload)
        digest = sha256_bytes(payload)
        pages.append(
            ComicPage(
                id=f"page_{digest}",
                index=index,
                locator=locator,
                filename=path.name,
                sha256=digest,
                size_bytes=size,
                width=width,
                height=height,
                mode=mode,
                extension=path.suffix.casefold(),
            )
        )

    source_digest = sha256_bytes(
        canonical_json_bytes({"kind": ComicSourceKind.IMAGE_FOLDER.value, "path": str(root)})
    )
    source = ComicSource(
        id=f"source_{source_digest}",
        kind=ComicSourceKind.IMAGE_FOLDER,
        path=str(root),
        display_name=root.name,
    )
    fingerprint_digest = sha256_bytes(
        canonical_json_bytes(
            [
                {
                    "locator": page.locator,
                    "sha256": page.sha256,
                    "size_bytes": page.size_bytes,
                }
                for page in pages
            ]
        )
    )
    issue_digest = sha256_bytes(canonical_json_bytes([page.sha256 for page in pages]))
    return ComicInventory(
        source=source,
        issue_id=f"issue_{issue_digest}",
        fingerprint=f"sha256:{fingerprint_digest}",
        pages=tuple(pages),
    )
