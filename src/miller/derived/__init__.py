"""Clean-crop selection and reproducible derived comic assets."""

from .crops import choose_clean_crop
from .models import CropCandidate, DerivedAsset, DerivedMethod
from .pipeline import DerivedAssetPipeline
from .worker import ExternalInpaintWorker

__all__ = [
    "CropCandidate",
    "DerivedAsset",
    "DerivedAssetPipeline",
    "DerivedMethod",
    "ExternalInpaintWorker",
    "choose_clean_crop",
]
