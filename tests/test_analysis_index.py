from pathlib import Path

from miller.analysis import (
    AnalysisIndex,
    NormalizedBox,
    OcrResult,
    OcrSpan,
    PageAnalysis,
    PageDescription,
    PanelCandidate,
    PanelSource,
    TechnicalQuality,
)


def record(page_letter: str, text: str, character: str, mood: str) -> PageAnalysis:
    page_id = "page_" + page_letter * 64
    return PageAnalysis(
        page_id=page_id,
        source_sha256=page_letter * 64,
        source_locator=f"Series/Issue/page-{page_letter}.png",
        image_width=800,
        image_height=1200,
        panels=(
            PanelCandidate(
                id=f"panel_{page_letter}_full",
                page_id=page_id,
                box=NormalizedBox(x=0, y=0, width=1, height=1),
                order=0,
                confidence=1,
                source=PanelSource.FULL_PAGE,
                is_full_page=True,
            ),
        ),
        ocr=OcrResult(
            engine="fixture",
            engine_version="1",
            language="eng",
            spans=(
                OcrSpan(
                    id=f"ocr_{page_letter}",
                    text=text,
                    box=NormalizedBox(x=0.1, y=0.1, width=0.4, height=0.1),
                    confidence=1,
                ),
            ),
        ),
        description=PageDescription(
            summary=text,
            characters=(character,),
            moods=(mood,),
            confidence=1,
            generator="fixture",
        ),
        quality=TechnicalQuality(
            width=800,
            height=1200,
            aspect_ratio=2 / 3,
            brightness=0.5,
            contrast=0.5,
            sharpness=0.5,
            text_coverage=0.1,
            resolution_score=0.7,
            overall_score=0.6,
        ),
    )


def test_analysis_index_searches_ocr_and_metadata(tmp_path: Path) -> None:
    index = AnalysisIndex(tmp_path / "analysis.sqlite3")
    index.initialize()
    spider = record("a", "Responsibility follows power", "Peter", "reflective")
    bat = record("b", "The city needs a symbol", "Bruce", "grim")
    index.upsert(spider)
    index.upsert(bat)

    assert index.count() == 2
    assert index.get(spider.page_id) == spider
    assert index.search("responsibility", character="Peter") == [spider]
    assert index.search("symbol", mood="grim") == [bat]
    assert index.search("missing") == []
