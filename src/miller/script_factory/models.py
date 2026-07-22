"""Typed sourced-script artifacts and generation responses."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..models import utc_now


class ScriptModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SourceKind(StrEnum):
    LOCAL = "local"
    WEB = "web"
    COMIC = "comic"
    USER = "user"


class SupportLevel(StrEnum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    CONTRADICTED = "contradicted"
    UNVERIFIED = "unverified"


class ResearchResult(ScriptModel):
    id: str = Field(min_length=1)
    kind: SourceKind
    title: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    score: float = Field(ge=0)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class EvidenceSource(ScriptModel):
    id: str = Field(pattern=r"^source_[A-Za-z0-9_.-]+$")
    kind: SourceKind
    title: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    retrieved_at: datetime = Field(default_factory=utc_now)


class EvidenceClaim(ScriptModel):
    id: str = Field(pattern=r"^claim_[A-Za-z0-9_.-]+$")
    statement: str = Field(min_length=1)
    source_ids: tuple[str, ...]
    support: SupportLevel
    confidence: float = Field(ge=0, le=1)
    used_in_sections: tuple[str, ...] = ()

    @field_validator("source_ids")
    @classmethod
    def require_sources(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("claim requires at least one source")
        if len(value) != len(set(value)):
            raise ValueError("claim source IDs must be unique")
        return value


class EvidenceLedger(ScriptModel):
    sources: tuple[EvidenceSource, ...]
    claims: tuple[EvidenceClaim, ...]

    @model_validator(mode="after")
    def validate_references(self) -> EvidenceLedger:
        source_ids = {source.id for source in self.sources}
        claim_ids = [claim.id for claim in self.claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("claim IDs must be unique")
        unknown = {
            source_id
            for claim in self.claims
            for source_id in claim.source_ids
            if source_id not in source_ids
        }
        if unknown:
            raise ValueError(f"claims reference unknown sources: {sorted(unknown)}")
        return self


class FramingCandidate(ScriptModel):
    id: str = Field(pattern=r"^frame_[0-9]{2}$")
    thesis: str = Field(min_length=1)
    viewer_promise: str = Field(min_length=1)
    claim_ids: tuple[str, ...]
    confidence: float = Field(ge=0, le=1)


class FramingResponse(ScriptModel):
    candidates: tuple[FramingCandidate, ...]

    @field_validator("candidates")
    @classmethod
    def require_candidates(
        cls, value: tuple[FramingCandidate, ...]
    ) -> tuple[FramingCandidate, ...]:
        if not value:
            raise ValueError("at least one framing candidate is required")
        return value


class OutlineSection(ScriptModel):
    id: str = Field(pattern=r"^section_[0-9]{2}$")
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    claim_ids: tuple[str, ...]
    target_words: int = Field(ge=20)


class ScriptOutline(ScriptModel):
    title: str = Field(min_length=1)
    thesis: str = Field(min_length=1)
    sections: tuple[OutlineSection, ...]

    @field_validator("sections")
    @classmethod
    def require_sections(cls, value: tuple[OutlineSection, ...]) -> tuple[OutlineSection, ...]:
        if not value:
            raise ValueError("outline requires sections")
        expected = [f"section_{index:02d}" for index in range(1, len(value) + 1)]
        if [section.id for section in value] != expected:
            raise ValueError("outline section IDs must be contiguous")
        return value


class DraftResponse(ScriptModel):
    text: str = Field(min_length=1)
    claim_ids_used: tuple[str, ...]


class VerificationFinding(ScriptModel):
    kind: str = Field(min_length=1)
    message: str = Field(min_length=1)
    claim_id: str | None = None
    severity: str = Field(pattern=r"^(info|warning|error)$")


class VerificationResponse(ScriptModel):
    text: str = Field(min_length=1)
    claim_ids_used: tuple[str, ...]
    findings: tuple[VerificationFinding, ...] = ()


class HumanizedResponse(ScriptModel):
    text: str = Field(min_length=1)
    claim_ids_used: tuple[str, ...]


class ScriptFactoryRequest(ScriptModel):
    briefing: str = Field(min_length=1)
    ledger: EvidenceLedger
    selected_frame_id: str | None = None
    style: str = Field(default="video essay", min_length=1)
    target_words: int = Field(default=1500, ge=100, le=20_000)


class ScriptPackage(ScriptModel):
    framing: FramingCandidate
    outline: ScriptOutline
    draft: DraftResponse
    verified: VerificationResponse
    final: HumanizedResponse
    generator_name: str
    generator_version: str | None = None

    @model_validator(mode="after")
    def preserve_evidence(self) -> ScriptPackage:
        verified = set(self.verified.claim_ids_used)
        final = set(self.final.claim_ids_used)
        if not final.issubset(verified):
            raise ValueError("humanization introduced unsupported claim IDs")
        return self
