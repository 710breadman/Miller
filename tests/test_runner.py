from pathlib import Path
from typing import Any

import pytest

from miller.db import Database
from miller.models import StageDefinition, StageStatus
from miller.runner import PipelineRunner, RuntimeStage, StageContext, StageExecutionError


def build_runner(tmp_path: Path, calls: dict[str, int]) -> tuple[Database, PipelineRunner, str]:
    db = Database(tmp_path / "miller.sqlite3")
    db.initialize()
    project = db.create_project("Example", tmp_path / "workspace", "project_example")

    def handler(name: str):
        def run(context: StageContext) -> dict[str, Any]:
            calls[name] = calls.get(name, 0) + 1
            if context.config.get("fail"):
                raise RuntimeError(f"{name} failed")
            return {
                "name": name,
                "config": dict(context.config),
                "inputs": [artifact.content_id for artifact in context.dependency_artifacts],
            }

        return run

    runner = PipelineRunner(
        db,
        tmp_path / "workspace",
        [
            RuntimeStage(StageDefinition(id="a", name="A", version="1"), handler("a")),
            RuntimeStage(
                StageDefinition(id="b", name="B", version="1", dependencies=("a",)),
                handler("b"),
            ),
            RuntimeStage(
                StageDefinition(id="c", name="C", version="1", dependencies=("b",)),
                handler("c"),
            ),
        ],
    )
    return db, runner, project.id


def test_cache_and_scoped_invalidation(tmp_path: Path) -> None:
    calls: dict[str, int] = {}
    db, runner, project_id = build_runner(tmp_path, calls)
    first = runner.run(project_id, configs={"a": {"value": 1}})
    assert calls == {"a": 1, "b": 1, "c": 1}

    second = runner.run(project_id, configs={"a": {"value": 1}})
    assert calls == {"a": 1, "b": 1, "c": 1}
    assert first["c"].content_id == second["c"].content_id

    runner.run(project_id, configs={"a": {"value": 2}})
    assert calls == {"a": 2, "b": 2, "c": 2}
    assert all(run.status == StageStatus.COMPLETED for run in db.list_stage_runs(project_id))


def test_missing_cached_artifact_is_rebuilt_without_rerunning_dependents(
    tmp_path: Path,
) -> None:
    calls: dict[str, int] = {}
    db, runner, project_id = build_runner(tmp_path, calls)
    first = runner.run(project_id)
    runner.artifacts.resolve(first["a"]).unlink()

    second = runner.run(project_id)

    assert calls == {"a": 2, "b": 1, "c": 1}
    assert runner.artifacts.resolve(second["a"]).is_file()
    assert first["a"].content_id == second["a"].content_id


def test_failed_stage_resumes_without_rerunning_completed_dependency(tmp_path: Path) -> None:
    calls: dict[str, int] = {}
    db, runner, project_id = build_runner(tmp_path, calls)

    with pytest.raises(StageExecutionError):
        runner.run(project_id, configs={"b": {"fail": True}})
    assert calls == {"a": 1, "b": 1}
    assert db.get_stage_run(project_id, "a").status == StageStatus.COMPLETED
    assert db.get_stage_run(project_id, "b").status == StageStatus.FAILED

    runner.run(project_id)
    assert calls == {"a": 1, "b": 2, "c": 1}
    assert db.get_stage_run(project_id, "c").status == StageStatus.COMPLETED
