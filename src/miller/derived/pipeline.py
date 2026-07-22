"""Content-addressed clean-crop and inpainting fallback chain."""

from __future__ import annotations

import io
from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

from ..analysis import PanelCandidate, TextRegion, render_region_mask
from ..artifacts import sha256_bytes, sha256_file
from ..comics.common import atomic_write
from .crops import choose_clean_crop
from .models import DerivedAsset, DerivedMethod
from .worker import ExternalInpaintWorker


class DerivedAssetPipeline:
    def __init__(self, workspace: Path | str) -> None:
        self.workspace = Path(workspace).expanduser().resolve()

    def derive(
        self,
        source_path: Path | str,
        text_regions: Iterable[TextRegion],
        *,
        target_aspect: float,
        panels: Iterable[PanelCandidate] = (),
        external_worker: ExternalInpaintWorker | None = None,
        clean_crop_threshold: float = 0.005,
    ) -> DerivedAsset:
        source = Path(source_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        source_hash = sha256_file(source)
        regions = tuple(text_regions)
        choice = choose_clean_crop(regions, target_aspect=target_aspect, panels=panels)
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
        cropped = self._crop(image, choice.box)
        if choice.text_coverage <= clean_crop_threshold:
            return self._store(
                source,
                source_hash,
                cropped,
                method=DerivedMethod.CLEAN_CROP,
                crop=choice.box,
                mask_sha256=None,
                tool="miller-clean-crop",
                tool_version="1",
            )
        mask = render_region_mask(image.width, image.height, regions, padding_pixels=3)
        warnings: list[str] = []
        if external_worker is not None:
            try:
                return self._external_inpaint(
                    source,
                    source_hash,
                    image,
                    mask.payload,
                    choice.box,
                    mask.sha256,
                    external_worker,
                )
            except Exception as exc:
                warnings.append(f"external inpaint failed: {exc}")
        if regions:
            filled = self._simple_fill(image, mask.payload)
            filled_crop = self._crop(filled, choice.box)
            return self._store(
                source,
                source_hash,
                filled_crop,
                method=DerivedMethod.SIMPLE_FILL,
                crop=choice.box,
                mask_sha256=mask.sha256,
                tool="miller-simple-fill",
                tool_version="1",
                warnings=tuple(warnings),
            )
        warnings.append("no text regions were available")
        return self._store(
            source,
            source_hash,
            cropped,
            method=DerivedMethod.ORIGINAL_FALLBACK,
            crop=choice.box,
            mask_sha256=None,
            tool="miller-original-fallback",
            tool_version="1",
            warnings=tuple(warnings),
        )

    def _external_inpaint(
        self,
        source: Path,
        source_hash: str,
        image: Image.Image,
        mask_payload: bytes,
        crop: object,
        mask_hash: str,
        worker: ExternalInpaintWorker,
    ) -> DerivedAsset:
        from ..analysis import NormalizedBox

        if not isinstance(crop, NormalizedBox):
            raise TypeError("crop must be a normalized box")
        temporary_root = self.workspace / "tmp" / "inpaint" / source_hash[:16]
        temporary_root.mkdir(parents=True, exist_ok=True)
        mask_path = temporary_root / "mask.png"
        output_path = temporary_root / "output.png"
        atomic_write(mask_path, mask_payload)
        worker.inpaint(source, mask_path, output_path)
        if not output_path.is_file():
            raise RuntimeError("external inpaint worker produced no output")
        with Image.open(output_path) as opened:
            result = ImageOps.exif_transpose(opened).convert("RGB")
        if result.size != image.size:
            raise RuntimeError("external inpaint changed image dimensions")
        return self._store(
            source,
            source_hash,
            self._crop(result, crop),
            method=DerivedMethod.EXTERNAL_INPAINT,
            crop=crop,
            mask_sha256=mask_hash,
            tool="external-inpaint-worker",
            tool_version=str(worker.probe().get("version", "unknown")),
        )

    def _store(
        self,
        source: Path,
        source_hash: str,
        image: Image.Image,
        *,
        method: DerivedMethod,
        crop: object,
        mask_sha256: str | None,
        tool: str,
        tool_version: str,
        warnings: tuple[str, ...] = (),
    ) -> DerivedAsset:
        from ..analysis import NormalizedBox

        if not isinstance(crop, NormalizedBox):
            raise TypeError("crop must be a normalized box")
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=False, compress_level=9)
        payload = output.getvalue()
        digest = sha256_bytes(payload)
        target = self.workspace / "cache" / "derived" / digest[:2] / f"{digest}.png"
        self._assert_managed(target)
        if target.exists():
            if sha256_file(target) != digest:
                raise RuntimeError(f"derived asset failed integrity check: {target}")
        else:
            atomic_write(target, payload)
        return DerivedAsset(
            source_path=str(source),
            source_sha256=source_hash,
            output_path=str(target),
            output_sha256=digest,
            method=method,
            crop=crop,
            mask_sha256=mask_sha256,
            tool=tool,
            tool_version=tool_version,
            warnings=warnings,
        )

    @staticmethod
    def _crop(image: Image.Image, box: object) -> Image.Image:
        from ..analysis import NormalizedBox

        if not isinstance(box, NormalizedBox):
            raise TypeError("box must be a normalized box")
        left = round(box.x * image.width)
        top = round(box.y * image.height)
        right = round((box.x + box.width) * image.width)
        bottom = round((box.y + box.height) * image.height)
        return image.crop((left, top, right, bottom))

    @staticmethod
    def _simple_fill(image: Image.Image, mask_payload: bytes) -> Image.Image:
        with Image.open(io.BytesIO(mask_payload)) as mask_opened:
            mask = mask_opened.convert("L")
        blurred = image.filter(ImageFilter.GaussianBlur(radius=14))
        feathered = mask.filter(ImageFilter.GaussianBlur(radius=2))
        return Image.composite(blurred, image, feathered)

    def _assert_managed(self, path: Path) -> None:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError(f"derived path escapes managed workspace: {resolved}") from exc
