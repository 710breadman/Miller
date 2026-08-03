import json
import math
import struct
import wave
from pathlib import Path

import pytest
from PIL import Image

from miller.analysis import ComicAnalysisPipeline
from miller.db import Database
from miller.models import StageStatus
from miller.pipeline import BaselineVideoPipeline
from miller.runner import StageExecutionError
from miller.video import FFmpegRenderer, RenderProfile


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


@pytest.mark.skipif(not __import__("shutil").which("ffmpeg"), reason="FFmpeg unavailable")
def test_baseline_pipeline_reuses_durable_stage_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = comic_folder(tmp_path / "comic")
    narration = tmp_path / "narration.wav"
    write_tone(narration)
    workspace = tmp_path / "workspace"
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Baseline", workspace, "project_cache")
    output = tmp_path / "baseline.mp4"
    calls = {"analysis": 0, "render": 0}
    original_analyze = ComicAnalysisPipeline.analyze
    original_render = FFmpegRenderer.render

    def count_analyze(*args: object, **kwargs: object):
        calls["analysis"] += 1
        return original_analyze(*args, **kwargs)

    def count_render(*args: object, **kwargs: object):
        calls["render"] += 1
        return original_render(*args, **kwargs)

    monkeypatch.setattr(ComicAnalysisPipeline, "analyze", count_analyze)
    monkeypatch.setattr(FFmpegRenderer, "render", count_render)
    pipeline = BaselineVideoPipeline(database, workspace)
    arguments = {
        "comic_source": source,
        "script": "Responsibility pulls the hero back to the city.",
        "narration_path": narration,
        "output_path": output,
        "use_ocr": False,
        "profile": RenderProfile(width=320, height=240, fps=12, threads=1),
    }

    first = pipeline.run("project_cache", **arguments)
    second = pipeline.run("project_cache", **arguments)

    assert calls == {"analysis": 1, "render": 1}
    assert first.render.output_sha256 == second.render.output_sha256
    assert all(
        run.status == StageStatus.COMPLETED
        for run in database.list_stage_runs("project_cache")
    )
    event_log = workspace / "projects" / "project_cache" / "logs" / "events.jsonl"
    cache_hits = [
        record
        for line in event_log.read_text(encoding="utf-8").splitlines()
        if (record := json.loads(line))["kind"] == "stage.cache_hit"
    ]
    assert len(cache_hits) == 5


@pytest.mark.skipif(not __import__("shutil").which("ffmpeg"), reason="FFmpeg unavailable")
def test_baseline_pipeline_rerenders_when_cached_output_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = comic_folder(tmp_path / "comic")
    narration = tmp_path / "narration.wav"
    write_tone(narration)
    workspace = tmp_path / "workspace"
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Baseline", workspace, "project_missing_output")
    output = tmp_path / "baseline.mp4"
    calls = 0
    original_render = FFmpegRenderer.render

    def count_render(*args: object, **kwargs: object):
        nonlocal calls
        calls += 1
        return original_render(*args, **kwargs)

    monkeypatch.setattr(FFmpegRenderer, "render", count_render)
    pipeline = BaselineVideoPipeline(database, workspace)
    arguments = {
        "comic_source": source,
        "script": "Responsibility pulls the hero back to the city.",
        "narration_path": narration,
        "output_path": output,
        "use_ocr": False,
        "profile": RenderProfile(width=320, height=240, fps=12, threads=1),
    }

    first = pipeline.run("project_missing_output", **arguments)
    output.unlink()
    second = pipeline.run("project_missing_output", **arguments)

    assert output.is_file()
    assert first.render.output_sha256 == second.render.output_sha256
    assert calls == 2
    assert any(
        json.loads(line)["kind"] == "stage.cache_invalid"
        for line in (
            workspace
            / "projects"
            / "project_missing_output"
            / "logs"
            / "events.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
    )


@pytest.mark.skipif(not __import__("shutil").which("ffmpeg"), reason="FFmpeg unavailable")
def test_baseline_pipeline_recovers_abandoned_render_without_recomputing_predecessors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = comic_folder(tmp_path / "comic")
    narration = tmp_path / "narration.wav"
    write_tone(narration)
    workspace = tmp_path / "workspace"
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Baseline", workspace, "project_restart")
    output = tmp_path / "baseline.mp4"
    calls = {"analysis": 0, "render": 0}
    original_analyze = ComicAnalysisPipeline.analyze
    original_render = FFmpegRenderer.render

    def count_analyze(*args: object, **kwargs: object):
        calls["analysis"] += 1
        return original_analyze(*args, **kwargs)

    def fail_once(*args: object, **kwargs: object):
        calls["render"] += 1
        if calls["render"] == 1:
            raise RuntimeError("synthetic render interruption")
        return original_render(*args, **kwargs)

    monkeypatch.setattr(ComicAnalysisPipeline, "analyze", count_analyze)
    monkeypatch.setattr(FFmpegRenderer, "render", fail_once)
    pipeline = BaselineVideoPipeline(database, workspace)
    arguments = {
        "comic_source": source,
        "script": "Responsibility pulls the hero back to the city.",
        "narration_path": narration,
        "output_path": output,
        "use_ocr": False,
        "profile": RenderProfile(width=320, height=240, fps=12, threads=1),
    }

    with pytest.raises(StageExecutionError, match="baseline.render"):
        pipeline.run("project_restart", **arguments)
    assert calls == {"analysis": 1, "render": 1}
    render_run = database.get_stage_run("project_restart", "baseline.render")
    assert render_run.status == StageStatus.FAILED
    assert render_run.input_fingerprint is not None
    database.begin_attempt(render_run.id, render_run.input_fingerprint)

    result = pipeline.run("project_restart", **arguments)

    assert output.is_file()
    assert result.render.output_sha256
    assert calls == {"analysis": 1, "render": 2}
    assert database.get_stage_run("project_restart", "baseline.render").status == (
        StageStatus.COMPLETED
    )
    assert any(
        event.kind == "attempt.abandoned"
        for event in database.list_events("project_restart")
    )
