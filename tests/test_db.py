from pathlib import Path

import pytest

from miller.db import Database
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
