"""Typed TOML settings with atomic local persistence."""

from __future__ import annotations

import json
import os
import tempfile
import tomllib
from pathlib import Path
from typing import Any

from .models import MillerSettings


def load_settings(path: Path | str) -> MillerSettings:
    target = Path(path)
    if not target.exists():
        return MillerSettings()
    with target.open("rb") as stream:
        payload = tomllib.load(stream)
    settings = payload.get("miller", payload)
    if not isinstance(settings, dict):
        raise ValueError("settings TOML must contain a table")
    return MillerSettings.model_validate(settings)


def save_settings(path: Path | str, settings: MillerSettings) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["[miller]"]
    for key, value in settings.model_dump(mode="python").items():
        lines.append(f"{key} = {_toml_value(value)}")
    payload = ("\n".join(lines) + "\n").encode("utf-8")
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


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (tuple, list)):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    raise TypeError(f"unsupported settings value: {type(value).__name__}")
