import json
import math
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

import pytest

import miller.audio.worker as _worker_package
from miller.artifacts import sha256_file
from miller.audio import (
    AlignmentResult,
    AudioTools,
    ExternalAlignmentWorker,
    ScriptDifferenceKind,
    WordTiming,
    build_beat_plan,
    compare_script_to_audio,
    normalize_alignment_words,
)

ALIGN_WORKER_SCRIPT = Path(_worker_package.__file__).parent / "align_worker.py"


def write_tone(path: Path, duration: float = 1.0, rate: int = 22_050) -> None:
    frames = int(duration * rate)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(rate)
        samples: list[bytes] = []
        for index in range(frames):
            value = int(4000 * math.sin(2 * math.pi * 440 * index / rate))
            packed = struct.pack("<h", value)
            samples.append(packed + packed)
        output.writeframes(b"".join(samples))


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="FFmpeg unavailable",
)
def test_audio_inspection_and_non_destructive_normalization(tmp_path: Path) -> None:
    source = tmp_path / "narration.wav"
    output = tmp_path / "working" / "narration-16k.wav"
    write_tone(source)
    source_hash = sha256_file(source)
    tools = AudioTools()
    metadata = tools.inspect(source)
    assert metadata.channels == 2
    assert metadata.sample_rate == 22_050

    normalized = tools.normalize(source, output)
    assert normalized.channels == 1
    assert normalized.sample_rate == 16_000
    assert tools.inspect(output).codec == "pcm_s16le"
    assert sha256_file(source) == source_hash


def test_alignment_normalization_comparison_and_beat_coverage() -> None:
    raw = (
        {"word": "The", "start": 0.1, "end": 0.3, "score": 0.99},
        {"word": "city", "start": 0.3, "end": 0.7, "score": 0.95},
        {"word": "needs", "start": 0.7, "end": 1.0, "score": 0.93},
        {"word": "a", "start": 1.0, "end": 1.1, "score": 0.9},
        {"word": "hero.", "start": 1.1, "end": 1.6, "score": 0.98},
        {"word": "Tonight", "start": 1.8, "end": 2.2, "score": 0.92},
        {"word": "he", "start": 2.2, "end": 2.4, "score": 0.9},
        {"word": "returns.", "start": 2.4, "end": 3.0, "score": 0.97},
    )
    alignment = normalize_alignment_words(
        raw,
        audio_duration_seconds=3.2,
        engine="whisperx",
        engine_version="fixture",
        model="small",
        language="eng",
    )
    comparison = compare_script_to_audio(
        "The city desperately needs a hero.\n\nTonight he returns.", alignment.words
    )
    assert comparison.match_ratio < 1
    assert any(
        difference.kind == ScriptDifferenceKind.OMISSION
        for difference in comparison.differences
    )
    plan = build_beat_plan(
        "The city needs a hero.\n\nTonight he returns.",
        alignment,
        maximum_duration_seconds=1.6,
        maximum_words=5,
    )
    assert plan.beats[0].first_word_index == 0
    assert plan.beats[-1].last_word_index == len(alignment.words) - 1
    for previous, current in zip(plan.beats, plan.beats[1:], strict=False):
        assert current.start == previous.end


def test_alignment_rejects_large_overlap() -> None:
    with pytest.raises(ValueError):
        normalize_alignment_words(
            (
                {"word": "one", "start": 0.0, "end": 1.0},
                {"word": "two", "start": 0.2, "end": 1.2},
            ),
            audio_duration_seconds=2.0,
            engine="fixture",
            engine_version="1",
            model="fixture",
            language="eng",
        )


def test_external_alignment_worker_contract(tmp_path: Path) -> None:
    worker = tmp_path / "alignment_worker.py"
    worker.write_text(
        "import json, sys\n"
        "request = json.loads(sys.stdin.read())\n"
        "if request['operation'] == 'probe':\n"
        "    print(json.dumps({'available': True, 'version': 'fixture'}))\n"
        "elif request['operation'] == 'unload':\n"
        "    print(json.dumps({'unloaded': True}))\n"
        "else:\n"
        "    print(json.dumps({'engine':'whisperx','engine_version':'fixture',"
        "'model':request['model'],'language':'eng','audio_duration_seconds':1.0,"
        "'words':[{'text':'hello','start':0.0,'end':0.5,'confidence':0.9}],"
        "'warnings':[]}))\n",
        encoding="utf-8",
    )
    adapter = ExternalAlignmentWorker((sys.executable, str(worker)))
    assert adapter.probe()["available"] is True
    result = adapter.align(tmp_path / "audio.wav", model="small")
    assert isinstance(result, AlignmentResult)
    assert result.words == (
        WordTiming(text="hello", start=0.0, end=0.5, confidence=0.9),
    )
    assert json.loads(json.dumps(adapter.unload()))["unloaded"] is True


def test_align_worker_script_exists_and_is_isolated_from_the_core_package() -> None:
    assert ALIGN_WORKER_SCRIPT.is_file()
    source = ALIGN_WORKER_SCRIPT.read_text(encoding="utf-8")
    assert "import miller" not in source
    assert "from miller" not in source


def test_align_worker_probe_reports_unavailable_heavy_deps_honestly() -> None:
    # torch/whisperx/stable_whisper are not in Miller's core environment by
    # design (D-005); this is a genuine probe of the current checkout, not a
    # simulated fixture.
    result = subprocess.run(
        [sys.executable, str(ALIGN_WORKER_SCRIPT)],
        input=json.dumps({"operation": "probe"}),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["cuda_available"] is False
    assert payload["recommended_device"] == "cpu"
    assert payload["recommended_compute_type"] == "int8"
    for key in ("torch", "whisperx", "stable_ts"):
        assert "available" in payload[key]


def test_align_worker_align_fails_clearly_when_engine_not_installed(tmp_path: Path) -> None:
    audio_path = tmp_path / "narration.wav"
    audio_path.write_bytes(b"not-real-audio")
    request = {
        "operation": "align",
        "engine": "whisperx",
        "audio_path": str(audio_path),
        "model": "small",
        "device": "cpu",
        "compute_type": "int8",
    }
    result = subprocess.run(
        [sys.executable, str(ALIGN_WORKER_SCRIPT)],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["error_type"] == "unavailable"
    assert "whisperx is not installed" in payload["error"]


def test_align_worker_unload_reports_no_models_when_nothing_was_loaded() -> None:
    result = subprocess.run(
        [sys.executable, str(ALIGN_WORKER_SCRIPT)],
        input=json.dumps({"operation": "unload"}),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == {"unloaded": True, "models_released": 0, "cuda_cache_cleared": False}


def test_adapter_surfaces_the_worker_s_structured_error_message(tmp_path: Path) -> None:
    adapter = ExternalAlignmentWorker((sys.executable, str(ALIGN_WORKER_SCRIPT)))
    with pytest.raises(RuntimeError, match="whisperx is not installed"):
        adapter.align(tmp_path / "narration.wav", device="cpu", compute_type="int8")


def _write_recording_worker(path: Path, *, cuda_available: bool) -> Path:
    """A fake worker that records the request it received to a sibling file."""

    path.write_text(
        "import json, sys\n"
        "from pathlib import Path\n"
        "request = json.loads(sys.stdin.read())\n"
        f"(Path(r'{path.parent}') / 'last_request.json').write_text(json.dumps(request))\n"
        "if request['operation'] == 'probe':\n"
        "    print(json.dumps({\n"
        "        'cuda_available': " + ("True" if cuda_available else "False") + ",\n"
        "        'recommended_device': " + ("'cuda'" if cuda_available else "'cpu'") + ",\n"
        "        'recommended_compute_type': "
        + ("'float16'" if cuda_available else "'int8'")
        + ",\n"
        "    }))\n"
        "elif request['operation'] == 'align':\n"
        "    print(json.dumps({'engine':'whisperx','engine_version':'fixture',"
        "'model':request['model'],'language':'eng','audio_duration_seconds':1.0,"
        "'words':[],'warnings':[]}))\n"
        "else:\n"
        "    print(json.dumps({'unloaded': True}))\n",
        encoding="utf-8",
    )
    return path


def test_align_auto_device_falls_back_to_cpu_when_cuda_unavailable(tmp_path: Path) -> None:
    worker = _write_recording_worker(tmp_path / "fake_worker.py", cuda_available=False)
    adapter = ExternalAlignmentWorker((sys.executable, str(worker)))
    adapter.align(tmp_path / "audio.wav", model="small")
    sent = json.loads((tmp_path / "last_request.json").read_text())
    assert sent["device"] == "cpu"
    assert sent["compute_type"] == "int8"


def test_align_auto_device_uses_cuda_when_available(tmp_path: Path) -> None:
    worker = _write_recording_worker(tmp_path / "fake_worker.py", cuda_available=True)
    adapter = ExternalAlignmentWorker((sys.executable, str(worker)))
    adapter.align(tmp_path / "audio.wav", model="small")
    sent = json.loads((tmp_path / "last_request.json").read_text())
    assert sent["device"] == "cuda"
    assert sent["compute_type"] == "float16"


def test_align_explicit_device_bypasses_auto_resolution(tmp_path: Path) -> None:
    # The fake worker's probe would recommend "cuda", but an explicit device
    # must not be overridden by the auto-fallback logic.
    worker = _write_recording_worker(tmp_path / "fake_worker.py", cuda_available=True)
    adapter = ExternalAlignmentWorker((sys.executable, str(worker)))
    adapter.align(tmp_path / "audio.wav", model="small", device="cpu", compute_type="int8")
    sent = json.loads((tmp_path / "last_request.json").read_text())
    assert sent["device"] == "cpu"
    assert sent["compute_type"] == "int8"
