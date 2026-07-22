"""Deterministic BM25 retrieval over page analysis text and metadata."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable

from ..analysis import PageAnalysis
from ..artifacts import canonical_json_bytes, sha256_bytes
from .models import RankedAsset

_TOKEN = re.compile(r"[A-Za-z0-9']+")


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(match.group(0).casefold() for match in _TOKEN.finditer(text))


class LexicalRetriever:
    def __init__(
        self,
        records: Iterable[PageAnalysis],
        *,
        k1: float = 1.2,
        b: float = 0.75,
    ) -> None:
        self.k1 = k1
        self.b = b
        self.records = {record.page_id: record for record in records}
        if not self.records:
            raise ValueError("lexical retriever requires records")
        self.documents = {
            asset_id: tokenize(self._document_text(record))
            for asset_id, record in self.records.items()
        }
        self.term_counts = {
            asset_id: Counter(tokens) for asset_id, tokens in self.documents.items()
        }
        self.document_frequency: Counter[str] = Counter()
        for tokens in self.documents.values():
            self.document_frequency.update(set(tokens))
        self.average_length = sum(len(tokens) for tokens in self.documents.values()) / len(
            self.documents
        )
        self.index_hash = "sha256:" + sha256_bytes(
            canonical_json_bytes(
                {
                    "documents": {
                        asset_id: list(tokens)
                        for asset_id, tokens in sorted(self.documents.items())
                    },
                    "k1": self.k1,
                    "b": self.b,
                }
            )
        )

    def search(self, query: str, *, limit: int = 20) -> tuple[RankedAsset, ...]:
        query_terms = tokenize(query)
        scores: list[tuple[str, float]] = []
        for asset_id, tokens in self.documents.items():
            score = sum(self._term_score(term, asset_id, len(tokens)) for term in query_terms)
            if score > 0:
                scores.append((asset_id, score))
        scores.sort(key=lambda item: (-item[1], item[0]))
        return tuple(
            RankedAsset(
                asset_id=asset_id,
                score=score,
                rank=index,
                components={"lexical": score},
            )
            for index, (asset_id, score) in enumerate(scores[:limit], start=1)
        )

    def _term_score(self, term: str, asset_id: str, document_length: int) -> float:
        frequency = self.term_counts[asset_id].get(term, 0)
        if frequency == 0:
            return 0.0
        document_count = len(self.documents)
        document_frequency = self.document_frequency[term]
        inverse_document_frequency = math.log(
            1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
        )
        normalization = frequency + self.k1 * (
            1 - self.b + self.b * document_length / max(self.average_length, 1)
        )
        return inverse_document_frequency * frequency * (self.k1 + 1) / normalization

    @staticmethod
    def _document_text(record: PageAnalysis) -> str:
        parts = [
            record.source_locator,
            record.description.summary,
            *record.description.characters,
            *record.description.actions,
            *record.description.moods,
            *record.description.visual_tags,
        ]
        if record.ocr is not None:
            parts.extend(span.text for span in record.ocr.spans)
        return "\n".join(parts)
