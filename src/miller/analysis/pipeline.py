"""No-AI comic analysis baseline using safe ingestion, panels, OCR, and metrics."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from ..comics import ComicIngestor, ComicInventory
from .index import AnalysisIndex
from .models import (
    OcrResult,
    PageAnalysis,
    PageDescription,
    TextRegion,
    TextRegionKind,
)
from .ocr import TesseractOcrAdapter
from .panels import GutterPanelDetector
from .quality import measure_technical_quality

_TOKEN = re.compile(r"[A-Za-z0-9]+")


class ComicAnalysisResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    inventory: ComicInventory
    pages: tuple[PageAnalysis, ...]
    asset_paths: dict[str, str]
    warnings: tuple[str, ...] = ()


class ComicAnalysisPipeline:
    def __init__(
        self,
        workspace: Path | str,
        *,
        panel_detector: GutterPanelDetector | None = None,
        ocr: TesseractOcrAdapter | None = None,
    ) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.ingestor = ComicIngestor(self.workspace)
        self.panel_detector = panel_detector or GutterPanelDetector()
        self.ocr = ocr or TesseractOcrAdapter()

    def analyze(
        self,
        source: Path | str,
        *,
        language: str = "eng",
        use_ocr: bool = True,
        index_path: Path | str | None = None,
    ) -> ComicAnalysisResult:
        inventory = self.ingestor.inventory(source)
        available, capability_detail = self.ocr.capability() if use_ocr else (False, "disabled")
        warnings: list[str] = []
        if use_ocr and not available:
            warnings.append(f"OCR unavailable: {capability_detail}")
        index = AnalysisIndex(index_path) if index_path is not None else None
        if index is not None:
            index.initialize()
        records: list[PageAnalysis] = []
        asset_paths: dict[str, str] = {}
        for page in inventory.pages:
            cached = self.ingestor.cache_page(inventory, page)
            image_path = (self.workspace / cached.relative_path).resolve()
            panels = self.panel_detector.detect(page.id, image_path)
            page_warnings: list[str] = []
            ocr_result: OcrResult | None = None
            if use_ocr and available:
                try:
                    ocr_result = self.ocr.recognize(image_path, language=language)
                except Exception as exc:
                    page_warnings.append(f"OCR failed: {exc}")
            regions, linked_ocr = self._regions(ocr_result)
            summary = " ".join(span.text for span in linked_ocr.spans) if linked_ocr else ""
            if not summary:
                summary = page.locator
            tags = self._tags(page.locator)
            quality = measure_technical_quality(image_path, text_regions=regions)
            record = PageAnalysis(
                page_id=page.id,
                source_sha256=page.sha256,
                source_locator=page.locator,
                image_width=page.width,
                image_height=page.height,
                panels=panels,
                text_regions=regions,
                ocr=linked_ocr,
                description=PageDescription(
                    summary=summary[:4000],
                    visual_tags=tags,
                    confidence=0.25 if linked_ocr and linked_ocr.spans else 0.05,
                    generator="deterministic-baseline",
                ),
                quality=quality,
                warnings=tuple(page_warnings),
            )
            records.append(record)
            asset_paths[page.id] = str(image_path)
            if index is not None:
                index.upsert(record)
        return ComicAnalysisResult(
            inventory=inventory,
            pages=tuple(records),
            asset_paths=asset_paths,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _regions(
        ocr: OcrResult | None,
    ) -> tuple[tuple[TextRegion, ...], OcrResult | None]:
        if ocr is None:
            return (), None
        regions: list[TextRegion] = []
        spans = []
        for index, span in enumerate(ocr.spans, start=1):
            region_id = f"region_ocr_{index:05d}"
            regions.append(
                TextRegion(
                    id=region_id,
                    box=span.box,
                    kind=TextRegionKind.UNKNOWN,
                    confidence=span.confidence,
                    detector=ocr.engine,
                )
            )
            spans.append(span.model_copy(update={"region_id": region_id}))
        return tuple(regions), ocr.model_copy(update={"spans": tuple(spans)})

    @staticmethod
    def _tags(locator: str) -> tuple[str, ...]:
        tags: list[str] = []
        for token in _TOKEN.findall(Path(locator).stem):
            folded = token.casefold()
            if folded not in {item.casefold() for item in tags}:
                tags.append(token)
        return tuple(tags[:20])
