"""Traceable automatic storyboard creation from narration beats and retrieval."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping

from ..analysis import PageAnalysis
from ..audio import BeatPlan, NarrationBeat
from ..retrieval import LexicalRetriever, RankedAsset
from .models import (
    CameraPlan,
    CameraPreset,
    SceneCandidate,
    SceneScore,
    SearchScope,
    StoryboardPlan,
    StoryboardScene,
    TransitionPreset,
)


class StoryboardBuilder:
    def __init__(
        self,
        records: Iterable[PageAnalysis],
        *,
        narrative_scores: Mapping[str, float] | None = None,
    ) -> None:
        self.records = {record.page_id: record for record in records}
        if not self.records:
            raise ValueError("storyboard builder requires analyzed pages")
        self.retriever = LexicalRetriever(self.records.values())
        self.narrative_scores = dict(narrative_scores or {})
        if any(value < 0 or value > 1 for value in self.narrative_scores.values()):
            raise ValueError("narrative scores must be between 0 and 1")

    def build(
        self,
        beats: BeatPlan,
        scope: SearchScope,
        *,
        excluded_assets: frozenset[str] = frozenset(),
        locked_choices: Mapping[str, str] | None = None,
        candidate_limit: int = 12,
    ) -> StoryboardPlan:
        locked_choices = locked_choices or {}
        usage: Counter[str] = Counter()
        scenes: list[StoryboardScene] = []
        warnings: list[str] = []
        for index, beat in enumerate(beats.beats, start=1):
            query = self._query(beat, scope)
            ranked = self.retriever.search(query, limit=max(candidate_limit * 3, 20))
            if not ranked:
                warnings.append(f"no lexical match for {beat.id}; used quality fallback")
                ranked = tuple(
                    RankedAsset(
                        asset_id=record.page_id,
                        score=max(record.quality.overall_score, 0.01),
                        rank=rank,
                        components={"quality_fallback": record.quality.overall_score},
                    )
                    for rank, record in enumerate(
                        sorted(
                            self.records.values(),
                            key=lambda item: (-item.quality.overall_score, item.page_id),
                        ),
                        start=1,
                    )
                )
            candidates = self._score_candidates(
                beat,
                ranked,
                scope,
                usage,
                excluded_assets,
                limit=candidate_limit,
            )
            locked_asset = locked_choices.get(beat.id)
            if locked_asset is not None:
                if locked_asset in excluded_assets:
                    raise ValueError(f"locked asset is excluded for {beat.id}: {locked_asset}")
                if locked_asset not in self.records:
                    raise KeyError(f"unknown locked asset for {beat.id}: {locked_asset}")
                candidates = self._ensure_locked_candidate(
                    locked_asset, candidates, beat, scope, usage
                )
            if not candidates:
                raise ValueError(f"no storyboard candidates for {beat.id}")
            primary = locked_asset or self._first_unused(candidates, usage)
            usage[primary] += 1
            alternatives = tuple(
                candidate.asset_id
                for candidate in candidates
                if candidate.asset_id != primary
            )[:3]
            mood = self._mood(beat, scope)
            scenes.append(
                StoryboardScene(
                    id=f"scene_{index:04d}",
                    beat_id=beat.id,
                    start=beat.start,
                    end=beat.end,
                    narration=beat.text,
                    intent=beat.text,
                    mood=mood,
                    primary_asset=primary,
                    alternatives=alternatives,
                    candidates=tuple(candidates),
                    camera=self._camera(index, beat.end - beat.start),
                    transition=self._transition(index, mood),
                    music_state=mood,
                    locked=locked_asset is not None,
                    review_status="locked" if locked_asset is not None else "automatic",
                )
            )
            if candidates[0].score.total < 0.25:
                warnings.append(f"low-confidence visual match for {beat.id}")
        return StoryboardPlan(scope=scope, scenes=tuple(scenes), warnings=tuple(warnings))

    def _score_candidates(
        self,
        beat: NarrationBeat,
        ranked: tuple[RankedAsset, ...],
        scope: SearchScope,
        usage: Counter[str],
        excluded_assets: frozenset[str],
        *,
        limit: int,
    ) -> list[SceneCandidate]:
        maximum_lexical = max((item.score for item in ranked), default=1.0)
        candidates: list[SceneCandidate] = []
        for item in ranked:
            if item.asset_id in excluded_assets:
                continue
            record = self.records[item.asset_id]
            lexical = item.score / maximum_lexical if maximum_lexical > 0 else 0.0
            characters = {
                character.casefold() for character in record.description.characters
            }
            scope_characters = {character.casefold() for character in scope.characters}
            character_score = 1.0 if characters & scope_characters else 0.25
            record_terms = {
                *[mood.casefold() for mood in record.description.moods],
                *[tag.casefold() for tag in record.description.visual_tags],
                *[action.casefold() for action in record.description.actions],
            }
            beat_terms = set(beat.text.casefold().split())
            theme_score = min(1.0, len(record_terms & beat_terms) / 2) if record_terms else 0.25
            continuity = 1.0 if not scope.series else float(
                any(
                    record.source_locator.casefold().startswith(series.casefold())
                    for series in scope.series
                )
            )
            quality = record.quality.overall_score
            narrative = self.narrative_scores.get(item.asset_id, 0.0)
            reuse_penalty = min(1.0, usage[item.asset_id] * 0.55)
            base_total = max(
                0.0,
                min(
                    1.0,
                    lexical * 0.48
                    + character_score * 0.16
                    + theme_score * 0.10
                    + continuity * 0.08
                    + quality * 0.18
                    - reuse_penalty * 0.45,
                ),
            )
            total = min(1.0, base_total * (0.75 if narrative else 1.0) + narrative * 0.25)
            reasons = [f"lexical={lexical:.3f}", f"quality={quality:.3f}"]
            if narrative:
                reasons.append(f"comic-sorter-narrative={narrative:.3f}")
            if characters & scope_characters:
                reasons.append("character match")
            if continuity == 1.0 and scope.series:
                reasons.append("series match")
            candidates.append(
                SceneCandidate(
                    asset_id=item.asset_id,
                    source_locator=record.source_locator,
                    score=SceneScore(
                        lexical=lexical,
                        character=character_score,
                        theme=theme_score,
                        continuity=continuity,
                        quality=quality,
                        narrative=narrative,
                        reuse_penalty=reuse_penalty,
                        total=total,
                    ),
                    reasons=tuple(reasons),
                )
            )
        candidates.sort(key=lambda candidate: (-candidate.score.total, candidate.asset_id))
        return candidates[:limit]

    def _ensure_locked_candidate(
        self,
        asset_id: str,
        candidates: list[SceneCandidate],
        beat: NarrationBeat,
        scope: SearchScope,
        usage: Counter[str],
    ) -> list[SceneCandidate]:
        if any(candidate.asset_id == asset_id for candidate in candidates):
            return candidates
        synthetic = self._score_candidates(
            beat,
            (RankedAsset(asset_id=asset_id, score=1.0, rank=1),),
            scope,
            usage,
            frozenset(),
            limit=1,
        )[0]
        return [synthetic, *candidates]

    @staticmethod
    def _first_unused(candidates: list[SceneCandidate], usage: Counter[str]) -> str:
        return next(
            (candidate.asset_id for candidate in candidates if usage[candidate.asset_id] == 0),
            candidates[0].asset_id,
        )

    @staticmethod
    def _query(beat: NarrationBeat, scope: SearchScope) -> str:
        return " ".join(
            (
                beat.text,
                *scope.characters,
                *scope.series,
                *scope.moods,
                *scope.steering_keywords,
            )
        )

    @staticmethod
    def _mood(beat: NarrationBeat, scope: SearchScope) -> str:
        text = beat.text.casefold()
        for mood in scope.moods:
            if mood.casefold() in text:
                return mood
        return scope.moods[0] if scope.moods else "neutral"

    @staticmethod
    def _camera(index: int, duration: float) -> CameraPlan:
        if duration >= 7:
            preset = CameraPreset.SLOW_PUSH
        else:
            cycle = (
                CameraPreset.SLOW_PUSH,
                CameraPreset.PAN_RIGHT,
                CameraPreset.SLOW_PULL,
                CameraPreset.PAN_LEFT,
            )
            preset = cycle[(index - 1) % len(cycle)]
        return CameraPlan(preset=preset, intensity=min(0.5, max(0.15, duration / 20)))

    @staticmethod
    def _transition(index: int, mood: str) -> TransitionPreset:
        if index == 1:
            return TransitionPreset.CUT
        if mood.casefold() in {"somber", "reflective", "grief", "mournful"}:
            return TransitionPreset.DIP_BLACK
        return TransitionPreset.CROSSFADE if index % 4 == 0 else TransitionPreset.CUT
