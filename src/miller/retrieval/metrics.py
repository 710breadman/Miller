"""Reproducible information-retrieval metrics."""

from __future__ import annotations

import math

from .models import BenchmarkQuery, QueryRanking, RetrievalMetrics


def calculate_metrics(
    queries: tuple[BenchmarkQuery, ...],
    rankings: tuple[QueryRanking, ...],
    *,
    cutoffs: tuple[int, ...] = (1, 5, 10, 20),
) -> RetrievalMetrics:
    ranking_by_query = {ranking.query_id: ranking for ranking in rankings}
    if set(ranking_by_query) != {query.id for query in queries}:
        raise ValueError("rankings must cover each evaluation query exactly once")
    recall_totals = {cutoff: 0.0 for cutoff in cutoffs}
    ndcg_totals = {cutoff: 0.0 for cutoff in cutoffs}
    reciprocal_total = 0.0
    latency_total = 0.0
    for query in queries:
        ranking = ranking_by_query[query.id]
        relevance = {item.asset_id: item.relevance for item in query.judgments}
        relevant_ids = {asset_id for asset_id, grade in relevance.items() if grade > 0}
        result_ids = [item.asset_id for item in ranking.results]
        for cutoff in cutoffs:
            found = relevant_ids.intersection(result_ids[:cutoff])
            recall_totals[cutoff] += len(found) / len(relevant_ids)
            ndcg_totals[cutoff] += _ndcg(result_ids[:cutoff], relevance, cutoff)
        first_rank = next(
            (
                index
                for index, asset_id in enumerate(result_ids, start=1)
                if asset_id in relevant_ids
            ),
            None,
        )
        if first_rank is not None:
            reciprocal_total += 1.0 / first_rank
        latency_total += ranking.latency_ms
    count = len(queries)
    return RetrievalMetrics(
        recall_at={cutoff: recall_totals[cutoff] / count for cutoff in cutoffs},
        mean_reciprocal_rank=reciprocal_total / count,
        ndcg_at={cutoff: ndcg_totals[cutoff] / count for cutoff in cutoffs},
        mean_latency_ms=latency_total / count,
    )


def _ndcg(result_ids: list[str], relevance: dict[str, int], cutoff: int) -> float:
    dcg = sum(
        (2 ** relevance.get(asset_id, 0) - 1) / math.log2(rank + 1)
        for rank, asset_id in enumerate(result_ids, start=1)
    )
    ideal_grades = sorted(relevance.values(), reverse=True)[:cutoff]
    ideal = sum(
        (2**grade - 1) / math.log2(rank + 1)
        for rank, grade in enumerate(ideal_grades, start=1)
    )
    return 0.0 if ideal == 0 else dcg / ideal
