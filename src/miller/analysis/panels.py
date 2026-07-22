"""Conservative deterministic panel candidates based on bright gutters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from PIL import Image, ImageOps

from .models import NormalizedBox, PanelCandidate, PanelSource


@dataclass(frozen=True)
class _PixelBox:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


class GutterPanelDetector:
    """Split pages on sufficiently wide near-white horizontal/vertical gutters."""

    def __init__(
        self,
        *,
        white_threshold: int = 245,
        white_ratio: float = 0.975,
        minimum_gutter: int = 4,
        minimum_panel_fraction: float = 0.12,
        maximum_panels: int = 24,
    ) -> None:
        self.white_threshold = white_threshold
        self.white_ratio = white_ratio
        self.minimum_gutter = minimum_gutter
        self.minimum_panel_fraction = minimum_panel_fraction
        self.maximum_panels = maximum_panels

    def detect(self, page_id: str, image_path: Path | str) -> tuple[PanelCandidate, ...]:
        path = Path(image_path)
        with Image.open(path) as opened:
            image = ImageOps.exif_transpose(opened).convert("L")
            original_width, original_height = image.size
            if max(image.size) > 900:
                scale = 900 / max(image.size)
                image = image.resize(
                    (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                    Image.Resampling.BILINEAR,
                )
        root = _PixelBox(0, 0, image.width, image.height)
        boxes = self._split_recursive(image, root)
        full_page = PanelCandidate(
            id=f"panel_{page_id[5:17]}_full",
            page_id=page_id,
            box=NormalizedBox(x=0.0, y=0.0, width=1.0, height=1.0),
            order=0,
            confidence=1.0,
            source=PanelSource.FULL_PAGE,
            is_full_page=True,
        )
        if len(boxes) <= 1:
            return (full_page,)
        candidates: list[PanelCandidate] = [full_page]
        sorted_boxes = sorted(boxes, key=lambda box: (box.top, box.left))[: self.maximum_panels]
        for index, box in enumerate(sorted_boxes, start=1):
            normalized = NormalizedBox(
                x=box.left / image.width,
                y=box.top / image.height,
                width=box.width / image.width,
                height=box.height / image.height,
            )
            candidates.append(
                PanelCandidate(
                    id=f"panel_{page_id[5:17]}_{index:03d}",
                    page_id=page_id,
                    box=normalized,
                    order=index,
                    confidence=0.65,
                    source=PanelSource.GUTTER_BASELINE,
                )
            )
        assert original_width > 0 and original_height > 0
        return tuple(candidates)

    def _split_recursive(self, image: Image.Image, box: _PixelBox) -> list[_PixelBox]:
        if box.width <= 1 or box.height <= 1:
            return [box]
        vertical = self._best_vertical_gutter(image, box)
        horizontal = self._best_horizontal_gutter(image, box)
        choices: list[tuple[int, str, tuple[int, int]]] = []
        if vertical is not None:
            choices.append((vertical[1] - vertical[0], "vertical", vertical))
        if horizontal is not None:
            choices.append((horizontal[1] - horizontal[0], "horizontal", horizontal))
        if not choices:
            return [box]
        _, direction, gutter = max(choices, key=lambda item: item[0])
        if direction == "vertical":
            first = _PixelBox(box.left, box.top, gutter[0], box.bottom)
            second = _PixelBox(gutter[1], box.top, box.right, box.bottom)
        else:
            first = _PixelBox(box.left, box.top, box.right, gutter[0])
            second = _PixelBox(box.left, gutter[1], box.right, box.bottom)
        minimum_width = max(8, round(image.width * self.minimum_panel_fraction))
        minimum_height = max(8, round(image.height * self.minimum_panel_fraction))
        for candidate in (first, second):
            if candidate.width < minimum_width or candidate.height < minimum_height:
                return [box]
        result = self._split_recursive(image, first) + self._split_recursive(image, second)
        return result if len(result) <= self.maximum_panels else [box]

    def _best_vertical_gutter(
        self, image: Image.Image, box: _PixelBox
    ) -> tuple[int, int] | None:
        runs = self._bright_runs(
            [
                self._column_white_ratio(image, x, box.top, box.bottom)
                for x in range(box.left, box.right)
            ],
            offset=box.left,
        )
        return self._select_internal_run(runs, box.left, box.right)

    def _best_horizontal_gutter(
        self, image: Image.Image, box: _PixelBox
    ) -> tuple[int, int] | None:
        runs = self._bright_runs(
            [
                self._row_white_ratio(image, y, box.left, box.right)
                for y in range(box.top, box.bottom)
            ],
            offset=box.top,
        )
        return self._select_internal_run(runs, box.top, box.bottom)

    def _select_internal_run(
        self, runs: list[tuple[int, int]], start: int, end: int
    ) -> tuple[int, int] | None:
        margin = max(self.minimum_gutter, round((end - start) * self.minimum_panel_fraction))
        internal = [
            run
            for run in runs
            if run[1] - run[0] >= self.minimum_gutter
            and run[0] - start >= margin
            and end - run[1] >= margin
        ]
        if not internal:
            return None
        center = (start + end) / 2
        return max(
            internal,
            key=lambda run: ((run[1] - run[0]), -abs(((run[0] + run[1]) / 2) - center)),
        )

    def _bright_runs(self, ratios: list[float], *, offset: int) -> list[tuple[int, int]]:
        runs: list[tuple[int, int]] = []
        current: int | None = None
        for index, ratio in enumerate(ratios):
            if ratio >= self.white_ratio and current is None:
                current = index
            elif ratio < self.white_ratio and current is not None:
                runs.append((offset + current, offset + index))
                current = None
        if current is not None:
            runs.append((offset + current, offset + len(ratios)))
        return runs

    def _column_white_ratio(self, image: Image.Image, x: int, top: int, bottom: int) -> float:
        values = [cast(int, image.getpixel((x, y))) for y in range(top, bottom)]
        return sum(value >= self.white_threshold for value in values) / max(len(values), 1)

    def _row_white_ratio(self, image: Image.Image, y: int, left: int, right: int) -> float:
        values = [cast(int, image.getpixel((x, y))) for x in range(left, right)]
        return sum(value >= self.white_threshold for value in values) / max(len(values), 1)
