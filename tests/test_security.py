"""SEC-001: archive/path/image fuzzing, localhost boundary, log sanitization,
and worker/subprocess failure-surface tests.

This file exercises Miller's existing safety boundaries with adversarial
inputs; it is meant to document and lock in the threat model as executable
tests, not just describe it in prose.
"""

from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from miller.cli import build_parser
from miller.comics.cbz import inventory_cbz
from miller.comics.common import ComicSourceError
from miller.comics.discovery import inventory_image_folder
from miller.db import Database
from miller.models import QueueKind, StageDefinition
from miller.runner import PipelineRunner, RuntimeStage
from miller.runtime.models import MillerSettings

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "miller"


def image_bytes(size: tuple[int, int] = (16, 16), value: int = 10) -> bytes:
    image = Image.new("RGB", size, (value, value, value))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def make_cbz(tmp_path: Path, name: str, builder) -> Path:
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as bundle:
        builder(bundle)
    return path


# ---------------------------------------------------------------------------
# CBZ archive/path fuzzing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "member_name",
    [
        "../escape.png",
        "pages/../../escape.png",
        "/etc/escape.png",
        "C:/escape.png",
        "C:evil.png",
        r"..\escape.png",
        ".",
        "..",
    ],
)
def test_cbz_rejects_every_unsafe_member_path(tmp_path: Path, member_name: str) -> None:
    archive = make_cbz(
        tmp_path,
        "unsafe.cbz",
        lambda bundle: bundle.writestr(member_name, image_bytes()),
    )
    with pytest.raises(ComicSourceError):
        inventory_cbz(archive)


def test_cbz_rejects_a_literal_backslash_member_name() -> None:
    # zipfile normalizes a backslash to a forward slash both when *writing*
    # an arcname (confirmed: writestr(r"pages\1.png", ...) is stored as
    # "pages/1.png") and, it turns out, again when *reading* a raw-patched
    # archive whose on-disk header bytes contain a literal backslash --
    # zipfile.ZipFile(...).namelist() reports "pages/1.png" even after
    # directly patching the header bytes to contain "pages\\1.png". That
    # means Miller's own "\\" in name check in _normalized_member_name can
    # never actually be reached by any real ZipFile-mediated read; it is
    # defensive dead code in practice, kept in case that platform/version
    # behavior ever changes. This tests the function directly instead of
    # pretending an end-to-end archive can exercise it.
    from miller.comics.cbz import _normalized_member_name

    with pytest.raises(ComicSourceError, match="backslash"):
        _normalized_member_name(r"pages\1.png")


def test_cbz_normalizes_but_does_not_reject_dot_segment_and_double_slash(
    tmp_path: Path,
) -> None:
    # These are not a traversal risk -- PurePosixPath collapses a "." segment
    # and a doubled separator to the same safe path as "pages/1.png" -- but
    # that normalization behavior is worth locking in explicitly.
    for member_name in ("pages/./1.png", "pages//1.png"):
        archive = make_cbz(
            tmp_path,
            f"normalize-{hash(member_name) & 0xffff}.cbz",
            lambda bundle, name=member_name: bundle.writestr(name, image_bytes()),
        )
        inventory = inventory_cbz(archive)
        assert [page.locator for page in inventory.pages] == ["pages/1.png"]


def test_cbz_rejects_duplicate_paths_that_differ_only_by_case(tmp_path: Path) -> None:
    archive = make_cbz(
        tmp_path,
        "dupe.cbz",
        lambda bundle: (
            bundle.writestr("Pages/1.png", image_bytes(value=1)),
            bundle.writestr("pages/1.PNG", image_bytes(value=2)),
        ),
    )
    with pytest.raises(ComicSourceError):
        inventory_cbz(archive)


def _mark_first_entry_encrypted(archive_bytes: bytes) -> bytes:
    """Flip the ZIP general-purpose bit-flag "encrypted" bit (bit 0) in both
    the local file header and the central directory header of the first
    entry, without actually encrypting the payload.

    ``zipfile`` cannot author a real ZipCrypto/AES entry, so this directly
    patches the on-disk format Miller's own inventory_cbz parses (via
    ``ZipInfo.flag_bits``) to exercise the encrypted-entry rejection path
    against real header bytes rather than an in-memory ZipInfo object that
    was never actually written or re-read.
    """

    data = bytearray(archive_bytes)
    local_offset = data.find(b"PK\x03\x04")
    central_offset = data.find(b"PK\x01\x02")
    assert local_offset != -1 and central_offset != -1
    local_flag_offset = local_offset + 6
    central_flag_offset = central_offset + 8
    data[local_flag_offset] |= 0x1
    data[central_flag_offset] |= 0x1
    return bytes(data)


def test_cbz_rejects_encrypted_member(tmp_path: Path) -> None:
    plain = tmp_path / "plain.cbz"
    with zipfile.ZipFile(plain, "w") as bundle:
        bundle.writestr("pages/1.png", image_bytes())

    patched_bytes = _mark_first_entry_encrypted(plain.read_bytes())
    patched = tmp_path / "encrypted.cbz"
    patched.write_bytes(patched_bytes)

    # Confirm the patch actually took effect before asserting on Miller's
    # rejection of it -- otherwise this test could pass for the wrong reason.
    with zipfile.ZipFile(patched) as bundle:
        assert bundle.infolist()[0].flag_bits & 0x1

    with pytest.raises(ComicSourceError, match="encrypted"):
        inventory_cbz(patched)


def test_cbz_rejects_entry_larger_than_max_entry_bytes(tmp_path: Path) -> None:
    archive = make_cbz(
        tmp_path,
        "oversized.cbz",
        lambda bundle: bundle.writestr("pages/1.png", image_bytes()),
    )
    with pytest.raises(ComicSourceError):
        inventory_cbz(archive, max_entry_bytes=4)


def test_cbz_rejects_total_size_over_limit(tmp_path: Path) -> None:
    archive = make_cbz(
        tmp_path,
        "toobig.cbz",
        lambda bundle: (
            bundle.writestr("pages/1.png", image_bytes()),
            bundle.writestr("pages/2.png", image_bytes()),
        ),
    )
    with pytest.raises(ComicSourceError):
        inventory_cbz(archive, max_total_bytes=8)


def test_cbz_rejects_zip_bomb_style_compression_ratio(tmp_path: Path) -> None:
    payload = b"0" * (1024 * 1024)  # highly compressible, unlike a real PNG

    def builder(bundle: zipfile.ZipFile) -> None:
        bundle.writestr(
            zipfile.ZipInfo("pages/1.png"), payload, compress_type=zipfile.ZIP_DEFLATED
        )

    archive = make_cbz(tmp_path, "bomb.cbz", builder)
    with pytest.raises(ComicSourceError):
        inventory_cbz(archive, max_compression_ratio=2.0)


def test_cbz_rejects_too_many_entries(tmp_path: Path) -> None:
    def builder(bundle: zipfile.ZipFile) -> None:
        for index in range(5):
            bundle.writestr(f"pages/{index}.png", image_bytes())

    archive = make_cbz(tmp_path, "many.cbz", builder)
    with pytest.raises(ComicSourceError):
        inventory_cbz(archive, max_entries=3)


def test_cbz_rejects_zero_byte_entry(tmp_path: Path) -> None:
    archive = make_cbz(
        tmp_path, "empty.cbz", lambda bundle: bundle.writestr("pages/1.png", b"")
    )
    with pytest.raises(ComicSourceError):
        inventory_cbz(archive)


def test_cbz_rejects_corrupted_image_bytes_despite_image_extension(tmp_path: Path) -> None:
    archive = make_cbz(
        tmp_path,
        "corrupt.cbz",
        lambda bundle: bundle.writestr("pages/1.png", b"not actually a png" * 4),
    )
    with pytest.raises(ComicSourceError):
        inventory_cbz(archive)


def test_cbz_ignores_non_image_members_without_erroring(tmp_path: Path) -> None:
    archive = make_cbz(
        tmp_path,
        "mixed.cbz",
        lambda bundle: (
            bundle.writestr("pages/1.png", image_bytes()),
            bundle.writestr("readme.txt", b"not an image, should be ignored"),
        ),
    )
    inventory = inventory_cbz(archive)
    assert [page.locator for page in inventory.pages] == ["pages/1.png"]


def test_cbz_rejects_invalid_archive(tmp_path: Path) -> None:
    fake = tmp_path / "fake.cbz"
    fake.write_bytes(b"not a zip file at all")
    with pytest.raises(ComicSourceError):
        inventory_cbz(fake)


def test_image_folder_rejects_symlink_escaping_the_source_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside.png"
    outside.write_bytes(image_bytes())
    root = tmp_path / "source"
    root.mkdir()
    (root / "1.png").write_bytes(image_bytes())
    link = root / "escape.png"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not permitted on this machine/account")
    with pytest.raises(ComicSourceError):
        inventory_image_folder(root)


# ---------------------------------------------------------------------------
# Localhost-only boundary
# ---------------------------------------------------------------------------


def test_cli_web_host_flag_rejects_non_loopback_addresses() -> None:
    parser = build_parser()
    for bad_host in ("0.0.0.0", "192.168.1.1", "example.com", "::"):
        with pytest.raises(SystemExit):
            parser.parse_args(["web", "--host", bad_host])


def test_cli_web_host_flag_accepts_only_loopback_addresses() -> None:
    parser = build_parser()
    for good_host in ("127.0.0.1", "localhost", "::1"):
        args = parser.parse_args(["web", "--host", good_host])
        assert args.host == good_host


def test_cli_web_host_defaults_to_loopback() -> None:
    parser = build_parser()
    args = parser.parse_args(["web"])
    assert args.host == "127.0.0.1"


def test_settings_reject_non_loopback_bind_host() -> None:
    for bad_host in ("0.0.0.0", "192.168.1.1", "example.com"):
        with pytest.raises(ValueError):
            MillerSettings(bind_host=bad_host)


def test_settings_accept_loopback_bind_hosts() -> None:
    for good_host in ("127.0.0.1", "localhost", "::1"):
        assert MillerSettings(bind_host=good_host).bind_host == good_host


def test_editor_never_interpolates_storyboard_values_into_html_handlers() -> None:
    """Untrusted scene data must reach DOM text/value properties, not executable HTML."""

    from miller.web.app import _EDITOR_HTML

    assert 'document.getElementById("scenes").innerHTML' not in _EDITOR_HTML
    assert "onclick=\"command('replace-asset'" not in _EDITOR_HTML
    assert "onchange=\"command('motion'" not in _EDITOR_HTML
    assert "onchange=\"command('transition'" not in _EDITOR_HTML
    assert "onchange=\"command('music'" not in _EDITOR_HTML
    assert 'button.addEventListener("click"' in _EDITOR_HTML
    assert 'music.addEventListener("change"' in _EDITOR_HTML


# ---------------------------------------------------------------------------
# Log / event sanitization: secrets never get written to logs
# ---------------------------------------------------------------------------


def test_project_log_never_contains_the_stage_attempt_guard(tmp_path: Path) -> None:
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    project = database.create_project("Sec", tmp_path / "workspace", "project_sec")

    stage = RuntimeStage(
        definition=StageDefinition(id="stage_a", name="A", version="1"),
        handler=lambda context: {"ok": True},
    )
    runner = PipelineRunner(database, tmp_path / "workspace", [stage])
    runner.run(project.id)

    log_path = tmp_path / "workspace" / "projects" / project.id / "logs" / "events.jsonl"
    contents = log_path.read_text(encoding="utf-8")
    lines = [json.loads(line) for line in contents.splitlines() if line.strip()]
    assert lines  # the run actually logged something

    attempts = database.list_stage_runs(project.id)
    assert attempts

    # No log line may contain a raw attempt_guard-shaped secret value: the
    # runner only ever logs stage/attempt/artifact IDs, never the guard token
    # used to authorize completing an attempt.
    for line in lines:
        for key in line:
            assert key != "attempt_guard"
        assert "attempt_guard" not in json.dumps(line)


def test_queue_events_never_contain_the_lease_token(tmp_path: Path) -> None:
    database = Database(tmp_path / "miller.sqlite3")
    database.initialize()
    project = database.create_project("Sec", tmp_path / "workspace", "project_sec")
    database.enqueue(project.id, QueueKind.SCRIPT)
    claimed = database.claim_next(QueueKind.SCRIPT)
    assert claimed is not None and claimed.lease_token is not None

    events = database.list_events(project.id)
    assert events
    for event in events:
        serialized = json.dumps(event.payload)
        assert claimed.lease_token not in serialized
        assert "lease_token" not in event.payload


# ---------------------------------------------------------------------------
# Subprocess/model failure surfaces
# ---------------------------------------------------------------------------


def test_no_shell_true_anywhere_in_the_core_package() -> None:
    """External tools must receive argument arrays, never a shell string."""

    offenders = []
    for path in SRC_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"shell\s*=\s*True", text) or "os.system(" in text:
            offenders.append(str(path.relative_to(SRC_ROOT)))
    assert offenders == []


def test_alignment_worker_surfaces_missing_binary_clearly(tmp_path: Path) -> None:
    from miller.audio import ExternalAlignmentWorker

    missing = tmp_path / "does-not-exist.exe"
    adapter = ExternalAlignmentWorker((str(missing),))
    with pytest.raises((RuntimeError, OSError)):
        adapter.probe()


def test_alignment_worker_surfaces_malformed_json_clearly(tmp_path: Path) -> None:
    from miller.audio import ExternalAlignmentWorker

    worker = tmp_path / "garbage_worker.py"
    worker.write_text("print('not json')\n", encoding="utf-8")
    adapter = ExternalAlignmentWorker((sys.executable, str(worker)))
    with pytest.raises(RuntimeError, match="invalid JSON"):
        adapter.probe()


def test_embedding_worker_surfaces_the_workers_structured_error_message(
    tmp_path: Path,
) -> None:
    from miller.retrieval.embedding_worker import ExternalEmbeddingWorker

    worker = tmp_path / "failing_embedding_worker.py"
    worker.write_text(
        "import json, sys\n"
        "json.loads(sys.stdin.read())\n"
        "print(json.dumps({'error': 'model checkpoint missing'}))\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    adapter = ExternalEmbeddingWorker((sys.executable, str(worker)))
    with pytest.raises(RuntimeError, match="model checkpoint missing"):
        adapter.probe()


def test_embedding_worker_surfaces_missing_binary_clearly(tmp_path: Path) -> None:
    from miller.retrieval.embedding_worker import ExternalEmbeddingWorker

    missing = tmp_path / "does-not-exist.exe"
    adapter = ExternalEmbeddingWorker((str(missing),))
    with pytest.raises((RuntimeError, OSError)):
        adapter.probe()


def test_capability_probe_handles_missing_or_failing_tool_without_raising() -> None:
    from miller.runtime.probe import probe_command

    result = probe_command("definitely-not-a-real-executable-xyz", ("--version",))
    assert result.available is False
