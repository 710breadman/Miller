from pathlib import Path

from miller.db import Database
from miller.models import QueueKind, QueueStatus
from miller.workers import QueueWorker


def test_worker_is_bounded_and_records_handler_failure(tmp_path: Path) -> None:
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    database.create_project("Worker", tmp_path / "workspace", "project_worker")
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
