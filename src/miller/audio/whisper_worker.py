"""Process-isolated WhisperX-compatible worker contract."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from .models import AlignmentResult


class ExternalAlignmentWorker:
    def __init__(self, command: Sequence[str], *, timeout_seconds: int = 3600) -> None:
        self.command = tuple(command)
        if not self.command:
            raise ValueError("alignment worker command cannot be empty")
        self.timeout_seconds = timeout_seconds

    def probe(self) -> dict[str, object]:
        return self._call({"operation": "probe"})

    def align(
        self,
        audio_path: Path | str,
        *,
        script: str | None = None,
        language: str | None = None,
        model: str = "small",
        device: str = "cuda",
        compute_type: str = "float16",
    ) -> AlignmentResult:
        request: dict[str, object] = {
            "operation": "align",
            "audio_path": str(Path(audio_path).expanduser().resolve()),
            "model": model,
            "device": device,
            "compute_type": compute_type,
            "diarization": False,
        }
        if script is not None:
            request["script"] = script
        if language is not None:
            request["language"] = language
        return AlignmentResult.model_validate(self._call(request))

    def unload(self) -> dict[str, object]:
        return self._call({"operation": "unload"})

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
            detail = result.stderr[-2000:]
            raise RuntimeError(f"alignment worker failed with exit {result.returncode}: {detail}")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("alignment worker returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("alignment worker response must be an object")
        return payload
