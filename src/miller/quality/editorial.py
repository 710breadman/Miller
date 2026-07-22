"""Deterministic storyboard quality checks."""

from __future__ import annotations

from collections import Counter

from ..storyboard import CameraPreset, StoryboardPlan
from .models import (
    FindingCategory,
    FindingSeverity,
    QualityFinding,
    QualityReport,
)


class StoryboardQualityEvaluator:
    def __init__(
        self,
        *,
        weak_match_threshold: float = 0.30,
        repeated_motion_limit: int = 3,
        static_run_limit: int = 3,
    ) -> None:
        self.weak_match_threshold = weak_match_threshold
        self.repeated_motion_limit = repeated_motion_limit
        self.static_run_limit = static_run_limit

    def evaluate(self, plan: StoryboardPlan, *, pass_index: int = 0) -> QualityReport:
        findings: list[QualityFinding] = []
        usage: Counter[str] = Counter(scene.primary_asset for scene in plan.scenes)
        for asset_id, count in sorted(usage.items()):
            if count <= 1:
                continue
            scene_ids = tuple(
                scene.id for scene in plan.scenes if scene.primary_asset == asset_id
            )
            findings.append(
                self._finding(
                    findings,
                    FindingCategory.DUPLICATE_ASSET,
                    FindingSeverity.WARNING,
                    scene_ids,
                    f"Asset is used {count} times without an explicit motif marker.",
                    {"asset_id": asset_id, "count": count},
                    "replace duplicate scene asset",
                )
            )
        for scene in plan.scenes:
            selected = next(
                candidate
                for candidate in scene.candidates
                if candidate.asset_id == scene.primary_asset
            )
            if selected.score.total < self.weak_match_threshold:
                findings.append(
                    self._finding(
                        findings,
                        FindingCategory.WEAK_MATCH,
                        FindingSeverity.WARNING,
                        (scene.id,),
                        "Selected visual has a weak deterministic match score.",
                        {
                            "score": selected.score.total,
                            "threshold": self.weak_match_threshold,
                        },
                        "select a stronger alternative",
                    )
                )
        findings.extend(self._motion_findings(plan, findings))
        findings.extend(self._continuity_findings(plan, findings))
        score = self._score(findings)
        renumbered = tuple(
            finding.model_copy(update={"id": f"finding_{index:04d}"})
            for index, finding in enumerate(findings, start=1)
        )
        return QualityReport(pass_index=pass_index, score=score, findings=renumbered)

    def _motion_findings(
        self,
        plan: StoryboardPlan,
        existing: list[QualityFinding],
    ) -> list[QualityFinding]:
        findings: list[QualityFinding] = []
        static_run: list[str] = []
        repeated: list[str] = []
        previous: CameraPreset | None = None
        for scene in plan.scenes:
            preset = scene.camera.preset
            if preset == CameraPreset.STATIC:
                static_run.append(scene.id)
            else:
                if len(static_run) >= self.static_run_limit:
                    findings.append(
                        self._finding(
                            [*existing, *findings],
                            FindingCategory.STATIC_RUN,
                            FindingSeverity.WARNING,
                            tuple(static_run),
                            "Too many consecutive static scenes.",
                            {"count": len(static_run)},
                            "vary scene motion",
                        )
                    )
                static_run = []
            if preset == previous:
                repeated.append(scene.id)
            else:
                if len(repeated) + 1 >= self.repeated_motion_limit and previous is not None:
                    start_index = max(0, plan.scenes.index(scene) - len(repeated) - 1)
                    ids = tuple(
                        item.id
                        for item in plan.scenes[
                            start_index : start_index + len(repeated) + 1
                        ]
                    )
                    findings.append(
                        self._finding(
                            [*existing, *findings],
                            FindingCategory.MOTION_REPETITION,
                            FindingSeverity.WARNING,
                            ids,
                            "The same motion preset repeats too often.",
                            {"preset": previous.value, "count": len(ids)},
                            "change motion preset",
                        )
                    )
                repeated = [scene.id]
            previous = preset
        if len(static_run) >= self.static_run_limit:
            findings.append(
                self._finding(
                    [*existing, *findings],
                    FindingCategory.STATIC_RUN,
                    FindingSeverity.WARNING,
                    tuple(static_run),
                    "Too many consecutive static scenes.",
                    {"count": len(static_run)},
                    "vary scene motion",
                )
            )
        return findings

    def _continuity_findings(
        self,
        plan: StoryboardPlan,
        existing: list[QualityFinding],
    ) -> list[QualityFinding]:
        findings: list[QualityFinding] = []
        if len(plan.scope.series) != 1:
            return findings
        expected = plan.scope.series[0].casefold()
        for scene in plan.scenes:
            candidate = next(
                item for item in scene.candidates if item.asset_id == scene.primary_asset
            )
            if not candidate.source_locator.casefold().startswith(expected):
                findings.append(
                    self._finding(
                        [*existing, *findings],
                        FindingCategory.CONTINUITY_SHIFT,
                        FindingSeverity.INFO,
                        (scene.id,),
                        "Selected visual shifts outside the preferred series scope.",
                        {"expected_series": plan.scope.series[0]},
                        "review continuity",
                    )
                )
        return findings

    @staticmethod
    def _finding(
        existing: list[QualityFinding],
        category: FindingCategory,
        severity: FindingSeverity,
        scene_ids: tuple[str, ...],
        message: str,
        evidence: dict[str, str | int | float | bool],
        action: str,
    ) -> QualityFinding:
        return QualityFinding(
            id=f"finding_{len(existing) + 1:04d}",
            category=category,
            severity=severity,
            scene_ids=scene_ids,
            message=message,
            evidence=evidence,
            suggested_action=action,
        )

    @staticmethod
    def _score(findings: list[QualityFinding]) -> float:
        penalties = {
            FindingSeverity.INFO: 0.01,
            FindingSeverity.WARNING: 0.06,
            FindingSeverity.ERROR: 0.16,
            FindingSeverity.BLOCKING: 0.40,
        }
        return max(0.0, 1.0 - sum(penalties[item.severity] for item in findings))
