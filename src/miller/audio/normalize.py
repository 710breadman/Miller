"""Normalization for raw word-level alignment output."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .models import AlignmentResult, WordTiming


def normalize_alignment_words(
    raw_words: Iterable[Mapping[str, Any]],
    *,
    audio_duration_seconds: float,
    engine: str,
    engine_version: str,
    model: str,
    language: str,
) -> AlignmentResult:
    words: list[WordTiming] = []
    warnings: list[str] = []
    previous_end = 0.0
    for index, raw in enumerate(raw_words):
        text = str(raw.get("word") or raw.get("text") or "").strip()
        if not text:
            warnings.append(f"word {index} omitted because text is empty")
            continue
        start_raw = raw.get("start")
        end_raw = raw.get("end")
        if start_raw is None or end_raw is None:
            warnings.append(f"word {index} is unaligned: {text}")
            continue
        start = max(0.0, float(start_raw))
        end = min(audio_duration_seconds, float(end_raw))
        if start < previous_end:
            if previous_end - start <= 0.05:
                start = previous_end
            else:
                raise ValueError(f"word {index} overlaps previous timing")
        if end <= start:
            warnings.append(f"word {index} has invalid timing: {text}")
            continue
        score_raw = raw.get("score") if raw.get("score") is not None else raw.get("confidence")
        confidence = None if score_raw is None else max(0.0, min(1.0, float(score_raw)))
        word = WordTiming(
            text=text,
            start=start,
            end=end,
            confidence=confidence,
            aligned=True,
        )
        words.append(word)
        previous_end = end
    return AlignmentResult(
        engine=engine,
        engine_version=engine_version,
        model=model,
        language=language,
        audio_duration_seconds=audio_duration_seconds,
        words=tuple(words),
        warnings=tuple(warnings),
    )
