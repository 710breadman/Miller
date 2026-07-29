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
from pathlib import Path

HERE = Path(__file__).parent
SCHEMA_PATH = HERE / "e5-acceptance-record.schema.json"
EXAMPLE_PATH = HERE / "e5-acceptance-record.example.json"


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    record = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    errors: list[str] = []

    missing = [key for key in schema["required"] if key not in record]
    if missing:
        errors.append(f"missing required fields: {missing}")

    undeclared = [key for key in record if key not in schema["properties"]]
    if undeclared:
        errors.append(f"fields not declared in schema properties: {undeclared}")

    for field, pattern in (
        ("record_id", schema["properties"]["record_id"]["pattern"]),
        ("content_hash", schema["properties"]["content_hash"]["pattern"]),
    ):
        if field in record and not re.match(pattern, record[field]):
            errors.append(f"{field} does not match its schema pattern")

    # The load-bearing check: recompute content_hash from the record's own
    # content (excluding content_hash and record_id, per the schema's
    # description) and confirm it matches the stored value byte-for-byte.
    payload = {k: v for k, v in record.items() if k not in ("content_hash", "record_id")}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    recomputed_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    stored_hash = record.get("content_hash", "")
    if recomputed_hash != stored_hash:
        errors.append(
            f"content_hash mismatch: stored={stored_hash!r} recomputed={recomputed_hash!r}"
        )

    expected_record_id = f"e5_{recomputed_hash}"
    if record.get("record_id") != expected_record_id:
        errors.append(
            f"record_id does not derive from content_hash: "
            f"stored={record.get('record_id')!r} expected={expected_record_id!r}"
        )

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("OK: example record matches its schema and content_hash is reproducible")
    print(f"  record_id={record['record_id']}")
    print(
        f"  overall_score={record['overall_score']} "
        f"threshold_result={record['threshold_result']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
