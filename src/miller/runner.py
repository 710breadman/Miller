"""Single-process deterministic dependency runner."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore, stage_fingerprint
from .db import Database
from .logging import JsonlProjectLog
from .models import Artifact, Project, StageDefinition, StageRun, StageStatus


class StageExecutionError(RuntimeError):
    """Raised when a stage handler fails."""


class StageCancelled(RuntimeError):
    """Raised cooperatively when cancellation is requested."""


@dataclass(frozen=True)
class StageContext:
    project: Project
    run: StageRun
    config: Mapping[str, Any]
    dependency_artifacts: tuple[Artifact, ...]
    artifact_store: ArtifactStore
    is_cancelled: Callable[[], bool]

    def check_cancelled(self) -> None:
        if self.is_cancelled():
            raise StageCancelled(f"stage cancelled: {self.run.stage_id}")


StageHandler = Callable[[StageContext], Any]


@dataclass(frozen=True)
class RuntimeStage:
    definition: StageDefinition
    handler: StageHandler


class PipelineRunner:
    """Execute a validated DAG one stage at a time."""

    def __init__(
        self,
        database: Database,
        workspace: Path | str,
        stages: Sequence[RuntimeStage],
    ) -> None:
        self.database = database
        self.workspace = Path(workspace)
        self.artifacts = ArtifactStore(self.workspace, database)
        self.stages = {stage.definition.id: stage for stage in stages}
        if len(self.stages) != len(stages):
            raise ValueError("duplicate runtime stage ID")
        self.order = self._topological_order()
        for stage_id in self.order:
            self.database.register_stage(self.stages[stage_id].definition)

    def run(
        self,
        project_id: str,
        *,
        targets: Sequence[str] | None = None,
        configs: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Artifact]:
        project = self.database.get_project(project_id)
        log = JsonlProjectLog(self.workspace, project_id)
        selected = self._selected_order(targets)
        outputs: dict[str, Artifact] = {}
        configs = configs or {}
        for stage_id in selected:
            stage = self.stages[stage_id]
            run = self.database.ensure_stage_run(project_id, stage_id)
            dependencies: list[Artifact] = []
            for dependency_id in stage.definition.dependencies:
                dependency_run = self.database.get_stage_run(project_id, dependency_id)
                if dependency_run.status != StageStatus.COMPLETED:
                    raise StageExecutionError(
                        f"dependency {dependency_id} is not completed for stage {stage_id}"
                    )
                assert dependency_run.output_artifact_id is not None
                dependency = self.database.get_artifact(dependency_run.output_artifact_id)
                self.artifacts.resolve(dependency)
                dependencies.append(dependency)
            config = dict(configs.get(stage_id, {}))
            fingerprint = stage_fingerprint(
                stage_id=stage.definition.id,
                stage_version=stage.definition.version,
                config=config,
                dependency_artifacts=[artifact.content_id for artifact in dependencies],
            )
            self.database.invalidate_if_changed(run.id, fingerprint)
            run = self.database.get_stage_run_by_id(run.id)
            if run.status == StageStatus.COMPLETED and run.input_fingerprint == fingerprint:
                assert run.output_artifact_id is not None
                cached = self.database.get_artifact(run.output_artifact_id)
                self.artifacts.resolve(cached)
                outputs[stage_id] = cached
                log.append(
                    "stage.cache_hit",
                    stage_id=stage_id,
                    stage_run_id=run.id,
                    artifact_id=cached.id,
                )
                continue
            attempt = self.database.begin_attempt(run.id, fingerprint)
            running = self.database.get_stage_run_by_id(run.id)
            def is_cancelled(run_id: str = run.id) -> bool:
                return self.database.cancellation_requested(run_id)

            context = StageContext(
                project=project,
                run=running,
                config=config,
                dependency_artifacts=tuple(dependencies),
                artifact_store=self.artifacts,
                is_cancelled=is_cancelled,
            )
            log.append(
                "stage.started",
                stage_id=stage_id,
                stage_run_id=run.id,
                attempt_id=attempt.id,
                fingerprint=fingerprint,
            )
            try:
                context.check_cancelled()
                value = stage.handler(context)
                context.check_cancelled()
                artifact = self.artifacts.put_json(
                    project_id=project_id,
                    stage_run_id=run.id,
                    value=value,
                    metadata={
                        "stage_id": stage_id,
                        "stage_version": stage.definition.version,
                        "input_fingerprint": fingerprint,
                    },
                )
                self.database.complete_attempt(
                    run.id, attempt.id, attempt.attempt_guard, artifact.id
                )
                outputs[stage_id] = artifact
                log.append(
                    "stage.completed",
                    stage_id=stage_id,
                    stage_run_id=run.id,
                    attempt_id=attempt.id,
                    artifact_id=artifact.id,
                )
            except StageCancelled as exc:
                self.database.cancel_attempt(run.id, attempt.id, attempt.attempt_guard, str(exc))
                log.append(
                    "stage.cancelled",
                    stage_id=stage_id,
                    stage_run_id=run.id,
                    attempt_id=attempt.id,
                    error=str(exc),
                )
                raise
            except Exception as exc:
                self.database.fail_attempt(run.id, attempt.id, attempt.attempt_guard, str(exc))
                log.append(
                    "stage.failed",
                    stage_id=stage_id,
                    stage_run_id=run.id,
                    attempt_id=attempt.id,
                    error=str(exc),
                )
                raise StageExecutionError(f"stage {stage_id} failed: {exc}") from exc
        return outputs

    def request_cancel(self, project_id: str, stage_id: str) -> None:
        run = self.database.get_stage_run(project_id, stage_id)
        self.database.request_cancel(run.id)

    def _selected_order(self, targets: Sequence[str] | None) -> list[str]:
        if targets is None:
            return list(self.order)
        unknown = set(targets) - self.stages.keys()
        if unknown:
            raise KeyError(f"unknown targets: {sorted(unknown)}")
        selected: set[str] = set()

        def include(stage_id: str) -> None:
            if stage_id in selected:
                return
            for dependency in self.stages[stage_id].definition.dependencies:
                include(dependency)
            selected.add(stage_id)

        for target in targets:
            include(target)
        return [stage_id for stage_id in self.order if stage_id in selected]

    def _topological_order(self) -> list[str]:
        for stage in self.stages.values():
            unknown = set(stage.definition.dependencies) - self.stages.keys()
            if unknown:
                raise ValueError(
                    f"stage {stage.definition.id} has unknown dependencies: {sorted(unknown)}"
                )
        order: list[str] = []
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(stage_id: str) -> None:
            if stage_id in permanent:
                return
            if stage_id in temporary:
                raise ValueError(f"stage dependency cycle includes {stage_id}")
            temporary.add(stage_id)
            for dependency in self.stages[stage_id].definition.dependencies:
                visit(dependency)
            temporary.remove(stage_id)
            permanent.add(stage_id)
            order.append(stage_id)

        for stage_id in self.stages:
            visit(stage_id)
        return order
