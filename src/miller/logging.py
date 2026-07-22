"""Append-only structured project logs."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class JsonlProjectLog:
    def __init__(self, workspace: Path | str, project_id: str) -> None:
        self.path = Path(workspace) / "projects" / project_id / "logs" / "events.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, kind: str, **payload: Any) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "kind": kind,
            **payload,
        }
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
        descriptor = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            os.write(descriptor, encoded.encode("utf-8"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
