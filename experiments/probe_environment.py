"""Read-only local capability probe for Sprint 0.

This does not import or execute downloaded upstream source.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    available: bool
    path: str | None = None
    version: str | None = None
    detail: str | None = None


def probe_command(name: str, version_args: tuple[str, ...]) -> Capability:
    path = shutil.which(name)
    if path is None:
        return Capability(name=name, available=False)

    try:
        result = subprocess.run(
            [path, *version_args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = (result.stdout or result.stderr).splitlines()
        version = output[0].strip() if output else None
        return Capability(
            name=name,
            available=result.returncode == 0,
            path=path,
            version=version,
            detail=None if result.returncode == 0 else f"exit={result.returncode}",
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Capability(name=name, available=False, path=path, detail=str(exc))


def probe_ollama_api() -> Capability:
    url = "http://127.0.0.1:11434/api/version"
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            payload = json.load(response)
        return Capability(
            name="ollama_api",
            available=True,
            path=url,
            version=str(payload.get("version", "unknown")),
        )
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return Capability(
            name="ollama_api",
            available=False,
            path=url,
            detail=str(exc),
        )


def main() -> int:
    capabilities = [
        probe_command("ffmpeg", ("-version",)),
        probe_command("ffprobe", ("-version",)),
        probe_command("python", ("--version",)),
        probe_command("node", ("--version",)),
        probe_command("ollama", ("--version",)),
        probe_ollama_api(),
    ]
    print(
        json.dumps(
            {
                "schema_version": 1,
                "capabilities": [asdict(item) for item in capabilities],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
