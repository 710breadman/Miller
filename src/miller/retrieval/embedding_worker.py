"""JSON subprocess boundary for optional embedding-model environments."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EmbeddingWorkerResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    dimensions: int = Field(gt=0)
    vectors: tuple[tuple[float, ...], ...]
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_vectors(self) -> EmbeddingWorkerResult:
        if not self.vectors:
            raise ValueError("embedding worker returned no vectors")
        if any(len(vector) != self.dimensions for vector in self.vectors):
            raise ValueError("embedding vector dimensions do not match declaration")
        return self



class ExternalEmbeddingWorker:
    """Call a pinned OpenCLIP/SigLIP worker without importing its dependencies."""

    def __init__(self, command: Sequence[str], *, timeout_seconds: int = 600) -> None:
        self.command = tuple(command)
        if not self.command:
            raise ValueError("embedding worker command cannot be empty")
        self.timeout_seconds = timeout_seconds

    def probe(self) -> dict[str, object]:
        return self._call({"operation": "probe"})

    def embed_text(self, texts: Sequence[str]) -> EmbeddingWorkerResult:
        payload = self._call({"operation": "embed_text", "texts": list(texts)})
        return EmbeddingWorkerResult.model_validate(payload)

    def embed_images(self, paths: Sequence[Path | str]) -> EmbeddingWorkerResult:
        resolved = [str(Path(path).expanduser().resolve()) for path in paths]
        payload = self._call({"operation": "embed_images", "paths": resolved})
        return EmbeddingWorkerResult.model_validate(payload)

    def _call(self, request: dict[str, object]) -> dict[str, object]:
        result = subprocess.run(
            self.command,
            input=json.dumps(request, sort_keys=True),
            capture_output=True,
            text=True,
            check=False,
            timeout=self.timeout_seconds,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"embedding worker failed with exit {result.returncode}: {result.stderr[-2000:]}"
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("embedding worker returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("embedding worker response must be an object")
        return payload
