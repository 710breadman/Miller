"""Read-only local capability and hardware probing."""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from .models import (
    Capability,
    CapabilityReport,
    GpuInfo,
    HardwareProfile,
    HardwareTier,
)


def probe_command(name: str, version_args: tuple[str, ...]) -> Capability:
    path = shutil.which(name)
    if path is None:
        return Capability(name=name, available=False)
    try:
        result = subprocess.run(
            [path, *version_args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Capability(name=name, available=False, path=path, detail=str(exc))
    output = (result.stdout or result.stderr).splitlines()
    return Capability(
        name=name,
        available=result.returncode == 0,
        path=str(Path(path)),
        version=output[0].strip() if output else None,
        detail=None if result.returncode == 0 else f"exit={result.returncode}",
    )


def probe_ollama(url: str = "http://127.0.0.1:11434") -> Capability:
    endpoint = url.rstrip("/") + "/api/version"
    try:
        with urllib.request.urlopen(endpoint, timeout=2) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return Capability(
            name="ollama_api",
            available=False,
            path=endpoint,
            detail=str(exc),
        )
    return Capability(
        name="ollama_api",
        available=True,
        path=endpoint,
        version=str(payload.get("version", "unknown")),
    )


def probe_qdrant(url: str = "http://127.0.0.1:6333") -> Capability:
    endpoint = url.rstrip("/") + "/healthz"
    try:
        with urllib.request.urlopen(endpoint, timeout=2) as response:
            body = response.read(512).decode("utf-8", errors="replace").strip()
    except (OSError, urllib.error.URLError) as exc:
        return Capability(
            name="qdrant_api",
            available=False,
            path=endpoint,
            detail=str(exc),
        )
    return Capability(
        name="qdrant_api",
        available=True,
        path=endpoint,
        version=body or "available",
    )


def probe_gpus() -> tuple[GpuInfo, ...]:
    path = shutil.which("nvidia-smi")
    if path is None:
        return ()
    try:
        result = subprocess.run(
            [
                path,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ()
    if result.returncode != 0:
        return ()
    gpus: list[GpuInfo] = []
    for line in result.stdout.splitlines():
        name, separator, memory = line.rpartition(",")
        if not separator:
            continue
        try:
            gpus.append(GpuInfo(name=name.strip(), memory_mb=int(memory.strip())))
        except ValueError:
            continue
    return tuple(gpus)


def select_hardware_profile(gpus: tuple[GpuInfo, ...]) -> HardwareProfile:
    maximum = max((gpu.memory_mb for gpu in gpus), default=0)
    if maximum >= 7_500:
        return HardwareProfile(
            tier=HardwareTier.RTX_3070,
            device="cuda",
            max_gpu_workers=1,
            embedding_batch_size=16,
            whisper_compute_type="float16",
        )
    if maximum >= 3_500:
        return HardwareProfile(
            tier=HardwareTier.LOW_MEMORY_GPU,
            device="cuda",
            max_gpu_workers=1,
            embedding_batch_size=4,
            whisper_compute_type="int8_float16",
        )
    return HardwareProfile(
        tier=HardwareTier.CPU,
        device="cpu",
        max_gpu_workers=0,
        embedding_batch_size=1,
        whisper_compute_type="int8",
    )


def probe_runtime(
    ollama_url: str = "http://127.0.0.1:11434",
    qdrant_url: str = "http://127.0.0.1:6333",
) -> CapabilityReport:
    capabilities = (
        probe_command("python", ("--version",)),
        probe_command("ffmpeg", ("-version",)),
        probe_command("ffprobe", ("-version",)),
        probe_command("tesseract", ("--version",)),
        probe_command("node", ("--version",)),
        probe_command("ollama", ("--version",)),
        probe_ollama(ollama_url),
        probe_qdrant(qdrant_url),
    )
    gpus = probe_gpus()
    return CapabilityReport(
        capabilities=capabilities,
        gpus=gpus,
        profile=select_hardware_profile(gpus),
    )
