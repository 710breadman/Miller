from miller.models import Project, StageDefinition


def test_schema_smoke() -> None:
    project = Project(id="project_demo", name="Demo", workspace="workspace")
    stage = StageDefinition(id="prepare", name="Prepare", version="1")
    assert project.id == "project_demo"
    assert stage.dependencies == ()
