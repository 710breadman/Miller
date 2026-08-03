"""Process-isolated WhisperX-compatible worker contract.

See ``worker/align_worker.py`` for the standalone, isolated-environment
process this class is meant to launch, and ``worker/requirements.txt`` for
its pinned, reproducible dependency set (kept separate from Miller's core
environment; D-005 in DECISIONS.md).
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from .models import AlignmentResult

_CPU_FALLBACK_COMPUTE_TYPE = "int8"


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
        engine: str = "whisperx",
        device: str = "auto",
        compute_type: str = "auto",
    ) -> AlignmentResult:
        """Align ``audio_path``.

        ``device="auto"`` (the default) probes the worker environment first
        and falls back to CPU when CUDA is unavailable, rather than failing
        on a machine without a usable GPU; pass an explicit ``"cuda"`` or
        ``"cpu"`` to skip that probe call.
        """

        if device == "auto" or compute_type == "auto":
            probe = self.probe()
            if device == "auto":
                device = str(probe.get("recommended_device", "cpu"))
            if compute_type == "auto":
                compute_type = str(
                    probe.get("recommended_compute_type", _CPU_FALLBACK_COMPUTE_TYPE)
                )
        request: dict[str, object] = {
            "operation": "align",
            "engine": engine,
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
            detail = self._extract_error_message(result.stdout) or result.stderr[-2000:]
            raise RuntimeError(f"alignment worker failed with exit {result.returncode}: {detail}")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("alignment worker returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("alignment worker response must be an object")
        return payload

    @staticmethod
    def _extract_error_message(stdout: str) -> str | None:
        """Prefer the worker's structured ``{"error": ...}`` body, if present."""

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            return None
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, str):
                return error
        return None
