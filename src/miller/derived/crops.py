"""Prefer clean crops before generating inpainted pixels."""

from __future__ import annotations

from collections.abc import Iterable

from ..analysis import NormalizedBox, PanelCandidate, TextRegion
from .models import CropCandidate


def choose_clean_crop(
    text_regions: Iterable[TextRegion],
    *,
    target_aspect: float,
    panels: Iterable[PanelCandidate] = (),
) -> CropCandidate:
    if target_aspect <= 0:
        raise ValueError("target aspect must be positive")
    candidates: list[tuple[str, NormalizedBox]] = [
        ("full_page", NormalizedBox(x=0, y=0, width=1, height=1))
    ]
    candidates.extend(
        (panel.id, panel.box) for panel in panels if not panel.is_full_page
    )
    regions = tuple(text_regions)
    scored: list[CropCandidate] = []
    for source, box in candidates:
        overlap = sum(_intersection_area(box, region.box) for region in regions)
        text_coverage = min(1.0, overlap / box.area)
        aspect = box.width / box.height
        aspect_penalty = min(1.0, abs(aspect - target_aspect) / max(target_aspect, 1e-9))
        score = max(0.0, min(1.0, (1 - text_coverage) * 0.8 + (1 - aspect_penalty) * 0.2))
        scored.append(
            CropCandidate(
                box=box,
                text_coverage=text_coverage,
                aspect_penalty=aspect_penalty,
                score=score,
                source=source,
            )
        )
    return max(scored, key=lambda candidate: (candidate.score, -candidate.box.area))


def _intersection_area(left: NormalizedBox, right: NormalizedBox) -> float:
    x1 = max(left.x, right.x)
    y1 = max(left.y, right.y)
    x2 = min(left.x + left.width, right.x + right.width)
    y2 = min(left.y + left.height, right.y + right.height)
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)
