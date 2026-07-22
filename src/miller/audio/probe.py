"""FFprobe-backed validation and non-destructive audio normalization."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ..artifacts import sha256_file
from .models import AudioMetadata, NormalizedAudio


class AudioProbeError(RuntimeError):
    pass


class AudioTools:
    def __init__(self, ffmpeg: str | None = None, ffprobe: str | None = None) -> None:
        self.ffmpeg = ffmpeg or shutil.which("ffmpeg") or ""
        self.ffprobe = ffprobe or shutil.which("ffprobe") or ""
        if not self.ffmpeg or not self.ffprobe:
            raise AudioProbeError("FFmpeg and FFprobe must both be installed")

    def inspect(self, path: Path | str) -> AudioMetadata:
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        result = subprocess.run(
            [
                self.ffprobe,
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(source),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 0:
            raise AudioProbeError(f"FFprobe failed: {result.stderr[-2000:]}")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AudioProbeError("FFprobe returned invalid JSON") from exc
        streams = payload.get("streams") if isinstance(payload, dict) else None
        format_data = payload.get("format") if isinstance(payload, dict) else None
        if not isinstance(streams, list) or not isinstance(format_data, dict):
            raise AudioProbeError("FFprobe response is missing streams or format")
        audio_streams = [
            stream
            for stream in streams
            if isinstance(stream, dict) and stream.get("codec_type") == "audio"
        ]
        if len(audio_streams) != 1:
            raise AudioProbeError("audio input must contain exactly one audio stream")
        stream = audio_streams[0]
        duration_raw = stream.get("duration") or format_data.get("duration")
        if duration_raw is None:
            raise AudioProbeError("audio duration is unavailable")
        bit_rate_raw = stream.get("bit_rate") or format_data.get("bit_rate")
        return AudioMetadata(
            path=str(source),
            duration_seconds=float(duration_raw),
            codec=str(stream.get("codec_name") or "unknown"),
            sample_rate=int(stream.get("sample_rate") or 0),
            channels=int(stream.get("channels") or 0),
            bit_rate=int(bit_rate_raw) if bit_rate_raw else None,
            format_name=str(format_data.get("format_name") or "unknown"),
            ffprobe_version=self._version(self.ffprobe),
        )

    def normalize(
        self,
        source: Path | str,
        output: Path | str,
        *,
        sample_rate: int = 16_000,
        channels: int = 1,
    ) -> NormalizedAudio:
        source_path = Path(source).expanduser().resolve()
        output_path = Path(output).expanduser().resolve()
        self.inspect(source_path)
        if output_path == source_path:
            raise ValueError("normalized audio output must not overwrite source")
        if output_path.exists():
            raise FileExistsError(f"normalized audio output already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            self.ffmpeg,
            "-hide_banner",
            "-y",
            "-v",
            "error",
            "-i",
            str(source_path),
            "-vn",
            "-ac",
            str(channels),
            "-ar",
            str(sample_rate),
            "-c:a",
            "pcm_s16le",
            "-map_metadata",
            "-1",
            str(output_path),
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        if result.returncode != 0:
            output_path.unlink(missing_ok=True)
            raise AudioProbeError(f"FFmpeg normalization failed: {result.stderr[-2000:]}")
        normalized = self.inspect(output_path)
        if normalized.sample_rate != sample_rate or normalized.channels != channels:
            raise AudioProbeError("normalized audio does not match requested format")
        return NormalizedAudio(
            source_path=str(source_path),
            output_path=str(output_path),
            source_sha256=sha256_file(source_path),
            output_sha256=sha256_file(output_path),
            sample_rate=sample_rate,
            channels=channels,
            ffmpeg_version=self._version(self.ffmpeg),
            command=tuple(command),
        )

    @staticmethod
    def _version(executable: str) -> str:
        result = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if result.returncode != 0:
            raise AudioProbeError(f"unable to query version for {executable}")
        output = (result.stdout or result.stderr).splitlines()
        return output[0].strip() if output else "unknown"
