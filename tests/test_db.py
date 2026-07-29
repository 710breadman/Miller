import sqlite3
from pathlib import Path

import pytest

from miller.db import _MIGRATIONS, Database, DatabaseIntegrityError, MigrationError
from miller.models import StageDefinition, StageStatus
from miller.transitions import InvalidTransition


def make_db(tmp_path: Path) -> Database:
    db = Database(tmp_path / "miller.sqlite3")
    db.initialize()
    return db


def test_create_project_and_stage_transaction(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    project = db.create_project("Example", tmp_path / "workspace", "project_example")
    db.register_stage(StageDefinition(id="stage_a", name="A", version="1"))
    run = db.ensure_stage_run(project.id, "stage_a")
    assert run.status == StageStatus.PENDING

    attempt = db.begin_attempt(run.id, "sha256:" + "1" * 64)
    running = db.get_stage_run_by_id(run.id)
    assert running.status == StageStatus.RUNNING
    assert running.active_attempt_id == attempt.id

    with pytest.raises(InvalidTransition):
        db.begin_attempt(run.id, "sha256:" + "1" * 64)

    still_running = db.get_stage_run_by_id(run.id)
    assert still_running.status == StageStatus.RUNNING
    assert still_running.active_attempt_id == attempt.id


def test_recover_abandoned_attempt(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    project = db.create_project("Example", tmp_path / "workspace", "project_example")
    db.register_stage(StageDefinition(id="stage_a", name="A", version="1"))
    run = db.ensure_stage_run(project.id, "stage_a")
    db.begin_attempt(run.id, "sha256:" + "2" * 64)

    assert db.recover_abandoned() == 1
    recovered = db.get_stage_run_by_id(run.id)
    assert recovered.status == StageStatus.FAILED
    assert recovered.active_attempt_id is None


def test_migrations_are_dense_ordered_and_reach_latest_version() -> None:
    versions = [migration.version for migration in _MIGRATIONS]
    assert versions == sorted(versions)
    assert versions == list(range(1, versions[-1] + 1))


def test_initialize_fresh_database_creates_no_backup(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    assert not (tmp_path / "backups").exists()
    db.verify_integrity()


def test_initialize_migrates_legacy_database_with_ordered_steps_and_backup(
    tmp_path: Path,
) -> None:
    path = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(_MIGRATIONS[0].script)
    connection.execute("INSERT INTO schema_meta(version) VALUES (1)")
    connection.commit()
    connection.close()

    db = Database(path)
    db.initialize()

    verify = sqlite3.connect(path)
    try:
        version_row = verify.execute("SELECT version FROM schema_meta").fetchone()
        tables = {
            row[0]
            for row in verify.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        verify.close()
    assert version_row is not None and version_row[0] == 3
    assert {"project_documents", "project_document_history", "work_queue"} <= tables

    backups = list((tmp_path / "backups").glob("legacy.*.sqlite3"))
    assert len(backups) == 1
    assert "pre-migration-v1-to-v3" in backups[0].name

    backup_connection = sqlite3.connect(backups[0])
    try:
        backup_version = backup_connection.execute(
            "SELECT version FROM schema_meta"
        ).fetchone()
    finally:
        backup_connection.close()
    assert backup_version is not None and backup_version[0] == 1


def test_initialize_detects_corrupt_database(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.sqlite3"
    path.write_bytes(b"not a sqlite database")

    with pytest.raises(DatabaseIntegrityError):
        Database(path).initialize()


def test_initialize_rejects_database_from_newer_schema(tmp_path: Path) -> None:
    path = tmp_path / "future.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(_MIGRATIONS[0].script)
    connection.execute("INSERT INTO schema_meta(version) VALUES (99)")
    connection.commit()
    connection.close()

    with pytest.raises(MigrationError):
        Database(path).initialize()


def test_backup_and_restore_drill_recovers_data(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    project = db.create_project("Example", tmp_path / "workspace", "project_example")

    backup_path = db.create_backup(reason="drill")
    assert backup_path.exists()

    db.path.write_bytes(b"corrupted")
    with pytest.raises(DatabaseIntegrityError):
        db.verify_integrity()

    db.restore_from_backup(backup_path)

    db.verify_integrity()
    restored = db.get_project(project.id)
    assert restored.id == project.id
    assert restored.name == "Example"


def test_restore_from_backup_rejects_corrupt_backup(tmp_path: Path) -> None:
    db = make_db(tmp_path)
    db.create_project("Example", tmp_path / "workspace", "project_example")

    fake_backup = tmp_path / "fake_backup.sqlite3"
    fake_backup.write_bytes(b"not a sqlite database")

    with pytest.raises(DatabaseIntegrityError):
        db.restore_from_backup(fake_backup)

    db.verify_integrity()
