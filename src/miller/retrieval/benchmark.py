"""Retrieval benchmark execution and report creation."""

from __future__ import annotations

import time
from typing import Protocol

from .metrics import calculate_metrics
from .models import (
    EvaluationSet,
    QueryRanking,
    RankedAsset,
    RetrievalBenchmarkReport,
    RetrievalRunConfig,
)


class Retriever(Protocol):
    index_hash: str

    def search(self, query: str, *, limit: int = 20) -> tuple[RankedAsset, ...]: ...


def run_benchmark(
    evaluation: EvaluationSet,
    retriever: Retriever,
    *,
    name: str,
    version: str,
    top_k: int = 20,
    parameters: dict[str, str | int | float | bool] | None = None,
) -> RetrievalBenchmarkReport:
    rankings: list[QueryRanking] = []
    for query in evaluation.queries:
        started = time.perf_counter()
        results = retriever.search(query.text, limit=top_k)
        latency_ms = (time.perf_counter() - started) * 1000
        rankings.append(
            QueryRanking(query_id=query.id, results=results, latency_ms=latency_ms)
        )
    ranking_tuple = tuple(rankings)
    return RetrievalBenchmarkReport(
        evaluation_name=evaluation.name,
        corpus_hash=evaluation.corpus_hash,
        config=RetrievalRunConfig(
            retriever=name,
            retriever_version=version,
            top_k=top_k,
            parameters=parameters or {},
            index_hash=retriever.index_hash,
        ),
        rankings=ranking_tuple,
        metrics=calculate_metrics(evaluation.queries, ranking_tuple),
    )
