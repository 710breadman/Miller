"""Safe read-only CBZ inventory and page access."""

from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath

from ..artifacts import canonical_json_bytes, sha256_bytes
from .common import SUPPORTED_IMAGE_EXTENSIONS, ComicSourceError, inspect_image, natural_key
from .models import ComicInventory, ComicPage, ComicSource, ComicSourceKind

_DEFAULT_MAX_ENTRIES = 10_000
_DEFAULT_MAX_ENTRY_BYTES = 128 * 1024 * 1024
_DEFAULT_MAX_TOTAL_BYTES = 20 * 1024 * 1024 * 1024
_DEFAULT_MAX_COMPRESSION_RATIO = 1_000.0


def _normalized_member_name(name: str) -> str:
    if "\\" in name:
        raise ComicSourceError(f"CBZ member uses backslashes: {name}")
    member = PurePosixPath(name)
    if member.is_absolute() or not member.parts:
        raise ComicSourceError(f"CBZ member has unsafe path: {name}")
    if any(part in {"", ".", ".."} for part in member.parts):
        raise ComicSourceError(f"CBZ member has unsafe path: {name}")
    if ":" in member.parts[0]:
        raise ComicSourceError(f"CBZ member resembles an absolute Windows path: {name}")
    return member.as_posix()


def inventory_cbz(
    archive: Path | str,
    *,
    max_entries: int = _DEFAULT_MAX_ENTRIES,
    max_entry_bytes: int = _DEFAULT_MAX_ENTRY_BYTES,
    max_total_bytes: int = _DEFAULT_MAX_TOTAL_BYTES,
    max_compression_ratio: float = _DEFAULT_MAX_COMPRESSION_RATIO,
) -> ComicInventory:
    path = Path(archive).expanduser().resolve()
    if not path.is_file() or path.suffix.casefold() != ".cbz":
        raise ComicSourceError(f"CBZ does not exist or has unsupported extension: {path}")

    try:
        with zipfile.ZipFile(path) as bundle:
            members = [member for member in bundle.infolist() if not member.is_dir()]
            if len(members) > max_entries:
                raise ComicSourceError(f"CBZ contains too many entries: {len(members)}")
            total_size = sum(member.file_size for member in members)
            if total_size > max_total_bytes:
                raise ComicSourceError(f"CBZ expands beyond allowed total size: {total_size}")

            image_members: list[tuple[str, zipfile.ZipInfo]] = []
            seen: set[str] = set()
            for member in members:
                normalized = _normalized_member_name(member.filename)
                key = normalized.casefold()
                if key in seen:
                    raise ComicSourceError(f"CBZ has duplicate normalized path: {normalized}")
                seen.add(key)
                if member.flag_bits & 0x1:
                    raise ComicSourceError(f"encrypted CBZ member is unsupported: {normalized}")
                if member.file_size <= 0 or member.file_size > max_entry_bytes:
                    raise ComicSourceError(
                        f"CBZ member size outside allowed range: {normalized} ({member.file_size})"
                    )
                compressed = max(member.compress_size, 1)
                if member.file_size / compressed > max_compression_ratio:
                    raise ComicSourceError(
                        f"CBZ member has suspicious compression ratio: {normalized}"
                    )
                if PurePosixPath(normalized).suffix.casefold() in SUPPORTED_IMAGE_EXTENSIONS:
                    image_members.append((normalized, member))

            image_members.sort(key=lambda item: natural_key(item[0]))
            if not image_members:
                raise ComicSourceError(f"CBZ contains no supported images: {path}")

            pages: list[ComicPage] = []
            for index, (locator, member) in enumerate(image_members):
                with bundle.open(member, "r") as stream:
                    payload = stream.read(max_entry_bytes + 1)
                if len(payload) != member.file_size or len(payload) > max_entry_bytes:
                    raise ComicSourceError(f"CBZ member read size mismatch: {locator}")
                width, height, mode = inspect_image(payload)
                digest = sha256_bytes(payload)
                pages.append(
                    ComicPage(
                        id=f"page_{digest}",
                        index=index,
                        locator=locator,
                        filename=PurePosixPath(locator).name,
                        sha256=digest,
                        size_bytes=len(payload),
                        width=width,
                        height=height,
                        mode=mode,
                        extension=PurePosixPath(locator).suffix.casefold(),
                    )
                )
    except zipfile.BadZipFile as exc:
        raise ComicSourceError(f"invalid CBZ archive: {path}") from exc

    source_digest = sha256_bytes(
        canonical_json_bytes({"kind": ComicSourceKind.CBZ.value, "path": str(path)})
    )
    source = ComicSource(
        id=f"source_{source_digest}",
        kind=ComicSourceKind.CBZ,
        path=str(path),
        display_name=path.stem,
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


def read_cbz_page(inventory: ComicInventory, page: ComicPage) -> bytes:
    if inventory.source.kind != ComicSourceKind.CBZ:
        raise ValueError("inventory is not a CBZ source")
    archive = Path(inventory.source.path)
    try:
        with zipfile.ZipFile(archive) as bundle, bundle.open(page.locator, "r") as stream:
            payload = stream.read(page.size_bytes + 1)
    except (KeyError, zipfile.BadZipFile) as exc:
        raise ComicSourceError(f"cannot read CBZ page: {page.locator}") from exc
    if len(payload) != page.size_bytes or sha256_bytes(payload) != page.sha256:
        raise ComicSourceError(f"CBZ page changed after inventory: {page.locator}")
    return payload
