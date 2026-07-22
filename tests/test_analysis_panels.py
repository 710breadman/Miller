from pathlib import Path

from PIL import Image, ImageDraw

from miller.analysis import GutterPanelDetector

PAGE_ID = "page_" + "c" * 64


def test_gutter_detector_preserves_full_page_and_finds_grid(tmp_path: Path) -> None:
    image = Image.new("RGB", (600, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 285, 385), fill="black")
    draw.rectangle((315, 20, 580, 385), fill="black")
    draw.rectangle((20, 415, 285, 780), fill="black")
    draw.rectangle((315, 415, 580, 780), fill="black")
    path = tmp_path / "page.png"
    image.save(path)

    candidates = GutterPanelDetector(minimum_gutter=8).detect(PAGE_ID, path)
    assert candidates[0].is_full_page
    assert len(candidates) == 5
    assert [candidate.order for candidate in candidates] == list(range(5))
    assert all(candidate.box.area > 0.15 for candidate in candidates[1:])


def test_gutter_detector_falls_back_for_unsplit_page(tmp_path: Path) -> None:
    path = tmp_path / "page.png"
    Image.new("RGB", (400, 600), "black").save(path)
    candidates = GutterPanelDetector().detect(PAGE_ID, path)
    assert len(candidates) == 1
    assert candidates[0].is_full_page
