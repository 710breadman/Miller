import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from miller.cli import main
from miller.comic_sorter_import import (
    ComicSorterBundleImporter,
    combine_candidate_score,
    load_comic_sorter_schema,
)
from miller.db import Database

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "comic sorter"
    / "tests"
    / "fixtures"
    / "narrative"
    / "miller-bundle-valid.json"
)
AUTHORITATIVE_SCHEMA = (
    Path(__file__).resolve().parents[2] / "comic sorter" / "schemas" / "miller-bundle.schema.json"
)


def _bundle() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _database(tmp_path: Path) -> Database:
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Fixture", tmp_path / "workspace", "project_fixture")
    return database


def test_packaged_schema_matches_comic_sorter_contract() -> None:
    assert load_comic_sorter_schema() == json.loads(
        AUTHORITATIVE_SCHEMA.read_text(encoding="utf-8")
    )


def test_import_is_transactional_idempotent_and_retains_provenance(tmp_path: Path) -> None:
    database = _database(tmp_path)
    importer = ComicSorterBundleImporter(database)
    first = importer.import_bundle("project_fixture", _bundle())
    second = importer.import_bundle("project_fixture", _bundle())
    assert first.imported is True
    assert second.imported is False
    assert first.payload_sha256 == second.payload_sha256
    candidates = importer.list_candidates("project_fixture")
    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "candidate_fixture_001"
    assert candidates[0]["document_id"] == "document_fixture_001"
    assert candidates[0]["page_id"] == "page_fixture_001"
    assert candidates[0]["evidence_ids"] == ["evidence_fixture_001"]
    assert candidates[0]["narrative_score"] == 0.9


def test_validation_happens_before_mutation(tmp_path: Path) -> None:
    database = _database(tmp_path)
    invalid = _bundle()
    invalid["candidates"][0]["score"] = 2
    with pytest.raises(ValidationError):
        ComicSorterBundleImporter(database).import_bundle("project_fixture", invalid)
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM comic_sorter_imports").fetchone()[0] == 0


def test_same_bundle_id_with_changed_payload_is_rejected(tmp_path: Path) -> None:
    database = _database(tmp_path)
    importer = ComicSorterBundleImporter(database)
    importer.import_bundle("project_fixture", _bundle())
    changed = copy.deepcopy(_bundle())
    changed["warnings"].append("changed")
    with pytest.raises(ValueError, match="different content"):
        importer.import_bundle("project_fixture", changed)


def test_forward_compatible_optional_fields_are_retained(tmp_path: Path) -> None:
    database = _database(tmp_path)
    bundle = _bundle()
    bundle["candidates"][0]["future_optional_field"] = {"version": 2}
    result = ComicSorterBundleImporter(database).import_bundle("project_fixture", bundle)
    assert result.imported is True
    with database.connect() as connection:
        payload = json.loads(
            connection.execute("SELECT payload_json FROM comic_sorter_imports").fetchone()[0]
        )
    assert payload["candidates"][0]["future_optional_field"] == {"version": 2}


def test_combined_score_keeps_narrative_and_miller_components_separate() -> None:
    score = combine_candidate_score(
        narrative=0.9,
        technical=0.8,
        crop=0.7,
        text_mask=0.6,
        continuity=1.0,
        reuse_penalty=0.2,
        alignment=0.75,
    )
    assert score.narrative == 0.9
    assert score.technical == 0.8
    assert 0 < score.total <= 1


def test_cli_import_contract(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    database = _database(tmp_path)
    assert database.get_project("project_fixture").id == "project_fixture"
    assert (
        main(
            [
                "--db",
                str(database.path),
                "import-comic-sorter",
                "--project-id",
                "project_fixture",
                "--bundle",
                str(FIXTURE),
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["bundle_id"] == "bundle_fixture_001"
    assert output["imported"] is True
