import sqlite3
from pathlib import Path

import pytest

from miller.artifacts import ArtifactStore
from miller.db import _MIGRATIONS, Database, DocumentConflict
from miller.models import StageDefinition, StageStatus


def test_document_revision_history_and_conflict(tmp_path: Path) -> None:
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Editor", tmp_path / "workspace", "project_editor")

    first = database.put_document(
        "project_editor",
        "storyboard",
        {"scenes": [{"id": "scene_0001"}]},
        expected_revision=0,
    )
    second = database.put_document(
        "project_editor",
        "storyboard",
        {"scenes": [{"id": "scene_0001"}, {"id": "scene_0002"}]},
        expected_revision=1,
    )
    assert first.revision == 1
    assert second.revision == 2
    assert database.get_document("project_editor", "storyboard") == second
    history = database.list_document_history("project_editor", "storyboard")
    assert [item.revision for item in history] == [1, 2]

    with pytest.raises(DocumentConflict):
        database.put_document(
            "project_editor",
            "storyboard",
            {"scenes": []},
            expected_revision=1,
        )


def test_schema_version_one_migrates_additively(tmp_path: Path) -> None:
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE schema_meta(version INTEGER NOT NULL)")
        connection.execute("INSERT INTO schema_meta(version) VALUES (1)")
    database = Database(path)
    database.initialize()
    with database.connect() as connection:
        version = connection.execute("SELECT version FROM schema_meta").fetchone()
        documents = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='project_documents'"
        ).fetchone()
    assert version is not None and int(version["version"]) == _MIGRATIONS[-1].version
    assert documents is not None


def test_storyboard_edit_invalidates_only_stage_and_dependents(tmp_path: Path) -> None:
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    project = database.create_project("Editor", tmp_path / "workspace", "project_editor")
    definitions = (
        StageDefinition(id="ingest", name="Ingest", version="1"),
        StageDefinition(
            id="storyboard",
            name="Storyboard",
            version="1",
            dependencies=("ingest",),
        ),
        StageDefinition(
            id="render",
            name="Render",
            version="1",
            dependencies=("storyboard",),
        ),
    )
    store = ArtifactStore(tmp_path / "workspace", database)
    for definition in definitions:
        database.register_stage(definition)
        run = database.ensure_stage_run(project.id, definition.id)
        fingerprint = f"sha256:{definition.id.encode().hex():0<64}"[:71]
        attempt = database.begin_attempt(run.id, fingerprint)
        artifact = store.put_json(
            project_id=project.id,
            stage_run_id=run.id,
            value={"stage": definition.id},
        )
        database.complete_attempt(run.id, attempt.id, attempt.attempt_guard, artifact.id)

    invalidated = database.invalidate_stage_tree(
        project.id,
        "storyboard",
        reason="scene override",
    )
    assert invalidated == ("storyboard", "render")
    assert database.get_stage_run(project.id, "ingest").status == StageStatus.COMPLETED
    assert database.get_stage_run(project.id, "storyboard").status == StageStatus.PENDING
    assert database.get_stage_run(project.id, "render").status == StageStatus.PENDING
