from pathlib import Path

import pytest

from miller.db import Database
from miller.models import QueueKind, QueueStatus, WorkerErrorClass
from miller.workers import (
    QueueWorker,
    WorkerCancelledError,
    WorkerContext,
    WorkerTransientError,
)


def make_database(tmp_path: Path) -> Database:
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Worker", tmp_path / "workspace", "project_worker")
    return database


def test_worker_is_bounded_and_records_handler_failure(tmp_path: Path) -> None:
    database = make_database(tmp_path)
    database.enqueue("project_worker", QueueKind.SCRIPT, {"value": 1})
    database.enqueue("project_worker", QueueKind.SCRIPT, {"value": 2})

    def handler(item):
        if item.payload["value"] == 2:
            raise RuntimeError("seeded failure")
        return {"value": item.payload["value"]}

    results = QueueWorker(database, QueueKind.SCRIPT, handler).run_until_empty(max_items=2)
    assert [result.completed for result in results] == [True, False]
    items = database.list_queue(kind=QueueKind.SCRIPT)
    assert [item.status for item in items] == [QueueStatus.COMPLETED, QueueStatus.FAILED]
    assert items[1].error == "seeded failure"
    assert items[1].error_class == WorkerErrorClass.FATAL


def test_worker_error_subclass_reports_its_own_error_class(tmp_path: Path) -> None:
    database = make_database(tmp_path)
    database.enqueue("project_worker", QueueKind.SCRIPT)

    def handler(item):
        raise WorkerTransientError("network blip")

    result = QueueWorker(database, QueueKind.SCRIPT, handler).run_once()
    assert result is not None
    assert result.completed is False
    assert result.error_class == WorkerErrorClass.TRANSIENT
    stored = database.list_queue(kind=QueueKind.SCRIPT)[0]
    assert stored.error_class == WorkerErrorClass.TRANSIENT


def test_handler_with_context_can_heartbeat_and_check_cancellation(tmp_path: Path) -> None:
    database = make_database(tmp_path)
    item = database.enqueue("project_worker", QueueKind.SCRIPT)

    seen_cancel_requested: list[bool] = []

    def handler(claimed_item, context: WorkerContext):
        context.heartbeat()
        seen_cancel_requested.append(context.cancel_requested)
        return {"ok": True}

    result = QueueWorker(database, QueueKind.SCRIPT, handler).run_once()
    assert result is not None and result.completed is True
    assert seen_cancel_requested == [False]
    completed = database.list_queue(kind=QueueKind.SCRIPT)[0]
    assert completed.id == item.id
    assert completed.status == QueueStatus.COMPLETED


def test_handler_context_raise_if_cancelled_fails_the_item_as_cancelled(
    tmp_path: Path,
) -> None:
    database = make_database(tmp_path)
    database.enqueue("project_worker", QueueKind.SCRIPT)

    def handler(item, context: WorkerContext):
        database.request_cancel_queue_item(item.id)
        context.raise_if_cancelled()
        return {"unreachable": True}

    result = QueueWorker(database, QueueKind.SCRIPT, handler).run_once()
    assert result is not None
    assert result.completed is False
    assert result.error_class == WorkerErrorClass.CANCELLED
    assert isinstance(WorkerCancelledError("x"), Exception)


def test_worker_rejects_unsupported_protocol_version_without_calling_handler(
    tmp_path: Path,
) -> None:
    database = make_database(tmp_path)
    database.enqueue("project_worker", QueueKind.SCRIPT, protocol_version="99")

    calls: list[str] = []

    def handler(item):
        calls.append(item.id)
        return {}

    result = QueueWorker(database, QueueKind.SCRIPT, handler).run_once()
    assert result is not None
    assert result.completed is False
    assert result.error_class == WorkerErrorClass.PROTOCOL_MISMATCH
    assert calls == []
    stored = database.list_queue(kind=QueueKind.SCRIPT)[0]
    assert stored.status == QueueStatus.FAILED
    assert stored.error_class == WorkerErrorClass.PROTOCOL_MISMATCH


def test_worker_gpu_capacity_blocks_a_second_kinds_gpu_claim(tmp_path: Path) -> None:
    database = make_database(tmp_path)
    database.enqueue("project_worker", QueueKind.SCRIPT, requires_gpu=True)
    database.enqueue("project_worker", QueueKind.VIDEO, requires_gpu=True)

    def blocking_handler(item, context: WorkerContext) -> dict[str, bool]:
        # While this (still "running" in the DB) item holds the GPU slot, a
        # worker for a different kind must not be able to claim its GPU item.
        video_worker = QueueWorker(
            database, QueueKind.VIDEO, lambda other: {}, gpu_capacity=1
        )
        assert video_worker.run_once() is None
        return {"held_gpu_slot": True}

    script_worker = QueueWorker(
        database, QueueKind.SCRIPT, blocking_handler, gpu_capacity=1
    )
    result = script_worker.run_once()
    assert result is not None and result.completed is True
    assert result.output == {"held_gpu_slot": True}

    # Now that the GPU-holding item finished, the VIDEO worker can claim.
    video_worker = QueueWorker(database, QueueKind.VIDEO, lambda item: {}, gpu_capacity=1)
    assert video_worker.run_once() is not None


def test_constructor_rejects_handler_with_unsupported_arity(tmp_path: Path) -> None:
    database = make_database(tmp_path)
    with pytest.raises(TypeError):
        QueueWorker(database, QueueKind.SCRIPT, lambda: None)
    with pytest.raises(TypeError):
        QueueWorker(database, QueueKind.SCRIPT, lambda a, b, c: None)
