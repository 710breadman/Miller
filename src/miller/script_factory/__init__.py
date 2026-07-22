"""Evidence-led local script factory."""

from .factory import ScriptFactory, ScriptFactoryService
from .generator import OllamaGenerator, StructuredGenerator, StubGenerator
from .models import (
    DraftResponse,
    EvidenceClaim,
    EvidenceLedger,
    EvidenceSource,
    FramingCandidate,
    HumanizedResponse,
    OutlineSection,
    ResearchResult,
    ScriptFactoryRequest,
    ScriptOutline,
    ScriptPackage,
    SourceKind,
    SupportLevel,
    VerificationFinding,
    VerificationResponse,
)
from .providers import LocalTextProvider, ResearchProvider

__all__ = [
    "DraftResponse",
    "EvidenceClaim",
    "EvidenceLedger",
    "EvidenceSource",
    "FramingCandidate",
    "HumanizedResponse",
    "LocalTextProvider",
    "OllamaGenerator",
    "OutlineSection",
    "ResearchProvider",
    "ResearchResult",
    "ScriptFactory",
    "ScriptFactoryRequest",
    "ScriptFactoryService",
    "ScriptOutline",
    "ScriptPackage",
    "SourceKind",
    "StructuredGenerator",
    "StubGenerator",
    "SupportLevel",
    "VerificationFinding",
    "VerificationResponse",
]
