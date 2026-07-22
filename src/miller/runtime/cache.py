"""Safe inspection and pruning of Miller-managed cache files."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from .models import CacheEntry, CachePlan


class CacheManager:
    def __init__(self, workspace: Path | str) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.cache_root = (self.workspace / "cache").resolve()

    def entries(self) -> tuple[CacheEntry, ...]:
        if not self.cache_root.exists():
            return ()
        records: list[CacheEntry] = []
        for path in self.cache_root.rglob("*"):
            if path.is_symlink():
                continue
            if not path.is_file():
                continue
            resolved = path.resolve()
            self._require_cache_path(resolved)
            stat = resolved.stat()
            records.append(
                CacheEntry(
                    relative_path=resolved.relative_to(self.workspace).as_posix(),
                    size_bytes=stat.st_size,
                    modified_ns=stat.st_mtime_ns,
                )
            )
        return tuple(sorted(records, key=lambda item: (item.modified_ns, item.relative_path)))

    def plan_prune(self, target_bytes: int, *, dry_run: bool = True) -> CachePlan:
        if target_bytes < 0:
            raise ValueError("target_bytes cannot be negative")
        entries = self.entries()
        total = sum(entry.size_bytes for entry in entries)
        remaining = total
        selected: list[CacheEntry] = []
        for entry in entries:
            if remaining <= target_bytes:
                break
            selected.append(entry)
            remaining -= entry.size_bytes
        return CachePlan(
            total_bytes=total,
            target_bytes=target_bytes,
            reclaim_bytes=total - remaining,
            entries=tuple(selected),
            dry_run=dry_run,
        )

    def apply(self, plan: CachePlan) -> CachePlan:
        if plan.dry_run:
            return plan
        for entry in plan.entries:
            path = (self.workspace / entry.relative_path).resolve()
            self._require_cache_path(path)
            if path.is_symlink():
                raise ValueError(f"refusing to delete cache symlink: {path}")
            if path.is_file():
                path.unlink()
        self._remove_empty_directories()
        return plan

    def prune(self, target_bytes: int, *, dry_run: bool = True) -> CachePlan:
        plan = self.plan_prune(target_bytes, dry_run=dry_run)
        return self.apply(plan)

    def _require_cache_path(self, path: Path) -> None:
        try:
            path.relative_to(self.cache_root)
        except ValueError as exc:
            raise ValueError(f"path is outside Miller cache: {path}") from exc

    def _remove_empty_directories(self) -> None:
        if not self.cache_root.exists():
            return
        directories = sorted(
            (path for path in self.cache_root.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        )
        for directory in directories:
            with suppress(OSError):
                directory.rmdir()
