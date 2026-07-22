"""Stage-state transition invariants."""

from __future__ import annotations

from .models import StageStatus


class InvalidTransition(ValueError):
    """Raised when a stage transition violates the state machine."""


_ALLOWED: dict[StageStatus, frozenset[StageStatus]] = {
    StageStatus.PENDING: frozenset({StageStatus.RUNNING, StageStatus.CANCELLED}),
    StageStatus.RUNNING: frozenset(
        {StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.CANCELLED}
    ),
    StageStatus.COMPLETED: frozenset({StageStatus.PENDING}),
    StageStatus.FAILED: frozenset({StageStatus.RUNNING, StageStatus.CANCELLED}),
    StageStatus.CANCELLED: frozenset({StageStatus.RUNNING}),
}


def validate_transition(current: StageStatus, target: StageStatus) -> None:
    """Validate a state transition or raise ``InvalidTransition``."""

    if target not in _ALLOWED[current]:
        raise InvalidTransition(f"illegal stage transition: {current.value} -> {target.value}")
