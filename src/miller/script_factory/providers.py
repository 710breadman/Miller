"""Read-only research provider contracts and a local text implementation."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from ..artifacts import sha256_bytes
from .models import ResearchResult, SourceKind

_TOKEN = re.compile(r"[A-Za-z0-9']+")
_SUPPORTED = frozenset({".txt", ".md", ".json", ".jsonl"})


class ResearchProvider(Protocol):
    def search(self, query: str, *, limit: int = 10) -> tuple[ResearchResult, ...]: ...


class LocalTextProvider:
    def __init__(
        self,
        roots: Iterable[Path | str],
        *,
        max_file_bytes: int = 8 * 1024 * 1024,
    ) -> None:
        self.roots = tuple(Path(root).expanduser().resolve() for root in roots)
        self.max_file_bytes = max_file_bytes

    def search(self, query: str, *, limit: int = 10) -> tuple[ResearchResult, ...]:
        terms = {token.casefold() for token in _TOKEN.findall(query)}
        if not terms or limit < 1:
            return ()
        results: list[ResearchResult] = []
        for root in self.roots:
            for path in self._files(root):
                payload = path.read_bytes()
                text = payload.decode("utf-8", errors="replace")
                tokens = [token.casefold() for token in _TOKEN.findall(text)]
                matches = sum(tokens.count(term) for term in terms)
                if matches == 0:
                    continue
                excerpt = self._excerpt(text, terms)
                digest = sha256_bytes(payload)
                results.append(
                    ResearchResult(
                        id=f"local_{digest[:16]}",
                        kind=SourceKind.LOCAL,
                        title=path.stem,
                        locator=str(path),
                        excerpt=excerpt,
                        score=float(matches),
                        content_hash=f"sha256:{digest}",
                    )
                )
        results.sort(key=lambda item: (-item.score, item.locator.casefold()))
        return tuple(results[:limit])

    def _files(self, root: Path) -> tuple[Path, ...]:
        candidates: tuple[Path, ...]
        if root.is_file():
            candidates = (root,)
        elif root.is_dir():
            candidates = tuple(path for path in root.rglob("*") if path.is_file())
        else:
            return ()
        safe: list[Path] = []
        for path in candidates:
            if path.suffix.casefold() not in _SUPPORTED:
                continue
            resolved = path.resolve()
            if root.is_dir():
                try:
                    resolved.relative_to(root)
                except ValueError:
                    continue
            size = resolved.stat().st_size
            if 0 < size <= self.max_file_bytes and not resolved.is_symlink():
                safe.append(resolved)
        return tuple(sorted(safe, key=lambda path: str(path).casefold()))

    @staticmethod
    def _excerpt(text: str, terms: set[str], *, length: int = 500) -> str:
        folded = text.casefold()
        positions = [folded.find(term) for term in terms if folded.find(term) >= 0]
        center = min(positions) if positions else 0
        start = max(0, center - length // 4)
        excerpt = " ".join(text[start : start + length].split())
        return excerpt or text[:length]
