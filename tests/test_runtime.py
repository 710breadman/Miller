import os
from pathlib import Path

from miller.runtime import (
    CacheManager,
    GpuInfo,
    HardwareTier,
    MillerSettings,
    load_settings,
    save_settings,
    select_hardware_profile,
)


def test_hardware_profile_selection() -> None:
    assert select_hardware_profile(()).tier == HardwareTier.CPU
    low = select_hardware_profile((GpuInfo(name="GPU", memory_mb=4096),))
    assert low.tier == HardwareTier.LOW_MEMORY_GPU
    target = select_hardware_profile((GpuInfo(name="RTX 3070", memory_mb=8192),))
    assert target.tier == HardwareTier.RTX_3070
    assert target.max_gpu_workers == 1


def test_settings_toml_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    settings = MillerSettings(
        workspace="D:/Miller/workspace",
        database="D:/Miller/miller.sqlite3",
        comic_roots=("D:/Comics", "E:/Manga"),
        repair_passes=3,
    )
    save_settings(path, settings)
    assert load_settings(path) == settings
    assert "[miller]" in path.read_text(encoding="utf-8")


def test_cache_prune_is_dry_run_by_default_and_stays_managed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    cache = workspace / "cache" / "artifacts"
    cache.mkdir(parents=True)
    old = cache / "old.bin"
    new = cache / "new.bin"
    old.write_bytes(b"a" * 10)
    new.write_bytes(b"b" * 20)
    os.utime(old, (100, 100))
    os.utime(new, (200, 200))

    manager = CacheManager(workspace)
    plan = manager.prune(20)
    assert plan.dry_run
    assert plan.reclaim_bytes == 10
    assert old.exists() and new.exists()

    applied = manager.prune(20, dry_run=False)
    assert not applied.dry_run
    assert sum(entry.size_bytes for entry in manager.entries()) <= 20
    assert new.exists()
