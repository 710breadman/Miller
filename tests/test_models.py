from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from miller.models import StageRun, StageStatus
from miller.transitions import InvalidTransition, validate_transition


def test_stage_run_rejects_running_without_attempt() -> None:
    with pytest.raises(ValidationError):
        StageRun(
            id="run_a",
            project_id="project_a",
            stage_id="stage_a",
            status=StageStatus.RUNNING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def test_invalid_transition_rejected() -> None:
    with pytest.raises(InvalidTransition):
        validate_transition(StageStatus.PENDING, StageStatus.COMPLETED)
