"""Compare the supplied script against words actually present in narration."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from .models import (
    ScriptComparison,
    ScriptDifference,
    ScriptDifferenceKind,
    WordTiming,
)

_WORD = re.compile(r"[A-Za-z0-9']+")


def normalized_words(text: str) -> tuple[str, ...]:
    return tuple(match.group(0).casefold() for match in _WORD.finditer(text))


def compare_script_to_audio(script: str, audio_words: tuple[WordTiming, ...]) -> ScriptComparison:
    script_words = normalized_words(script)
    recognized_tokens: list[str] = []
    for word in audio_words:
        tokens = normalized_words(word.text)
        if tokens:
            recognized_tokens.append(tokens[0])
    recognized = tuple(recognized_tokens)
    matcher = SequenceMatcher(a=script_words, b=recognized, autojunk=False)
    differences: list[ScriptDifference] = []
    pickups: set[int] = set()
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        kind = {
            "equal": ScriptDifferenceKind.EQUAL,
            "delete": ScriptDifferenceKind.OMISSION,
            "insert": ScriptDifferenceKind.INSERTION,
            "replace": ScriptDifferenceKind.SUBSTITUTION,
        }[tag]
        differences.append(
            ScriptDifference(
                kind=kind,
                script_start=i1,
                script_end=i2,
                audio_start=j1,
                audio_end=j2,
                script_text=" ".join(script_words[i1:i2]),
                audio_text=" ".join(recognized[j1:j2]),
            )
        )
        if kind in {ScriptDifferenceKind.OMISSION, ScriptDifferenceKind.SUBSTITUTION}:
            pickups.update(range(i1, i2))
    return ScriptComparison(
        differences=tuple(differences),
        script_word_count=len(script_words),
        audio_word_count=len(recognized),
        match_ratio=matcher.ratio(),
        pickup_word_indexes=tuple(sorted(pickups)),
    )
