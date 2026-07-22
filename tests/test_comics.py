import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from miller.artifacts import sha256_file
from miller.comics import ComicIngestor, reconcile_inventories
from miller.comics.cbz import inventory_cbz
from miller.comics.common import ComicSourceError
from miller.comics.discovery import inventory_image_folder


def image_bytes(size: tuple[int, int], value: int) -> bytes:
    image = Image.new("RGB", size, (value, value, value))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def write_fixture_folder(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "10.png").write_bytes(image_bytes((120, 180), 10))
    (root / "2.png").write_bytes(image_bytes((100, 160), 20))
    (root / "1.png").write_bytes(image_bytes((80, 140), 30))


def test_image_folder_natural_order_and_stable_content_identity(tmp_path: Path) -> None:
    first_root = tmp_path / "first-name"
    write_fixture_folder(first_root)
    first = inventory_image_folder(first_root)
    assert [page.filename for page in first.pages] == ["1.png", "2.png", "10.png"]

    renamed = tmp_path / "renamed"
    first_root.rename(renamed)
    second = inventory_image_folder(renamed)
    assert first.issue_id == second.issue_id
    assert [page.id for page in first.pages] == [page.id for page in second.pages]


def test_cbz_inventory_and_zip_slip_rejection(tmp_path: Path) -> None:
    valid = tmp_path / "valid.cbz"
    with zipfile.ZipFile(valid, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("pages/2.png", image_bytes((100, 100), 20))
        bundle.writestr("pages/1.png", image_bytes((100, 100), 10))
    inventory = inventory_cbz(valid)
    assert [page.locator for page in inventory.pages] == ["pages/1.png", "pages/2.png"]

    unsafe = tmp_path / "unsafe.cbz"
    with zipfile.ZipFile(unsafe, "w") as bundle:
        bundle.writestr("../escape.png", image_bytes((10, 10), 1))
    with pytest.raises(ComicSourceError):
        inventory_cbz(unsafe)


def test_cache_and_thumbnail_do_not_modify_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_fixture_folder(source)
    before = {path.name: sha256_file(path) for path in source.iterdir()}

    workspace = tmp_path / "workspace"
    ingestor = ComicIngestor(workspace)
    inventory = ingestor.inventory(source)
    cached = ingestor.cache_inventory(inventory)
    second = ingestor.cache_inventory(inventory)

    assert cached == second
    assert all(page.width <= 512 and page.height <= 512 for _, page in cached)
    assert {path.name: sha256_file(path) for path in source.iterdir()} == before


def test_incremental_reconciliation_marks_only_changed_page(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_fixture_folder(source)
    previous = inventory_image_folder(source)

    (source / "2.png").write_bytes(image_bytes((100, 160), 99))
    current = inventory_image_folder(source)
    result = reconcile_inventories(previous, current)

    assert result.changed == ("2.png",)
    assert result.unchanged == ("1.png", "10.png")
    assert result.added == ()
    assert result.removed == ()
