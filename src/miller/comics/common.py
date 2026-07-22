"""Shared safe image and file helpers."""

from __future__ import annotations

import hashlib
import io
import os
import re
import tempfile
from pathlib import Path

from PIL import Image

SUPPORTED_IMAGE_EXTENSIONS = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
)
_NATURAL_PART = re.compile(r"(\d+)")


class ComicSourceError(ValueError):
    """Raised when a comic source is unsafe or unsupported."""


def natural_key(value: str) -> tuple[object, ...]:
    return tuple(
        int(part) if part.isdigit() else part.casefold()
        for part in _NATURAL_PART.split(value)
    )


def hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def hash_stream(stream: io.BufferedIOBase, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    while chunk := stream.read(chunk_size):
        digest.update(chunk)
    return digest.hexdigest()


def inspect_image(payload: bytes) -> tuple[int, int, str]:
    try:
        with Image.open(io.BytesIO(payload)) as image:
            image.verify()
        with Image.open(io.BytesIO(payload)) as image:
            width, height = image.size
            mode = image.mode
    except Exception as exc:
        raise ComicSourceError(f"invalid image: {exc}") from exc
    if width <= 0 or height <= 0:
        raise ComicSourceError("image has invalid dimensions")
    return width, height, mode


def atomic_write(target: Path, payload: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".miller-", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
