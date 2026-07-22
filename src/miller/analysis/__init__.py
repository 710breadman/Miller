"""Comic page understanding, masks, OCR, quality, and search."""

from .index import AnalysisIndex
from .masks import MaskArtifact, render_region_mask
from .models import (
    NormalizedBox,
    NormalizedPoint,
    NormalizedPolygon,
    OcrResult,
    OcrSpan,
    PageAnalysis,
    PageDescription,
    PanelCandidate,
    PanelSource,
    TechnicalQuality,
    TextRegion,
    TextRegionKind,
)
from .ocr import OcrAdapter, TesseractOcrAdapter
from .panels import GutterPanelDetector
from .pipeline import ComicAnalysisPipeline, ComicAnalysisResult
from .quality import measure_technical_quality, parse_page_description

__all__ = [
    "AnalysisIndex",
    "GutterPanelDetector",
    "MaskArtifact",
    "NormalizedBox",
    "NormalizedPoint",
    "NormalizedPolygon",
    "OcrAdapter",
    "OcrResult",
    "OcrSpan",
    "PageAnalysis",
    "PageDescription",
    "PanelCandidate",
    "PanelSource",
    "TechnicalQuality",
    "TesseractOcrAdapter",
    "TextRegion",
    "TextRegionKind",
    "measure_technical_quality",
    "parse_page_description",
    "render_region_mask",
    "ComicAnalysisPipeline",
    "ComicAnalysisResult",
]
