import math
import struct
import wave
from pathlib import Path

import pytest
from PIL import Image

from miller.analysis import ComicAnalysisPipeline
from miller.db import Database
from miller.pipeline import BaselineVideoPipeline
from miller.video import RenderProfile


def write_tone(path: Path, duration: float = 1.5, rate: int = 16_000) -> None:
    frames = int(duration * rate)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(
            b"".join(
                struct.pack("<h", int(3000 * math.sin(2 * math.pi * 330 * index / rate)))
                for index in range(frames)
            )
        )


def comic_folder(path: Path) -> Path:
    path.mkdir()
    Image.new("RGB", (320, 480), (40, 60, 90)).save(path / "responsibility_1.png")
    Image.new("RGB", (320, 480), (90, 40, 50)).save(path / "city_2.png")
    return path


def test_no_ai_analysis_produces_searchable_records(tmp_path: Path) -> None:
    source = comic_folder(tmp_path / "comic")
    result = ComicAnalysisPipeline(tmp_path / "workspace").analyze(
        source,
        use_ocr=False,
        index_path=tmp_path / "analysis.sqlite3",
    )
    assert len(result.pages) == 2
    assert all(page.panels[0].is_full_page for page in result.pages)
    assert set(result.asset_paths) == {page.page_id for page in result.pages}
    assert all(Path(path).is_file() for path in result.asset_paths.values())


@pytest.mark.skipif(not __import__("shutil").which("ffmpeg"), reason="FFmpeg unavailable")
def test_no_ai_pipeline_reaches_verified_mp4(tmp_path: Path) -> None:
    source = comic_folder(tmp_path / "comic")
    narration = tmp_path / "narration.wav"
    write_tone(narration)
    workspace = tmp_path / "workspace"
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Baseline", workspace, "project_baseline")
    output = tmp_path / "baseline.mp4"

    result = BaselineVideoPipeline(database, workspace).run(
        "project_baseline",
        comic_source=source,
        script="Responsibility pulls the hero back to the city.",
        narration_path=narration,
        output_path=output,
        use_ocr=False,
        profile=RenderProfile(width=320, height=240, fps=12, threads=1),
    )
    assert output.is_file()
    assert result.render.output_sha256
    assert result.storyboard.scenes
    assert result.alignment.engine == "uniform-fallback"
    assert database.get_document("project_baseline", "render.last").revision == 1
