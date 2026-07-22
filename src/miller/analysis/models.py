"""Versioned comic page-understanding records."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AnalysisModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class NormalizedPoint(AnalysisModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


class NormalizedBox(AnalysisModel):
    x: float = Field(ge=0.0, lt=1.0)
    y: float = Field(ge=0.0, lt=1.0)
    width: float = Field(gt=0.0, le=1.0)
    height: float = Field(gt=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_bounds(self) -> NormalizedBox:
        epsilon = 1e-9
        if self.x + self.width > 1.0 + epsilon:
            raise ValueError("box extends beyond the right image boundary")
        if self.y + self.height > 1.0 + epsilon:
            raise ValueError("box extends beyond the bottom image boundary")
        return self

    @property
    def area(self) -> float:
        return self.width * self.height


class NormalizedPolygon(AnalysisModel):
    points: tuple[NormalizedPoint, ...]

    @field_validator("points")
    @classmethod
    def validate_points(cls, value: tuple[NormalizedPoint, ...]) -> tuple[NormalizedPoint, ...]:
        if len(value) < 3:
            raise ValueError("polygon requires at least three points")
        unique = {(point.x, point.y) for point in value}
        if len(unique) < 3:
            raise ValueError("polygon requires at least three unique points")
        area = 0.0
        for index, point in enumerate(value):
            next_point = value[(index + 1) % len(value)]
            area += point.x * next_point.y - next_point.x * point.y
        if abs(area) < 1e-8:
            raise ValueError("polygon area must be non-zero")
        return value


class PanelSource(StrEnum):
    FULL_PAGE = "full_page"
    GUTTER_BASELINE = "gutter_baseline"
    MANUAL = "manual"
    MODEL = "model"


class PanelCandidate(AnalysisModel):
    id: str = Field(pattern=r"^panel_[A-Za-z0-9_.-]+$")
    page_id: str = Field(pattern=r"^page_[0-9a-f]{64}$")
    box: NormalizedBox
    order: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    source: PanelSource
    is_full_page: bool = False
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_full_page(self) -> PanelCandidate:
        if self.is_full_page:
            expected = (0.0, 0.0, 1.0, 1.0)
            actual = (self.box.x, self.box.y, self.box.width, self.box.height)
            if any(abs(left - right) > 1e-9 for left, right in zip(actual, expected, strict=True)):
                raise ValueError("full-page panel must cover the complete normalized image")
        return self


class TextRegionKind(StrEnum):
    DIALOGUE = "dialogue"
    CAPTION = "caption"
    SOUND_EFFECT = "sound_effect"
    CREDIT = "credit"
    UNKNOWN = "unknown"


class TextRegion(AnalysisModel):
    id: str = Field(pattern=r"^region_[A-Za-z0-9_.-]+$")
    box: NormalizedBox
    polygon: NormalizedPolygon | None = None
    kind: TextRegionKind = TextRegionKind.UNKNOWN
    confidence: float = Field(ge=0.0, le=1.0)
    detector: str = Field(min_length=1, max_length=200)
    balloon_hint: bool = False


class OcrSpan(AnalysisModel):
    id: str = Field(pattern=r"^ocr_[A-Za-z0-9_.-]+$")
    text: str = Field(min_length=1)
    box: NormalizedBox
    confidence: float = Field(ge=0.0, le=1.0)
    language: str = Field(default="und", min_length=2, max_length=32)
    region_id: str | None = Field(default=None, pattern=r"^region_[A-Za-z0-9_.-]+$")
    line_index: int | None = Field(default=None, ge=0)


class OcrResult(AnalysisModel):
    engine: str = Field(min_length=1, max_length=200)
    engine_version: str = Field(min_length=1, max_length=200)
    language: str = Field(min_length=2, max_length=32)
    spans: tuple[OcrSpan, ...] = ()
    warnings: tuple[str, ...] = ()


class PageDescription(AnalysisModel):
    summary: str = Field(default="", max_length=4000)
    characters: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    moods: tuple[str, ...] = ()
    visual_tags: tuple[str, ...] = ()
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    generator: str = Field(default="none", min_length=1, max_length=200)

    @field_validator("characters", "actions", "moods", "visual_tags")
    @classmethod
    def normalize_labels(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(label.strip() for label in value if label.strip())
        if len({label.casefold() for label in cleaned}) != len(cleaned):
            raise ValueError("description labels must be unique ignoring case")
        return cleaned


class TechnicalQuality(AnalysisModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    aspect_ratio: float = Field(gt=0.0)
    brightness: float = Field(ge=0.0, le=1.0)
    contrast: float = Field(ge=0.0, le=1.0)
    sharpness: float = Field(ge=0.0, le=1.0)
    text_coverage: float = Field(ge=0.0, le=1.0)
    resolution_score: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)


class PageAnalysis(AnalysisModel):
    schema_version: int = Field(default=1, ge=1)
    page_id: str = Field(pattern=r"^page_[0-9a-f]{64}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_locator: str = Field(min_length=1)
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)
    panels: tuple[PanelCandidate, ...]
    text_regions: tuple[TextRegion, ...] = ()
    ocr: OcrResult | None = None
    description: PageDescription = Field(default_factory=PageDescription)
    quality: TechnicalQuality
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_links_and_identity(self) -> PageAnalysis:
        panel_ids = [panel.id for panel in self.panels]
        if len(panel_ids) != len(set(panel_ids)):
            raise ValueError("panel IDs must be unique")
        if not any(panel.is_full_page for panel in self.panels):
            raise ValueError("page analysis must preserve a full-page candidate")
        for panel in self.panels:
            if panel.page_id != self.page_id:
                raise ValueError("panel page_id must match page analysis page_id")
        region_ids = [region.id for region in self.text_regions]
        if len(region_ids) != len(set(region_ids)):
            raise ValueError("text region IDs must be unique")
        allowed_regions = set(region_ids)
        if self.ocr is not None:
            span_ids = [span.id for span in self.ocr.spans]
            if len(span_ids) != len(set(span_ids)):
                raise ValueError("OCR span IDs must be unique")
            missing = {
                span.region_id
                for span in self.ocr.spans
                if span.region_id is not None and span.region_id not in allowed_regions
            }
            if missing:
                raise ValueError(f"OCR spans reference unknown regions: {sorted(missing)}")
        return self
