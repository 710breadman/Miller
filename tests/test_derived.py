from pathlib import Path

from PIL import Image, ImageDraw

from miller.analysis import (
    NormalizedBox,
    PanelCandidate,
    PanelSource,
    TextRegion,
)
from miller.artifacts import sha256_file
from miller.derived import DerivedAssetPipeline, DerivedMethod, choose_clean_crop

PAGE_ID = "page_" + "a" * 64


def test_clean_crop_prefers_text_free_panel() -> None:
    text = TextRegion(
        id="region_1",
        box=NormalizedBox(x=0.05, y=0.05, width=0.4, height=0.2),
        confidence=1,
        detector="fixture",
    )
    panels = (
        PanelCandidate(
            id="panel_left",
            page_id=PAGE_ID,
            box=NormalizedBox(x=0, y=0, width=0.5, height=1),
            order=1,
            confidence=1,
            source=PanelSource.MANUAL,
        ),
        PanelCandidate(
            id="panel_right",
            page_id=PAGE_ID,
            box=NormalizedBox(x=0.5, y=0, width=0.5, height=1),
            order=2,
            confidence=1,
            source=PanelSource.MANUAL,
        ),
    )
    choice = choose_clean_crop((text,), target_aspect=0.5, panels=panels)
    assert choice.source == "panel_right"
    assert choice.text_coverage == 0


def test_derived_asset_is_reproducible_and_source_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "page.png"
    image = Image.new("RGB", (400, 300), "beige")
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 100, 300, 160), fill="white")
    draw.text((120, 115), "DIALOGUE", fill="black")
    image.save(source)
    before = sha256_file(source)
    region = TextRegion(
        id="region_dialogue",
        box=NormalizedBox(x=0.24, y=0.31, width=0.53, height=0.25),
        confidence=1,
        detector="fixture",
        balloon_hint=True,
    )
    pipeline = DerivedAssetPipeline(tmp_path / "workspace")
    first = pipeline.derive(source, (region,), target_aspect=4 / 3)
    second = pipeline.derive(source, (region,), target_aspect=4 / 3)
    assert first.method == DerivedMethod.SIMPLE_FILL
    assert first.output_sha256 == second.output_sha256
    assert Path(first.output_path).read_bytes() == Path(second.output_path).read_bytes()
    assert sha256_file(source) == before
