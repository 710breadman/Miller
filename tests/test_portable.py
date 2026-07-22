from pathlib import Path

from miller.artifacts import ArtifactStore
from miller.db import Database
from miller.models import StageDefinition, StageStatus
from miller.portable import PortableProjectExporter, PortableProjectImporter


def test_portable_project_round_trip_preserves_state_and_artifacts(tmp_path: Path) -> None:
    source_workspace = tmp_path / "source-workspace"
    source_db = Database(tmp_path / "source.sqlite3")
    source_db.initialize()
    project = source_db.create_project(
        "Portable", source_workspace, "project_portable"
    )
    definition = StageDefinition(id="prepare", name="Prepare", version="1")
    source_db.register_stage(definition)
    run = source_db.ensure_stage_run(project.id, definition.id)
    attempt = source_db.begin_attempt(run.id, "sha256:" + "1" * 64)
    store = ArtifactStore(source_workspace, source_db)
    artifact = store.put_json(
        project_id=project.id,
        stage_run_id=run.id,
        value={"result": "ready"},
    )
    source_db.complete_attempt(run.id, attempt.id, attempt.attempt_guard, artifact.id)
    source_db.put_document(
        project.id,
        "storyboard",
        {"schema_version": 1, "scenes": ["scene_0001"]},
        expected_revision=0,
    )
    project_file = source_workspace / "projects" / project.id / "notes.txt"
    project_file.parent.mkdir(parents=True, exist_ok=True)
    project_file.write_text("portable notes", encoding="utf-8")

    package = tmp_path / "project.miller.zip"
    PortableProjectExporter(source_db, source_workspace).export(project.id, package)

    target_workspace = tmp_path / "target-workspace"
    target_db = Database(tmp_path / "target.sqlite3")
    target_db.initialize()
    imported = PortableProjectImporter(target_db, target_workspace).import_package(package)

    assert imported.project.id == project.id
    assert target_db.get_project(project.id).workspace == str(target_workspace)
    restored_run = target_db.get_stage_run(project.id, definition.id)
    assert restored_run.status == StageStatus.COMPLETED
    assert restored_run.output_artifact_id == artifact.id
    restored_artifact = target_db.get_artifact(artifact.id)
    assert (target_workspace / restored_artifact.relative_path).is_file()
    assert target_db.get_document(project.id, "storyboard").document["scenes"] == [
        "scene_0001"
    ]
    assert (
        target_workspace / "projects" / project.id / "notes.txt"
    ).read_text(encoding="utf-8") == "portable notes"
