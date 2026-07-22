"""Score fusion helpers for lexical and semantic retrieval."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .models import RankedAsset


def fuse_scores(
    lexical: Sequence[RankedAsset],
    semantic: Mapping[str, float],
    *,
    lexical_weight: float = 0.45,
    semantic_weight: float = 0.55,
    limit: int = 20,
) -> tuple[RankedAsset, ...]:
    if lexical_weight < 0 or semantic_weight < 0 or lexical_weight + semantic_weight <= 0:
        raise ValueError("hybrid weights must be non-negative and sum above zero")
    lexical_scores = {item.asset_id: item.score for item in lexical}
    normalized_lexical = _normalize(lexical_scores)
    normalized_semantic = _normalize(dict(semantic))
    asset_ids = set(normalized_lexical) | set(normalized_semantic)
    combined = [
        (
            asset_id,
            normalized_lexical.get(asset_id, 0.0) * lexical_weight
            + normalized_semantic.get(asset_id, 0.0) * semantic_weight,
        )
        for asset_id in asset_ids
    ]
    combined.sort(key=lambda item: (-item[1], item[0]))
    return tuple(
        RankedAsset(
            asset_id=asset_id,
            score=score,
            rank=rank,
            components={
                "lexical": normalized_lexical.get(asset_id, 0.0),
                "semantic": normalized_semantic.get(asset_id, 0.0),
            },
        )
        for rank, (asset_id, score) in enumerate(combined[:limit], start=1)
    )


def _normalize(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    minimum = min(scores.values())
    maximum = max(scores.values())
    if maximum == minimum:
        return {asset_id: 1.0 for asset_id in scores}
    return {
        asset_id: (score - minimum) / (maximum - minimum)
        for asset_id, score in scores.items()
    }
