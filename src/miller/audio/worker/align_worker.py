"""Standalone process-isolated alignment worker (WhisperX / stable-ts).

Reads one JSON request object from stdin, writes one JSON response object to
stdout, matching the protocol consumed by
``miller.audio.whisper_worker.ExternalAlignmentWorker``.

Deliberately has no dependency on the ``miller`` package: it is meant to run
inside its own isolated, pinned environment (see ``requirements.txt`` next to
this file), built and maintained separately from Miller's core environment so
heavy ML dependencies never become mandatory for a basic render (D-005 in
DECISIONS.md). Heavy dependencies (torch, whisperx, stable_whisper) are
imported lazily, only when actually aligning, so ``probe`` always works even
when they are not installed -- reporting that honestly instead of crashing.
"""

from __future__ import annotations

import json
import sys
from typing import Any

_MODEL_CACHE: dict[tuple[str, str, str, str], Any] = {}


class WorkerUnavailable(RuntimeError):
    """Raised for a request this worker cannot currently satisfy."""


def _probe_torch() -> dict[str, Any]:
    try:
        import torch  # type: ignore[import-not-found]
    except ImportError:
        return {"available": False}
    cuda_available = False
    cuda_device_name = None
    try:
        cuda_available = bool(torch.cuda.is_available())
        if cuda_available:
            cuda_device_name = torch.cuda.get_device_name(0)
    except Exception:
        cuda_available = False
    return {
        "available": True,
        "version": getattr(torch, "__version__", "unknown"),
        "cuda_available": cuda_available,
        "cuda_device_name": cuda_device_name,
    }


def _probe_module(module_name: str) -> dict[str, Any]:
    try:
        module = __import__(module_name)
    except ImportError:
        return {"available": False}
    return {"available": True, "version": getattr(module, "__version__", "unknown")}


def handle_probe() -> dict[str, Any]:
    torch_probe = _probe_torch()
    # stable-ts's PyPI distribution name is "stable-ts"; its import name is
    # "stable_whisper".
    whisperx_probe = _probe_module("whisperx")
    stable_ts_probe = _probe_module("stable_whisper")
    cuda_available = bool(torch_probe.get("cuda_available", False))
    recommended_device = "cuda" if cuda_available else "cpu"
    recommended_compute_type = "float16" if cuda_available else "int8"
    return {
        "torch": torch_probe,
        "whisperx": whisperx_probe,
        "stable_ts": stable_ts_probe,
        "cuda_available": cuda_available,
        "recommended_device": recommended_device,
        "recommended_compute_type": recommended_compute_type,
    }


def _align_with_whisperx(
    audio_path: str,
    model_name: str,
    device: str,
    compute_type: str,
    language: str | None,
) -> dict[str, Any]:
    import whisperx  # type: ignore[import-not-found]  # heavy; only reached once confirmed available

    cache_key = ("whisperx", model_name, device, compute_type)
    model = _MODEL_CACHE.get(cache_key)
    if model is None:
        model = whisperx.load_model(model_name, device, compute_type=compute_type)
        _MODEL_CACHE[cache_key] = model
    audio = whisperx.load_audio(audio_path)
    transcription = model.transcribe(audio, language=language)
    align_model, metadata = whisperx.load_align_model(
        language_code=transcription["language"], device=device
    )
    aligned = whisperx.align(transcription["segments"], align_model, metadata, audio, device)

    words: list[dict[str, Any]] = []
    for segment in aligned.get("segments", []):
        for word in segment.get("words", []):
            if "start" not in word or "end" not in word:
                continue
            words.append(
                {
                    "text": str(word.get("word", "")).strip(),
                    "start": float(word["start"]),
                    "end": float(word["end"]),
                    "confidence": word.get("score"),
                }
            )
    duration = words[-1]["end"] if words else 0.0
    return {
        "engine": "whisperx",
        "engine_version": _probe_module("whisperx")["version"],
        "model": model_name,
        "language": transcription.get("language", language or "unknown"),
        "audio_duration_seconds": duration,
        "words": words,
        "warnings": [],
    }


def _align_with_stable_ts(
    audio_path: str, model_name: str, device: str, language: str | None
) -> dict[str, Any]:
    import stable_whisper  # type: ignore[import-not-found]  # heavy; only reached once confirmed available

    cache_key = ("stable-ts", model_name, device, "")
    model = _MODEL_CACHE.get(cache_key)
    if model is None:
        model = stable_whisper.load_model(model_name, device=device)
        _MODEL_CACHE[cache_key] = model
    result = model.transcribe(audio_path, language=language)

    words: list[dict[str, Any]] = []
    for segment in result.segments:
        for word in segment.words:
            words.append(
                {
                    "text": str(word.word).strip(),
                    "start": float(word.start),
                    "end": float(word.end),
                    "confidence": getattr(word, "probability", None),
                }
            )
    duration = words[-1]["end"] if words else 0.0
    return {
        "engine": "stable-ts",
        "engine_version": _probe_module("stable_whisper")["version"],
        "model": model_name,
        "language": language or "unknown",
        "audio_duration_seconds": duration,
        "words": words,
        "warnings": [],
    }


def handle_align(request: dict[str, Any]) -> dict[str, Any]:
    engine = request.get("engine", "whisperx")
    audio_path = request["audio_path"]
    model_name = request.get("model", "small")
    device = request.get("device", "cpu")
    compute_type = request.get("compute_type", "int8")
    language = request.get("language")

    probe = handle_probe()
    if engine == "whisperx":
        if not probe["whisperx"]["available"]:
            raise WorkerUnavailable(
                "whisperx is not installed in this worker environment; "
                "see src/miller/audio/worker/requirements.txt"
            )
        return _align_with_whisperx(audio_path, model_name, device, compute_type, language)
    if engine == "stable-ts":
        if not probe["stable_ts"]["available"]:
            raise WorkerUnavailable(
                "stable-ts is not installed in this worker environment; "
                "see src/miller/audio/worker/requirements.txt"
            )
        return _align_with_stable_ts(audio_path, model_name, device, language)
    raise WorkerUnavailable(f"unsupported alignment engine: {engine!r}")


def handle_unload() -> dict[str, Any]:
    released = len(_MODEL_CACHE)
    _MODEL_CACHE.clear()
    cuda_cache_cleared = False
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            cuda_cache_cleared = True
    except ImportError:
        pass
    return {"unloaded": True, "models_released": released, "cuda_cache_cleared": cuda_cache_cleared}


def main() -> None:
    request = json.loads(sys.stdin.read())
    operation = request.get("operation")
    try:
        if operation == "probe":
            response: dict[str, Any] = handle_probe()
        elif operation == "align":
            response = handle_align(request)
        elif operation == "unload":
            response = handle_unload()
        else:
            raise WorkerUnavailable(f"unsupported operation: {operation!r}")
    except WorkerUnavailable as exc:
        print(json.dumps({"error": str(exc), "error_type": "unavailable"}))
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - defensive last resort
        print(json.dumps({"error": str(exc), "error_type": "internal"}))
        sys.exit(1)
    print(json.dumps(response))


if __name__ == "__main__":
    main()
