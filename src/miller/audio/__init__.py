"""Audio inspection, alignment worker boundaries, comparison, and beat timing."""

from .beats import build_beat_plan
from .compare import compare_script_to_audio, normalized_words
from .models import (
    AlignmentResult,
    AudioMetadata,
    BeatPlan,
    NarrationBeat,
    NormalizedAudio,
    ScriptComparison,
    ScriptDifference,
    ScriptDifferenceKind,
    WordTiming,
)
from .normalize import normalize_alignment_words
from .probe import AudioProbeError, AudioTools
from .uniform import uniform_alignment
from .whisper_worker import ExternalAlignmentWorker

__all__ = [
    "AlignmentResult",
    "AudioMetadata",
    "AudioProbeError",
    "AudioTools",
    "BeatPlan",
    "ExternalAlignmentWorker",
    "NarrationBeat",
    "NormalizedAudio",
    "ScriptComparison",
    "ScriptDifference",
    "ScriptDifferenceKind",
    "WordTiming",
    "build_beat_plan",
    "compare_script_to_audio",
    "normalize_alignment_words",
    "normalized_words",
    "uniform_alignment",
]
