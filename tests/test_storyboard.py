from miller.analysis import (
    NormalizedBox,
    OcrResult,
    OcrSpan,
    PageAnalysis,
    PageDescription,
    PanelCandidate,
    PanelSource,
    TechnicalQuality,
)
from miller.audio import BeatPlan, NarrationBeat
from miller.storyboard import SearchScope, StoryboardBuilder, propose_search_scope


def page(
    letter: str,
    summary: str,
    ocr: str,
    character: str,
    mood: str,
    quality: float,
) -> PageAnalysis:
    page_id = "page_" + letter * 64
    return PageAnalysis(
        page_id=page_id,
        source_sha256=letter * 64,
        source_locator=f"Example Series/Issue 1/{letter}.png",
        image_width=800,
        image_height=1200,
        panels=(
            PanelCandidate(
                id=f"panel_{letter}_full",
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
                    id=f"ocr_{letter}",
                    text=ocr,
                    box=NormalizedBox(x=0.1, y=0.1, width=0.3, height=0.1),
                    confidence=1,
                ),
            ),
        ),
        description=PageDescription(
            summary=summary,
            characters=(character,),
            moods=(mood,),
            visual_tags=("city",) if "city" in summary.casefold() else (),
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
            overall_score=quality,
        ),
    )


def test_scope_and_storyboard_are_complete_traceable_and_respect_locks() -> None:
    records = (
        page(
            "a",
            "Peter accepts responsibility in the city",
            "great power",
            "Peter",
            "reflective",
            0.9,
        ),
        page("b", "Peter swings over the city", "save them", "Peter", "urgent", 0.8),
        page("c", "Bruce watches another city", "vengeance", "Bruce", "grim", 0.95),
    )
    scope = propose_search_scope(
        "Peter accepts responsibility. Peter returns to the city.",
        records,
        steering_keywords=("reflective", "Example Series"),
        exclusions=("Bruce",),
    )
    assert scope.characters == ("Peter",)
    assert "Bruce" not in scope.characters

    beats = BeatPlan(
        audio_duration_seconds=6.0,
        beats=(
            NarrationBeat(
                id="beat_0001",
                section_index=0,
                start=0,
                end=3,
                text="Peter accepts responsibility.",
                first_word_index=0,
                last_word_index=3,
            ),
            NarrationBeat(
                id="beat_0002",
                section_index=0,
                start=3,
                end=6,
                text="Peter returns to the city.",
                first_word_index=4,
                last_word_index=8,
            ),
        ),
    )
    plan = StoryboardBuilder(records).build(
        beats,
        scope,
        excluded_assets=frozenset({records[2].page_id}),
        locked_choices={"beat_0002": records[1].page_id},
    )
    assert len(plan.scenes) == 2
    assert plan.scenes[0].start == 0
    assert plan.scenes[-1].end == 6
    assert plan.scenes[1].primary_asset == records[1].page_id
    assert plan.scenes[1].locked
    assert records[2].page_id not in {
        candidate.asset_id for scene in plan.scenes for candidate in scene.candidates
    }
    assert plan.scenes[0].candidates[0].reasons


def test_imported_narrative_rank_combines_without_replacing_miller_quality() -> None:
    first = page("a", "A quiet room", "wait", "Peter", "calm", 0.9)
    second = page("b", "A quiet room", "wait", "Peter", "calm", 0.4)
    beats = BeatPlan(
        audio_duration_seconds=2.0,
        beats=(
            NarrationBeat(
                id="beat_0001",
                section_index=0,
                start=0,
                end=2,
                text="A quiet room",
                first_word_index=0,
                last_word_index=2,
            ),
        ),
    )
    plan = StoryboardBuilder((first, second), narrative_scores={second.page_id: 1.0}).build(
        beats, SearchScope(characters=("Peter",))
    )
    imported = next(
        candidate for candidate in plan.scenes[0].candidates if candidate.asset_id == second.page_id
    )
    assert imported.score.narrative == 1.0
    assert imported.score.quality == 0.4
    assert "comic-sorter-narrative=1.000" in imported.reasons
