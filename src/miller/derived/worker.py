"""External comic inpainting worker boundary."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path


class ExternalInpaintWorker:
    def __init__(self, command: Sequence[str], *, timeout_seconds: int = 900) -> None:
        self.command = tuple(command)
        if not self.command:
            raise ValueError("inpaint worker command cannot be empty")
        self.timeout_seconds = timeout_seconds

    def probe(self) -> dict[str, object]:
        return self._call({"operation": "probe"})

    def inpaint(
        self,
        image_path: Path | str,
        mask_path: Path | str,
        output_path: Path | str,
    ) -> dict[str, object]:
        return self._call(
            {
                "operation": "inpaint",
                "image_path": str(Path(image_path).expanduser().resolve()),
                "mask_path": str(Path(mask_path).expanduser().resolve()),
                "output_path": str(Path(output_path).expanduser().resolve()),
            }
        )

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
            raise RuntimeError(f"inpaint worker failed with exit {result.returncode}: {detail}")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("inpaint worker returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("inpaint worker response must be an object")
        return payload
