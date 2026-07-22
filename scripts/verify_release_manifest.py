"""Verify every file recorded in RELEASE_MANIFEST.json."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "RELEASE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for record in manifest["files"]:
        path = root / record["path"]
        if not path.is_file():
            failures.append(f"missing: {record['path']}")
            continue
        if path.stat().st_size != record["size_bytes"]:
            failures.append(f"size mismatch: {record['path']}")
            continue
        if sha256_file(path) != record["sha256"]:
            failures.append(f"hash mismatch: {record['path']}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Release manifest verified: {len(manifest['files'])} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
