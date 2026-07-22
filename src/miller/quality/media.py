"""Technical checks over rendered media and its declared specification."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from ..video import ManualVideoSpec, RenderResult
from .models import FindingCategory, FindingSeverity, QualityFinding, QualityReport

_BLACK_DURATION = re.compile(r"black_duration:([0-9.]+)")
_MAX_VOLUME = re.compile(r"max_volume:\s*(-?[0-9.]+) dB")


class RenderQualityEvaluator:
    def __init__(self, ffmpeg: str | None = None) -> None:
        self.ffmpeg = ffmpeg or shutil.which("ffmpeg") or ""

    def evaluate(
        self,
        result: RenderResult,
        spec: ManualVideoSpec,
        *,
        pass_index: int = 0,
    ) -> QualityReport:
        findings: list[QualityFinding] = []
        output = Path(result.output_path)
        if not output.is_file() or output.stat().st_size == 0:
            findings.append(
                self._finding(
                    findings,
                    FindingCategory.MISSING_MEDIA,
                    FindingSeverity.BLOCKING,
                    "Rendered output is missing or empty.",
                    {},
                )
            )
            return QualityReport(pass_index=pass_index, score=0.0, findings=tuple(findings))
        streams = result.probe.get("streams")
        streams = streams if isinstance(streams, list) else []
        stream_types = [
            stream.get("codec_type")
            for stream in streams
            if isinstance(stream, dict)
        ]
        if stream_types.count("video") != 1:
            findings.append(
                self._finding(
                    findings,
                    FindingCategory.STREAM_LAYOUT,
                    FindingSeverity.BLOCKING,
                    "Output must contain exactly one video stream.",
                    {"video_streams": stream_types.count("video")},
                )
            )
        expects_audio = spec.narration_path is not None or spec.music_path is not None
        if expects_audio and stream_types.count("audio") != 1:
            findings.append(
                self._finding(
                    findings,
                    FindingCategory.STREAM_LAYOUT,
                    FindingSeverity.ERROR,
                    "Expected audio stream is missing or duplicated.",
                    {"audio_streams": stream_types.count("audio")},
                )
            )
        expected_duration = sum(scene.duration_seconds for scene in spec.scenes)
        actual_duration = self._duration(result)
        difference = abs(actual_duration - expected_duration)
        if difference > max(0.12, 1 / spec.profile.fps * 2):
            findings.append(
                self._finding(
                    findings,
                    FindingCategory.DURATION_MISMATCH,
                    FindingSeverity.ERROR,
                    "Rendered duration differs from the scene plan.",
                    {
                        "expected_seconds": expected_duration,
                        "actual_seconds": actual_duration,
                        "difference_seconds": difference,
                    },
                )
            )
        if self.ffmpeg:
            black_duration = self._black_duration(output)
            if black_duration > max(0.5, expected_duration * 0.08):
                findings.append(
                    self._finding(
                        findings,
                        FindingCategory.BLACK_FRAMES,
                        FindingSeverity.ERROR,
                        "Output contains an excessive black-frame duration.",
                        {"black_duration_seconds": black_duration},
                    )
                )
            if expects_audio:
                max_volume = self._max_volume(output)
                if max_volume is not None and max_volume >= -0.1:
                    findings.append(
                        self._finding(
                            findings,
                            FindingCategory.AUDIO_CLIPPING,
                            FindingSeverity.WARNING,
                            "Audio peaks are too close to digital full scale.",
                            {"max_volume_db": max_volume},
                        )
                    )
        penalties = {
            FindingSeverity.INFO: 0.01,
            FindingSeverity.WARNING: 0.06,
            FindingSeverity.ERROR: 0.16,
            FindingSeverity.BLOCKING: 0.40,
        }
        score = max(0.0, 1.0 - sum(penalties[item.severity] for item in findings))
        return QualityReport(pass_index=pass_index, score=score, findings=tuple(findings))

    def _black_duration(self, output: Path) -> float:
        result = subprocess.run(
            [
                self.ffmpeg,
                "-hide_banner",
                "-i",
                str(output),
                "-vf",
                "blackdetect=d=0.15:pix_th=0.10",
                "-an",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        return sum(float(match) for match in _BLACK_DURATION.findall(result.stderr))

    def _max_volume(self, output: Path) -> float | None:
        result = subprocess.run(
            [
                self.ffmpeg,
                "-hide_banner",
                "-i",
                str(output),
                "-vn",
                "-af",
                "volumedetect",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        match = _MAX_VOLUME.search(result.stderr)
        return float(match.group(1)) if match else None

    @staticmethod
    def _duration(result: RenderResult) -> float:
        format_data = result.probe.get("format")
        if isinstance(format_data, dict) and format_data.get("duration") is not None:
            return float(format_data["duration"])
        return result.duration_seconds

    @staticmethod
    def _finding(
        existing: list[QualityFinding],
        category: FindingCategory,
        severity: FindingSeverity,
        message: str,
        evidence: dict[str, str | int | float | bool],
    ) -> QualityFinding:
        return QualityFinding(
            id=f"finding_{len(existing) + 1:04d}",
            category=category,
            severity=severity,
            message=message,
            evidence=evidence,
            suggested_action="rerender affected output",
        )
