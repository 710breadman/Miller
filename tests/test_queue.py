from datetime import timedelta
from pathlib import Path

import pytest

from miller.db import Database
from miller.models import QueueKind, QueueStatus, WorkerErrorClass
from miller.transitions import InvalidTransition


def database(tmp_path: Path) -> Database:
    result = Database(tmp_path / "miller.sqlite3")
    result.initialize()
    result.create_project("A", tmp_path / "a", "project_a")
    result.create_project("B", tmp_path / "b", "project_b")
    return result


def test_queue_claims_in_priority_order_and_serializes_by_kind(tmp_path: Path) -> None:
    db = database(tmp_path)
    later = db.enqueue("project_a", QueueKind.VIDEO, {"name": "later"}, priority=20)
    earlier = db.enqueue("project_b", QueueKind.VIDEO, {"name": "earlier"}, priority=10)

    claimed = db.claim_next(QueueKind.VIDEO)
    assert claimed is not None and claimed.id == earlier.id
    assert claimed.status == QueueStatus.RUNNING
    assert db.claim_next(QueueKind.VIDEO) is None

    completed = db.complete_queue_item(claimed.id)
    assert completed.status == QueueStatus.COMPLETED
    next_item = db.claim_next(QueueKind.VIDEO)
    assert next_item is not None and next_item.id == later.id


def test_script_and_video_queues_can_progress_independently(tmp_path: Path) -> None:
    db = database(tmp_path)
    script = db.enqueue("project_a", QueueKind.SCRIPT)
    video = db.enqueue("project_b", QueueKind.VIDEO)
    assert db.claim_next(QueueKind.SCRIPT).id == script.id  # type: ignore[union-attr]
    assert db.claim_next(QueueKind.VIDEO).id == video.id  # type: ignore[union-attr]


def test_running_items_requeue_after_restart(tmp_path: Path) -> None:
    db = database(tmp_path)
    item = db.enqueue("project_a", QueueKind.SCRIPT)
    claimed = db.claim_next(QueueKind.SCRIPT)
    assert claimed is not None and claimed.id == item.id
    assert db.recover_queue() == 1
    recovered = db.list_queue(kind=QueueKind.SCRIPT)[0]
    assert recovered.status == QueueStatus.PENDING
    assert recovered.started_at is None
    assert recovered.lease_token is None
    assert db.claim_next(QueueKind.SCRIPT) is not None


def test_claim_next_sets_a_lease_and_worker_id(tmp_path: Path) -> None:
    db = database(tmp_path)
    db.enqueue("project_a", QueueKind.SCRIPT)
    claimed = db.claim_next(QueueKind.SCRIPT, worker_id="worker_1", lease_seconds=60)
    assert claimed is not None
    assert claimed.claimed_by == "worker_1"
    assert claimed.lease_token is not None
    assert claimed.lease_expires_at is not None
    assert claimed.heartbeat_at is not None


def test_gpu_admission_blocks_a_second_concurrent_gpu_item_across_kinds(
    tmp_path: Path,
) -> None:
    db = database(tmp_path)
    db.enqueue("project_a", QueueKind.SCRIPT, requires_gpu=True)
    db.enqueue("project_b", QueueKind.VIDEO, requires_gpu=True)

    first = db.claim_next(QueueKind.SCRIPT, gpu_capacity=1)
    assert first is not None and first.requires_gpu is True

    # Capacity is exhausted system-wide, even though VIDEO is a different kind.
    assert db.claim_next(QueueKind.VIDEO, gpu_capacity=1) is None

    db.complete_queue_item(first.id, lease_token=first.lease_token)
    second = db.claim_next(QueueKind.VIDEO, gpu_capacity=1)
    assert second is not None and second.requires_gpu is True


def test_non_gpu_item_is_unaffected_by_gpu_admission(tmp_path: Path) -> None:
    db = database(tmp_path)
    db.enqueue("project_a", QueueKind.SCRIPT, requires_gpu=True)
    db.enqueue("project_b", QueueKind.VIDEO, requires_gpu=False)
    db.claim_next(QueueKind.SCRIPT, gpu_capacity=1)
    assert db.claim_next(QueueKind.VIDEO, gpu_capacity=1) is not None


def test_lease_token_guards_stale_completion(tmp_path: Path) -> None:
    db = database(tmp_path)
    db.enqueue("project_a", QueueKind.SCRIPT)
    claimed = db.claim_next(QueueKind.SCRIPT)
    assert claimed is not None and claimed.lease_token is not None

    with pytest.raises(PermissionError):
        db.complete_queue_item(claimed.id, lease_token="wrong-token")

    still_running = db.list_queue(kind=QueueKind.SCRIPT)[0]
    assert still_running.status == QueueStatus.RUNNING

    completed = db.complete_queue_item(claimed.id, lease_token=claimed.lease_token)
    assert completed.status == QueueStatus.COMPLETED
    assert completed.lease_token is None


def test_complete_without_lease_token_stays_backward_compatible(tmp_path: Path) -> None:
    db = database(tmp_path)
    db.enqueue("project_a", QueueKind.SCRIPT)
    claimed = db.claim_next(QueueKind.SCRIPT)
    assert claimed is not None
    completed = db.complete_queue_item(claimed.id)
    assert completed.status == QueueStatus.COMPLETED


def test_heartbeat_renews_lease_and_rejects_wrong_token(tmp_path: Path) -> None:
    db = database(tmp_path)
    db.enqueue("project_a", QueueKind.SCRIPT)
    claimed = db.claim_next(QueueKind.SCRIPT, lease_seconds=60)
    assert claimed is not None and claimed.lease_token is not None

    with pytest.raises(PermissionError):
        db.heartbeat_queue_item(claimed.id, "wrong-token")

    db.heartbeat_queue_item(claimed.id, claimed.lease_token, lease_seconds=600)
    renewed = db.list_queue(kind=QueueKind.SCRIPT)[0]
    assert renewed.lease_expires_at is not None
    assert claimed.lease_expires_at is not None
    assert renewed.lease_expires_at > claimed.lease_expires_at


def test_heartbeat_rejects_non_running_item(tmp_path: Path) -> None:
    db = database(tmp_path)
    db.enqueue("project_a", QueueKind.SCRIPT)
    claimed = db.claim_next(QueueKind.SCRIPT)
    assert claimed is not None and claimed.lease_token is not None
    db.complete_queue_item(claimed.id, lease_token=claimed.lease_token)
    with pytest.raises(InvalidTransition):
        db.heartbeat_queue_item(claimed.id, claimed.lease_token)


def test_reclaim_expired_leases_fails_silent_claims_with_timeout(tmp_path: Path) -> None:
    db = database(tmp_path)
    db.enqueue("project_a", QueueKind.SCRIPT)
    claimed = db.claim_next(QueueKind.SCRIPT, lease_seconds=1)
    assert claimed is not None and claimed.lease_expires_at is not None

    future = claimed.lease_expires_at + timedelta(seconds=1)
    assert db.reclaim_expired_leases(now=future) == 1

    reclaimed = db.list_queue(kind=QueueKind.SCRIPT)[0]
    assert reclaimed.status == QueueStatus.FAILED
    assert reclaimed.error_class == WorkerErrorClass.TIMEOUT
    assert reclaimed.lease_token is None

    # The now-failed claim's original lease token cannot resurrect it.
    with pytest.raises(InvalidTransition):
        db.complete_queue_item(claimed.id, lease_token=claimed.lease_token)


def test_reclaim_expired_leases_ignores_leases_still_valid(tmp_path: Path) -> None:
    db = database(tmp_path)
    db.enqueue("project_a", QueueKind.SCRIPT)
    claimed = db.claim_next(QueueKind.SCRIPT, lease_seconds=600)
    assert claimed is not None and claimed.lease_expires_at is not None

    soon = claimed.lease_expires_at - timedelta(seconds=1)
    assert db.reclaim_expired_leases(now=soon) == 0
    still_running = db.list_queue(kind=QueueKind.SCRIPT)[0]
    assert still_running.status == QueueStatus.RUNNING


def test_cancellation_request_is_observable_and_recorded(tmp_path: Path) -> None:
    db = database(tmp_path)
    item = db.enqueue("project_a", QueueKind.SCRIPT)
    assert db.queue_cancellation_requested(item.id) is False
    db.request_cancel_queue_item(item.id)
    assert db.queue_cancellation_requested(item.id) is True

    claimed = db.claim_next(QueueKind.SCRIPT)
    assert claimed is not None and claimed.lease_token is not None
    cancelled = db.cancel_queue_item(claimed.id, lease_token=claimed.lease_token)
    assert cancelled.status == QueueStatus.CANCELLED
    assert cancelled.error_class == WorkerErrorClass.CANCELLED
