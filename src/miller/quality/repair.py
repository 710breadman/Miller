"""Bounded repair planning and scoped storyboard updates."""

from __future__ import annotations

from collections import Counter

from ..storyboard import CameraPreset, StoryboardPlan
from .models import (
    FindingCategory,
    QualityReport,
    RepairAction,
    RepairActionKind,
    RepairPlan,
)


class RepairPlanner:
    def plan(
        self,
        report: QualityReport,
        storyboard: StoryboardPlan,
        *,
        pass_index: int,
        maximum_passes: int,
    ) -> RepairPlan:
        if pass_index < 1:
            raise ValueError("repair pass index must be at least one")
        if pass_index > maximum_passes:
            return RepairPlan(
                pass_index=pass_index,
                maximum_passes=maximum_passes,
                actions=(),
            )
        scenes = {scene.id: scene for scene in storyboard.scenes}
        usage: Counter[str] = Counter(scene.primary_asset for scene in storyboard.scenes)
        actions: list[RepairAction] = []
        blocked: set[str] = set()
        for finding in report.findings:
            for scene_id in finding.scene_ids:
                scene = scenes.get(scene_id)
                if scene is None:
                    continue
                if scene.locked:
                    blocked.add(scene_id)
                    continue
                if finding.category in {
                    FindingCategory.DUPLICATE_ASSET,
                    FindingCategory.WEAK_MATCH,
                }:
                    replacement = next(
                        (
                            asset_id
                            for asset_id in scene.alternatives
                            if usage[asset_id] == 0
                        ),
                        scene.alternatives[0] if scene.alternatives else None,
                    )
                    if replacement is not None:
                        actions.append(
                            self._action(
                                actions,
                                RepairActionKind.REPLACE_ASSET,
                                scene_id,
                                finding.id,
                                {"asset_id": replacement},
                            )
                        )
                        usage[scene.primary_asset] -= 1
                        usage[replacement] += 1
                elif finding.category in {
                    FindingCategory.STATIC_RUN,
                    FindingCategory.MOTION_REPETITION,
                }:
                    replacement_motion = self._alternate_motion(scene.camera.preset)
                    actions.append(
                        self._action(
                            actions,
                            RepairActionKind.CHANGE_MOTION,
                            scene_id,
                            finding.id,
                            {"motion": replacement_motion.value},
                        )
                    )
        return RepairPlan(
            pass_index=pass_index,
            maximum_passes=maximum_passes,
            actions=tuple(actions),
            blocked_scene_ids=tuple(sorted(blocked)),
        )

    def apply(self, storyboard: StoryboardPlan, plan: RepairPlan) -> StoryboardPlan:
        actions_by_scene: dict[str, list[RepairAction]] = {}
        for action in plan.actions:
            actions_by_scene.setdefault(action.scene_id, []).append(action)
        updated = []
        for scene in storyboard.scenes:
            current = scene
            for action in actions_by_scene.get(scene.id, []):
                if current.locked:
                    continue
                if action.kind == RepairActionKind.REPLACE_ASSET:
                    replacement = str(action.parameters["asset_id"])
                    alternatives = tuple(
                        asset_id
                        for asset_id in (current.primary_asset, *current.alternatives)
                        if asset_id != replacement
                    )
                    current = current.model_copy(
                        update={
                            "primary_asset": replacement,
                            "alternatives": alternatives[:3],
                            "review_status": f"repair-pass-{plan.pass_index}",
                        }
                    )
                elif action.kind == RepairActionKind.CHANGE_MOTION:
                    preset = CameraPreset(str(action.parameters["motion"]))
                    current = current.model_copy(
                        update={
                            "camera": current.camera.model_copy(update={"preset": preset}),
                            "review_status": f"repair-pass-{plan.pass_index}",
                        }
                    )
            updated.append(current)
        return storyboard.model_copy(update={"scenes": tuple(updated)})

    @staticmethod
    def improvement_is_acceptable(
        previous: QualityReport,
        current: QualityReport,
        *,
        minimum_improvement: float = 0.01,
    ) -> bool:
        return current.score >= previous.score + minimum_improvement

    @staticmethod
    def _alternate_motion(current: CameraPreset) -> CameraPreset:
        cycle = (
            CameraPreset.SLOW_PUSH,
            CameraPreset.PAN_RIGHT,
            CameraPreset.SLOW_PULL,
            CameraPreset.PAN_LEFT,
            CameraPreset.STATIC,
        )
        return cycle[(cycle.index(current) + 1) % len(cycle)]

    @staticmethod
    def _action(
        existing: list[RepairAction],
        kind: RepairActionKind,
        scene_id: str,
        finding_id: str,
        parameters: dict[str, str | int | float | bool],
    ) -> RepairAction:
        return RepairAction(
            id=f"repair_{len(existing) + 1:04d}",
            kind=kind,
            scene_id=scene_id,
            reason_finding_id=finding_id,
            parameters=parameters,
        )
