"""Sourced, validated, repeatable script-production stages."""

from __future__ import annotations

import json

from ..db import Database
from .generator import StructuredGenerator
from .models import (
    DraftResponse,
    EvidenceLedger,
    FramingCandidate,
    FramingResponse,
    HumanizedResponse,
    ScriptFactoryRequest,
    ScriptOutline,
    ScriptPackage,
    VerificationResponse,
)

_SYSTEM = (
    "Return only the requested structured object. Preserve source claim IDs. "
    "Do not invent evidence, quotations, issue locators, or factual claims."
)


class ScriptFactory:
    def __init__(self, generator: StructuredGenerator) -> None:
        self.generator = generator

    def run(self, request: ScriptFactoryRequest) -> ScriptPackage:
        framing_response = self.generator.generate(
            FramingResponse,
            system=_SYSTEM,
            prompt=self._framing_prompt(request.briefing, request.ledger),
        )
        framing = self._select_frame(framing_response, request)
        self._validate_claim_ids(framing.claim_ids, request.ledger)

        outline = self.generator.generate(
            ScriptOutline,
            system=_SYSTEM,
            prompt=self._outline_prompt(framing, request),
        )
        for section in outline.sections:
            self._validate_claim_ids(section.claim_ids, request.ledger)

        draft = self.generator.generate(
            DraftResponse,
            system=_SYSTEM,
            prompt=self._draft_prompt(outline, request),
        )
        self._validate_claim_ids(draft.claim_ids_used, request.ledger)

        verified = self.generator.generate(
            VerificationResponse,
            system=_SYSTEM,
            prompt=self._verify_prompt(draft, request.ledger),
        )
        self._validate_claim_ids(verified.claim_ids_used, request.ledger)
        if any(finding.severity == "error" for finding in verified.findings):
            raise ValueError("verified script still contains error-severity findings")

        final = self.generator.generate(
            HumanizedResponse,
            system=_SYSTEM,
            prompt=self._humanize_prompt(verified, request),
        )
        self._validate_claim_ids(final.claim_ids_used, request.ledger)
        return ScriptPackage(
            framing=framing,
            outline=outline,
            draft=draft,
            verified=verified,
            final=final,
            generator_name=self.generator.name,
            generator_version=self.generator.version,
        )

    @staticmethod
    def _select_frame(
        response: FramingResponse, request: ScriptFactoryRequest
    ) -> FramingCandidate:
        if request.selected_frame_id is None:
            return max(response.candidates, key=lambda item: item.confidence)
        for candidate in response.candidates:
            if candidate.id == request.selected_frame_id:
                return candidate
        raise ValueError(f"selected framing does not exist: {request.selected_frame_id}")

    @staticmethod
    def _validate_claim_ids(claim_ids: tuple[str, ...], ledger: EvidenceLedger) -> None:
        known = {claim.id for claim in ledger.claims}
        unknown = set(claim_ids) - known
        if unknown:
            raise ValueError(f"generated stage references unknown claims: {sorted(unknown)}")

    @staticmethod
    def _framing_prompt(briefing: str, ledger: EvidenceLedger) -> str:
        evidence = json.dumps(ledger.model_dump(mode="json"), sort_keys=True)
        return (
            "Propose 3 evidence-backed angles.\nBriefing:\n"
            + briefing
            + "\nEvidence:\n"
            + evidence
        )

    @staticmethod
    def _outline_prompt(frame: FramingCandidate, request: ScriptFactoryRequest) -> str:
        return (
            f"Create a {request.target_words}-word {request.style} outline.\n"
            f"Frame:\n{frame.model_dump_json()}\nEvidence:\n"
            + request.ledger.model_dump_json()
        )

    @staticmethod
    def _draft_prompt(outline: ScriptOutline, request: ScriptFactoryRequest) -> str:
        return (
            f"Draft a natural spoken {request.style} script. "
            "Cite evidence internally by claim ID.\n"
            f"Outline:\n{outline.model_dump_json()}\nEvidence:\n"
            + request.ledger.model_dump_json()
        )

    @staticmethod
    def _verify_prompt(draft: DraftResponse, ledger: EvidenceLedger) -> str:
        return (
            "Remove, qualify, or flag every unsupported statement. Do not add new claims.\n"
            f"Draft:\n{draft.model_dump_json()}\nEvidence:\n{ledger.model_dump_json()}"
        )

    @staticmethod
    def _humanize_prompt(verified: VerificationResponse, request: ScriptFactoryRequest) -> str:
        return (
            "Improve spoken rhythm, transitions, clarity, and repetition without adding claims.\n"
            f"Style: {request.style}\nTarget words: {request.target_words}\n"
            f"Verified script:\n{verified.model_dump_json()}"
        )


class ScriptFactoryService:
    """Run the factory and save every stage as a revisioned project document."""

    def __init__(self, database: Database, factory: ScriptFactory) -> None:
        self.database = database
        self.factory = factory

    def run(self, project_id: str, request: ScriptFactoryRequest) -> ScriptPackage:
        package = self.factory.run(request)
        documents = {
            "script.evidence": request.ledger.model_dump(mode="json"),
            "script.framing": package.framing.model_dump(mode="json"),
            "script.outline": package.outline.model_dump(mode="json"),
            "script.draft": package.draft.model_dump(mode="json"),
            "script.verified": package.verified.model_dump(mode="json"),
            "script.final": package.final.model_dump(mode="json"),
        }
        for kind, document in documents.items():
            try:
                revision = self.database.get_document(project_id, kind).revision
            except KeyError:
                revision = 0
            self.database.put_document(
                project_id,
                kind,
                document,
                expected_revision=revision,
            )
        return package
