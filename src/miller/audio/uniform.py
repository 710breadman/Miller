"""Deterministic fallback timing when forced alignment is unavailable."""

from __future__ import annotations

import re

from .models import AlignmentResult, WordTiming

_WORD = re.compile(r"\S+")


def uniform_alignment(
    script: str,
    audio_duration_seconds: float,
    *,
    language: str = "en",
) -> AlignmentResult:
    """Spread script tokens uniformly over audio as an explicit low-confidence fallback."""

    if audio_duration_seconds <= 0:
        raise ValueError("audio duration must be positive")
    tokens = tuple(match.group(0) for match in _WORD.finditer(script.strip()))
    if not tokens:
        raise ValueError("script contains no words")
    interval = audio_duration_seconds / len(tokens)
    words = tuple(
        WordTiming(
            text=token,
            start=index * interval,
            end=(index + 1) * interval,
            confidence=None,
            aligned=False,
        )
        for index, token in enumerate(tokens)
    )
    return AlignmentResult(
        engine="uniform-fallback",
        engine_version="1",
        model="none",
        language=language,
        audio_duration_seconds=audio_duration_seconds,
        words=words,
        warnings=(
            "word timings are uniformly estimated; run WhisperX for accurate alignment",
        ),
    )
