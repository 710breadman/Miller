import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(root: Path, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    result = subprocess.run(
        [sys.executable, "-m", "miller", *args],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == expected, result.stderr
    return result


def test_fail_restart_resume_subprocess(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    db = tmp_path / "miller.sqlite3"
    workspace = tmp_path / "workspace"
    common = ("--db", str(db))

    created = run_cli(
        root,
        *common,
        "project-create",
        "--name",
        "Acceptance",
        "--workspace",
        str(workspace),
        "--id",
        "project_acceptance",
    )
    assert json.loads(created.stdout)["id"] == "project_acceptance"

    run_cli(
        root,
        *common,
        "demo-run",
        "--project-id",
        "project_acceptance",
        "--workspace",
        str(workspace),
        "--fail-stage",
        "transform",
        expected=2,
    )

    completed = run_cli(
        root,
        *common,
        "demo-run",
        "--project-id",
        "project_acceptance",
        "--workspace",
        str(workspace),
    )
    output = json.loads(completed.stdout)
    final_content_id = output["finalize"]["content_id"]

    cached = run_cli(
        root,
        *common,
        "demo-run",
        "--project-id",
        "project_acceptance",
        "--workspace",
        str(workspace),
    )
    assert json.loads(cached.stdout)["finalize"]["content_id"] == final_content_id
