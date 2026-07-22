from pathlib import Path

import pytest
from pydantic import ValidationError

from miller.analysis import (
    NormalizedBox,
    OcrResult,
    OcrSpan,
    PageAnalysis,
    PageDescription,
    PanelCandidate,
    PanelSource,
    TechnicalQuality,
    TextRegion,
)

PAGE_ID = "page_" + "a" * 64


def quality() -> TechnicalQuality:
    return TechnicalQuality(
        width=1000,
        height=1500,
        aspect_ratio=2 / 3,
        brightness=0.5,
        contrast=0.4,
        sharpness=0.7,
        text_coverage=0.1,
        resolution_score=0.8,
        overall_score=0.65,
    )


def full_page() -> PanelCandidate:
    return PanelCandidate(
        id="panel_fixture_full",
        page_id=PAGE_ID,
        box=NormalizedBox(x=0, y=0, width=1, height=1),
        order=0,
        confidence=1,
        source=PanelSource.FULL_PAGE,
        is_full_page=True,
    )


def test_page_analysis_round_trip_and_region_links(tmp_path: Path) -> None:
    region = TextRegion(
        id="region_dialogue_1",
        box=NormalizedBox(x=0.1, y=0.1, width=0.3, height=0.2),
        confidence=0.9,
        detector="fixture",
    )
    ocr = OcrResult(
        engine="fixture",
        engine_version="1",
        language="eng",
        spans=(
            OcrSpan(
                id="ocr_1",
                text="With great power",
                box=region.box,
                confidence=0.95,
                language="eng",
                region_id=region.id,
            ),
        ),
    )
    record = PageAnalysis(
        page_id=PAGE_ID,
        source_sha256="b" * 64,
        source_locator="Example/Issue 1/page-001.png",
        image_width=1000,
        image_height=1500,
        panels=(full_page(),),
        text_regions=(region,),
        ocr=ocr,
        description=PageDescription(
            summary="A hero reflects on responsibility.",
            characters=("Hero",),
            moods=("reflective",),
            confidence=0.8,
            generator="fixture",
        ),
        quality=quality(),
    )
    path = tmp_path / "analysis.json"
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    restored = PageAnalysis.model_validate_json(path.read_text(encoding="utf-8"))
    assert restored == record


def test_invalid_coordinates_and_missing_full_page_reject() -> None:
    with pytest.raises(ValidationError):
        NormalizedBox(x=0.9, y=0.0, width=0.2, height=1.0)
    with pytest.raises(ValidationError):
        PageAnalysis(
            page_id=PAGE_ID,
            source_sha256="b" * 64,
            source_locator="page.png",
            image_width=100,
            image_height=100,
            panels=(),
            quality=quality(),
        )
