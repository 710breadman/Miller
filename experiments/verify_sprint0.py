"""Verify Sprint 0 audit artifacts without third-party dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REQUIRED_DOCS = (
    "TOOL_AUDIT.md",
    "REUSE_MATRIX.md",
    "LICENSE_MATRIX.md",
    "CAPABILITY_MATRIX.md",
    "ARCHITECTURE_CANDIDATES.md",
)
REQUIRED_REPOSITORIES = {
    "MoneyPrinterTurbo",
    "BallonsTranslator",
    "StoryToolkitAI",
    "Revideo",
    "WhisperX",
    "OpenTimelineIO",
    "OpenCLIP",
    "SigLIP 2 reference",
    "Qdrant Python client",
    "SAM 2",
    "Depth Anything V2",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_DECISIONS = {"Call", "Adapt", "Port", "Recreate", "Study", "Reject"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    for filename in REQUIRED_DOCS:
        path = DOCS / filename
        require(path.is_file(), f"missing {path.relative_to(ROOT)}")
        require(path.stat().st_size > 200, f"empty/undersized {path.relative_to(ROOT)}")

    lock = json.loads((DOCS / "upstream-lock.json").read_text(encoding="utf-8"))
    repositories = lock["repositories"]
    names = {item["name"] for item in repositories}
    require(names == REQUIRED_REPOSITORIES, "upstream repository set differs")
    require(len(names) == len(repositories), "duplicate upstream repository")
    for item in repositories:
        require(
            SHA_PATTERN.fullmatch(item["revision"]) is not None,
            f"invalid revision for {item['name']}",
        )
        require(
            item["repository"].startswith("https://github.com/"),
            f"unexpected repository URL for {item['name']}",
        )
        require(bool(item["license"]), f"missing license for {item['name']}")

    reuse_text = (DOCS / "REUSE_MATRIX.md").read_text(encoding="utf-8")
    for decision in ALLOWED_DECISIONS:
        require(decision in reuse_text, f"decision vocabulary missing: {decision}")

    sprint_state = json.loads((ROOT / "SPRINT_STATE.json").read_text(encoding="utf-8"))
    sprint_zero = next(item for item in sprint_state["sprints"] if item["id"] == 0)
    require(sprint_zero["status"] == "completed", "Sprint 0 is not completed")
    require(sprint_state["current_sprint"] == 1, "next sprint is not Sprint 1")

    print(f"Sprint 0 verified: {len(REQUIRED_DOCS)} docs, {len(repositories)} pins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
