"""Deterministic text and balloon-hint mask artifacts."""

from __future__ import annotations

import io
from collections.abc import Iterable
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFilter

from ..artifacts import sha256_bytes
from .models import TextRegion


@dataclass(frozen=True)
class MaskArtifact:
    payload: bytes
    sha256: str
    width: int
    height: int


def render_region_mask(
    width: int,
    height: int,
    regions: Iterable[TextRegion],
    *,
    padding_pixels: int = 2,
    balloon_hints_only: bool = False,
) -> MaskArtifact:
    if width <= 0 or height <= 0:
        raise ValueError("mask dimensions must be positive")
    image = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(image)
    for region in regions:
        if balloon_hints_only and not region.balloon_hint:
            continue
        if region.polygon is not None:
            points = [
                (round(point.x * (width - 1)), round(point.y * (height - 1)))
                for point in region.polygon.points
            ]
            draw.polygon(points, fill=255)
        else:
            left = round(region.box.x * width)
            top = round(region.box.y * height)
            right = round((region.box.x + region.box.width) * width) - 1
            bottom = round((region.box.y + region.box.height) * height) - 1
            draw.rectangle((left, top, right, bottom), fill=255)
    if padding_pixels > 0:
        size = padding_pixels * 2 + 1
        image = image.filter(ImageFilter.MaxFilter(size=size))
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=9)
    payload = output.getvalue()
    return MaskArtifact(payload, sha256_bytes(payload), width, height)
