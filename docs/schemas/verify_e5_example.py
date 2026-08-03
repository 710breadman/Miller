"""Verify docs/schemas/e5-acceptance-record.example.json against its schema
and confirm content_hash is actually reproducible from the stored record.

This is the concrete, runnable evidence (not just prose) that the E5 record
format described in EVALUATION_PLAN.md is genuinely content-addressed:
record_id and content_hash are both re-derived from the record's own
content and compared against the stored values.

Run: python docs/schemas/verify_e5_example.py
Exits non-zero on any mismatch.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
SCHEMA_PATH = HERE / "e5-acceptance-record.schema.json"
EXAMPLE_PATH = HERE / "e5-acceptance-record.example.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def canonical_hash(record: dict[str, Any]) -> str:
    """Hash record content without its two derived identity fields."""

    payload = {k: v for k, v in record.items() if k not in ("content_hash", "record_id")}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _missing_or_extra(
    errors: list[str],
    value: dict[str, Any],
    *,
    required: set[str],
    allowed: set[str],
    context: str,
) -> None:
    missing = sorted(required - value.keys())
    extra = sorted(value.keys() - allowed)
    if missing:
        errors.append(f"{context} missing required fields: {missing}")
    if extra:
        errors.append(f"{context} has undeclared fields: {extra}")


def _valid_date(value: object) -> bool:
    try:
        date.fromisoformat(str(value))
    except ValueError:
        return False
    return True


def _valid_datetime(value: object) -> bool:
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_record(schema: dict[str, Any], record: dict[str, Any]) -> list[str]:
    """Validate schema shape plus QAE-001's cross-field business rules."""

    errors: list[str] = []
    _missing_or_extra(
        errors,
        record,
        required=set(schema["required"]),
        allowed=set(schema["properties"]),
        context="record",
    )

    if record.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if not re.fullmatch(r"e5_[0-9a-f]{64}", str(record.get("record_id", ""))):
        errors.append("record_id does not match its schema pattern")
    if not _valid_datetime(record.get("created_at")):
        errors.append("created_at must be an ISO 8601 date-time")
    supersedes = record.get("supersedes")
    if supersedes is not None and not re.fullmatch(r"e5_[0-9a-f]{64}", str(supersedes)):
        errors.append("supersedes must be null or an E5 record ID")
    if not isinstance(record.get("roadmap_item"), str) or not record["roadmap_item"]:
        errors.append("roadmap_item must be a non-empty string")

    artifact = record.get("artifact")
    if not isinstance(artifact, dict):
        errors.append("artifact must be an object")
    else:
        _missing_or_extra(
            errors,
            artifact,
            required={"project_id", "render_path", "render_sha256"},
            allowed={"project_id", "render_path", "render_sha256", "source_hashes"},
            context="artifact",
        )
        for field in ("project_id", "render_path"):
            if not isinstance(artifact.get(field), str) or not artifact[field]:
                errors.append(f"artifact.{field} must be a non-empty string")
        if not HEX64.fullmatch(str(artifact.get("render_sha256", ""))):
            errors.append("artifact.render_sha256 must be a lowercase SHA-256")
        source_hashes = artifact.get("source_hashes", {})
        if not isinstance(source_hashes, dict) or any(
            not isinstance(name, str) or not HEX64.fullmatch(str(digest))
            for name, digest in getattr(source_hashes, "items", lambda: ())()
        ):
            errors.append("artifact.source_hashes must map names to lowercase SHA-256 values")

    reviewers = record.get("reviewers")
    if not isinstance(reviewers, list) or not reviewers:
        errors.append("reviewers must be a non-empty array")
    else:
        roles: list[str] = []
        for index, reviewer in enumerate(reviewers):
            context = f"reviewers[{index}]"
            if not isinstance(reviewer, dict):
                errors.append(f"{context} must be an object")
                continue
            _missing_or_extra(
                errors,
                reviewer,
                required={"role", "identifier", "date"},
                allowed={"role", "identifier", "date"},
                context=context,
            )
            role = reviewer.get("role")
            if role not in {"primary_reviewer", "secondary_reviewer"}:
                errors.append(f"{context}.role is invalid")
            else:
                roles.append(role)
            if not isinstance(reviewer.get("identifier"), str) or not reviewer["identifier"]:
                errors.append(f"{context}.identifier must be a non-empty string")
            if not _valid_date(reviewer.get("date")):
                errors.append(f"{context}.date must be an ISO 8601 date")
        if roles.count("primary_reviewer") != 1:
            errors.append("reviewers must contain exactly one primary_reviewer")
        if roles.count("secondary_reviewer") > 1:
            errors.append("reviewers may contain at most one secondary_reviewer")

    scores = record.get("scores")
    valid_scores = isinstance(scores, dict) and bool(scores)
    if not valid_scores:
        errors.append("scores must be a non-empty object")
    elif any(
        not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5
        for score in scores.values()
    ):
        errors.append("every score must be an integer from 1 through 5")
        valid_scores = False

    overall = record.get("overall_score")
    if not isinstance(overall, (int, float)) or isinstance(overall, bool) or not 1 <= overall <= 5:
        errors.append("overall_score must be a number from 1 through 5")
    elif valid_scores:
        expected_overall = sum(scores.values()) / len(scores)
        if abs(float(overall) - expected_overall) > 1e-9:
            errors.append(
                f"overall_score mismatch: stored={overall!r} expected={expected_overall!r}"
            )
        expected_result = (
            "rejected"
            if expected_overall < 3
            else "accepted"
            if expected_overall >= 4 and min(scores.values()) > 1
            else "needs_repair"
        )
        if record.get("threshold_result") != expected_result:
            errors.append(
                "threshold_result mismatch: "
                f"stored={record.get('threshold_result')!r} expected={expected_result!r}"
            )
    if record.get("threshold_result") not in {"accepted", "needs_repair", "rejected"}:
        errors.append("threshold_result is invalid")

    disagreement = record.get("disagreement")
    if not isinstance(disagreement, dict):
        errors.append("disagreement must be an object")
    else:
        allowed_disagreement = {
            "occurred",
            "dimension",
            "primary_score",
            "secondary_score",
            "resolution",
        }
        _missing_or_extra(
            errors,
            disagreement,
            required={"occurred"},
            allowed=allowed_disagreement,
            context="disagreement",
        )
        occurred = disagreement.get("occurred")
        if not isinstance(occurred, bool):
            errors.append("disagreement.occurred must be boolean")
        elif occurred:
            missing_detail = sorted(
                {"dimension", "primary_score", "secondary_score", "resolution"}
                - disagreement.keys()
            )
            if missing_detail:
                errors.append(f"disagreement detail missing fields: {missing_detail}")
        elif set(disagreement) != {"occurred"}:
            errors.append("disagreement detail must be absent when occurred is false")

    flags = record.get("automated_flags")
    if not isinstance(flags, list) or any(not isinstance(flag, str) for flag in flags):
        errors.append("automated_flags must be an array of strings")
    if "comments" in record and not isinstance(record["comments"], str):
        errors.append("comments must be a string")

    stored_hash = record.get("content_hash", "")
    if not HEX64.fullmatch(str(stored_hash)):
        errors.append("content_hash does not match its schema pattern")
    recomputed_hash = canonical_hash(record)
    if recomputed_hash != stored_hash:
        errors.append(
            f"content_hash mismatch: stored={stored_hash!r} recomputed={recomputed_hash!r}"
        )
    expected_record_id = f"e5_{recomputed_hash}"
    if record.get("record_id") != expected_record_id:
        errors.append(
            "record_id does not derive from content_hash: "
            f"stored={record.get('record_id')!r} expected={expected_record_id!r}"
        )
    return errors


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    record = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    errors = validate_record(schema, record)

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("OK: example record matches its schema and content_hash is reproducible")
    print(f"  record_id={record['record_id']}")
    print(
        f"  overall_score={record['overall_score']} threshold_result={record['threshold_result']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
