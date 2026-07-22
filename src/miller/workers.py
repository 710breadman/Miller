"""Bounded durable queue workers with core-owned completion state."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .db import Database
from .models import QueueItem, QueueKind


class WorkResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    item_id: str
    completed: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


QueueHandler = Callable[[QueueItem], dict[str, Any] | None]


class QueueWorker:
    """Claim one item at a time; core commits completion or failure."""

    def __init__(self, database: Database, kind: QueueKind, handler: QueueHandler) -> None:
        self.database = database
        self.kind = kind
        self.handler = handler

    def run_once(self) -> WorkResult | None:
        item = self.database.claim_next(self.kind)
        if item is None:
            return None
        try:
            output = self.handler(item) or {}
        except Exception as exc:
            self.database.fail_queue_item(item.id, str(exc))
            return WorkResult(item_id=item.id, completed=False, error=str(exc))
        self.database.complete_queue_item(item.id)
        return WorkResult(item_id=item.id, completed=True, output=output)

    def run_until_empty(self, *, max_items: int = 100) -> tuple[WorkResult, ...]:
        if max_items < 1:
            raise ValueError("max_items must be positive")
        results: list[WorkResult] = []
        for _ in range(max_items):
            result = self.run_once()
            if result is None:
                break
            results.append(result)
        return tuple(results)
