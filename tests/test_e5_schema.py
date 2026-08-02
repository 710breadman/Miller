from __future__ import annotations

import copy
import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import Any

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "docs" / "schemas"
MODULE = runpy.run_path(str(SCHEMA_DIR / "verify_e5_example.py"))
VALIDATE: Callable[[dict[str, Any], dict[str, Any]], list[str]] = MODULE["validate_record"]


def load_example() -> tuple[dict[str, Any], dict[str, Any]]:
    schema = json.loads((SCHEMA_DIR / "e5-acceptance-record.schema.json").read_text())
    record = json.loads((SCHEMA_DIR / "e5-acceptance-record.example.json").read_text())
    return schema, record


def test_e5_example_satisfies_schema_and_business_rules() -> None:
    schema, record = load_example()
    assert VALIDATE(schema, record) == []


def test_e5_record_requires_exactly_one_primary_reviewer() -> None:
    schema, record = load_example()
    invalid = copy.deepcopy(record)
    invalid["reviewers"][0]["role"] = "secondary_reviewer"
    assert any("exactly one primary_reviewer" in error for error in VALIDATE(schema, invalid))


def test_e5_record_rejects_out_of_range_scores() -> None:
    schema, record = load_example()
    invalid = copy.deepcopy(record)
    invalid["scores"]["av_sync"] = 6
    assert any("integer from 1 through 5" in error for error in VALIDATE(schema, invalid))


def test_e5_record_recomputes_overall_score_and_threshold() -> None:
    schema, record = load_example()
    invalid = copy.deepcopy(record)
    invalid["overall_score"] = 4.9
    invalid["threshold_result"] = "rejected"
    errors = VALIDATE(schema, invalid)
    assert any("overall_score mismatch" in error for error in errors)
    assert any("threshold_result mismatch" in error for error in errors)
