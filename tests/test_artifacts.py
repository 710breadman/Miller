from pathlib import Path

import pytest

from miller.artifacts import ArtifactStore, sha256_file, stage_fingerprint
from miller.db import Database


def test_artifact_is_stable_and_source_untouched(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    source = tmp_path / "source.cbz"
    source.write_bytes(b"source-data")
    before = sha256_file(source)

    db = Database(tmp_path / "miller.sqlite3")
    db.initialize()
    db.create_project("Example", workspace, "project_example")
    store = ArtifactStore(workspace, db)

    first = store.put_bytes(
        project_id="project_example",
        stage_run_id=None,
        payload=b"derived-data",
        suffix=".txt",
        media_type="text/plain",
    )
    second = store.put_bytes(
        project_id="project_example",
        stage_run_id=None,
        payload=b"derived-data",
        suffix=".txt",
        media_type="text/plain",
    )

    assert first.id == second.id
    assert first.content_id == second.content_id
    assert store.resolve(first).read_bytes() == b"derived-data"
    assert sha256_file(source) == before


def test_project_path_escape_rejected(tmp_path: Path) -> None:
    db = Database(tmp_path / "miller.sqlite3")
    db.initialize()
    store = ArtifactStore(tmp_path / "workspace", db)
    with pytest.raises(ValueError):
        store.ensure_project_layout("../escape")


def test_stage_fingerprint_is_canonical() -> None:
    left = stage_fingerprint(
        stage_id="a",
        stage_version="1",
        config={"b": 2, "a": 1},
        dependency_artifacts=["sha256:" + "1" * 64],
    )
    right = stage_fingerprint(
        stage_id="a",
        stage_version="1",
        config={"a": 1, "b": 2},
        dependency_artifacts=["sha256:" + "1" * 64],
    )
    assert left == right
