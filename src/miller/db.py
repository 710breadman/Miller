"""SQLite persistence and transactional stage transitions."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from .models import (
    Artifact,
    AttemptStatus,
    Event,
    Project,
    ProjectDocument,
    QueueItem,
    QueueKind,
    QueueStatus,
    StageAttempt,
    StageDefinition,
    StageRun,
    StageStatus,
    WorkerErrorClass,
    utc_now,
)
from .transitions import InvalidTransition, validate_transition

_SCHEMA_VERSION = 5


def _iso(value: datetime) -> str:
    return value.isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class DocumentConflict(RuntimeError):
    """Raised when optimistic document revision checking fails."""


class DatabaseIntegrityError(RuntimeError):
    """Raised when a database file fails a SQLite integrity check."""


class MigrationError(RuntimeError):
    """Raised when ordered schema migration cannot proceed safely."""


@dataclass(frozen=True)
class _Migration:
    """One ordered, idempotent schema migration step."""

    version: int
    description: str
    script: str


# Each migration's DDL is grouped by the feature that introduced it. The
# repository history does not preserve the original per-version diffs (the
# schema was published in one commit), so these boundaries are a faithful
# reconstruction by feature area rather than a literal replay of past
# upgrades: 1) core stage/attempt/artifact/event tables, 2) revisioned
# project documents, 3) the persistent work queue. See DECISIONS.md D-004.
_MIGRATIONS: tuple[_Migration, ...] = (
    _Migration(
        version=1,
        description="Core project, stage, attempt, artifact, and event tables.",
        script="""
            CREATE TABLE IF NOT EXISTS schema_meta (
                version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                workspace TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stage_definitions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stage_dependencies (
                stage_id TEXT NOT NULL REFERENCES stage_definitions(id) ON DELETE CASCADE,
                dependency_id TEXT NOT NULL REFERENCES stage_definitions(id) ON DELETE RESTRICT,
                PRIMARY KEY (stage_id, dependency_id),
                CHECK (stage_id <> dependency_id)
            );

            CREATE TABLE IF NOT EXISTS stage_runs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                stage_id TEXT NOT NULL REFERENCES stage_definitions(id) ON DELETE RESTRICT,
                status TEXT NOT NULL,
                input_fingerprint TEXT,
                output_artifact_id TEXT,
                active_attempt_id TEXT,
                cancel_requested INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(project_id, stage_id)
            );

            CREATE TABLE IF NOT EXISTS stage_attempts (
                id TEXT PRIMARY KEY,
                stage_run_id TEXT NOT NULL REFERENCES stage_runs(id) ON DELETE CASCADE,
                number INTEGER NOT NULL,
                status TEXT NOT NULL,
                attempt_guard TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                error TEXT,
                UNIQUE(stage_run_id, number)
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                stage_run_id TEXT REFERENCES stage_runs(id) ON DELETE SET NULL,
                relative_path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(project_id, relative_path)
            );

            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                stage_run_id TEXT REFERENCES stage_runs(id) ON DELETE CASCADE,
                attempt_id TEXT REFERENCES stage_attempts(id) ON DELETE CASCADE,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_stage_runs_project
                ON stage_runs(project_id, stage_id);
            CREATE INDEX IF NOT EXISTS idx_attempts_run
                ON stage_attempts(stage_run_id, number);
            CREATE INDEX IF NOT EXISTS idx_events_project
                ON events(project_id, created_at);
        """,
    ),
    _Migration(
        version=2,
        description="Revisioned project documents and their history.",
        script="""
            CREATE TABLE IF NOT EXISTS project_documents (
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                revision INTEGER NOT NULL,
                document_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(project_id, kind)
            );

            CREATE TABLE IF NOT EXISTS project_document_history (
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                revision INTEGER NOT NULL,
                document_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY(project_id, kind, revision)
            );

            CREATE INDEX IF NOT EXISTS idx_project_document_history
                ON project_document_history(project_id, kind, revision);
        """,
    ),
    _Migration(
        version=3,
        description="Persistent bounded work queue.",
        script="""
            CREATE TABLE IF NOT EXISTS work_queue (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                error TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_work_queue_claim
                ON work_queue(kind, status, priority, created_at);
        """,
    ),
    _Migration(
        version=4,
        description=(
            "Worker protocol versioning, lease/heartbeat, cancellation, and "
            "GPU admission for the work queue (ARC-003)."
        ),
        script="""
            ALTER TABLE work_queue ADD COLUMN requires_gpu INTEGER NOT NULL DEFAULT 0;
            ALTER TABLE work_queue ADD COLUMN protocol_version TEXT NOT NULL DEFAULT '1';
            ALTER TABLE work_queue ADD COLUMN claimed_by TEXT;
            ALTER TABLE work_queue ADD COLUMN lease_token TEXT;
            ALTER TABLE work_queue ADD COLUMN lease_expires_at TEXT;
            ALTER TABLE work_queue ADD COLUMN heartbeat_at TEXT;
            ALTER TABLE work_queue ADD COLUMN cancel_requested INTEGER NOT NULL DEFAULT 0;
            ALTER TABLE work_queue ADD COLUMN error_class TEXT;

            CREATE INDEX IF NOT EXISTS idx_work_queue_lease_expiry
                ON work_queue(status, lease_expires_at);
        """,
    ),
    _Migration(
        version=5,
        description="Validated Comic Sorter narrative bundle imports.",
        script="""
            CREATE TABLE comic_sorter_imports (
                bundle_id TEXT PRIMARY KEY,
                schema_version TEXT NOT NULL,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                library_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                imported_at TEXT NOT NULL
            );

            CREATE TABLE comic_sorter_candidates (
                bundle_id TEXT NOT NULL
                    REFERENCES comic_sorter_imports(bundle_id) ON DELETE CASCADE,
                candidate_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                issue_id TEXT NOT NULL,
                story_id TEXT NOT NULL,
                page_id TEXT NOT NULL,
                panel_id TEXT,
                rank INTEGER NOT NULL CHECK(rank >= 1),
                narrative_score REAL NOT NULL CHECK(narrative_score BETWEEN 0 AND 1),
                confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
                summary TEXT NOT NULL,
                moment_type TEXT NOT NULL,
                entity_ids_json TEXT NOT NULL,
                event_ids_json TEXT NOT NULL,
                theme_ids_json TEXT NOT NULL,
                arc_ids_json TEXT NOT NULL,
                evidence_ids_json TEXT NOT NULL,
                technical_hints_json TEXT NOT NULL,
                PRIMARY KEY(bundle_id, candidate_id)
            );

            CREATE INDEX idx_comic_sorter_import_project
                ON comic_sorter_imports(project_id, imported_at);
            CREATE INDEX idx_comic_sorter_candidate_page
                ON comic_sorter_candidates(page_id, panel_id);
            CREATE INDEX idx_comic_sorter_candidate_score
                ON comic_sorter_candidates(bundle_id, narrative_score DESC, rank);
        """,
    ),
)

assert [migration.version for migration in _MIGRATIONS] == list(
    range(1, _SCHEMA_VERSION + 1)
), "migrations must be dense and ordered from 1 to _SCHEMA_VERSION"


class Database:
    """Miller's source-of-truth SQLite database."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Bring the database file up to ``_SCHEMA_VERSION`` via ordered migrations.

        A database file that already exists is integrity-checked before anything
        else runs. If pending migrations exist, a verified preflight backup is
        taken first so :meth:`restore_from_backup` can recover the prior state.
        A brand-new (missing or empty) database file is created directly at the
        latest schema with no backup, since there is no prior state to lose.
        """

        self.path.parent.mkdir(parents=True, exist_ok=True)
        pre_existing = self.path.exists() and self.path.stat().st_size > 0
        if pre_existing:
            self._check_integrity(context=f"preflight check of {self.path}")

        current_version = self._read_schema_version() if pre_existing else 0
        if current_version > _SCHEMA_VERSION:
            raise MigrationError(
                f"database schema {current_version} is newer than supported "
                f"{_SCHEMA_VERSION}; refusing to downgrade {self.path}"
            )

        pending = tuple(m for m in _MIGRATIONS if m.version > current_version)
        if not pending:
            return

        backup_path: Path | None = None
        if pre_existing:
            backup_path = self.create_backup(
                reason=f"pre-migration-v{current_version}-to-v{_SCHEMA_VERSION}"
            )

        try:
            for migration in pending:
                with self.transaction() as connection:
                    connection.executescript(migration.script)
                    connection.execute("DELETE FROM schema_meta")
                    connection.execute(
                        "INSERT INTO schema_meta(version) VALUES (?)", (migration.version,)
                    )
            self._check_integrity(context=f"post-migration check of {self.path}")
        except Exception as exc:
            hint = (
                f" A verified preflight backup is available at {backup_path}."
                if backup_path is not None
                else ""
            )
            raise MigrationError(
                f"migration to schema {_SCHEMA_VERSION} failed for {self.path}: {exc}.{hint}"
            ) from exc

    def verify_integrity(self) -> None:
        """Raise :class:`DatabaseIntegrityError` if the database file is corrupt."""

        self._check_integrity(context=f"explicit verification of {self.path}")

    def create_backup(self, *, reason: str | None = None, destination: Path | None = None) -> Path:
        """Copy this database to a verified backup file using SQLite's backup API.

        The backup is read back and integrity-checked before this method returns,
        so callers can trust that a returned path is restorable.
        """

        if not self.path.exists():
            raise FileNotFoundError(f"cannot back up missing database: {self.path}")
        if destination is None:
            backup_dir = self.path.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
            suffix = f"-{reason}" if reason else ""
            destination = backup_dir / f"{self.path.stem}.{timestamp}{suffix}.sqlite3"
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)

        source_connection = sqlite3.connect(self.path)
        destination_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
            source_connection.close()

        Database(destination)._check_integrity(context=f"backup verification of {destination}")
        return destination

    def restore_from_backup(self, backup_path: Path | str) -> None:
        """Atomically replace this database's live file with a verified backup.

        The backup is integrity-checked before touching the live file. The
        restored content is staged next to the live path and integrity-checked
        again before the atomic replace, so a failure never leaves the live
        file partially overwritten.
        """

        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"backup not found: {backup_path}")
        Database(backup_path)._check_integrity(context=f"restore source {backup_path}")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = self.path.with_name(f"{self.path.name}.restore-{secrets.token_hex(8)}.tmp")
        source_connection = sqlite3.connect(backup_path)
        staging_connection = sqlite3.connect(staging_path)
        try:
            source_connection.backup(staging_connection)
        finally:
            staging_connection.close()
            source_connection.close()

        try:
            Database(staging_path)._check_integrity(context=f"restore staging {staging_path}")
            os.replace(staging_path, self.path)
        finally:
            if staging_path.exists():
                staging_path.unlink()

    def _check_integrity(self, *, context: str) -> None:
        try:
            connection = sqlite3.connect(self.path, timeout=30)
            try:
                result = connection.execute("PRAGMA integrity_check").fetchone()
            finally:
                connection.close()
        except sqlite3.DatabaseError as exc:
            raise DatabaseIntegrityError(f"integrity check failed during {context}: {exc}") from exc
        outcome = str(result[0]) if result is not None else "unknown"
        if outcome != "ok":
            raise DatabaseIntegrityError(f"integrity check failed during {context}: {outcome}")

    def _read_schema_version(self) -> int:
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'"
            ).fetchone()
            if table is None:
                return 0
            row = connection.execute("SELECT version FROM schema_meta").fetchone()
            return int(row[0]) if row is not None else 0
        finally:
            connection.close()

    def create_project(
        self, name: str, workspace: Path | str, project_id: str | None = None
    ) -> Project:
        now = utc_now()
        project = Project(
            id=project_id or _new_id("project"),
            name=name,
            workspace=str(Path(workspace)),
            created_at=now,
            updated_at=now,
        )
        with self.transaction() as connection:
            connection.execute(
                """
                INSERT INTO projects(id, name, workspace, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    project.id,
                    project.name,
                    project.workspace,
                    _iso(project.created_at),
                    _iso(project.updated_at),
                ),
            )
            self._insert_event(
                connection,
                project_id=project.id,
                kind="project.created",
                payload={"name": project.name},
            )
        return project

    def get_project(self, project_id: str) -> Project:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown project: {project_id}")
        return Project.model_validate(dict(row))

    def register_stage(self, definition: StageDefinition) -> None:
        with self.transaction() as connection:
            connection.execute(
                """
                INSERT INTO stage_definitions(id, name, version)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name, version=excluded.version
                """,
                (definition.id, definition.name, definition.version),
            )
            connection.execute(
                "DELETE FROM stage_dependencies WHERE stage_id = ?", (definition.id,)
            )
            for dependency in definition.dependencies:
                exists = connection.execute(
                    "SELECT 1 FROM stage_definitions WHERE id = ?", (dependency,)
                ).fetchone()
                if exists is None:
                    raise KeyError(f"dependency must be registered first: {dependency}")
                connection.execute(
                    "INSERT INTO stage_dependencies(stage_id, dependency_id) VALUES (?, ?)",
                    (definition.id, dependency),
                )

    def get_stage_definition(self, stage_id: str) -> StageDefinition:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM stage_definitions WHERE id = ?", (stage_id,)
            ).fetchone()
            deps = connection.execute(
                """
                SELECT dependency_id FROM stage_dependencies
                WHERE stage_id = ? ORDER BY dependency_id
                """,
                (stage_id,),
            ).fetchall()
        if row is None:
            raise KeyError(f"unknown stage definition: {stage_id}")
        return StageDefinition(
            id=row["id"],
            name=row["name"],
            version=row["version"],
            dependencies=tuple(item["dependency_id"] for item in deps),
        )

    def ensure_stage_run(self, project_id: str, stage_id: str) -> StageRun:
        now = utc_now()
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM stage_runs WHERE project_id = ? AND stage_id = ?",
                (project_id, stage_id),
            ).fetchone()
            if row is None:
                run_id = _new_id("run")
                connection.execute(
                    """
                    INSERT INTO stage_runs(
                        id, project_id, stage_id, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        project_id,
                        stage_id,
                        StageStatus.PENDING.value,
                        _iso(now),
                        _iso(now),
                    ),
                )
                self._insert_event(
                    connection,
                    project_id=project_id,
                    stage_run_id=run_id,
                    kind="stage.created",
                    payload={"stage_id": stage_id},
                )
                row = connection.execute(
                    "SELECT * FROM stage_runs WHERE id = ?", (run_id,)
                ).fetchone()
        assert row is not None
        return self._stage_run_from_row(row)

    def get_stage_run(self, project_id: str, stage_id: str) -> StageRun:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM stage_runs WHERE project_id = ? AND stage_id = ?",
                (project_id, stage_id),
            ).fetchone()
        if row is None:
            raise KeyError(f"no run for project={project_id} stage={stage_id}")
        return self._stage_run_from_row(row)

    def get_stage_run_by_id(self, stage_run_id: str) -> StageRun:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM stage_runs WHERE id = ?", (stage_run_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown stage run: {stage_run_id}")
        return self._stage_run_from_row(row)

    def list_stage_runs(self, project_id: str) -> list[StageRun]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM stage_runs WHERE project_id = ? ORDER BY created_at", (project_id,)
            ).fetchall()
        return [self._stage_run_from_row(row) for row in rows]

    def invalidate_if_changed(self, stage_run_id: str, fingerprint: str) -> bool:
        with self.transaction() as connection:
            row = self._require_stage_run(connection, stage_run_id)
            current = StageStatus(row["status"])
            previous = row["input_fingerprint"]
            if current != StageStatus.COMPLETED or previous == fingerprint:
                return False
            validate_transition(current, StageStatus.PENDING)
            now = utc_now()
            connection.execute(
                """
                UPDATE stage_runs
                SET status=?, input_fingerprint=?, output_artifact_id=NULL,
                    error=NULL, updated_at=?
                WHERE id=?
                """,
                (StageStatus.PENDING.value, fingerprint, _iso(now), stage_run_id),
            )
            self._insert_event(
                connection,
                project_id=row["project_id"],
                stage_run_id=stage_run_id,
                kind="stage.invalidated",
                payload={"previous_fingerprint": previous, "fingerprint": fingerprint},
            )
            return True

    def begin_attempt(self, stage_run_id: str, fingerprint: str) -> StageAttempt:
        with self.transaction() as connection:
            row = self._require_stage_run(connection, stage_run_id)
            current = StageStatus(row["status"])
            validate_transition(current, StageStatus.RUNNING)
            number_row = connection.execute(
                """
                SELECT COALESCE(MAX(number), 0) + 1 AS next_number
                FROM stage_attempts WHERE stage_run_id=?
                """,
                (stage_run_id,),
            ).fetchone()
            assert number_row is not None
            now = utc_now()
            attempt = StageAttempt(
                id=_new_id("attempt"),
                stage_run_id=stage_run_id,
                number=int(number_row["next_number"]),
                status=AttemptStatus.RUNNING,
                attempt_guard=secrets.token_urlsafe(32),
                started_at=now,
            )
            connection.execute(
                """
                INSERT INTO stage_attempts(
                    id, stage_run_id, number, status, attempt_guard, started_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt.id,
                    attempt.stage_run_id,
                    attempt.number,
                    attempt.status.value,
                    attempt.attempt_guard,
                    _iso(attempt.started_at),
                ),
            )
            connection.execute(
                """
                UPDATE stage_runs
                SET status=?, input_fingerprint=?, active_attempt_id=?,
                    cancel_requested=0, error=NULL, updated_at=?
                WHERE id=?
                """,
                (
                    StageStatus.RUNNING.value,
                    fingerprint,
                    attempt.id,
                    _iso(now),
                    stage_run_id,
                ),
            )
            self._insert_event(
                connection,
                project_id=row["project_id"],
                stage_run_id=stage_run_id,
                attempt_id=attempt.id,
                kind="attempt.started",
                payload={"number": attempt.number, "fingerprint": fingerprint},
            )
        return attempt

    def complete_attempt(
        self,
        stage_run_id: str,
        attempt_id: str,
        attempt_guard: str,
        artifact_id: str,
    ) -> StageRun:
        return self._finish_attempt(
            stage_run_id,
            attempt_id,
            attempt_guard,
            attempt_status=AttemptStatus.SUCCEEDED,
            stage_status=StageStatus.COMPLETED,
            artifact_id=artifact_id,
            error=None,
        )

    def fail_attempt(
        self, stage_run_id: str, attempt_id: str, attempt_guard: str, error: str
    ) -> StageRun:
        return self._finish_attempt(
            stage_run_id,
            attempt_id,
            attempt_guard,
            attempt_status=AttemptStatus.FAILED,
            stage_status=StageStatus.FAILED,
            artifact_id=None,
            error=error,
        )

    def cancel_attempt(
        self, stage_run_id: str, attempt_id: str, attempt_guard: str, error: str = "cancelled"
    ) -> StageRun:
        return self._finish_attempt(
            stage_run_id,
            attempt_id,
            attempt_guard,
            attempt_status=AttemptStatus.CANCELLED,
            stage_status=StageStatus.CANCELLED,
            artifact_id=None,
            error=error,
        )

    def request_cancel(self, stage_run_id: str) -> None:
        with self.transaction() as connection:
            row = self._require_stage_run(connection, stage_run_id)
            connection.execute(
                "UPDATE stage_runs SET cancel_requested=1, updated_at=? WHERE id=?",
                (_iso(utc_now()), stage_run_id),
            )
            self._insert_event(
                connection,
                project_id=row["project_id"],
                stage_run_id=stage_run_id,
                kind="stage.cancel_requested",
                payload={},
            )

    def cancellation_requested(self, stage_run_id: str) -> bool:
        with self.connect() as connection:
            row = self._require_stage_run(connection, stage_run_id)
        return bool(row["cancel_requested"])

    def recover_abandoned(self, project_id: str | None = None) -> int:
        """Mark in-progress attempts abandoned after an unclean process exit."""

        recovered = 0
        with self.transaction() as connection:
            query = "SELECT * FROM stage_runs WHERE status=?"
            parameters: tuple[str, ...] = (StageStatus.RUNNING.value,)
            if project_id is not None:
                query += " AND project_id=?"
                parameters += (project_id,)
            rows = connection.execute(query, parameters).fetchall()
            for row in rows:
                attempt_id = row["active_attempt_id"]
                now = utc_now()
                if attempt_id:
                    connection.execute(
                        """
                        UPDATE stage_attempts
                        SET status=?, completed_at=?, error=?
                        WHERE id=? AND status=?
                        """,
                        (
                            AttemptStatus.ABANDONED.value,
                            _iso(now),
                            "process ended before attempt completion",
                            attempt_id,
                            AttemptStatus.RUNNING.value,
                        ),
                    )
                connection.execute(
                    """
                    UPDATE stage_runs
                    SET status=?, active_attempt_id=NULL, error=?, updated_at=?
                    WHERE id=?
                    """,
                    (
                        StageStatus.FAILED.value,
                        "abandoned after restart",
                        _iso(now),
                        row["id"],
                    ),
                )
                self._insert_event(
                    connection,
                    project_id=row["project_id"],
                    stage_run_id=row["id"],
                    attempt_id=attempt_id,
                    kind="attempt.abandoned",
                    payload={},
                )
                recovered += 1
        return recovered

    def add_artifact(self, artifact: Artifact) -> None:
        with self.transaction() as connection:
            connection.execute(
                """
                INSERT INTO artifacts(
                    id, content_id, project_id, stage_run_id, relative_path, sha256,
                    size_bytes, media_type, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
                """,
                (
                    artifact.id,
                    artifact.content_id,
                    artifact.project_id,
                    artifact.stage_run_id,
                    artifact.relative_path,
                    artifact.sha256,
                    artifact.size_bytes,
                    artifact.media_type,
                    json.dumps(artifact.metadata, sort_keys=True, separators=(",", ":")),
                    _iso(artifact.created_at),
                ),
            )

    def list_artifacts(self, project_id: str) -> list[Artifact]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM artifacts WHERE project_id=? ORDER BY created_at, id",
                (project_id,),
            ).fetchall()
        artifacts: list[Artifact] = []
        for row in rows:
            values = dict(row)
            values["metadata"] = json.loads(values.pop("metadata_json"))
            artifacts.append(Artifact.model_validate(values))
        return artifacts

    def get_artifact(self, artifact_id: str) -> Artifact:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM artifacts WHERE id=?", (artifact_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown artifact: {artifact_id}")
        values = dict(row)
        values["metadata"] = json.loads(values.pop("metadata_json"))
        return Artifact.model_validate(values)

    def list_documents(self, project_id: str) -> list[ProjectDocument]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM project_documents WHERE project_id=? ORDER BY kind",
                (project_id,),
            ).fetchall()
        documents: list[ProjectDocument] = []
        for row in rows:
            values = dict(row)
            values["document"] = json.loads(values.pop("document_json"))
            documents.append(ProjectDocument.model_validate(values))
        return documents

    def restore_stage_run(self, run: StageRun) -> None:
        if run.active_attempt_id is not None:
            raise ValueError("portable stage run cannot restore an active attempt")
        with self.transaction() as connection:
            connection.execute(
                """
                INSERT INTO stage_runs(
                    id, project_id, stage_id, status, input_fingerprint,
                    output_artifact_id, active_attempt_id, cancel_requested, error,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.project_id,
                    run.stage_id,
                    run.status.value,
                    run.input_fingerprint,
                    run.output_artifact_id,
                    int(run.cancel_requested),
                    run.error,
                    _iso(run.created_at),
                    _iso(run.updated_at),
                ),
            )

    def put_document(
        self,
        project_id: str,
        kind: str,
        document: dict[str, Any],
        *,
        expected_revision: int | None = None,
    ) -> ProjectDocument:
        ProjectDocument(
            project_id=project_id,
            kind=kind,
            revision=1,
            document=document,
        )
        now = utc_now()
        with self.transaction() as connection:
            project = connection.execute(
                "SELECT 1 FROM projects WHERE id=?", (project_id,)
            ).fetchone()
            if project is None:
                raise KeyError(f"unknown project: {project_id}")
            row = connection.execute(
                "SELECT * FROM project_documents WHERE project_id=? AND kind=?",
                (project_id, kind),
            ).fetchone()
            if row is None:
                if expected_revision not in (None, 0):
                    raise DocumentConflict(
                        f"document does not exist; expected revision {expected_revision}"
                    )
                revision = 1
                created_at = now
                connection.execute(
                    """
                    INSERT INTO project_documents(
                        project_id, kind, revision, document_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        kind,
                        revision,
                        json.dumps(document, sort_keys=True, separators=(",", ":")),
                        _iso(created_at),
                        _iso(now),
                    ),
                )
            else:
                current_revision = int(row["revision"])
                if expected_revision is not None and expected_revision != current_revision:
                    message = (
                        f"revision mismatch: expected {expected_revision}, "
                        f"current {current_revision}"
                    )
                    raise DocumentConflict(message)
                revision = current_revision + 1
                created_at = datetime.fromisoformat(str(row["created_at"]))
                connection.execute(
                    """
                    UPDATE project_documents
                    SET revision=?, document_json=?, updated_at=?
                    WHERE project_id=? AND kind=?
                    """,
                    (
                        revision,
                        json.dumps(document, sort_keys=True, separators=(",", ":")),
                        _iso(now),
                        project_id,
                        kind,
                    ),
                )
            connection.execute(
                """
                INSERT INTO project_document_history(
                    project_id, kind, revision, document_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    kind,
                    revision,
                    json.dumps(document, sort_keys=True, separators=(",", ":")),
                    _iso(now),
                ),
            )
            self._insert_event(
                connection,
                project_id=project_id,
                kind="document.updated",
                payload={"kind": kind, "revision": revision},
            )
        return ProjectDocument(
            project_id=project_id,
            kind=kind,
            revision=revision,
            document=document,
            created_at=created_at,
            updated_at=now,
        )

    def get_document(self, project_id: str, kind: str) -> ProjectDocument:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM project_documents WHERE project_id=? AND kind=?",
                (project_id, kind),
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown document: project={project_id} kind={kind}")
        values = dict(row)
        values["document"] = json.loads(values.pop("document_json"))
        return ProjectDocument.model_validate(values)

    def list_document_history(self, project_id: str, kind: str) -> list[ProjectDocument]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT project_id, kind, revision, document_json, created_at
                FROM project_document_history
                WHERE project_id=? AND kind=? ORDER BY revision
                """,
                (project_id, kind),
            ).fetchall()
        history: list[ProjectDocument] = []
        for row in rows:
            values = dict(row)
            values["document"] = json.loads(values.pop("document_json"))
            values["updated_at"] = values["created_at"]
            history.append(ProjectDocument.model_validate(values))
        return history

    def invalidate_stage_tree(
        self, project_id: str, stage_id: str, *, reason: str
    ) -> tuple[str, ...]:
        with self.transaction() as connection:
            queue = [stage_id]
            ordered: list[str] = []
            seen: set[str] = set()
            while queue:
                current = queue.pop(0)
                if current in seen:
                    continue
                seen.add(current)
                ordered.append(current)
                rows = connection.execute(
                    "SELECT stage_id FROM stage_dependencies WHERE dependency_id=?",
                    (current,),
                ).fetchall()
                queue.extend(str(row["stage_id"]) for row in rows)
            invalidated: list[str] = []
            for current in ordered:
                row = connection.execute(
                    "SELECT * FROM stage_runs WHERE project_id=? AND stage_id=?",
                    (project_id, current),
                ).fetchone()
                if row is None:
                    continue
                status = StageStatus(row["status"])
                if status == StageStatus.RUNNING:
                    raise InvalidTransition(
                        f"cannot invalidate running stage: {current}"
                    )
                if status != StageStatus.COMPLETED:
                    continue
                validate_transition(status, StageStatus.PENDING)
                connection.execute(
                    """
                    UPDATE stage_runs SET status=?, output_artifact_id=NULL,
                        error=NULL, updated_at=? WHERE id=?
                    """,
                    (StageStatus.PENDING.value, _iso(utc_now()), row["id"]),
                )
                invalidated.append(current)
            if invalidated:
                self._insert_event(
                    connection,
                    project_id=project_id,
                    kind="stage.tree_invalidated",
                    payload={"stages": invalidated, "reason": reason},
                )
        return tuple(invalidated)

    def enqueue(
        self,
        project_id: str,
        kind: QueueKind,
        payload: dict[str, Any] | None = None,
        *,
        priority: int = 100,
        requires_gpu: bool = False,
        protocol_version: str = "1",
    ) -> QueueItem:
        now = utc_now()
        item = QueueItem(
            id=_new_id("queue"),
            project_id=project_id,
            kind=kind,
            priority=priority,
            payload=payload or {},
            requires_gpu=requires_gpu,
            protocol_version=protocol_version,
            created_at=now,
            updated_at=now,
        )
        with self.transaction() as connection:
            project = connection.execute(
                "SELECT 1 FROM projects WHERE id=?", (project_id,)
            ).fetchone()
            if project is None:
                raise KeyError(f"unknown project: {project_id}")
            connection.execute(
                """
                INSERT INTO work_queue(
                    id, project_id, kind, status, priority, payload_json,
                    requires_gpu, protocol_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.project_id,
                    item.kind.value,
                    item.status.value,
                    item.priority,
                    json.dumps(item.payload, sort_keys=True, separators=(",", ":")),
                    int(item.requires_gpu),
                    item.protocol_version,
                    _iso(item.created_at),
                    _iso(item.updated_at),
                ),
            )
            self._insert_event(
                connection,
                project_id=project_id,
                kind="queue.enqueued",
                payload={
                    "queue_id": item.id,
                    "kind": kind.value,
                    "requires_gpu": item.requires_gpu,
                },
            )
        return item

    def claim_next(
        self,
        kind: QueueKind,
        *,
        worker_id: str | None = None,
        lease_seconds: int = 300,
        gpu_capacity: int = 1,
    ) -> QueueItem | None:
        """Claim the next pending item for ``kind``, or ``None`` if not admissible.

        At most one item per ``kind`` runs at a time. If the highest-priority
        pending item requires the GPU, it is only claimed while fewer than
        ``gpu_capacity`` GPU-requiring items are running system-wide (across
        all kinds); otherwise this call returns ``None`` for now rather than
        skipping ahead to a lower-priority non-GPU item.
        """

        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        if gpu_capacity < 0:
            raise ValueError("gpu_capacity must not be negative")
        with self.transaction() as connection:
            running = connection.execute(
                "SELECT 1 FROM work_queue WHERE kind=? AND status=? LIMIT 1",
                (kind.value, QueueStatus.RUNNING.value),
            ).fetchone()
            if running is not None:
                return None
            row = connection.execute(
                """
                SELECT * FROM work_queue
                WHERE kind=? AND status=?
                ORDER BY priority, created_at, id LIMIT 1
                """,
                (kind.value, QueueStatus.PENDING.value),
            ).fetchone()
            if row is None:
                return None
            if row["requires_gpu"]:
                gpu_running = connection.execute(
                    "SELECT COUNT(*) AS n FROM work_queue WHERE status=? AND requires_gpu=1",
                    (QueueStatus.RUNNING.value,),
                ).fetchone()
                if int(gpu_running["n"]) >= gpu_capacity:
                    return None
            now = utc_now()
            lease_token = secrets.token_urlsafe(32)
            lease_expires_at = now + timedelta(seconds=lease_seconds)
            connection.execute(
                """
                UPDATE work_queue
                SET status=?, started_at=?, updated_at=?, error=NULL, error_class=NULL,
                    lease_token=?, lease_expires_at=?, heartbeat_at=?, claimed_by=?
                WHERE id=?
                """,
                (
                    QueueStatus.RUNNING.value,
                    _iso(now),
                    _iso(now),
                    lease_token,
                    _iso(lease_expires_at),
                    _iso(now),
                    worker_id,
                    row["id"],
                ),
            )
            updated = connection.execute(
                "SELECT * FROM work_queue WHERE id=?", (row["id"],)
            ).fetchone()
            assert updated is not None
            self._insert_event(
                connection,
                project_id=row["project_id"],
                kind="queue.started",
                payload={"queue_id": row["id"], "kind": kind.value, "worker_id": worker_id},
            )
        return self._queue_item_from_row(updated)

    def heartbeat_queue_item(
        self, item_id: str, lease_token: str, *, lease_seconds: int = 300
    ) -> None:
        """Renew a running item's lease; proves the claiming worker is alive."""

        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM work_queue WHERE id=?", (item_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown queue item: {item_id}")
            if QueueStatus(row["status"]) != QueueStatus.RUNNING:
                raise InvalidTransition("only a running queue item can be heartbeated")
            if row["lease_token"] != lease_token:
                raise PermissionError(
                    "queue item lease token does not match; stale worker cannot renew this claim"
                )
            now = utc_now()
            connection.execute(
                """
                UPDATE work_queue SET heartbeat_at=?, lease_expires_at=?, updated_at=?
                WHERE id=?
                """,
                (_iso(now), _iso(now + timedelta(seconds=lease_seconds)), _iso(now), item_id),
            )

    def reclaim_expired_leases(self, *, now: datetime | None = None) -> int:
        """Fail running items whose lease expired without a heartbeat/completion.

        Complements :meth:`recover_queue` (which handles a full process
        restart) by detecting a claim that has gone silent -- for example a
        crashed external worker subprocess -- without requiring this process
        to be the one that restarted.
        """

        current = now or utc_now()
        with self.transaction() as connection:
            rows = connection.execute(
                """
                SELECT * FROM work_queue
                WHERE status=? AND lease_expires_at IS NOT NULL AND lease_expires_at < ?
                """,
                (QueueStatus.RUNNING.value, _iso(current)),
            ).fetchall()
            for row in rows:
                connection.execute(
                    """
                    UPDATE work_queue
                    SET status=?, completed_at=?, updated_at=?, error=?, error_class=?,
                        lease_token=NULL, lease_expires_at=NULL
                    WHERE id=?
                    """,
                    (
                        QueueStatus.FAILED.value,
                        _iso(current),
                        _iso(current),
                        "lease expired without heartbeat or completion",
                        WorkerErrorClass.TIMEOUT.value,
                        row["id"],
                    ),
                )
                self._insert_event(
                    connection,
                    project_id=row["project_id"],
                    kind="queue.lease_expired",
                    payload={"queue_id": row["id"], "worker_id": row["claimed_by"]},
                )
        return len(rows)

    def request_cancel_queue_item(self, item_id: str) -> None:
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM work_queue WHERE id=?", (item_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown queue item: {item_id}")
            connection.execute(
                "UPDATE work_queue SET cancel_requested=1, updated_at=? WHERE id=?",
                (_iso(utc_now()), item_id),
            )
            self._insert_event(
                connection,
                project_id=row["project_id"],
                kind="queue.cancel_requested",
                payload={"queue_id": item_id},
            )

    def queue_cancellation_requested(self, item_id: str) -> bool:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT cancel_requested FROM work_queue WHERE id=?", (item_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown queue item: {item_id}")
        return bool(row["cancel_requested"])

    def complete_queue_item(self, item_id: str, lease_token: str | None = None) -> QueueItem:
        return self._finish_queue_item(
            item_id,
            QueueStatus.COMPLETED,
            error=None,
            error_class=None,
            lease_token=lease_token,
        )

    def fail_queue_item(
        self,
        item_id: str,
        error: str,
        *,
        error_class: WorkerErrorClass | None = None,
        lease_token: str | None = None,
    ) -> QueueItem:
        return self._finish_queue_item(
            item_id,
            QueueStatus.FAILED,
            error=error,
            error_class=error_class,
            lease_token=lease_token,
        )

    def cancel_queue_item(
        self, item_id: str, error: str = "cancelled", *, lease_token: str | None = None
    ) -> QueueItem:
        return self._finish_queue_item(
            item_id,
            QueueStatus.CANCELLED,
            error=error,
            error_class=WorkerErrorClass.CANCELLED,
            lease_token=lease_token,
        )

    def recover_queue(self) -> int:
        now = utc_now()
        with self.transaction() as connection:
            rows = connection.execute(
                "SELECT id, project_id, kind FROM work_queue WHERE status=?",
                (QueueStatus.RUNNING.value,),
            ).fetchall()
            for row in rows:
                connection.execute(
                    """
                    UPDATE work_queue
                    SET status=?, started_at=NULL, updated_at=?, error=?, error_class=NULL,
                        lease_token=NULL, lease_expires_at=NULL, heartbeat_at=NULL,
                        claimed_by=NULL
                    WHERE id=?
                    """,
                    (
                        QueueStatus.PENDING.value,
                        _iso(now),
                        "requeued after restart",
                        row["id"],
                    ),
                )
                self._insert_event(
                    connection,
                    project_id=row["project_id"],
                    kind="queue.recovered",
                    payload={"queue_id": row["id"], "kind": row["kind"]},
                )
        return len(rows)

    def list_queue(
        self,
        *,
        kind: QueueKind | None = None,
        status: QueueStatus | None = None,
    ) -> list[QueueItem]:
        conditions: list[str] = []
        parameters: list[str] = []
        if kind is not None:
            conditions.append("kind=?")
            parameters.append(kind.value)
        if status is not None:
            conditions.append("status=?")
            parameters.append(status.value)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM work_queue" + where + " ORDER BY priority, created_at, id",
                parameters,
            ).fetchall()
        return [self._queue_item_from_row(row) for row in rows]

    def _finish_queue_item(
        self,
        item_id: str,
        status: QueueStatus,
        *,
        error: str | None,
        error_class: WorkerErrorClass | None,
        lease_token: str | None,
    ) -> QueueItem:
        if status not in {
            QueueStatus.COMPLETED,
            QueueStatus.FAILED,
            QueueStatus.CANCELLED,
        }:
            raise ValueError("queue finish status must be terminal")
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM work_queue WHERE id=?", (item_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown queue item: {item_id}")
            if QueueStatus(row["status"]) != QueueStatus.RUNNING:
                raise InvalidTransition("only a running queue item can finish")
            if (
                lease_token is not None
                and row["lease_token"] is not None
                and row["lease_token"] != lease_token
            ):
                raise PermissionError(
                    "queue item lease token does not match; stale worker cannot finish this claim"
                )
            now = utc_now()
            connection.execute(
                """
                UPDATE work_queue
                SET status=?, completed_at=?, updated_at=?, error=?, error_class=?,
                    lease_token=NULL, lease_expires_at=NULL
                WHERE id=?
                """,
                (
                    status.value,
                    _iso(now),
                    _iso(now),
                    error,
                    error_class.value if error_class else None,
                    item_id,
                ),
            )
            updated = connection.execute(
                "SELECT * FROM work_queue WHERE id=?", (item_id,)
            ).fetchone()
            assert updated is not None
            self._insert_event(
                connection,
                project_id=row["project_id"],
                kind=f"queue.{status.value}",
                payload={
                    "queue_id": item_id,
                    "error": error,
                    "error_class": error_class.value if error_class else None,
                },
            )
        return self._queue_item_from_row(updated)

    @staticmethod
    def _queue_item_from_row(row: sqlite3.Row) -> QueueItem:
        values: dict[str, Any] = dict(row)
        values["payload"] = json.loads(values.pop("payload_json"))
        values["requires_gpu"] = bool(values["requires_gpu"])
        values["cancel_requested"] = bool(values["cancel_requested"])
        return QueueItem.model_validate(values)

    def list_events(self, project_id: str) -> list[Event]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE project_id=? ORDER BY created_at, id", (project_id,)
            ).fetchall()
        events: list[Event] = []
        for row in rows:
            values = dict(row)
            values["payload"] = json.loads(values.pop("payload_json"))
            events.append(Event.model_validate(values))
        return events

    def _finish_attempt(
        self,
        stage_run_id: str,
        attempt_id: str,
        attempt_guard: str,
        *,
        attempt_status: AttemptStatus,
        stage_status: StageStatus,
        artifact_id: str | None,
        error: str | None,
    ) -> StageRun:
        with self.transaction() as connection:
            row = self._require_stage_run(connection, stage_run_id)
            current = StageStatus(row["status"])
            validate_transition(current, stage_status)
            if row["active_attempt_id"] != attempt_id:
                raise InvalidTransition("stale attempt cannot finish current stage run")
            attempt_row = connection.execute(
                "SELECT * FROM stage_attempts WHERE id=?", (attempt_id,)
            ).fetchone()
            if attempt_row is None or attempt_row["stage_run_id"] != stage_run_id:
                raise KeyError(f"unknown attempt for stage run: {attempt_id}")
            if attempt_row["attempt_guard"] != attempt_guard:
                raise PermissionError("attempt guard does not match")
            if AttemptStatus(attempt_row["status"]) != AttemptStatus.RUNNING:
                raise InvalidTransition("attempt is already terminal")
            now = utc_now()
            connection.execute(
                """
                UPDATE stage_attempts
                SET status=?, completed_at=?, error=? WHERE id=?
                """,
                (attempt_status.value, _iso(now), error, attempt_id),
            )
            connection.execute(
                """
                UPDATE stage_runs
                SET status=?, output_artifact_id=?, active_attempt_id=NULL,
                    cancel_requested=0, error=?, updated_at=? WHERE id=?
                """,
                (stage_status.value, artifact_id, error, _iso(now), stage_run_id),
            )
            self._insert_event(
                connection,
                project_id=row["project_id"],
                stage_run_id=stage_run_id,
                attempt_id=attempt_id,
                kind=f"attempt.{attempt_status.value}",
                payload={"artifact_id": artifact_id, "error": error},
            )
            updated = self._require_stage_run(connection, stage_run_id)
        return self._stage_run_from_row(updated)

    @staticmethod
    def _require_stage_run(
        connection: sqlite3.Connection, stage_run_id: str
    ) -> sqlite3.Row:
        row = cast(
            sqlite3.Row | None,
            connection.execute(
                "SELECT * FROM stage_runs WHERE id=?", (stage_run_id,)
            ).fetchone(),
        )
        if row is None:
            raise KeyError(f"unknown stage run: {stage_run_id}")
        return row

    @staticmethod
    def _stage_run_from_row(row: sqlite3.Row) -> StageRun:
        values: dict[str, Any] = dict(row)
        values["cancel_requested"] = bool(values["cancel_requested"])
        return StageRun.model_validate(values)

    @staticmethod
    def _insert_event(
        connection: sqlite3.Connection,
        *,
        project_id: str,
        kind: str,
        payload: dict[str, Any],
        stage_run_id: str | None = None,
        attempt_id: str | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO events(
                id, project_id, kind, stage_run_id, attempt_id, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _new_id("event"),
                project_id,
                kind,
                stage_run_id,
                attempt_id,
                json.dumps(payload, sort_keys=True, separators=(",", ":")),
                _iso(utc_now()),
            ),
        )
