"""Runtime capability, hardware, settings, and cache records."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RuntimeModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Capability(RuntimeModel):
    name: str = Field(min_length=1)
    available: bool
    path: str | None = None
    version: str | None = None
    detail: str | None = None


class GpuInfo(RuntimeModel):
    name: str = Field(min_length=1)
    memory_mb: int = Field(ge=0)


class HardwareTier(StrEnum):
    RTX_3070 = "rtx_3070"
    LOW_MEMORY_GPU = "low_memory_gpu"
    CPU = "cpu"


class HardwareProfile(RuntimeModel):
    tier: HardwareTier
    device: str
    max_gpu_workers: int = Field(ge=0, le=1)
    embedding_batch_size: int = Field(ge=1)
    whisper_compute_type: str
    unload_models_between_stages: bool = True


class CapabilityReport(RuntimeModel):
    capabilities: tuple[Capability, ...]
    gpus: tuple[GpuInfo, ...] = ()
    profile: HardwareProfile


class CacheEntry(RuntimeModel):
    relative_path: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    modified_ns: int = Field(ge=0)


class CachePlan(RuntimeModel):
    total_bytes: int = Field(ge=0)
    target_bytes: int = Field(ge=0)
    reclaim_bytes: int = Field(ge=0)
    entries: tuple[CacheEntry, ...]
    dry_run: bool


class MillerSettings(RuntimeModel):
    workspace: str = ".miller/workspace"
    database: str = ".miller/miller.sqlite3"
    comic_roots: tuple[str, ...] = ()
    ollama_url: str = "http://127.0.0.1:11434"
    qdrant_url: str = "http://127.0.0.1:6333"
    bind_host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1, le=65535)
    repair_passes: int = 2
    hardware_profile: str = "auto"

    @field_validator("bind_host")
    @classmethod
    def local_bind_only(cls, value: str) -> str:
        if value not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Miller web service must bind to a loopback address")
        return value

    @field_validator("repair_passes")
    @classmethod
    def supported_repair_passes(cls, value: int) -> int:
        if value not in {0, 1, 2, 3, 5}:
            raise ValueError("repair_passes must be one of 0, 1, 2, 3, or 5")
        return value
