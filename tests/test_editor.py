from pathlib import Path

import pytest

from miller.analysis import NormalizedPoint
from miller.db import Database, DocumentConflict
from miller.editor import (
    ReplaceAssetCommand,
    SaveStoryboardCommand,
    SetLockCommand,
    SetMotionCommand,
    StoryboardEditor,
)
from miller.storyboard import (
    CameraPlan,
    CameraPreset,
    SceneCandidate,
    SceneScore,
    SearchScope,
    StoryboardPlan,
    StoryboardScene,
)


def score(value: float) -> SceneScore:
    return SceneScore(
        lexical=value,
        character=value,
        theme=value,
        continuity=value,
        quality=value,
        reuse_penalty=0,
        total=value,
    )


def plan() -> StoryboardPlan:
    candidates = (
        SceneCandidate(asset_id="page_a", source_locator="a.png", score=score(0.9)),
        SceneCandidate(asset_id="page_b", source_locator="b.png", score=score(0.8)),
    )
    return StoryboardPlan(
        scope=SearchScope(characters=("Peter",)),
        scenes=(
            StoryboardScene(
                id="scene_0001",
                beat_id="beat_0001",
                start=0,
                end=3,
                narration="Peter accepts responsibility.",
                intent="Peter accepts responsibility.",
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


def editor(tmp_path: Path) -> StoryboardEditor:
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Editor", tmp_path / "workspace", "project_editor")
    return StoryboardEditor(database)


def test_editor_preserves_revisions_and_changes_only_target_scene(tmp_path: Path) -> None:
    service = editor(tmp_path)
    first = service.save(
        "project_editor",
        SaveStoryboardCommand(expected_revision=0, storyboard=plan()),
    )
    second = service.replace_asset(
        "project_editor",
        ReplaceAssetCommand(
            expected_revision=first.revision,
            scene_id="scene_0001",
            asset_id="page_b",
        ),
    )
    assert first.revision == 1
    assert second.revision == 2
    scene = second.storyboard.scenes[0]
    assert scene.primary_asset == "page_b"
    assert scene.alternatives == ("page_a",)
    assert scene.review_status == "manual"
    assert [item.revision for item in service.history("project_editor")] == [1, 2]


def test_lock_blocks_edits_but_can_be_unlocked(tmp_path: Path) -> None:
    service = editor(tmp_path)
    current = service.save(
        "project_editor",
        SaveStoryboardCommand(expected_revision=0, storyboard=plan()),
    )
    locked = service.set_lock(
        "project_editor",
        SetLockCommand(
            expected_revision=current.revision,
            scene_id="scene_0001",
            locked=True,
        ),
    )
    with pytest.raises(ValueError, match="locked"):
        service.set_motion(
            "project_editor",
            SetMotionCommand(
                expected_revision=locked.revision,
                scene_id="scene_0001",
                preset=CameraPreset.STATIC,
            ),
        )
    unlocked = service.set_lock(
        "project_editor",
        SetLockCommand(
            expected_revision=locked.revision,
            scene_id="scene_0001",
            locked=False,
        ),
    )
    changed = service.set_motion(
        "project_editor",
        SetMotionCommand(
            expected_revision=unlocked.revision,
            scene_id="scene_0001",
            preset=CameraPreset.STATIC,
        ),
    )
    assert changed.storyboard.scenes[0].camera.preset == CameraPreset.STATIC


def test_stale_revision_is_rejected(tmp_path: Path) -> None:
    service = editor(tmp_path)
    current = service.save(
        "project_editor",
        SaveStoryboardCommand(expected_revision=0, storyboard=plan()),
    )
    service.set_lock(
        "project_editor",
        SetLockCommand(
            expected_revision=current.revision,
            scene_id="scene_0001",
            locked=True,
        ),
    )
    with pytest.raises((ValueError, DocumentConflict), match="revision"):
        service.set_lock(
            "project_editor",
            SetLockCommand(
                expected_revision=current.revision,
                scene_id="scene_0001",
                locked=False,
            ),
        )
