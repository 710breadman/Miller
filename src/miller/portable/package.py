"""Integrity-checked portable project export and import."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from ..artifacts import sha256_bytes, sha256_file
from ..db import Database
from ..models import StageDefinition
from .models import PortableProjectManifest

_MANIFEST = "miller-project.json"
_MAX_MEMBERS = 100_000
_MAX_MEMBER_BYTES = 20 * 1024 * 1024 * 1024


def _safe_member(name: str) -> str:
    if "\\" in name:
        raise ValueError(f"portable member uses backslashes: {name}")
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe portable member: {name}")
    return path.as_posix()


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(_safe_member(name), date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    return info


class PortableProjectExporter:
    def __init__(self, database: Database, workspace: Path | str) -> None:
        self.database = database
        self.workspace = Path(workspace).expanduser().resolve()

    def export(self, project_id: str, output: Path | str) -> PortableProjectManifest:
        project = self.database.get_project(project_id)
        runs = tuple(self.database.list_stage_runs(project_id))
        definitions = tuple(
            self.database.get_stage_definition(stage_id)
            for stage_id in dict.fromkeys(run.stage_id for run in runs)
        )
        documents = tuple(self.database.list_documents(project_id))
        history = tuple(
            item
            for document in documents
            for item in self.database.list_document_history(project_id, document.kind)
        )
        manifest = PortableProjectManifest(
            project=project,
            stage_definitions=definitions,
            stage_runs=runs,
            artifacts=tuple(self.database.list_artifacts(project_id)),
            documents=documents,
            document_history=history,
            events=tuple(self.database.list_events(project_id)),
        )
        target = Path(output).expanduser().resolve()
        if target.exists():
            raise FileExistsError(f"portable output already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".miller-", dir=target.parent)
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary, "w", allowZip64=True) as bundle:
                payload = manifest.model_dump_json(indent=2).encode("utf-8") + b"\n"
                bundle.writestr(_zip_info(_MANIFEST), payload)
                for artifact in manifest.artifacts:
                    source = (self.workspace / artifact.relative_path).resolve()
                    self._require_workspace_path(source)
                    if sha256_file(source) != artifact.sha256:
                        raise RuntimeError(f"artifact integrity check failed: {source}")
                    bundle.writestr(
                        _zip_info("managed/" + artifact.relative_path),
                        source.read_bytes(),
                    )
                project_root = (self.workspace / "projects" / project_id).resolve()
                if project_root.is_dir():
                    self._require_workspace_path(project_root)
                    for source in sorted(project_root.rglob("*")):
                        if source.is_symlink() or not source.is_file():
                            continue
                        relative = source.relative_to(project_root).as_posix()
                        bundle.writestr(
                            _zip_info("project-files/" + relative),
                            source.read_bytes(),
                        )
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return manifest

    def _require_workspace_path(self, path: Path) -> None:
        try:
            path.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError(f"path escapes Miller workspace: {path}") from exc


class PortableProjectImporter:
    def __init__(self, database: Database, workspace: Path | str) -> None:
        self.database = database
        self.workspace = Path(workspace).expanduser().resolve()

    def import_package(self, package: Path | str) -> PortableProjectManifest:
        source = Path(package).expanduser().resolve()
        with zipfile.ZipFile(source) as bundle:
            members = [member for member in bundle.infolist() if not member.is_dir()]
            if len(members) > _MAX_MEMBERS:
                raise ValueError("portable package contains too many files")
            normalized: dict[str, zipfile.ZipInfo] = {}
            for member in members:
                name = _safe_member(member.filename)
                if member.file_size > _MAX_MEMBER_BYTES:
                    raise ValueError(f"portable member is too large: {name}")
                if name in normalized:
                    raise ValueError(f"duplicate portable member: {name}")
                normalized[name] = member
            manifest_member = normalized.get(_MANIFEST)
            if manifest_member is None:
                raise ValueError("portable package is missing its manifest")
            manifest = PortableProjectManifest.model_validate_json(
                bundle.read(manifest_member)
            )
            self._ensure_project_absent(manifest.project.id)
            imported_project = manifest.project.model_copy(
                update={"workspace": str(self.workspace)}
            )
            self.database.create_project(
                imported_project.name,
                self.workspace,
                imported_project.id,
            )
            self._register_definitions(manifest.stage_definitions)
            for run in manifest.stage_runs:
                self.database.restore_stage_run(run)
            for artifact in manifest.artifacts:
                artifact_member = normalized.get("managed/" + artifact.relative_path)
                if artifact_member is None:
                    raise ValueError(
                        f"portable artifact is missing: {artifact.relative_path}"
                    )
                payload = bundle.read(artifact_member)
                if sha256_bytes(payload) != artifact.sha256:
                    raise ValueError(f"portable artifact hash mismatch: {artifact.relative_path}")
                target = (self.workspace / artifact.relative_path).resolve()
                self._write_managed(target, payload)
                self.database.add_artifact(artifact)
            for item in manifest.document_history:
                try:
                    current = self.database.get_document(item.project_id, item.kind).revision
                except KeyError:
                    current = 0
                self.database.put_document(
                    item.project_id,
                    item.kind,
                    item.document,
                    expected_revision=current,
                )
            for name, member in normalized.items():
                if not name.startswith("project-files/"):
                    continue
                relative = name.removeprefix("project-files/")
                target = (self.workspace / "projects" / manifest.project.id / relative).resolve()
                self._write_managed(target, bundle.read(member))
        return manifest

    def _ensure_project_absent(self, project_id: str) -> None:
        try:
            self.database.get_project(project_id)
        except KeyError:
            return
        raise ValueError(f"project already exists: {project_id}")

    def _register_definitions(self, definitions: tuple[StageDefinition, ...]) -> None:
        pending = {definition.id: definition for definition in definitions}
        while pending:
            progressed = False
            for stage_id, definition in tuple(pending.items()):
                if all(dependency not in pending for dependency in definition.dependencies):
                    self.database.register_stage(definition)
                    del pending[stage_id]
                    progressed = True
            if not progressed:
                raise ValueError("portable stage definitions contain a cycle")

    def _write_managed(self, target: Path, payload: bytes) -> None:
        try:
            target.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError(f"portable output escapes workspace: {target}") from exc
        if target.exists() and target.read_bytes() != payload:
            raise ValueError(f"portable output would overwrite different data: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(payload)
