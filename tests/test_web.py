from pathlib import Path

from fastapi.testclient import TestClient

from miller.analysis import NormalizedPoint
from miller.db import Database
from miller.storyboard import (
    CameraPlan,
    CameraPreset,
    SceneCandidate,
    SceneScore,
    SearchScope,
    StoryboardPlan,
    StoryboardScene,
)
from miller.web import create_app


def storyboard() -> StoryboardPlan:
    score = SceneScore(
        lexical=0.9,
        character=0.9,
        theme=0.9,
        continuity=0.9,
        quality=0.9,
        reuse_penalty=0,
        total=0.9,
    )
    candidates = (
        SceneCandidate(asset_id="page_a", source_locator="a.png", score=score),
        SceneCandidate(asset_id="page_b", source_locator="b.png", score=score),
    )
    return StoryboardPlan(
        scope=SearchScope(characters=("Peter",)),
        scenes=(
            StoryboardScene(
                id="scene_0001",
                beat_id="beat_0001",
                start=0,
                end=2,
                narration="Peter accepts responsibility.",
                intent="Responsibility",
                primary_asset="page_a",
                alternatives=("page_b",),
                candidates=candidates,
                camera=CameraPlan(
                    preset=CameraPreset.SLOW_PUSH,
                    focus=NormalizedPoint(x=0.5, y=0.5),
                ),
            ),
        ),
    )


def client(tmp_path: Path) -> TestClient:
    database_path = tmp_path / "miller.sqlite3"
    database = Database(database_path)
    database.initialize()
    database.create_project("Web", tmp_path / "workspace", "project_web")
    return TestClient(create_app(database_path))


def test_health_and_editor_page(tmp_path: Path) -> None:
    web = client(tmp_path)
    assert web.get("/health").json()["status"] == "ok"
    page = web.get("/")
    assert page.status_code == 200
    assert "Miller Storyboard Editor" in page.text


def test_storyboard_commands_and_revision_conflict(tmp_path: Path) -> None:
    web = client(tmp_path)
    saved = web.put(
        "/api/projects/project_web/storyboard",
        json={"expected_revision": 0, "storyboard": storyboard().model_dump(mode="json")},
    )
    assert saved.status_code == 200
    assert saved.json()["revision"] == 1

    changed = web.post(
        "/api/projects/project_web/commands/replace-asset",
        json={
            "expected_revision": 1,
            "scene_id": "scene_0001",
            "asset_id": "page_b",
        },
    )
    assert changed.status_code == 200
    assert changed.json()["storyboard"]["scenes"][0]["primary_asset"] == "page_b"

    stale = web.post(
        "/api/projects/project_web/commands/lock",
        json={"expected_revision": 1, "scene_id": "scene_0001", "locked": True},
    )
    assert stale.status_code == 409

    history = web.get("/api/projects/project_web/storyboard/history")
    assert [item["revision"] for item in history.json()] == [1, 2]


def test_missing_storyboard_is_not_found(tmp_path: Path) -> None:
    web = client(tmp_path)
    response = web.get("/api/projects/project_web/storyboard")
    assert response.status_code == 404
