"""Deterministic technical quality and structured description validation."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import cast

from PIL import Image, ImageOps, ImageStat

from .models import PageDescription, TechnicalQuality, TextRegion


def parse_page_description(payload: str) -> PageDescription:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("page description must be a JSON object")
    return PageDescription.model_validate(value)


def measure_technical_quality(
    image_path: Path | str,
    *,
    text_regions: tuple[TextRegion, ...] = (),
) -> TechnicalQuality:
    with Image.open(image_path) as opened:
        grayscale = ImageOps.exif_transpose(opened).convert("L")
        width, height = grayscale.size
        sample = grayscale.copy()
        sample.thumbnail((512, 512), Image.Resampling.BILINEAR)
    statistics = ImageStat.Stat(sample)
    brightness = statistics.mean[0] / 255.0
    contrast = min(1.0, statistics.stddev[0] / 96.0)
    sharpness = _sharpness_score(sample)
    text_coverage = min(1.0, sum(region.box.area for region in text_regions))
    pixels = width * height
    resolution_score = min(1.0, math.sqrt(pixels / (1920 * 1080)))
    exposure_score = max(0.0, 1.0 - abs(brightness - 0.55) / 0.55)
    overall = (
        resolution_score * 0.30
        + contrast * 0.20
        + sharpness * 0.30
        + exposure_score * 0.15
        + (1.0 - text_coverage) * 0.05
    )
    return TechnicalQuality(
        width=width,
        height=height,
        aspect_ratio=width / height,
        brightness=brightness,
        contrast=contrast,
        sharpness=sharpness,
        text_coverage=text_coverage,
        resolution_score=resolution_score,
        overall_score=max(0.0, min(1.0, overall)),
    )


def _sharpness_score(image: Image.Image) -> float:
    if image.width < 3 or image.height < 3:
        return 0.0
    pixels = image.load()
    assert pixels is not None
    values: list[float] = []
    step = max(1, min(image.width, image.height) // 160)
    for y in range(1, image.height - 1, step):
        for x in range(1, image.width - 1, step):
            center = float(cast(int, pixels[x, y])) * 4
            laplacian = center - float(cast(int, pixels[x - 1, y]))
            laplacian -= float(cast(int, pixels[x + 1, y]))
            laplacian -= float(cast(int, pixels[x, y - 1]))
            laplacian -= float(cast(int, pixels[x, y + 1]))
            values.append(laplacian)
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return min(1.0, math.sqrt(variance) / 80.0)
