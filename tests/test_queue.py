from pathlib import Path

from miller.db import Database
from miller.models import QueueKind, QueueStatus


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
    assert db.claim_next(QueueKind.SCRIPT) is not None
