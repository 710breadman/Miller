"""Replaceable OCR contract and a Tesseract TSV subprocess adapter."""

from __future__ import annotations

import csv
import hashlib
import io
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from PIL import Image

from .models import NormalizedBox, OcrResult, OcrSpan


class OcrAdapter(Protocol):
    def capability(self) -> tuple[bool, str]: ...

    def recognize(self, image_path: Path | str, *, language: str = "eng") -> OcrResult: ...


class TesseractOcrAdapter:
    """Call Tesseract through its stable TSV output instead of parsing prose."""

    def __init__(
        self,
        command: Sequence[str] | None = None,
        *,
        timeout_seconds: int = 120,
        minimum_confidence: float = 0.0,
    ) -> None:
        self.command: tuple[str, ...]
        if command is None:
            executable = shutil.which("tesseract")
            self.command = (executable,) if executable else ()
        else:
            self.command = tuple(command)
        self.timeout_seconds = timeout_seconds
        self.minimum_confidence = minimum_confidence

    def capability(self) -> tuple[bool, str]:
        if not self.command:
            return False, "Tesseract executable was not found"
        try:
            result = subprocess.run(
                [*self.command, "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, str(exc)
        output = (result.stdout or result.stderr).splitlines()
        return result.returncode == 0, output[0].strip() if output else "unknown"

    def recognize(self, image_path: Path | str, *, language: str = "eng") -> OcrResult:
        path = Path(image_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        available, version = self.capability()
        if not available:
            raise RuntimeError(version)
        with Image.open(path) as image:
            width, height = image.size
        result = subprocess.run(
            [*self.command, str(path), "stdout", "-l", language, "tsv"],
            capture_output=True,
            text=True,
            check=False,
            timeout=self.timeout_seconds,
        )
        if result.returncode != 0:
            detail = result.stderr[-2000:]
            raise RuntimeError(f"Tesseract failed with exit {result.returncode}: {detail}")
        spans: list[OcrSpan] = []
        reader = csv.DictReader(io.StringIO(result.stdout), delimiter="\t")
        for row in reader:
            text = (row.get("text") or "").strip()
            if not text:
                continue
            try:
                confidence_raw = float(row.get("conf") or -1)
                left = int(row.get("left") or 0)
                top = int(row.get("top") or 0)
                box_width = int(row.get("width") or 0)
                box_height = int(row.get("height") or 0)
            except ValueError:
                continue
            confidence = max(0.0, min(1.0, confidence_raw / 100.0))
            if confidence < self.minimum_confidence or box_width <= 0 or box_height <= 0:
                continue
            normalized_x = max(0.0, min(1.0 - 1e-9, left / width))
            normalized_y = max(0.0, min(1.0 - 1e-9, top / height))
            normalized = NormalizedBox(
                x=normalized_x,
                y=normalized_y,
                width=min(1.0 - normalized_x, box_width / width),
                height=min(1.0 - normalized_y, box_height / height),
            )
            line_key = ".".join(
                str(row.get(field) or "0")
                for field in ("block_num", "par_num", "line_num")
            )
            spans.append(
                OcrSpan(
                    id=f"ocr_{len(spans):05d}",
                    text=text,
                    box=normalized,
                    confidence=confidence,
                    language=language,
                    line_index=int(hashlib.sha256(line_key.encode("utf-8")).hexdigest()[:8], 16),
                )
            )
        return OcrResult(
            engine="tesseract",
            engine_version=version,
            language=language,
            spans=tuple(spans),
        )
