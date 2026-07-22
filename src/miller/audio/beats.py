"""Deterministic visual-beat timing over normalized narration words."""

from __future__ import annotations

import re

from .compare import normalized_words
from .models import AlignmentResult, BeatPlan, NarrationBeat

_SENTENCE_END = re.compile(r"[.!?]+(?:[\"')\]]+)?$")


def build_beat_plan(
    script: str,
    alignment: AlignmentResult,
    *,
    maximum_duration_seconds: float = 8.0,
    maximum_words: int = 28,
) -> BeatPlan:
    if not alignment.words:
        raise ValueError("alignment contains no words")
    script_tokens = normalized_words(script)
    section_boundaries = _section_boundaries(script)
    warnings: list[str] = []
    if len(script_tokens) != len(alignment.words):
        warnings.append(
            "script/audio word counts differ; beat text follows aligned narration words"
        )
    beats: list[NarrationBeat] = []
    start_index = 0
    section_index = 0
    for index, word in enumerate(alignment.words):
        while section_index + 1 < len(section_boundaries) and index >= section_boundaries[
            section_index + 1
        ]:
            section_index += 1
        current_count = index - start_index + 1
        current_duration = word.end - alignment.words[start_index].start
        sentence_end = bool(_SENTENCE_END.search(word.text))
        final_word = index == len(alignment.words) - 1
        should_close = (
            final_word
            or current_count >= maximum_words
            or current_duration >= maximum_duration_seconds
            or (sentence_end and current_duration >= 1.2)
        )
        if not should_close:
            continue
        start = alignment.words[start_index].start if not beats else beats[-1].end
        end = word.end
        words = alignment.words[start_index : index + 1]
        beats.append(
            NarrationBeat(
                id=f"beat_{len(beats) + 1:04d}",
                section_index=section_index,
                start=start,
                end=end,
                text=" ".join(item.text for item in words),
                first_word_index=start_index,
                last_word_index=index,
            )
        )
        start_index = index + 1
    return BeatPlan(
        beats=tuple(beats),
        audio_duration_seconds=alignment.audio_duration_seconds,
        warnings=tuple(warnings),
    )


def _section_boundaries(script: str) -> tuple[int, ...]:
    boundaries = [0]
    consumed = 0
    for paragraph in re.split(r"\n\s*\n", script.strip()):
        consumed += len(normalized_words(paragraph))
        boundaries.append(consumed)
    return tuple(boundaries)
