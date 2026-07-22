"""Search scope, candidate ranking, and automatic storyboard creation."""

from .builder import StoryboardBuilder
from .models import (
    CameraPlan,
    CameraPreset,
    SceneCandidate,
    SceneScore,
    SearchScope,
    StoryboardPlan,
    StoryboardScene,
    TransitionPreset,
)
from .scope import propose_search_scope

__all__ = [
    "CameraPlan",
    "CameraPreset",
    "SceneCandidate",
    "SceneScore",
    "SearchScope",
    "StoryboardBuilder",
    "StoryboardPlan",
    "StoryboardScene",
    "TransitionPreset",
    "propose_search_scope",
]
