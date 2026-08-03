"""Bounded durable queue workers with core-owned completion state.

Adds, on top of the basic claim/complete/fail loop: a versioned worker
protocol (items declare the protocol version their payload/result expect;
a worker rejects versions it does not support before ever invoking a
handler), lease/heartbeat with a stale-result guard (a worker whose lease
already expired and was reclaimed by someone else cannot silently finish
the old claim), cooperative cancellation, and single-GPU admission.
"""

from __future__ import annotations

import inspect
import secrets
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .db import Database
from .models import QueueItem, QueueKind, WorkerErrorClass

DEFAULT_PROTOCOL_VERSION = "1"
SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = ("1",)


class WorkerError(RuntimeError):
    """Base class for worker execution failures with an explicit error class.

    A bare (non-:class:`WorkerError`) exception raised by a handler is
    treated as :attr:`WorkerErrorClass.FATAL` -- an unclassified failure is
    not assumed safe to retry.
    """

    error_class: WorkerErrorClass = WorkerErrorClass.FATAL


class WorkerTransientError(WorkerError):
    """Raised by a handler for a failure a retry might plausibly fix."""

    error_class = WorkerErrorClass.TRANSIENT


class WorkerTimeoutError(WorkerError):
    error_class = WorkerErrorClass.TIMEOUT


class WorkerCancelledError(WorkerError):
    error_class = WorkerErrorClass.CANCELLED


class WorkerProtocolError(WorkerError):
    error_class = WorkerErrorClass.PROTOCOL_MISMATCH


class WorkerResourceExhaustedError(WorkerError):
    error_class = WorkerErrorClass.RESOURCE_EXHAUSTED


class WorkResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    item_id: str
    completed: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    error_class: WorkerErrorClass | None = None


class WorkerContext:
    """Given to handlers that accept it, for liveness and cancellation.

    A handler that expects a long-running operation may accept
    ``(item, context)`` instead of just ``(item,)`` to call
    :meth:`heartbeat` periodically and check :attr:`cancel_requested`.
    """

    def __init__(self, database: Database, item_id: str, lease_token: str) -> None:
        self._database = database
        self._item_id = item_id
        self._lease_token = lease_token

    def heartbeat(self, *, lease_seconds: int = 300) -> None:
        self._database.heartbeat_queue_item(
            self._item_id, self._lease_token, lease_seconds=lease_seconds
        )

    @property
    def cancel_requested(self) -> bool:
        return self._database.queue_cancellation_requested(self._item_id)

    def raise_if_cancelled(self) -> None:
        if self.cancel_requested:
            raise WorkerCancelledError("cancellation requested for this queue item")


QueueHandler = Callable[[QueueItem], dict[str, Any] | None]
QueueHandlerWithContext = Callable[[QueueItem, WorkerContext], dict[str, Any] | None]


class QueueWorker:
    """Claim one item at a time; core commits completion or failure.

    Whether a claimed item needs the GPU is a property of the item itself
    (set via ``Database.enqueue(..., requires_gpu=True)``), not of this
    worker; ``gpu_capacity`` only bounds how many such items may be
    running system-wide at once, enforced by ``Database.claim_next``.
    """

    def __init__(
        self,
        database: Database,
        kind: QueueKind,
        handler: QueueHandler | QueueHandlerWithContext,
        *,
        worker_id: str | None = None,
        lease_seconds: int = 300,
        gpu_capacity: int = 1,
        supported_protocol_versions: tuple[str, ...] = SUPPORTED_PROTOCOL_VERSIONS,
    ) -> None:
        parameter_count = len(inspect.signature(handler).parameters)
        if parameter_count not in (1, 2):
            raise TypeError(
                "queue handler must accept (item) or (item, context); "
                f"got {parameter_count} parameters"
            )
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        if gpu_capacity < 0:
            raise ValueError("gpu_capacity must not be negative")
        if not supported_protocol_versions:
            raise ValueError("supported_protocol_versions must not be empty")
        self.database = database
        self.kind = kind
        self.handler = handler
        self._handler_takes_context = parameter_count == 2
        self.worker_id = worker_id or f"worker_{secrets.token_hex(8)}"
        self.lease_seconds = lease_seconds
        self.gpu_capacity = gpu_capacity
        self.supported_protocol_versions = supported_protocol_versions

    def run_once(self) -> WorkResult | None:
        item = self.database.claim_next(
            self.kind,
            worker_id=self.worker_id,
            lease_seconds=self.lease_seconds,
            gpu_capacity=self.gpu_capacity,
        )
        if item is None:
            return None
        assert item.lease_token is not None  # claim_next always sets one

        if item.protocol_version not in self.supported_protocol_versions:
            message = (
                f"unsupported worker protocol version {item.protocol_version!r}; "
                f"this worker supports {self.supported_protocol_versions}"
            )
            self.database.fail_queue_item(
                item.id,
                message,
                error_class=WorkerErrorClass.PROTOCOL_MISMATCH,
                lease_token=item.lease_token,
            )
            return WorkResult(
                item_id=item.id,
                completed=False,
                error=message,
                error_class=WorkerErrorClass.PROTOCOL_MISMATCH,
            )

        try:
            if self._handler_takes_context:
                context = WorkerContext(self.database, item.id, item.lease_token)
                output = self.handler(item, context) or {}  # type: ignore[call-arg]
            else:
                output = self.handler(item) or {}  # type: ignore[call-arg]
        except WorkerError as exc:
            self.database.fail_queue_item(
                item.id, str(exc), error_class=exc.error_class, lease_token=item.lease_token
            )
            return WorkResult(
                item_id=item.id, completed=False, error=str(exc), error_class=exc.error_class
            )
        except Exception as exc:
            self.database.fail_queue_item(
                item.id,
                str(exc),
                error_class=WorkerErrorClass.FATAL,
                lease_token=item.lease_token,
            )
            return WorkResult(
                item_id=item.id,
                completed=False,
                error=str(exc),
                error_class=WorkerErrorClass.FATAL,
            )
        self.database.complete_queue_item(item.id, lease_token=item.lease_token)
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
