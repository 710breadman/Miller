"""Persistent storyboard editing with optimistic revisions."""

from __future__ import annotations

from collections.abc import Callable

from ..db import Database, DocumentConflict
from ..storyboard import StoryboardPlan, StoryboardScene
from .models import (
    ReplaceAssetCommand,
    SaveStoryboardCommand,
    SetFocusCommand,
    SetLockCommand,
    SetMotionCommand,
    SetMusicCommand,
    SetTransitionCommand,
    StoryboardSnapshot,
)

_STORYBOARD_KIND = "storyboard"


class StoryboardEditor:
    """Apply atomic, auditable edits to a persisted storyboard."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self, project_id: str) -> StoryboardSnapshot:
        record = self.database.get_document(project_id, _STORYBOARD_KIND)
        return StoryboardSnapshot(
            revision=record.revision,
            storyboard=StoryboardPlan.model_validate(record.document),
        )

    def save(self, project_id: str, command: SaveStoryboardCommand) -> StoryboardSnapshot:
        record = self.database.put_document(
            project_id,
            _STORYBOARD_KIND,
            command.storyboard.model_dump(mode="json"),
            expected_revision=command.expected_revision,
        )
        self.database.invalidate_stage_tree(
            project_id,
            _STORYBOARD_KIND,
            reason="storyboard document saved",
        )
        return StoryboardSnapshot(revision=record.revision, storyboard=command.storyboard)

    def replace_asset(
        self, project_id: str, command: ReplaceAssetCommand
    ) -> StoryboardSnapshot:
        def update(scene: StoryboardScene) -> StoryboardScene:
            self._require_unlocked(scene)
            candidate_ids = tuple(candidate.asset_id for candidate in scene.candidates)
            if command.asset_id not in candidate_ids:
                raise ValueError(f"asset is not a candidate for {scene.id}: {command.asset_id}")
            alternatives = tuple(
                asset_id for asset_id in candidate_ids if asset_id != command.asset_id
            )
            return scene.model_copy(
                update={
                    "primary_asset": command.asset_id,
                    "alternatives": alternatives,
                    "review_status": "manual",
                }
            )

        return self._edit(project_id, command.expected_revision, command.scene_id, update)

    def set_motion(self, project_id: str, command: SetMotionCommand) -> StoryboardSnapshot:
        def update(scene: StoryboardScene) -> StoryboardScene:
            self._require_unlocked(scene)
            return scene.model_copy(
                update={
                    "camera": scene.camera.model_copy(update={"preset": command.preset}),
                    "review_status": "manual",
                }
            )

        return self._edit(project_id, command.expected_revision, command.scene_id, update)

    def set_focus(self, project_id: str, command: SetFocusCommand) -> StoryboardSnapshot:
        def update(scene: StoryboardScene) -> StoryboardScene:
            self._require_unlocked(scene)
            return scene.model_copy(
                update={
                    "camera": scene.camera.model_copy(update={"focus": command.focus}),
                    "review_status": "manual",
                }
            )

        return self._edit(project_id, command.expected_revision, command.scene_id, update)

    def set_transition(
        self, project_id: str, command: SetTransitionCommand
    ) -> StoryboardSnapshot:
        def update(scene: StoryboardScene) -> StoryboardScene:
            self._require_unlocked(scene)
            return scene.model_copy(
                update={"transition": command.transition, "review_status": "manual"}
            )

        return self._edit(project_id, command.expected_revision, command.scene_id, update)

    def set_lock(self, project_id: str, command: SetLockCommand) -> StoryboardSnapshot:
        def update(scene: StoryboardScene) -> StoryboardScene:
            return scene.model_copy(
                update={"locked": command.locked, "review_status": "manual"}
            )

        return self._edit(project_id, command.expected_revision, command.scene_id, update)

    def set_music(self, project_id: str, command: SetMusicCommand) -> StoryboardSnapshot:
        def update(scene: StoryboardScene) -> StoryboardScene:
            self._require_unlocked(scene)
            return scene.model_copy(
                update={"music_state": command.music_state.strip(), "review_status": "manual"}
            )

        return self._edit(project_id, command.expected_revision, command.scene_id, update)

    def history(self, project_id: str) -> tuple[StoryboardSnapshot, ...]:
        return tuple(
            StoryboardSnapshot(
                revision=record.revision,
                storyboard=StoryboardPlan.model_validate(record.document),
            )
            for record in self.database.list_document_history(project_id, _STORYBOARD_KIND)
        )

    def _edit(
        self,
        project_id: str,
        expected_revision: int,
        scene_id: str,
        update: Callable[[StoryboardScene], StoryboardScene],
    ) -> StoryboardSnapshot:
        current = self.get(project_id)
        if current.revision != expected_revision:
            # Database remains the final authority, but fail early with a clearer message.
            raise DocumentConflict(
                f"stale storyboard revision: expected {expected_revision}, "
                f"current {current.revision}"
            )
        found = False
        scenes: list[StoryboardScene] = []
        for scene in current.storyboard.scenes:
            if scene.id == scene_id:
                found = True
                scenes.append(update(scene))
            else:
                scenes.append(scene)
        if not found:
            raise KeyError(f"unknown storyboard scene: {scene_id}")
        revised = current.storyboard.model_copy(update={"scenes": tuple(scenes)})
        record = self.database.put_document(
            project_id,
            _STORYBOARD_KIND,
            revised.model_dump(mode="json"),
            expected_revision=expected_revision,
        )
        self.database.invalidate_stage_tree(
            project_id,
            _STORYBOARD_KIND,
            reason=f"manual scene edit: {scene_id}",
        )
        return StoryboardSnapshot(revision=record.revision, storyboard=revised)

    @staticmethod
    def _require_unlocked(scene: StoryboardScene) -> None:
        if scene.locked:
            raise ValueError(f"scene is locked: {scene.id}")
