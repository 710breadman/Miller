from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from pydantic import ValidationError

from miller.analysis import (
    NormalizedBox,
    PageDescription,
    TextRegion,
    measure_technical_quality,
    parse_page_description,
    render_region_mask,
)


def test_mask_is_deterministic_and_quality_reproducible(tmp_path: Path) -> None:
    region = TextRegion(
        id="region_1",
        box=NormalizedBox(x=0.25, y=0.25, width=0.25, height=0.25),
        confidence=1,
        detector="fixture",
        balloon_hint=True,
    )
    first = render_region_mask(200, 100, (region,), padding_pixels=1)
    second = render_region_mask(200, 100, (region,), padding_pixels=1)
    assert first.sha256 == second.sha256
    assert first.payload == second.payload

    image = Image.new("RGB", (640, 480), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 100, 500, 380), fill="black")
    path = tmp_path / "quality.png"
    image.save(path)
    left = measure_technical_quality(path, text_regions=(region,))
    right = measure_technical_quality(path, text_regions=(region,))
    assert left == right
    assert left.text_coverage == region.box.area


def test_description_parser_rejects_invalid_structured_output() -> None:
    description = parse_page_description(
        '{"summary":"A rooftop confrontation","moods":["tense"],"generator":"fixture"}'
    )
    assert isinstance(description, PageDescription)
    with pytest.raises((ValueError, ValidationError)):
        parse_page_description('{"moods":["tense","TENSE"]}')
