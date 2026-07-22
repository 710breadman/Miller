"""Content-addressed managed artifacts and deterministic fingerprints."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .db import Database
from .models import Artifact

_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    """Encode JSON-like data in a stable representation."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")


def stage_fingerprint(
    *,
    stage_id: str,
    stage_version: str,
    config: Mapping[str, Any],
    dependency_artifacts: Sequence[str],
    implementation_version: str = "1",
) -> str:
    payload = {
        "implementation_version": implementation_version,
        "stage_id": stage_id,
        "stage_version": stage_version,
        "config": dict(config),
        "dependency_artifacts": list(dependency_artifacts),
    }
    return f"sha256:{sha256_bytes(canonical_json_bytes(payload))}"


class ArtifactStore:
    """Write derived data only inside Miller's managed workspace."""

    def __init__(self, workspace: Path | str, database: Database) -> None:
        self.workspace = Path(workspace).resolve()
        self.database = database

    def ensure_project_layout(self, project_id: str) -> Path:
        project_root = self._project_root(project_id)
        for child in ("artifacts", "logs", "tmp"):
            (project_root / child).mkdir(parents=True, exist_ok=True)
        return project_root

    def put_bytes(
        self,
        *,
        project_id: str,
        stage_run_id: str | None,
        payload: bytes,
        suffix: str = ".bin",
        media_type: str = "application/octet-stream",
        metadata: dict[str, Any] | None = None,
    ) -> Artifact:
        if not suffix.startswith(".") or "/" in suffix or "\\" in suffix:
            raise ValueError("artifact suffix must be a simple extension")
        digest = sha256_bytes(payload)
        self.ensure_project_layout(project_id)
        target = self.workspace / "cache" / "artifacts" / digest[:2] / f"{digest}{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        self._assert_managed(target)
        if target.exists():
            if sha256_file(target) != digest:
                raise RuntimeError(f"artifact collision or corruption: {target}")
        else:
            self._atomic_write(target, payload)
        relative_path = target.relative_to(self.workspace).as_posix()
        record_digest = sha256_bytes(
            canonical_json_bytes(
                {
                    "project_id": project_id,
                    "stage_run_id": stage_run_id,
                    "content_id": f"sha256:{digest}",
                    "media_type": media_type,
                }
            )
        )
        artifact = Artifact(
            id=f"artifact_{record_digest}",
            content_id=f"sha256:{digest}",
            project_id=project_id,
            stage_run_id=stage_run_id,
            relative_path=relative_path,
            sha256=digest,
            size_bytes=len(payload),
            media_type=media_type,
            metadata=metadata or {},
        )
        self.database.add_artifact(artifact)
        return artifact

    def put_json(
        self,
        *,
        project_id: str,
        stage_run_id: str | None,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> Artifact:
        return self.put_bytes(
            project_id=project_id,
            stage_run_id=stage_run_id,
            payload=canonical_json_bytes(value) + b"\n",
            suffix=".json",
            media_type="application/json",
            metadata=metadata,
        )

    def resolve(self, artifact: Artifact) -> Path:
        path = (self.workspace / artifact.relative_path).resolve()
        self._assert_managed(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256_file(path) != artifact.sha256:
            raise RuntimeError(f"artifact failed integrity check: {path}")
        return path

    def _project_root(self, project_id: str) -> Path:
        if not _SAFE_COMPONENT.fullmatch(project_id):
            raise ValueError("project ID is not a safe path component")
        root = (self.workspace / "projects" / project_id).resolve()
        self._assert_managed(root)
        return root

    def _assert_managed(self, path: Path) -> None:
        try:
            path.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError(f"path escapes managed workspace: {path}") from exc

    @staticmethod
    def _atomic_write(target: Path, payload: bytes) -> None:
        descriptor, temporary_name = tempfile.mkstemp(prefix=".miller-", dir=target.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
