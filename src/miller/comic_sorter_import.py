"""Validated, transactional Comic Sorter bundle import."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

from .db import Database
from .models import utc_now


@dataclass(frozen=True)
class ComicSorterImportResult:
    bundle_id: str
    project_id: str
    candidate_count: int
    imported: bool
    payload_sha256: str


@dataclass(frozen=True)
class CombinedCandidateScore:
    narrative: float
    technical: float
    crop: float
    text_mask: float
    continuity: float
    reuse_penalty: float
    alignment: float
    total: float


def combine_candidate_score(
    *,
    narrative: float,
    technical: float,
    crop: float,
    text_mask: float,
    continuity: float,
    reuse_penalty: float,
    alignment: float,
) -> CombinedCandidateScore:
    values = [narrative, technical, crop, text_mask, continuity, reuse_penalty, alignment]
    if any(value < 0 or value > 1 for value in values):
        raise ValueError("candidate score components must be between 0 and 1")
    total = max(
        0.0,
        min(
            1.0,
            narrative * 0.30
            + technical * 0.20
            + crop * 0.12
            + text_mask * 0.08
            + continuity * 0.10
            + alignment * 0.20
            - reuse_penalty * 0.25,
        ),
    )
    return CombinedCandidateScore(
        narrative=narrative,
        technical=technical,
        crop=crop,
        text_mask=text_mask,
        continuity=continuity,
        reuse_penalty=reuse_penalty,
        alignment=alignment,
        total=total,
    )


def load_comic_sorter_schema() -> dict[str, Any]:
    resource = files("miller").joinpath("schemas/comic-sorter-miller-bundle.schema.json")
    return cast(dict[str, Any], json.loads(resource.read_text(encoding="utf-8")))


def validate_comic_sorter_bundle(bundle: dict[str, Any]) -> None:
    schema = load_comic_sorter_schema()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(bundle)


class ComicSorterBundleImporter:
    """Import a file contract only. Never opens Comic Sorter's SQLite database."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def import_file(self, project_id: str, bundle_path: str | Path) -> ComicSorterImportResult:
        path = Path(bundle_path).expanduser().resolve()
        bundle = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(bundle, dict):
            raise ValueError("Comic Sorter bundle must be a JSON object")
        return self.import_bundle(project_id, bundle)

    def import_bundle(self, project_id: str, bundle: dict[str, Any]) -> ComicSorterImportResult:
        # Full schema validation happens before initialize or any transaction.
        validate_comic_sorter_bundle(bundle)
        if str(bundle["schema_version"]).split(".", 1)[0] != "1":
            raise ValueError("unsupported Comic Sorter bundle major version")
        canonical = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        bundle_id = str(bundle["bundle_id"])
        candidates = bundle["candidates"]
        self.database.initialize()
        with self.database.transaction() as connection:
            project = connection.execute(
                "SELECT 1 FROM projects WHERE id=?", (project_id,)
            ).fetchone()
            if project is None:
                raise KeyError(f"unknown project: {project_id}")
            prior = connection.execute(
                "SELECT project_id,payload_sha256 FROM comic_sorter_imports WHERE bundle_id=?",
                (bundle_id,),
            ).fetchone()
            if prior is not None:
                if str(prior["project_id"]) != project_id:
                    raise ValueError("bundle_id was already imported into a different project")
                if str(prior["payload_sha256"]) != checksum:
                    raise ValueError("bundle_id was already imported with different content")
                count = connection.execute(
                    "SELECT COUNT(*) FROM comic_sorter_candidates WHERE bundle_id=?",
                    (bundle_id,),
                ).fetchone()[0]
                return ComicSorterImportResult(bundle_id, project_id, int(count), False, checksum)
            imported_at = utc_now().isoformat()
            connection.execute(
                """
                INSERT INTO comic_sorter_imports(
                    bundle_id,schema_version,project_id,library_id,payload_json,
                    payload_sha256,imported_at
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    bundle_id,
                    bundle["schema_version"],
                    project_id,
                    bundle["library_id"],
                    canonical,
                    checksum,
                    imported_at,
                ),
            )
            for candidate in candidates:
                connection.execute(
                    """
                    INSERT INTO comic_sorter_candidates(
                        bundle_id,candidate_id,document_id,issue_id,story_id,page_id,panel_id,
                        rank,narrative_score,confidence,summary,moment_type,entity_ids_json,
                        event_ids_json,theme_ids_json,arc_ids_json,evidence_ids_json,technical_hints_json
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        bundle_id,
                        candidate["candidate_id"],
                        candidate["document_id"],
                        candidate["issue_id"],
                        candidate["story_id"],
                        candidate["page_id"],
                        candidate.get("panel_id"),
                        candidate["rank"],
                        candidate.get("narrative_score", candidate["score"]),
                        candidate["confidence"],
                        candidate["summary"],
                        candidate["moment_type"],
                        _json(candidate["entities"]),
                        _json(candidate["events"]),
                        _json(candidate["themes"]),
                        _json(candidate["arc_ids"]),
                        _json(candidate["evidence_ids"]),
                        _json(candidate.get("technical_hints", {})),
                    ),
                )
            document_kind = f"comic_sorter.bundle.{bundle_id}"
            provenance = _json(
                {
                    "bundle_id": bundle_id,
                    "schema_version": bundle["schema_version"],
                    "library_id": bundle["library_id"],
                    "payload_sha256": checksum,
                    "candidate_ids": [item["candidate_id"] for item in candidates],
                    "source": "comic-sorter",
                }
            )
            connection.execute(
                """
                INSERT INTO project_documents(
                    project_id,kind,revision,document_json,created_at,updated_at
                ) VALUES (?,?,1,?,?,?)
                """,
                (project_id, document_kind, provenance, imported_at, imported_at),
            )
            connection.execute(
                """
                INSERT INTO project_document_history(
                    project_id,kind,revision,document_json,created_at
                ) VALUES (?,?,1,?,?)
                """,
                (project_id, document_kind, provenance, imported_at),
            )
            connection.execute(
                "INSERT INTO events(id,project_id,kind,payload_json,created_at) VALUES (?,?,?,?,?)",
                (
                    _event_id(project_id, bundle_id),
                    project_id,
                    "comic_sorter.bundle_imported",
                    _json(
                        {
                            "bundle_id": bundle_id,
                            "candidate_count": len(candidates),
                            "payload_sha256": checksum,
                        }
                    ),
                    imported_at,
                ),
            )
        return ComicSorterImportResult(bundle_id, project_id, len(candidates), True, checksum)

    def list_candidates(self, project_id: str) -> list[dict[str, Any]]:
        self.database.initialize()
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT c.* FROM comic_sorter_candidates c
                JOIN comic_sorter_imports i ON i.bundle_id=c.bundle_id
                WHERE i.project_id=? ORDER BY c.narrative_score DESC,c.rank,c.candidate_id
                """,
                (project_id,),
            ).fetchall()
        return [_candidate(dict(row)) for row in rows]

    def narrative_scores(self, project_id: str) -> dict[str, float]:
        scores: dict[str, float] = {}
        for candidate in self.list_candidates(project_id):
            page_id = str(candidate["page_id"])
            scores[page_id] = max(scores.get(page_id, 0.0), float(candidate["narrative_score"]))
        return scores


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _event_id(project_id: str, bundle_id: str) -> str:
    digest = hashlib.sha256((project_id + bundle_id).encode()).hexdigest()[:24]
    return f"event_comic_sorter_{digest}"


def _candidate(row: dict[str, Any]) -> dict[str, Any]:
    for field in (
        "entity_ids_json",
        "event_ids_json",
        "theme_ids_json",
        "arc_ids_json",
        "evidence_ids_json",
        "technical_hints_json",
    ):
        row[field.removesuffix("_json")] = json.loads(row.pop(field))
    return row
