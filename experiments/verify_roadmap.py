"""Validate roadmap identifiers and active sub-sprint state."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUB_SPRINT_PATTERN = re.compile(r"^### (\d+\.\d+) — .+$", re.MULTILINE)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def id_key(identifier: str) -> tuple[int, int]:
    major, minor = identifier.split(".")
    return int(major), int(minor)


def main() -> int:
    roadmap = (ROOT / "SPRINTS.md").read_text(encoding="utf-8")
    identifiers = SUB_SPRINT_PATTERN.findall(roadmap)
    require(identifiers, "no sub-sprints found")
    require(len(identifiers) == len(set(identifiers)), "duplicate sub-sprint ID")
    require(identifiers == sorted(identifiers, key=id_key), "sub-sprints out of order")

    by_major: dict[int, list[int]] = {}
    for identifier in identifiers:
        major, minor = id_key(identifier)
        by_major.setdefault(major, []).append(minor)
    require(set(by_major) == set(range(14)), "expected parent sprints 0 through 13")
    for major, minors in by_major.items():
        require(
            minors == list(range(1, len(minors) + 1)),
            f"non-contiguous sub-sprints under Sprint {major}",
        )

    state = json.loads((ROOT / "SPRINT_STATE.json").read_text(encoding="utf-8"))
    active = state["active_sub_sprint"]
    completed = state["completed_sub_sprints"]
    blocked = state["blocked_sub_sprints"]
    require(active in identifiers, "active sub-sprint missing from roadmap")
    require(len(completed) == len(set(completed)), "duplicate completed sub-sprint")
    require(all(item in identifiers for item in completed), "unknown completed ID")
    require(all(item in identifiers for item in blocked), "unknown blocked ID")
    require(active not in completed, "active sub-sprint already completed")
    require(active not in blocked, "active sub-sprint also blocked")

    first_incomplete = next(item for item in identifiers if item not in completed)
    require(active == first_incomplete, "active sub-sprint is not first incomplete")
    require(
        state["last_completed_sub_sprint"] == completed[-1],
        "last-completed pointer differs from completed list",
    )

    print(
        f"Roadmap verified: {len(identifiers)} sub-sprints; "
        f"active={active}; completed={len(completed)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
