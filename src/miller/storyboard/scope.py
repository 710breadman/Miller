"""Deterministic script-led comic search scope proposal."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from ..analysis import PageAnalysis
from .models import SearchScope


def propose_search_scope(
    script: str,
    records: Iterable[PageAnalysis],
    *,
    steering_keywords: tuple[str, ...] = (),
    exclusions: tuple[str, ...] = (),
    character_limit: int = 8,
    series_limit: int = 8,
) -> SearchScope:
    haystack = f"{script}\n{' '.join(steering_keywords)}".casefold()
    exclusion_set = {item.casefold() for item in exclusions}
    character_counts: Counter[str] = Counter()
    series_counts: Counter[str] = Counter()
    mood_counts: Counter[str] = Counter()
    for record in records:
        for character in record.description.characters:
            if character.casefold() in exclusion_set:
                continue
            if character.casefold() in haystack:
                character_counts[character] += 1
        series = record.source_locator.split("/", maxsplit=1)[0]
        if series.casefold() not in exclusion_set and series.casefold() in haystack:
            series_counts[series] += 1
        for mood in record.description.moods:
            if mood.casefold() not in exclusion_set and mood.casefold() in haystack:
                mood_counts[mood] += 1
    return SearchScope(
        characters=tuple(item for item, _ in character_counts.most_common(character_limit)),
        series=tuple(item for item, _ in series_counts.most_common(series_limit)),
        moods=tuple(item for item, _ in mood_counts.most_common(5)),
        steering_keywords=steering_keywords,
        exclusions=exclusions,
    )
